"""Untimed selected-footprint/lifecycle preparation. Public installation blocked.

Only actual live native tensors can enter NativeReader. Serialized observations
are not execution capabilities. No controller, math or numerical gate is added.
"""
import contextvars
import functools
import hashlib
import inspect
import os
from pathlib import Path

ENABLE = 'DL_SELECTED_FOOTPRINT_LIVE_PREP_ENABLE'
CURRENT = contextvars.ContextVar('dl_actual_native_execution_frame', default=None)
MAX_INDEX_VALUES = 1024 * 1024
MAX_SNAPSHOT_BYTES = 32 * 1024**3  # NEW experiment plan only; old4/12GiB sources untouched
RUNNER_SHA = '94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'
BLOCK_SHA = '8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a'
MIRROR_SHA = '32dedd1fae3f93e6dd8a9b6a3d23229448b30b022b9c3182b931e5f7c1f76677'
INTEGRATION_SHA = 'f79c59a28bc626e8efe583baf0c8adf879cc87649c81f31a0e6fbe1cc88307a8'
ROLE_TO_AUX = dict(K='k_log', U='u_log', lambda_log='lambda_log', decay='decay', length='length')
_SEAL = object()


class Refusal(RuntimeError):
    pass


def need(v, why):
    if not v:
        raise Refusal(why)


def digest_file(path, sha):
    p = Path(path)
    raw = p.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == sha, 'whole original source ' + str(p))
    return raw


def static_layer_name(layer, kind):
    need(kind in ('GDN', 'FA'), 'source-proven native layer kind')
    return layer.prefix if kind == 'GDN' else layer.layer_name


def require_forward_gate(binding, r):
    """The replaced static guard must not exist without its actual gateway.

    Accept only the gateway itself or the ONE exact reviewed W.wrapped_forward
    whose actual `forward` closure contains it. No generic unwrap traversal or
    writable __wrapped__-only assertion can unlock provisional registration.
    """
    gateway = binding.gateway
    need(gateway is not None, 'actual selected gateway must be prepared before static deferral')
    current = type(r)._model_forward
    if current is gateway:
        return
    # functools.wraps deliberately changes __qualname__; the real code object
    # name/file plus the reviewed closure, not that copied label, is the seam.
    need(current.__code__.co_name == 'wrapped_forward', 'unknown model-forward hook stack')
    digest_file(current.__code__.co_filename, INTEGRATION_SHA)
    names = current.__code__.co_freevars
    need('forward' in names and current.__closure__ is not None and
         current.__closure__[names.index('forward')].cell_contents is gateway,
         'exact reviewed native integration calls the required selected gateway')


def merged_ranges(ranges, size):
    """Canonical whole-pool allowed-write union, never discard gaps."""
    out = []
    for lo, hi in sorted(ranges):
        need(type(lo) is int and type(hi) is int and 0 <= lo < hi <= size, 'exact pool-relative write bounds')
        if out and lo <= out[-1][1]:
            out[-1] = (out[-1][0], max(hi, out[-1][1]))
        else:
            out.append((lo, hi))
    return tuple(out)


def inactive_equal(before, after, writes):
    """Complete bytes, including gaps/tails/shared views; NaN and +/-0 exact."""
    need(type(before) is bytes and type(after) is bytes and len(before) == len(after), 'whole same-size pool snapshots')
    cursor = 0
    for lo, hi in merged_ranges(writes, len(before)):
        need(before[cursor:lo] == after[cursor:lo], 'whole inactive pool byte changed')
        cursor = hi
    need(before[cursor:] == after[cursor:], 'whole inactive pool byte changed')


class ExecutionFrame:
    """Made only by the native execute wrapper; no JSON/bool constructor permit."""
    def __init__(self, seal, runner, scheduler, ordinal):
        need(seal is _SEAL, 'only source-bound native execution wrapper creates frame')
        self.runner, self.scheduler, self.ordinal = runner, scheduler, ordinal
        self.prepared = False
        self.epoch = None


