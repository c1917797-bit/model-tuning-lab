"""Metadata comparison only. No hook, tensor read, execution or qualification."""
from dataclasses import dataclass
from typing import Tuple


class Refusal(ValueError):
    pass


def require(value, message):
    if not value:
        raise Refusal(message)


@dataclass(frozen=True)
class Ref:
    path: str
    bytes: int
    sha256: str

    def valid(self):
        return (self.path.startswith('/') and self.bytes > 0 and
                len(self.sha256) == 64 and all(c in '0123456789abcdef' for c in self.sha256))


@dataclass(frozen=True)
class Domain:
    cid: str
    host_pid: int
    start_ticks: int
    physical: int
    rank: int

    def valid(self):
        return (len(self.cid) == 64 and all(c in '0123456789abcdef' for c in self.cid)
                and self.host_pid > 0 and self.start_ticks > 0
                and self.physical in (4, 5, 6, 7) and self.rank in range(4))


@dataclass(frozen=True)
class Pool:
    domain: Domain
    pointer: int
    nbytes: int
    storage: object                 # Retain actual storage object, not id(storage).
    allocation_ref: Ref


@dataclass(frozen=True)
class Geometry:
    pointer: int
    storage_offset: int             # Elements, as returned by actual tensor.
    element_bytes: int
    dtype: str
    shape: Tuple[int, ...]
    strides: Tuple[int, ...]
    format_code: int


@dataclass(frozen=True)
class View:
    prefix: str
    group: int
    role: str
    pool: Pool
    tensor: object                  # Retain actual view object.
    geometry: Geometry
    binding_ref: Ref


@dataclass(frozen=True)
class Selection:
    view: View
    metadata: object                # Actual built native metadata, strongly retained.
    commit_ref: Ref
    cpu_rows: Tuple[int, ...]
    gpu_rows: Tuple[int, ...]
    observed_geometry: Geometry
    observed_storage: object
    physical_rows: Tuple[int, ...] = ()
    physical_block_tokens: int = 0
    kernel_block_tokens: int = 0
    # FA exact current-token writes: (kernel row, byte begin/end within row).
    # This adapter-supplied mapping still needs actual source proof; no inference
    # of physical format/page size is made here.
    writes: Tuple[Tuple[int, int, int], ...] = ()


@dataclass(frozen=True)
class Access:
    prefix: str
    role: str
    view: View
    begin: int
    end: int
    mode: str


def row_bytes(g):
    require(len(g.shape) >= 2 and len(g.shape) == len(g.strides), 'rank/stride evidence')
    require(g.format_code == 2, 'actual ND2 format mandatory')
    require(type(g.element_bytes) is int and g.element_bytes in (1, 2, 4, 8), 'element size')
    require(g.dtype in {'u8': 1, 'bf16': 2, 'f32': 4, 'i32': 4, 'i64': 8}
            and {'u8': 1, 'bf16': 2, 'f32': 4, 'i32': 4, 'i64': 8}[g.dtype] == g.element_bytes,
            'typed element identity')
    require(all(type(n) is int and n > 0 for n in g.shape), 'positive shape')
    require(all(type(n) is int and n > 0 for n in g.strides), 'integer positive strides')
    expected = 1
    for size, stride in zip(reversed(g.shape[1:]), reversed(g.strides[1:])):
        require(stride == expected, 'inner contiguous layout only')
        expected *= size
    require(g.strides[0] >= expected, 'nonoverlapping rows')
    return expected * g.element_bytes


def check_view(v):
    p, g = v.pool, v.geometry
    require(p.domain.valid() and p.storage is not None and v.tensor is not None, 'strong actual domain/storage/view')
    require(p.allocation_ref.valid() and v.binding_ref.valid(), 'allocation/binding sources missing')
    n = row_bytes(g)
    require(all(type(n) is int for n in (g.storage_offset, g.pointer, p.pointer, p.nbytes))
            and g.storage_offset >= 0 and p.pointer > 0 and p.nbytes > 0, 'integer storage extent')
    require(g.pointer == p.pointer + g.storage_offset * g.element_bytes, 'pointer/offset join')
    require(g.pointer + (g.shape[0] - 1) * g.strides[0] * g.element_bytes + n <= p.pointer + p.nbytes,
            'full view storage bounds')
    require(p.pointer + p.nbytes < 2**64, 'address overflow')
    return n


