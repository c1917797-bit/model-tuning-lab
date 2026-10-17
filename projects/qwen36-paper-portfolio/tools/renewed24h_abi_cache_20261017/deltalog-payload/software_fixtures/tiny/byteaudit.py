"""Actual-storage byte alias and bounded CPU streaming comparison preparation.

No owner/admission/lease is created here. NPU API support remains unverified.
Hash authenticates the baseline; the inactive equality decision is BYTEWISE.
"""
import hashlib
import json
import os
from pathlib import Path

GIB = 1024**3
WORKSPACE_CAP = 32 * GIB
TOTAL_CAP = 80 * GIB
DISK_RESERVE = int(8.5 * GIB)
OVERHEAD_RESERVE = 16 * 1024**2
CHUNK_BYTES = 1024**2


class Refusal(RuntimeError):
    pass


class ByteMismatch(Refusal):
    pass


def need(v, why):
    if not v:
        raise Refusal(why)


def whole_storage_bytes(torch, exemplar, format_getter, *, device='npu'):
    """set_(actual UntypedStorage, byte offset0, full nbytes, stride1).

    CPU device option exists only for explicit software API tests. NativeReader
    always passes literal device='npu', never caller/JSON-selected device.
    No clone of the GPU pool. Native storage's exposed tail/alignment bytes are
    included; unexposed allocator capacity is NOT claimed as addressable proof.
    """
    need(type(exemplar) is torch.Tensor and exemplar.device.type == device,
         'actual tensor on explicit test/native device only')
    need(int(format_getter(exemplar)) == 2, 'actual source view unpacked ND2 required')
    storage = exemplar.untyped_storage()
    identity = (storage.data_ptr(), storage.nbytes(), exemplar.data_ptr(), exemplar.storage_offset(),
                tuple(exemplar.shape), tuple(exemplar.stride()), exemplar.element_size())
    ptr, size = identity[:2]
    need(type(ptr) is int and ptr > 0 and type(size) is int and size > 0, 'actual nonempty storage extent')
    need(exemplar.data_ptr() == ptr + exemplar.storage_offset()*exemplar.element_size(), 'actual original offset/pointer')
    alias = torch.empty(0, dtype=torch.uint8, device=exemplar.device)
    alias.set_(storage, 0, (size,), (1,))
    need(alias.untyped_storage() is storage and alias.data_ptr() == ptr and alias.storage_offset() == 0
         and alias.dtype == torch.uint8 and tuple(alias.shape) == (size,) and tuple(alias.stride()) == (1,)
         and alias.numel() == alias.untyped_storage().nbytes() == size and int(format_getter(alias)) == 2,
         'full ND2 actual-storage byte alias ABI')
    now = (storage.data_ptr(), storage.nbytes(), exemplar.data_ptr(), exemplar.storage_offset(),
           tuple(exemplar.shape), tuple(exemplar.stride()), exemplar.element_size())
    need(now == identity, 'original typed view/storage changed while making byte alias')
    return alias


def chunk_bytes(torch, alias, begin, end, *, device='npu'):
    need(type(alias) is torch.Tensor and alias.device.type == device and alias.dtype == torch.uint8
         and alias.ndim == 1 and alias.stride() == (1,), 'actual complete byte alias')
    need(type(begin) is int and type(end) is int and 0 <= begin < end <= alias.numel()
         and end-begin <= CHUNK_BYTES, 'bounded exact byte chunk')
    raw = alias[begin:end].detach().cpu().numpy().tobytes()
    need(type(raw) is bytes and len(raw) == end-begin, 'complete actual D2H byte chunk')
    return raw