class NativeReader:
    """Created only after the admitted native platform/module load sequence.

    Constructor imports the *actual* modules, not a supplied torch-like object.
    CPU tests deliberately cannot create a valid NPU tensor via a fixture.
    """
    def __init__(self, layout_source, checked):
        import torch
        import torch_npu
        from vllm_ascend.worker import model_runner_v1 as runner
        from vllm_ascend.worker import block_table
        digest_file(runner.__file__, RUNNER_SHA)
        digest_file(block_table.__file__, BLOCK_SHA)
        # checked is existing source-bound exact Ref loader, not an allow flag.
        layout = checked(layout_source)
        import base64
        header = base64.b64decode(layout['acl_base_rt.h']['base64'], validate=True)
        need(len(header) == 13720 and hashlib.sha256(header).hexdigest() ==
             '4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529'
             and b'ACL_FORMAT_ND = 2' in header, 'actual fixed ACL ND2 source')
        init = Path(torch_npu.__file__).read_bytes()
        pin = layout['torch_npu_init.py']
        need(len(init) == pin['bytes'] and hashlib.sha256(init).hexdigest() == pin['sha256'], 'actual installed torch_npu source')
        self.torch, self.runner_class = torch, runner.NPUModelRunner
        self.get_format = getattr(torch_npu, 'get_npu_format', None)
        need(callable(self.get_format), 'actual native get_npu_format absent')
        self.count = 0

    def tensor(self, t, device):
        need(type(t) is self.torch.Tensor and t.device.type == device, 'actual native Tensor/device only, no JSON or fake tensor')
        return t

    def small(self, t, device='npu'):
        t = self.tensor(t, device)
        need(t.dtype in (self.torch.int32, self.torch.int64, self.torch.bool), 'only real integer/bool metadata')
        need(0 <= t.numel() <= 65536, 'bounded integer metadata')
        self.count += t.numel()
        need(self.count <= MAX_INDEX_VALUES, 'bounded whole-step metadata D2H')
        return t.detach().cpu().tolist()

    def geometry(self, t, F):
        t = self.tensor(t, 'npu')
        need(t.is_contiguous() and t.numel() > 0 and int(self.get_format(t)) == 2, 'actual unpacked ND2 contiguous positive view only')
        names = {self.torch.uint8: 'u8', self.torch.bfloat16: 'bf16', self.torch.float32: 'f32',
                 self.torch.int32: 'i32', self.torch.int64: 'i64'}
        need(t.dtype in names, 'reviewed typed view only')
        storage = t.untyped_storage()
        geometry = F.Geometry(t.data_ptr(), t.storage_offset(), t.element_size(), names[t.dtype],
                              tuple(t.shape), tuple(t.stride()), 2)
        need(t.data_ptr() == storage.data_ptr() + t.storage_offset() * t.element_size(), 'actual pointer/offset')
        return geometry, storage

    def pool_alias(self, pool, exemplar):
        """Diagnostic-only, actual byte alias. NPU backend support unverified.

        Unsupported set_ or a non-ND byte alias fails, never falls back to a
        partial typed-view snapshot. A later owner must separately budget this
        work; MAX_SNAPSHOT_BYTES is not an authorization or promised fit.
        """
        self.tensor(exemplar, 'npu')
        need(exemplar.untyped_storage() is pool.storage, 'actual exemplar of same strong storage')
        from byteaudit import whole_storage_bytes
        t = whole_storage_bytes(self.torch, exemplar, self.get_format, device='npu')
        need(t.data_ptr() == pool.pointer and t.storage_offset() == 0 and
             t.numel() == pool.nbytes and int(self.get_format(t)) == 2, 'exact whole ND pool byte alias')
        return t  # Only an alias: bounded D2H happens later, chunk by chunk.