class Registry:
    """Static registration remains pending; overlapping full views authorize nothing."""
    def __init__(self, layers):
        require(len(layers) == 64 and len(set(layers)) == 64, 'exact all64 prefixes')
        require(sum(kind == 'GDN' for kind, group, views in layers.values()) == 48,
                'exact48 GDN and16 FA')
        self.layers = dict(layers)
        self.views = {}
        domains = set()
        for prefix, (kind, group, views) in self.layers.items():
            roles = {'conv', 'base', 'K', 'U', 'lambda_log', 'decay', 'length'} if kind == 'GDN' else {'K', 'V'}
            require(kind in ('GDN', 'FA') and type(group) is int and group >= 0, 'actual layer/group kind')
            require(len(views) == len(roles) and {v.role for v in views} == roles, 'complete distinct typed roles')
            for v in views:
                require(v.prefix == prefix and v.group == group, 'prefix/group mapping')
                check_view(v)
                domains.add(v.pool.domain)
                self.views[(prefix, v.role)] = v
        require(len(domains) == 1, 'one actual worker domain per registry')
        pools = []
        for v in self.views.values():
            if not any(v.pool is p for p in pools):
                pools.append(v.pool)
        for i, a in enumerate(pools):
            for b in pools[i + 1:]:
                if max(a.pointer, b.pointer) < min(a.pointer + a.nbytes, b.pointer + b.nbytes):
                    require(a.pointer == b.pointer and a.nbytes == b.nbytes and
                            a.storage is b.storage and a.allocation_ref == b.allocation_ref,
                            'overlapping pool identities must be the exact native allocation')
        self.active = None
        self.generation = 0            # Local ordinal, NEVER a native scheduler epoch.
        self.current = None
        self.last_step = 0
        self.slots = None
        self.retired = []             # Strong retired objects; absence never releases ownership.

    def fresh(self, request, request_id, *, native_reset_ref):
        require(self.current is None and self.active is None, 'retire before fresh/reuse')
        require(request is not None and request_id and native_reset_ref.valid(), 'original fresh reset evidence')
        require(all(request is not obj and request_id != rid for obj, rid in self.retired),
                'distinct native request object and request ID for reuse')
        self.generation += 1
        self.active = (request, request_id, self.generation)
        self.slots = None

    def retire(self, request, *, terminal_ref, native_removed, normal_eos):
        require(self.current is None and self.active is not None and request is self.active[0], 'actual active retire')
        require(terminal_ref.valid() and native_removed is True and normal_eos is True, 'actual terminal/removal, not absence')
        self.retired.append(self.active[:2])
        self.active = None
        self.slots = None

    def open(self, *, step, request, request_id, phase, selections, context,
             original_prepare_complete, metadata_complete, dummy=False, resumed=False):
        require(self.current is None and type(step) is int and step > self.last_step, 'no reentry/stale step')
        require(self.active is not None and request is self.active[0] and request_id == self.active[1],
                'strong current request generation')
        require(not dummy and not resumed and phase in ('prefill', 'decode', 'continuation'), 'unproved history/dummy')
        require(context is not None and original_prepare_complete is True and metadata_complete is True,
                'real postprepare/predecoder required')
        require(len(selections) == len(self.views), 'all64 complete selections')
        accepted, metadata, accesses, slots, fa_tables = {}, {}, [], {}, {}
        for s in selections:
            key = (s.view.prefix, s.view.role)
            require(key in self.views and key not in accepted and s.view is self.views[key], 'exact static view/no duplicate')
            require(s.observed_geometry == s.view.geometry and s.observed_storage is s.view.pool.storage,
                    'fresh actual view/storage geometry unchanged')
            require(s.metadata is not None and s.commit_ref.valid(), 'actual committed metadata evidence missing')
            if s.view.prefix in metadata:
                require(metadata[s.view.prefix] is s.metadata, 'same actual prefix metadata')
            metadata[s.view.prefix] = s.metadata
            require(s.cpu_rows == s.gpu_rows and s.cpu_rows and len(set(s.cpu_rows)) == len(s.cpu_rows),
                    'CPU/GPU committed rows unique exact join')
            v, g = s.view, s.view.geometry
            n = check_view(v)
            require(all(type(i) is int and 0 <= i < g.shape[0] for i in s.cpu_rows), 'selected row bounds')
            kind = self.layers[v.prefix][0]
            if kind == 'GDN':
                require(len(s.cpu_rows) == 1 and not s.physical_rows and not s.writes, 'C1 GDN exact slot')
                if v.prefix in slots:
                    require(slots[v.prefix] == s.cpu_rows, 'all GDN role slots agree')
                slots[v.prefix] = s.cpu_rows
            else:
                require(type(s.physical_block_tokens) is int and type(s.kernel_block_tokens) is int
                        and s.kernel_block_tokens > 0 and s.physical_block_tokens >= s.kernel_block_tokens
                        and s.physical_block_tokens % s.kernel_block_tokens == 0, 'actual page expansion parameters')
                ratio = s.physical_block_tokens // s.kernel_block_tokens
                require(s.physical_rows and all(type(i) is int and i >= 0 for i in s.physical_rows), 'physical table')
                require(tuple(i * ratio + j for i in s.physical_rows for j in range(ratio)) == s.cpu_rows,
                        'actual physical/kernel expansion join')
                table = (s.physical_rows, s.cpu_rows, s.physical_block_tokens, s.kernel_block_tokens)
                if v.prefix in fa_tables:
                    require(fa_tables[v.prefix] == table, 'FA K/V share the same committed block mapping')
                fa_tables[v.prefix] = table
                require(s.writes and len(set(s.writes)) == len(s.writes), 'exact nonempty FA current writes')
            for row in s.cpu_rows:
                begin = g.pointer + row * g.strides[0] * g.element_bytes
                accesses.append(Access(v.prefix, v.role, v, begin, begin + n, 'rw' if kind == 'GDN' else 'read'))
            for row, begin, end in s.writes:
                require(row in s.cpu_rows and type(begin) is int and type(end) is int and 0 <= begin < end <= n,
                        'FA exact write contained in own whole-block read')
                base = g.pointer + row * g.strides[0] * g.element_bytes
                accesses.append(Access(v.prefix, v.role, v, base + begin, base + end, 'write'))
            accepted[key] = s
        if phase in ('decode', 'continuation'):
            require(self.slots is not None and slots == self.slots, 'known same generation/slot continuation')
        else:
            require(self.slots is None, 'fresh prefill cannot replace unretired live history')
        check_intersections(accesses)
        token = Step(self, step, request, self.generation, context, accepted, metadata)
        self.current = token
        self.slots = slots
        return token