def plan_budget(per_rank_pool_sizes, existing_committed_bytes, actual_free_bytes):
    """Frozen global arithmetic only, never a resource admission/capability."""
    need(type(per_rank_pool_sizes) is dict and set(per_rank_pool_sizes) == {0,1,2,3}, 'all4 actual pool size vectors required')
    need(all(type(sizes) in (list,tuple) and sizes and all(type(x) is int and x > 0 for x in sizes)
             for sizes in per_rank_pool_sizes.values()), 'exact positive allocation sizes')
    need(type(existing_committed_bytes) is int and existing_committed_bytes >= 0
         and type(actual_free_bytes) is int and actual_free_bytes >= 0, 'fresh ledger/free facts, not booleans')
    payload = sum(sum(x) for x in per_rank_pool_sizes.values())
    requested = payload + OVERHEAD_RESERVE
    need(requested <= WORKSPACE_CAP, 'new experiment whole32GiB cap including failure evidence')
    need(existing_committed_bytes + requested <= TOTAL_CAP, 'original80GiB total commitment cap')
    need(actual_free_bytes >= requested + DISK_RESERVE, 'original8.5GiB live reserve unchanged')
    return dict(payload_bytes=payload, requested_bytes=requested, workspace_cap_bytes=WORKSPACE_CAP,
                total_cap_bytes=TOTAL_CAP, reserve_bytes=DISK_RESERVE, admitted=False,
                fresh_existing_ledger_still_required=True, actual_byte_alias_NPU_verified=False)


def ranges(values, size):
    out = []
    for lo, hi in sorted(values):
        need(type(lo) is int and type(hi) is int and 0 <= lo < hi <= size, 'pool-relative allowed write extent')
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(hi, out[-1][1]))
        else:
            out.append((lo, hi))
    return tuple(out)


def first_inactive_difference(before, after, begin, allowed):
    need(type(before) is bytes and type(after) is bytes and len(before) == len(after), 'exact chunk pair')
    end, cursor = begin+len(before), begin
    for lo, hi in allowed:
        if hi <= cursor:
            continue
        if lo >= end:
            break
        stop = min(lo, end)
        if cursor < stop and before[cursor-begin:stop-begin] != after[cursor-begin:stop-begin]:
            return next(i for i in range(cursor,stop) if before[i-begin] != after[i-begin])
        cursor = max(cursor, min(hi, end))
    if cursor < end and before[cursor-begin:] != after[cursor-begin:]:
        return next(i for i in range(cursor,end) if before[i-begin] != after[i-begin])
    return None