class StaticBinding:
    def __init__(self, F, reader, domain, allocation_ref, binding_ref):
        need(type(reader) is NativeReader, 'actual reader class, not boolean/JSON evidence')
        self.F, self.reader, self.domain = F, reader, domain
        self.allocation_ref, self.binding_ref = allocation_ref, binding_ref
        self.layers, self.native_layers, self.pools = {}, {}, []
        self.registry = None
        self.provisional = set()
        self.gateway = None

    def view(self, prefix, gid, role, t):
        F, g = self.F, None
        g, storage = self.reader.geometry(t, F)
        match = [p for p in self.pools if p.storage is storage]
        need(len(match) <= 1, 'one strong allocation binding')
        if match:
            pool = match[0]
            need(pool.pointer == storage.data_ptr() and pool.nbytes == storage.nbytes(), 'same complete pool extent')
        else:
            pool = F.Pool(self.domain, storage.data_ptr(), storage.nbytes(), storage, self.allocation_ref)
            # No mutation of the frozen core dataclass. Byte-snapshot device
            # source is retained separately from numerical/raw metadata.
            self.pools.append(pool)
        return F.View(prefix, gid, role, pool, t, g, self.binding_ref)

    def register(self, r, legacy, torch):
        need(type(r) is self.reader.runner_class and not self.layers, 'actual native runner, register once')
        need(torch is self.reader.torch, 'same actual installed torch module')
        digest_file(legacy.__file__, '1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470')
        groups, tables = r.kv_cache_config.kv_cache_groups, r.input_batch.block_table.block_tables
        need(len(groups) == len(tables), 'actual complete group tables')
        static = r.compilation_config.static_forward_context
        for gid, (group, table) in enumerate(zip(groups, tables)):
            for prefix in group.layer_names:
                need(prefix not in self.layers and prefix in static, 'unique actual static context prefix')
                layer = static[prefix]
                kind = 'GDN' if table.is_mamba_group else 'FA'
                # Native GDN base owns prefix; native FA Attention owns
                # layer_name. Never infer one from a missing attribute/default.
                need(static_layer_name(layer, kind) == prefix,
                     'actual same kind-specific native static object name')
                cache = layer.kv_cache
                if kind == 'FA' and len(cache) == 1 and isinstance(cache[0], (tuple, list)):
                    cache = cache[0]
                need(len(cache) == 2, 'actual two-state/two-KV view inventory')
                if kind == 'GDN':
                    base = cache[1]
                    need(tuple(base.shape[1:]) == (12, 128, 128) and str(base.dtype) == 'torch.float32'
                         and tuple(base.stride()) == (196608, 16384, 128, 1), 'original strong GDN base layout remains')
                    aux = legacy._ensure_aux(torch, layer)
                    need(aux is not None, 'actual five private aux allocation')
                    items = [('conv', cache[0]), ('base', base)] + [(role, aux[name]) for role, name in ROLE_TO_AUX.items()]
                    expected = dict(K=('torch.bfloat16', (base.shape[0], 4, 7, 128)),
                                    U=('torch.float32', (base.shape[0], 12, 7, 128)),
                                    lambda_log=('torch.float32', (base.shape[0], 12, 16)),
                                    decay=('torch.float32', (base.shape[0], 12, 16)), length=('torch.int32', (base.shape[0], 12, 16)))
                    need(cache[0].shape[0] == base.shape[0], 'native conv/base row domain')
                    need(all(str(aux[ROLE_TO_AUX[k]].dtype) == dt and tuple(aux[ROLE_TO_AUX[k]].shape) == sh
                             for k, (dt, sh) in expected.items()), 'exact unchanged five auxiliary ABI layouts')
                else:
                    items = list(zip(('K', 'V'), cache))
                views = tuple(self.view(prefix, gid, role, t) for role, t in items)
                self.layers[prefix] = (kind, gid, views)
                self.native_layers[prefix] = layer
        self.registry = self.F.Registry(self.layers)  # full static identity/bounds retained, not active permission
        return self

    def static_overlap_pending(self, r, layer, gid, base, start, end):
        """Exact replacement seam, not a shared_by exemption.

        A new source may register full views provisionally only when ALL64 are
        strongly bound. Decoder entry must still derive and admit the complete
        selected set for this real execution. No report/boolean calls this path.
        """
        frame = CURRENT.get()
        require_forward_gate(self, r)
        need(type(frame) is ExecutionFrame and frame.runner is r and not frame.prepared,
             'provisional registration only in actual preprepare execute window')
        need(self.registry is not None and self.native_layers.get(layer.prefix) is layer
             and self.layers[layer.prefix][:2] == ('GDN', gid), 'complete same strong all64 registration')
        v = self.registry.views[(layer.prefix, 'base')]
        g, storage = self.reader.geometry(base, self.F)
        need(base is v.tensor and g == v.geometry and storage is v.pool.storage
             and start == g.pointer and end == start + base.numel() * base.element_size(),
             'same original typed whole arena extent; no inferred layout')
        need(layer.prefix not in self.provisional, 'one static registration per actual GDN layer')
        self.provisional.add(layer.prefix)
        # No active alias permission returned; source-bound forward is blocked
        # until live_epoch + whole inactive check can be integrated/admitted.