class Step:
    def __init__(self, registry, step, request, generation, context, selections, metadata):
        self.registry, self.step, self.request = registry, step, request
        self.generation, self.context = generation, context
        self.selections, self.metadata = selections, metadata
        self.consumed = set()

    def before_core(self, prefix, *, request, context, metadata, observed, committed_rows):
        r = self.registry
        require(r.current is self and r.active is not None and r.active[2] == self.generation,
                'same current single-use prepared token')
        require(request is self.request and context is self.context, 'request/order/context identity')
        require(prefix in self.metadata and metadata is self.metadata[prefix] and prefix not in self.consumed,
                'same native metadata/core once')
        expected = r.layers[prefix][2]
        require(len(observed) == len(expected) and
                all(tensor is v.tensor and geometry == v.geometry and storage is v.pool.storage
                    for (tensor, geometry, storage), v in zip(observed, expected)), 'current strong typed views/geometry/storage')
        require(set(committed_rows) == {v.role for v in expected} and
                all(committed_rows[v.role] == (self.selections[(prefix, v.role)].cpu_rows,
                                               self.selections[(prefix, v.role)].gpu_rows)
                    for v in expected), 'current committed rows unchanged before core')
        self.consumed.add(prefix)

    def finish(self):
        r = self.registry
        require(r.current is self and self.consumed == set(r.layers), 'all64 core obligations including48 GDN')
        r.last_step = self.step
        r.current = None


def check_intersections(accesses):
    for i, a in enumerate(accesses):
        for b in accesses[i + 1:]:
            if a.view.pool.domain != b.view.pool.domain:
                continue
            if max(a.begin, b.begin) < min(a.end, b.end):
                require(a.prefix == b.prefix and a.view is b.view and
                        a.role in ('K', 'V') and {a.mode, b.mode} == {'read', 'write'},
                        'simultaneously active physical alias')


def isolated_unchanged(before, after, selected):
    """Compare ALL unselected bytes; no sibling/pool exemption or numeric equal."""
    require(set(before) == set(after) == set(selected) == {'base', 'K', 'U', 'lambda_log', 'decay', 'length'},
            'complete isolated six arrays')
    for name, old in before.items():
        new = after[name]
        require(type(old) is bytes and type(new) is bytes and len(old) == len(new), 'complete byte snapshots')
        ranges = sorted(selected[name])
        cursor = 0
        for start, end in ranges:
            require(type(start) is int and type(end) is int and cursor <= start < end <= len(old), 'selected bounds/overlap')
            require(old[cursor:start] == new[cursor:start], 'unselected byte changed')
            cursor = end
        require(old[cursor:] == new[cursor:], 'unselected byte changed')


def observation_complete(rank_reports, *, releases_verified, final_source_fence, expected_stop):
    """Observation completeness ONLY; never numerical/model/performance permission."""
    require(set(rank_reports) == {0, 1, 2, 3} and all(rank_reports.values()), 'all four actual rank observations')
    require(releases_verified is True and final_source_fence is True and expected_stop is True,
            'actual release/source/stop evidence')
    return dict(observation_complete=True, numeric_qualified=False, model_qualified=False,
                performance_qualified=False, task_qualified=False)