def identity(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def no_symlink_chain(p):
    need(p.is_absolute(), 'absolute exact owned leaf')
    for part in (p, *p.parents):
        need(not part.is_symlink(), 'no symlink in owned snapshot path')


def sync_dir(p):
    # POSIX runtime requires fsync. Windows software tests cannot open dirs;
    # this does not count as an actual Linux durability result.
    if os.name == 'nt':
        return
    fd = os.open(str(p), os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class Store:
    """Small streaming helper, not an owner/controller or independent grant.

    Caller must obtain a NEW explicit scope/whole32GiB+total80GiB/reserve ticket.
    The old 4GiB owner is not reused/expanded by constructing this object.
    max_bytes is the exact per-worker share frozen by that future global plan.
    """
    def __init__(self, root, max_bytes):
        root = Path(root)
        no_symlink_chain(root)
        need(root.parent.is_dir() and not root.exists(), 'new no-overwrite snapshot leaf')
        need(type(max_bytes) is int and 0 < max_bytes <= WORKSPACE_CAP, 'explicit bounded worker share, not a boolean')
        self.root, self.cap, self.used, self.records = root, max_bytes, 0, {}
        root.mkdir(mode=0o700)
        sync_dir(root.parent)

    def _write_new(self, name, raw):
        need(type(raw) is bytes and self.used + len(raw) <= self.cap, 'snapshot/diff hard cap, retain partial on failure')
        p = self.root/name
        fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            with os.fdopen(fd, 'wb', closefd=False) as out:
                out.write(raw);out.flush();os.fsync(out.fileno())
        finally:
            os.close(fd)
        self.used += len(raw)
        sync_dir(self.root)
        return p

    def before(self, name, size, read_chunk):
        need(type(name) is str and name and name.isascii() and all(c.isalnum() or c in '-_' for c in name), 'fixed snapshot basename only')
        need(name not in self.records and type(size) is int and size > 0 and
             self.used+size+3*CHUNK_BYTES <= self.cap, 'complete baseline plus bounded failure chunks must fit existing share')
        p = self.root/(name+'.before.bin')
        fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        sha = hashlib.sha256()
        try:
            with os.fdopen(fd, 'wb', closefd=False) as out:
                for begin in range(0,size,CHUNK_BYTES):
                    end = min(size,begin+CHUNK_BYTES)
                    raw = read_chunk(begin,end)
                    need(type(raw) is bytes and len(raw) == end-begin, 'complete original pool chunk')
                    need(self.used+len(raw) <= self.cap, 'hard cap while streaming original baseline')
                    out.write(raw);sha.update(raw);self.used += len(raw)
                out.flush();os.fsync(out.fileno())
            st = os.fstat(fd)
            need(st.st_size == size and st.st_nlink == 1, 'actual complete private baseline file')
        finally:
            os.close(fd)
            sync_dir(self.root)  # Preserve even a failed/partial baseline.
        self.records[name] = (p,size,identity(st),sha.hexdigest())
        return dict(path=str(p),bytes=size,sha256=sha.hexdigest())

    def compare(self, name, read_chunk, allowed_writes):
        need(name in self.records, 'actual complete before snapshot required')
        p,size,expected,sha = self.records[name]
        allowed = ranges(allowed_writes,size)
        fd = os.open(str(p), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        first, digest = None, hashlib.sha256()
        try:
            need(identity(os.fstat(fd)) == expected and os.fstat(fd).st_nlink == 1, 'original baseline stable inode/size/time')
            with os.fdopen(fd, 'rb', closefd=False) as old:
                for begin in range(0,size,CHUNK_BYTES):
                    end = min(size,begin+CHUNK_BYTES)
                    before = old.read(end-begin)
                    after = read_chunk(begin,end)
                    need(type(after) is bytes and len(before) == len(after) == end-begin, 'complete actual after chunk')
                    digest.update(before)
                    offset = first_inactive_difference(before,after,begin,allowed)
                    if offset is not None and first is None:
                        # Keep bounded exact byte evidence. Never repair/mutate
                        # the baseline or discard a mismatching byte.
                        bp = self._write_new(name+'.diff-before.bin',before)
                        ap = self._write_new(name+'.diff-after.bin',after)
                        first = dict(offset=offset,chunk_begin=begin,chunk_end=end,
                                     old_byte=before[offset-begin],new_byte=after[offset-begin],
                                     before_chunk=str(bp),after_chunk=str(ap))
                need(old.read(1) == b'', 'no unaccounted baseline tail')
            need(identity(os.fstat(fd)) == expected and digest.hexdigest() == sha,
                 'baseline exact full SHA/stable identity; not data laundering')
        finally:
            os.close(fd)
        report = dict(name=name,baseline=dict(path=str(p),bytes=size,sha256=sha),
                      bytewise_inactive_equal=first is None,first_difference=first,
                      allowed_write_ranges=allowed,NPU_verified=False,qualified=False)
        self._write_new(name+'.comparison.json',(json.dumps(report,sort_keys=True)+'\n').encode())
        if first is not None:
            raise ByteMismatch('actual inactive byte changed at '+str(first['offset']))
        return report


def tiny_npu_api_probe(torch, torch_npu, new_root):
    """For MAIN's separately admitted tiny canary only; never called here.

    Actual typed offset view, complete prefix+tail baseline, legal write then
    forbidden outside write. This is storage ABI proof only, not native cache
    layout/model/numerical qualification. No new owner or automatic run.
    """
    get_format = getattr(torch_npu,'get_npu_format',None)
    need(callable(get_format),'actual get_npu_format API')
    base = torch.arange(70,dtype=torch.float32,device='npu')
    source = base[3:17]
    alias = whole_storage_bytes(torch,source,get_format)
    store = Store(Path(new_root),4*CHUNK_BYTES)
    store.before('tiny-typed-offset',alias.numel(),lambda a,b:chunk_bytes(torch,alias,a,b))
    source[2] = -4.25
    allowed = ((source.storage_offset()*source.element_size(),
                source.storage_offset()*source.element_size()+source.numel()*source.element_size()),)
    store.compare('tiny-typed-offset',lambda a,b:chunk_bytes(torch,alias,a,b),allowed)
    # Different name avoids clobbering either comparison receipt.
    store.before('tiny-outside-negative',alias.numel(),lambda a,b:chunk_bytes(torch,alias,a,b))
    base[0] = -17
    detected = False
    try:
        store.compare('tiny-outside-negative',lambda a,b:chunk_bytes(torch,alias,a,b),allowed)
    except ByteMismatch:
        detected = True
    need(detected,'outside-view prefix mutation must be caught')
    store.before('tiny-tail-negative',alias.numel(),lambda a,b:chunk_bytes(torch,alias,a,b))
    base[-1] = -23
    tail_detected = False
    try: store.compare('tiny-tail-negative',lambda a,b:chunk_bytes(torch,alias,a,b),allowed)
    except ByteMismatch: tail_detected = True
    need(tail_detected,'outside-view storage tail mutation must be caught')
    import struct
    strided=base[3:31:2]
    strided_alias=whole_storage_bytes(torch,strided,get_format)
    geometry=lambda t:(t.data_ptr(),t.storage_offset(),tuple(t.shape),tuple(t.stride()),t.untyped_storage().data_ptr(),t.untyped_storage().nbytes(),int(get_format(t)))
    original_geometry=(geometry(base),geometry(strided),geometry(strided_alias))
    need(strided.storage_offset()==3 and strided.stride()==(2,),'actual noncontinuous typed offset view')
    expected_strided=bytearray(chunk_bytes(torch,strided_alias,0,strided_alias.numel()))
    strided[2]=-99
    expected_strided[28:32]=struct.pack('<f',-99)
    strided_alias[36:40].copy_(torch.tensor(list(struct.pack('<I',2147483648)),dtype=torch.uint8,device='npu:0'))
    expected_strided[36:40]=struct.pack('<I',2147483648)
    need(chunk_bytes(torch,strided_alias,0,strided_alias.numel())==bytes(expected_strided),'both typed source and uint8 alias write exact complete storage bytes')
    need((geometry(base),geometry(strided),geometry(strided_alias))==original_geometry,'source/alias pointer extent stride offset format unchanged after both writes')
    patterns=torch.tensor([2143294004,-2147483648,0,2139095040,-8388608,1065353216],dtype=torch.int32)
    expected=patterns.view(torch.uint8).numpy().tobytes()
    payload=patterns.view(torch.float32).to('npu:0')
    payload_alias=whole_storage_bytes(torch,payload,get_format)
    need(chunk_bytes(torch,payload_alias,0,payload_alias.numel())==expected,'NaN payload and signed zeros must remain byte-exact')
    store.before('tiny-nan-signedzero',payload_alias.numel(),lambda a,b:chunk_bytes(torch,payload_alias,a,b))
    store.compare('tiny-nan-signedzero',lambda a,b:chunk_bytes(torch,payload_alias,a,b),())
    shared=torch.empty(0,dtype=torch.bfloat16,device='npu:0')
    shared.set_(payload.untyped_storage(),2,(4,),(1,))
    shared_alias=whole_storage_bytes(torch,shared,get_format)
    need(shared_alias.untyped_storage() is payload.untyped_storage() and shared.storage_offset()==2 and shared.data_ptr()==payload.data_ptr()+4 and chunk_bytes(torch,shared_alias,0,shared_alias.numel())==expected,'actual shared BF16 offset view complete pool bytes')
    return dict(NPU=True,actual_ND_byte_alias=True,source_storage_offset=source.storage_offset(),
                alias_offset=alias.storage_offset(),complete_storage_bytes=alias.numel(),
                outside_write_negative_detected=True,tail_write_negative_detected=tail_detected,NaN_signed_zero_payload_byteexact=True,shared_BF16_offset_alias_byteexact=True,noncontinuous_typed_view=True,bidirectional_write_byteexact=True,source_alias_geometry_format_unchanged=True,whole_native_pool_verified=False,
                model_qualified=False,performance_qualified=False,task_qualified=False)