def selected_plan(F, binding, selections):
    """All64 access/read/write union from complete typed live selections.

    This pure comparison function also has synthetic software tests. It does
    NOT construct a LiveEpoch or unlock any hook by itself.
    """
    registry = binding.registry
    need(registry is not None and len(selections) == len(registry.views), 'complete all64 seven-GDN/two-FA roles')
    accepted, accesses, writes, metadata, gdslots, fa_tables = {}, [], {}, {}, {}, {}
    for s in selections:
        v, g = s.view, s.view.geometry
        key = (v.prefix, v.role)
        need(key in registry.views and registry.views[key] is v and key not in accepted, 'same strong static typed view, no omission/duplicate')
        need(s.observed_geometry == g and s.observed_storage is v.pool.storage and s.metadata is not None,
             'live geometry/storage/native metadata identity unchanged')
        need(s.commit_ref.valid() and s.cpu_rows == s.gpu_rows and s.cpu_rows
             and len(set(s.cpu_rows)) == len(s.cpu_rows), 'actual CPU/GPU selected rows join')
        need(all(type(i) is int and 0 <= i < g.shape[0] for i in s.cpu_rows), 'actual selected row bounds')
        need(v.prefix not in metadata or metadata[v.prefix] is s.metadata, 'all roles share actual metadata object')
        metadata[v.prefix] = s.metadata
        n = F.check_view(v)
        kind = registry.layers[v.prefix][0]
        if kind == 'GDN':
            need(len(s.cpu_rows) == 1 and not s.writes and not s.physical_rows, 'C1 exact selected native GDN slot')
            need(v.prefix not in gdslots or gdslots[v.prefix] == s.cpu_rows, 'all seven GDN roles use same slot')
            gdslots[v.prefix] = s.cpu_rows
        else:
            need(s.physical_block_tokens >= s.kernel_block_tokens > 0 and
                 s.physical_block_tokens % s.kernel_block_tokens == 0, 'actual physical/kernel ratio')
            ratio = s.physical_block_tokens // s.kernel_block_tokens
            need(tuple(i * ratio + j for i in s.physical_rows for j in range(ratio)) == s.cpu_rows,
                 'actual FA physical-to-kernel row expansion')
            table = (s.physical_rows, s.cpu_rows, s.physical_block_tokens, s.kernel_block_tokens)
            need(v.prefix not in fa_tables or fa_tables[v.prefix] == table, 'same actual FA K/V physical-to-kernel table')
            fa_tables[v.prefix] = table
            need(s.writes, 'exact FA current writes required, no read-only exemption')
        for row in s.cpu_rows:
            lo = g.pointer + row * g.strides[0] * g.element_bytes
            accesses.append(F.Access(v.prefix, v.role, v, lo, lo + n, 'rw' if kind == 'GDN' else 'read'))
            if kind == 'GDN':
                writes.setdefault(id(v.pool), []).append((lo - v.pool.pointer, lo + n - v.pool.pointer))
        # Exact interval union first. Native prefill can have2048 token writes
        # per FA view; enumerating all token-pairs would make a metadata guard
        # quadratic in tokens although contiguous per-block union is identical.
        by_row = {}
        for row, begin, end in s.writes:
            need(row in s.cpu_rows and 0 <= begin < end <= n, 'FA writes within conservative full-block reads')
            by_row.setdefault(row, []).append((begin, end))
        compact_writes = [(row, begin, end) for row, intervals in by_row.items()
                          for begin, end in merged_ranges(intervals, n)]
        for row, begin, end in compact_writes:
            lo = g.pointer + row * g.strides[0] * g.element_bytes
            accesses.append(F.Access(v.prefix, v.role, v, lo + begin, lo + end, 'write'))
            writes.setdefault(id(v.pool), []).append((lo + begin - v.pool.pointer, lo + end - v.pool.pointer))
        accepted[key] = s
    F.check_intersections(accesses)
    return accepted, metadata, {id(p): merged_ranges(writes.get(id(p), ()), p.nbytes) for p in binding.pools}


def live_epoch(binding, manager, context, commit_ref):
    """Read actual postprepare GPU indices, never hydrate an observation JSON.

    Untimed diagnostic metadata D2H is explicit. Every step rechecks the real
    source-derived group/table/request join, including decode and continuation.
    It does not call model/clear/writeback or grant current install authority.
    """
    frame = CURRENT.get()
    need(type(frame) is ExecutionFrame and frame.prepared, 'actual original native prepare must return first')
    r, scheduler = frame.runner, frame.scheduler
    need(type(r) is binding.reader.runner_class and manager.runner is r, 'same actual runner/lifecycle manager')
    need(frame.epoch is None and binding.registry is not None, 'one live epoch per real model forward')
    need(binding.provisional == {p for p, row in binding.layers.items() if row[0] == 'GDN'},
         'all48 original mirror registrations reached the new provisional seam')
    ids = tuple(r.input_batch.req_ids)
    need(len(ids) == 1 and type(ids[0]) is str and r.input_batch.req_id_to_index == {ids[0]: 0}, 'actual reordered C1 CPU row')
    rid = ids[0]
    generation = manager.generation((rid, r.requests[rid]))
    counts = dict(scheduler.num_scheduled_tokens)
    need(set(counts) == {rid} and type(counts[rid]) is int and counts[rid] > 0
         and scheduler.total_num_scheduled_tokens == counts[rid], 'actual real nonempty scheduled query, no dummy/padding')
    qlen = counts[rid]
    reader, F = binding.reader, binding.F
    reader.count = 0
    computed = reader.small(r.input_batch.num_computed_tokens_cpu_tensor[:1], 'cpu')
    need(len(computed) == 1 and type(computed[0]) is int and computed[0] >= 0, 'actual native CPU computed prefix length')
    endpos = computed[0] + qlen
    need(type(context.attn_metadata) is dict and set(binding.layers) <= set(context.attn_metadata), 'all64 real built metadata')
    need(all(context.no_compile_layers[p] is layer for p, layer in binding.native_layers.items()), 'all64 actual current framework layer objects')
    selections = []
    groups, tables = r.kv_cache_config.kv_cache_groups, r.input_batch.block_table.block_tables
    need(len(groups) == len(tables), 'all actual groups still present')
    for gid, (group, table) in enumerate(zip(groups, tables)):
        need(table.pcp_world_size == table.dcp_world_size == 1, 'native PCP/DCP1, no padded transformation')
        n = int(table.num_blocks_per_row[0])
        need(0 < n <= 65536, 'bounded actual committed row')
        cpu = tuple(reader.small(table.get_cpu_tensor()[0, :n], 'cpu'))
        gpu = tuple(reader.small(table.get_device_tensor(1)[0, :n]))
        physical = tuple(r.requests[rid].block_ids[gid])
        need(physical and all(type(x) is int and x >= 0 for x in physical), 'actual request strong physical block table')
        ratio = int(table.blocks_per_phys_block)
        pbs, kbs = int(table.physical_block_size), int(table.logical_block_size)
        need(ratio > 0 and pbs == kbs * ratio, 'native physical/kernel mapping size')
        expanded = tuple(p * ratio + j for p in physical for j in range(ratio)) if table.use_hybrid_blocks else physical
        need(cpu == gpu == expanded, 'actual postcommit GPU equals complete CPU source/physical expansion')
        for prefix in group.layer_names:
            need(prefix in binding.layers and binding.layers[prefix][1] == gid, 'current all64 group mapping unchanged')
            kind, _, views = binding.layers[prefix]
            m = context.attn_metadata[prefix]
            need((kind == 'GDN') == bool(table.is_mamba_group), 'same actual FA/GDN group kind')
            if kind == 'GDN':
                need(m.spec_sequence_masks is None and m.num_prefills + m.num_decodes == 1 and m.num_decodes in (0, 1)
                     and m.num_decode_tokens == m.num_decodes, 'native C1 nonspec partition')
                need(len(physical) == len(cpu) == 1, 'none-mode actual one temporal block')
                rows = tuple(reader.small(m.non_spec_state_indices_tensor[:1]))
                need(rows == cpu, 'actual GPU selected SSM indices equal committed row')
                if m.num_prefills:
                    need(tuple(reader.small(m.prefill_state_indices[:1])) == rows, 'actual prefill selected SSM index')
                    h = reader.small(m.prefill_has_initial_state[:1])
                    need(h == [computed[0] > 0], 'native GPU initial-state mask from actual CPU prefix')
                    conv = m.non_spec_prefill_metadata.causal_conv1d
                    need(reader.small(conv.initial_state_mode[:1]) == h, 'actual conv/SSM same history intent')
                else:
                    need(qlen == 1 and computed[0] > 0 and reader.small(m.non_spec_decode_metadata.actual_seq_lengths) == [0, 1],
                         'true one-token continuation decode, original individual-length ABI')
                    conv = m.non_spec_decode_metadata.causal_conv1d
                ci = reader.small(conv.cache_indices[:1])
                need(ci in (list(rows), [[rows[0]]]) and reader.small(conv.query_start_loc) == [0, qlen],
                     'actual conv/query/state GPU index agreement')
                state = r._deltalog018_state
                plan = state['current'].get('_native_lifecycle_plans', {}).get(gid)
                need(plan is not None and plan.generation is generation and plan.slot == rows[0]
                     and plan.step is state['current'] and plan.fresh == (computed[0] == 0),
                     'same actual strong lifecycle intent, not a JSON native-reset claim')
                for v in views:
                    g, st = reader.geometry(v.tensor, F)
                    selections.append(F.Selection(v, m, commit_ref, rows, rows, g, st))
            else:
                need(kbs > 0 and endpos <= len(gpu) * kbs, 'complete actual FA logical coverage')
                need(tuple(reader.small(m.block_tables[:1, :n])[0]) == gpu, 'real current FA metadata GPU table')
                sm = tuple(reader.small(m.slot_mapping[:qlen]))
                actual = tuple(reader.small(table.slot_mapping.gpu[:qlen]))
                expected = tuple(gpu[pos // kbs] * kbs + pos % kbs for pos in range(computed[0], endpos))
                need(sm == actual == expected and len(set(sm)) == qlen, 'actual token writes/metadata/table logical positions')
                need(list(m.actual_seq_lengths_q) == [qlen] and reader.small(m.seq_lens[:1]) == [endpos], 'actual FA query/history lengths')
                for v in views:
                    g, st = reader.geometry(v.tensor, F)
                    need(len(g.shape) == 4 and g.shape[1] == kbs, 'actual unpacked FA block/token/head/dim geometry')
                    tokenbytes = g.strides[1] * g.element_bytes
                    writes = tuple((s // kbs, (s % kbs) * tokenbytes, (s % kbs + 1) * tokenbytes) for s in sm)
                    # Conservatively retain ALL actual referenced/allocated
                    # kernel blocks. No guessed smaller FA-read exemption.
                    selections.append(F.Selection(v, m, commit_ref, cpu, gpu, g, st,
                        physical_rows=physical, physical_block_tokens=pbs, kernel_block_tokens=kbs, writes=writes))
    accepted, _, writes = selected_plan(F, binding, selections)
    epoch = LiveEpoch(_SEAL, frame, binding, context, r.requests[rid], generation, accepted, writes)
    frame.epoch = epoch
    return epoch


def prepared_native_wrappers(R, binding, manager_for, get_context):
    """Build—not install—actual execute/prepare/forward wrappers for review.

    They must be composed in a new source before M.install/W.install. Existing
    lifecycle update wrapper is separate and must run even on zero-token work.
    The forward wrapper currently refuses at snapshot(), before model math,
    because no source-bound whole-inactive byte budget has been admitted.
    """
    need(R is binding.reader.runner_class and binding.gateway is None, 'same actual source-pinned native runner class, prepare once')
    execute, prepare, forward = R.execute_model, R._prepare_inputs, R._model_forward
    need(all(inspect.getsourcefile(fn) == inspect.getsourcefile(R) for fn in (execute, prepare, forward)),
         'prepare against original direct native methods, no unknown hook stack')
    digest_file(inspect.getsourcefile(R), RUNNER_SHA)
    ordinal = [0]
    @functools.wraps(execute)
    def execute_wrapper(r, scheduler_output, *a, **kw):
        need(CURRENT.get() is None, 'nonreentrant source-bound actual execute')
        ordinal[0] += 1
        frame = ExecutionFrame(_SEAL, r, scheduler_output, ordinal[0])
        token = CURRENT.set(frame)
        try:
            return execute(r, scheduler_output, *a, **kw)
        finally:
            CURRENT.reset(token)
    @functools.wraps(prepare)
    def prepare_wrapper(r, *a, **kw):
        frame = CURRENT.get()
        need(type(frame) is ExecutionFrame and frame.runner is r and not frame.prepared, 'real execute owns one original native prepare')
        result = prepare(r, *a, **kw)
        frame.prepared = True  # Cannot be passed by an external JSON/bool argument.
        return result
    @functools.wraps(forward)
    def forward_wrapper(r, *a, **kw):
        frame = CURRENT.get()
        if frame is None:
            manager = manager_for(r)
            need(not manager.live and not any(x is not None for x in r.input_batch.req_ids),
                 'native dummy cannot touch any live or untracked actual request')
            return forward(r, *a, **kw)
        need(frame.runner is r, 'same real execute/forward runner')
        epoch = live_epoch(binding, manager_for(r), get_context(), binding.binding_ref)
        epoch.snapshot()  # hard pending; not a permission to run the decoder
        raise Refusal('unreachable without a separately source-reviewed snapshot/completion integration')
    binding.gateway = forward_wrapper  # Retained callable, never a JSON/bool marker.
    return dict(execute=execute_wrapper, prepare=prepare_wrapper, forward=forward_wrapper, installed=False, qualified=False)


GUARD_OLD = "  need(all(end<=lo or start>=hi for lo,hi in arena_ranges),'registered actual layer arenas must not overlap')"
GUARD_NEW = '  _SELECTED.static_overlap_pending(r,layer,gid,base,start,end)'


def proposed_mirror_source(module, lifecycle):
    """Two exact source scheduling seams; does not install either one.

    Lifecycle's native-derived gid insertion plus static overlap deferral.
    Whole inverse returns the original mirror, retaining every other guard.
    No conditional 'if shared_by' / JSON permit / skipped alias check is used.
    """
    original = digest_file(module.__file__, MIRROR_SHA).decode('utf8')
    text = lifecycle.clone_build(module)
    need(text.count(GUARD_OLD) == 1 and GUARD_NEW not in text, 'one exact old whole-arena seam')
    candidate = text.replace(GUARD_OLD, GUARD_NEW)
    inverse = candidate.replace(GUARD_NEW, GUARD_OLD).replace(lifecycle.BUILD_NEW, lifecycle.BUILD_OLD)
    need(inverse == original, 'whole original mirror inverse, no math/source gate removed')
    return candidate


def prepared_mirror_functions(module, lifecycle):
    """Only compile the two changed functions; retain original M globals.

    Caller cannot run register_layers before binding an actual StaticBinding as
    M._SELECTED in a newly reviewed source. This function performs no mutation.
    It does not clone a second contextvar/module universe.
    """
    import ast
    from types import FunctionType
    tree = ast.parse(proposed_mirror_source(module, lifecycle))
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('install', 'register_layers')]
    need({n.name for n in wanted} == {'install', 'register_layers'}, 'exact actual two mirror functions')
    scope = dict(vars(module))
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(module.__file__)+'#selected-lifecycle-only', 'exec'), scope)
    return {n.name: FunctionType(scope[n.name].__code__, vars(module), n.name,
                               scope[n.name].__defaults__, scope[n.name].__closure__) for n in wanted}


def snapshot_requirement(binding):
    """Scientific byte count only, not available-memory/storage admission."""
    need(binding.registry is not None, 'complete strong allocation set first')
    size = sum(p.nbytes for p in binding.pools)
    need(0 < size <= MAX_SNAPSHOT_BYTES, 'whole native+private allocation exceeds unchanged hard output envelope')
    return dict(bytes_per_before_snapshot=size, bytes_read_for_before_after=2 * size,
                unique_pools=len(binding.pools), chunked_byte_backend_verified=False,
                owner_combined_capture_budget_bound=False, admitted=False)


class LiveEpoch:
    def __init__(self, seal, frame, binding, context, request, generation, accepted, writes):
        need(seal is _SEAL and type(frame) is ExecutionFrame and frame.prepared, 'real wrapped postprepare, not JSON/bool token')
        self.frame, self.binding, self.context = frame, binding, context
        self.request, self.generation = request, generation
        self.accepted, self.writes = accepted, writes
        self.before, self.closed = None, False
        self.store = None
        self.pending_actual_memory_budget = True
        self.consumed_GDN = set()

    def before_core(self, layer, metadata, context, manager):
        need(not self.closed and CURRENT.get() is self.frame and context is self.context, 'same live execution context')
        rid = self.generation.request_id
        need(manager.live.get(rid) is self.generation and not self.generation.retired
             and self.frame.runner.requests.get(rid) is self.request, 'same actual nonretired strong generation')
        prefix = layer.prefix
        need(self.binding.native_layers.get(prefix) is layer, 'same strong real layer')
        kind, gid, _ = self.binding.layers[prefix]
        if kind == 'GDN':
            need(prefix not in self.consumed_GDN, 'actual GDN core once per live epoch')
        for v in self.binding.layers[prefix][2]:
            s = self.accepted[(prefix, v.role)]
            g, st = self.binding.reader.geometry(v.tensor, self.binding.F)
            need(s.metadata is metadata and s.observed_geometry == g and st is v.pool.storage, 'actual current metadata/view cannot drift')
        reader = self.binding.reader
        expected = self.accepted[(prefix, 'base' if kind == 'GDN' else 'K')]
        table = self.frame.runner.input_batch.block_table.block_tables[gid]
        n = int(table.num_blocks_per_row[0])
        need(tuple(reader.small(table.get_device_tensor(1)[0, :n])) == expected.gpu_rows,
             'actual committed device table unchanged immediately before core')
        if kind == 'GDN':
            need(tuple(reader.small(metadata.non_spec_state_indices_tensor[:1])) == expected.gpu_rows,
                 'actual selected state indices unchanged immediately before core')
            self.consumed_GDN.add(prefix)
        return True

    def snapshot(self):
        # No software bool or observation JSON can provide a memory admission.
        # Full native pool byte alias support and current owner snapshot budget
        # are unmeasured; do not allocate additional 12GiB under an old label.
        raise Refusal('PENDING actual whole-pool byte-alias support and source-bound existing-owner memory/output budget; no partial inactive check')

    def prepared_snapshot_calls(self, store):
        """Concrete streaming code for a later new admitted source to invoke.

        No public hook calls this method. It creates no permission/lease. The
        later source must bind successful tiny ABI evidence and the NEW explicit
        <=32GiB workspace / <=80GiB commitment ticket, not reuse an old4GiB
        controller label. Actual snapshot/data failures propagate, retain files,
        and invalidate the experiment.
        """
        from byteaudit import Store, chunk_bytes
        need(type(store) is Store and self.before is None and CURRENT.get() is self.frame,
             'one actual private store and native epoch')
        requirement = snapshot_requirement(self.binding)
        need(store.cap >= requirement['bytes_per_before_snapshot'] + 3*1024**2,
             'complete before plus first-difference evidence must fit explicit worker share')
        self.before, self.store = {}, store
        for i, pool in enumerate(self.binding.pools):
            exemplar = next(v.tensor for v in self.binding.registry.views.values() if v.pool is pool)
            alias = self.binding.reader.pool_alias(pool, exemplar)
            name = 'step%d-pool%d' % (self.frame.ordinal, i)
            store.before(name,pool.nbytes,lambda a,b:chunk_bytes(self.binding.reader.torch,alias,a,b,device='npu'))
            self.before[id(pool)] = name

    def finish(self, manager, mirror):
        """Prepared post-writeback seam; cannot succeed without actual before.

        No external `after` JSON/bytes argument exists. All pool bytes would be
        read again from the actual strong NPU allocations. This code is not
        installed, and snapshot currently hard-refuses its unadmitted budget.
        """
        need(not self.closed and CURRENT.get() is self.frame and self.before is not None and self.store is not None,
             'same actual epoch and complete actual before-snapshot mandatory')
        expected = {p for p, row in self.binding.layers.items() if row[0] == 'GDN'}
        need(self.consumed_GDN == expected and manager.live.get(self.generation.request_id) is self.generation
             and not self.generation.retired, 'all48 actual core callbacks and same live generation')
        mirror.finish_step(self.frame.runner)  # original 48 core/decode receipt gate
        self.binding.reader.torch.npu.current_stream().synchronize()  # diagnostic only
        need(expected <= self.generation.reset_complete, 'actual initial clear/writeback completion for every GDN prefix')
        need(set(self.before) == {id(p) for p in self.binding.pools}, 'every unique pool included, no sibling/whole-view exemption')
        for pool in self.binding.pools:
            exemplar = next(v.tensor for v in self.binding.registry.views.values() if v.pool is pool)
            alias = self.binding.reader.pool_alias(pool, exemplar)
            from byteaudit import chunk_bytes
            self.store.compare(self.before[id(pool)],
                lambda a,b:chunk_bytes(self.binding.reader.torch,alias,a,b,device='npu'), self.writes[id(pool)])
        self.closed = True
        return dict(all64_selected_footprint_checked=True, all48_GDN_core_observed=True,
                    all16_FA_core_observed=False, whole_inactive_bytes_checked=True,
                    model_numeric_qualified=False, performance_qualified=False, task_qualified=False)


def install(*args, **kwargs):
    if os.environ.get(ENABLE) != '1':
        return dict(installed=False, default_OFF=True, qualified=False)
    raise Refusal('PENDING all4 actual geometry, source-bound live hook integration and whole-inactive budget; no JSON/boolean unlock')
