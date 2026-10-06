"""Stdlib-only source-bound continuous-turn preparation, not a service/NPU gate."""
from dataclasses import dataclass
from math import prod

class Unsupported(ValueError):
    pass

def require(value, message):
    if not value:
        raise Unsupported(message)

def integer(value):
    return type(value) is int

@dataclass(frozen=True)
class Row:
    request_id: str
    slot: int
    query_tokens: int
    computed_tokens: int
    prompt_tokens: int
    generation: int  # actual CachedRequestState identity, not a batch row index

@dataclass(frozen=True)
class Turn:
    rows: tuple
    starts: tuple
    num_decodes: int
    decode_tokens: int
    prefill_starts: tuple
    prefill_slots: tuple
    has_initial: tuple

    @property
    def decode_rows(self):
        return self.rows[:self.num_decodes]

    @property
    def prefill_rows(self):
        return self.rows[self.num_decodes:]

    @property
    def mode(self):
        return "mixed" if self.num_decodes and self.prefill_rows else (
            "decode" if self.num_decodes else "prefill")

def native_region(row):
    # utils.reorder_batch_to_split_decodes_and_prefills, threshold=1:
    # decode -> short extend -> long extend -> initial prefill.
    if row.computed_tokens == 0:
        return 3
    if row.query_tokens > 1:
        return 2
    return 0 if row.computed_tokens >= row.prompt_tokens else 1

def plan(rows, starts, slots, max_requests=16):
    """Consume native POST-reorder CPU rows; never reorder a model's inputs."""
    rows, starts = tuple(rows), tuple(starts)
    require(integer(slots) and slots > 0 and integer(max_requests) and
            1 <= max_requests <= 16 and 1 <= len(rows) <= max_requests,
            "invalid actual slots/request bound")
    require(len({r.request_id for r in rows}) == len(rows) and
            len({r.slot for r in rows}) == len(rows), "duplicate request/state slot")
    require(len(starts) == len(rows)+1 and all(integer(x) for x in starts)
            and starts[0] == 0, "unpadded CPU GDN query boundaries required")
    for i, row in enumerate(rows):
        require(isinstance(row.request_id, str) and row.request_id and
                all(integer(x) for x in (row.slot, row.query_tokens,
                    row.computed_tokens, row.prompt_tokens, row.generation)) and
                0 <= row.slot < slots and row.query_tokens > 0 and
                row.computed_tokens >= 0 and row.prompt_tokens > 0 and row.generation > 0,
                "invalid identity/slot/length/PAD")
        require(starts[i+1]-starts[i] == row.query_tokens, "row/token boundary mismatch")
        if row.computed_tokens < row.prompt_tokens:
            require(row.computed_tokens+row.query_tokens <= row.prompt_tokens,
                    "prompt chunk may not cross into unverified generated tokens")
        else:
            require(row.query_tokens == 1, "non-spec decode requires one actual token")
    regions = tuple(native_region(r) for r in rows)
    require(regions == tuple(sorted(regions)), "not the native post-reorder order")
    # Builder's _treat_single_token_prefills_with_state_as_decodes maps a
    # one-token continuation with existing state to the SAME recurrent ABI.
    nd = 0
    for row in rows:
        if row.query_tokens == 1 and row.computed_tokens > 0:
            nd += 1
        else:
            break
    require(all(not (r.query_tokens == 1 and r.computed_tokens > 0)
                for r in rows[nd:]), "reclassified decode must be a token prefix")
    dt = starts[nd]
    require(dt == nd, "actual decode T is request count, never padded16")
    pstarts = tuple(x-dt for x in starts[nd:])
    prefills = rows[nd:]
    return Turn(rows, starts, nd, dt, pstarts,
                tuple(r.slot for r in prefills),
                tuple(r.computed_tokens > 0 for r in prefills))

def _conv_slots(values):
    require(isinstance(values, list), "native CPU conv slot receipt required")
    if all(integer(x) for x in values):
        return values
    require(all(isinstance(x, list) and len(x) == 1 and integer(x[0])
                for x in values), "mamba-none conv ABI is [T] or [T,1]")
    return [x[0] for x in values]

def verify_native(turn, receipt):
    """Verify values snapshotted before any writer; no D2H in this helper."""
    require(isinstance(receipt, dict), "native metadata receipt missing")
    rows = turn.rows
    slots = [r.slot for r in rows]
    starts = list(turn.starts)
    require(all(type(receipt.get(k)) is int for k in (
            "num_actual_tokens", "num_decodes", "num_decode_tokens", "num_prefills")),
            "native count receipt must contain integer ABI values")
    require(receipt.get("spec_sequence_masks") is None and
            receipt.get("num_actual_tokens") == starts[-1] and
            receipt.get("num_decodes") == turn.num_decodes and
            receipt.get("num_decode_tokens") == turn.decode_tokens and
            receipt.get("num_prefills") == len(turn.prefill_rows) and
            receipt.get("non_spec_state_indices") == slots,
            "native GDN count/ordered-slot/spec drift")
    require(receipt.get("conv_starts") == starts and
            _conv_slots(receipt.get("conv_slots")) == slots,
            "mixed conv operates ALL rows, not the prefill suffix")
    if turn.prefill_rows:
        all_initial = receipt.get("conv_has_initial")
        require(isinstance(all_initial, list) and len(all_initial) == len(rows)
                and all(type(x) is bool for x in all_initial) and
                all_initial == [r.computed_tokens > 0 for r in rows],
                "mixed conv existing-state flags drift")
        require(receipt.get("prefill_starts") == list(turn.prefill_starts) and
                receipt.get("prefill_slots") == list(turn.prefill_slots) and
                receipt.get("prefill_has_initial") == list(turn.has_initial) and
                all(type(x) is bool for x in receipt["prefill_has_initial"]),
                "prefill suffix must be rebased with exact native initial flags")
    if turn.num_decodes:
        require(receipt.get("decode_actual_seq_lengths") == [0]+[1]*turn.num_decodes,
                "native decode lengths are [0,1,...,1], not cumulative")
    return True

class LeaseBook:
    """CPU identities only. Unscheduled/paused rows retain their actual slot."""
    def __init__(self):
        self.records = {}
        self.retired = False

    def finish(self, finished_ids):
        require(not self.retired and isinstance(finished_ids, (set, frozenset))
                and all(isinstance(x, str) and x for x in finished_ids),
                "exact SchedulerOutput.finished_req_ids required")
        self.records = {slot: record for slot, record in self.records.items()
                        if record[0] not in finished_ids}

    def check(self, turn):
        require(not self.retired, "worker is retired")
        for row in turn.rows:
            old = self.records.get(row.slot)
            if row.computed_tokens == 0:
                require(old is None, "fresh prefill would overwrite a live lease")
                require(all(r[0] != row.request_id for r in self.records.values()),
                        "request silently moved/recomputed with a retained slot")
            else:
                require(old == (row.request_id, row.generation, row.computed_tokens),
                        "uninitialized/recycled/relocated/stale/rewound state")
        return True

    def commit(self, turn):
        self.check(turn)
        for row in turn.rows:
            self.records[row.slot] = (
                row.request_id, row.generation, row.computed_tokens+row.query_tokens)

    def retire(self):
        # No partial turn rollback/native fallback: scheduler may have run some layers.
        self.retired = True

@dataclass(frozen=True)
class Access:
    storage: int
    start: int
    end: int
    owner: str
    write: bool

def block_accesses(storage, storage_bytes, offset, shape, strides, item_bytes,
                   block_ids, owner, write):
    """Actual observed typed view, axis0=physical blocks, contiguous inner axis.
    FA callers provide separate actual K/V views and ALL live readable blocks.
    GDN callers protect all retained leases, not only this turn's active rows.
    """
    require(all(integer(x) for x in (storage, storage_bytes, offset, item_bytes))
            and storage > 0 and storage_bytes > 0 and offset >= 0 and item_bytes > 0,
            "invalid storage identity/bytes")
    shape, strides = tuple(shape), tuple(strides)
    require(len(shape) >= 2 and len(strides) == len(shape) and
            all(integer(x) and x > 0 for x in shape+strides) and
            isinstance(owner, str) and owner and type(write) is bool,
            "actual positive native view geometry required")
    expected = 1
    for i in range(len(shape)-1, 0, -1):
        require(strides[i] == expected, "noncontiguous inner block view unsupported")
        expected *= shape[i]
    width = prod(shape[1:])*item_bytes
    require(strides[0]*item_bytes >= width, "overlapping block stride")
    require(offset+(shape[0]-1)*strides[0]*item_bytes+width <= storage_bytes,
            "typed view leaves original raw storage")
    ids = tuple(block_ids)
    require(len(set(ids)) == len(ids) and all(integer(x) and 0 <= x < shape[0] for x in ids),
            "exact unique in-range live block IDs required")
    return tuple(Access(storage, offset+b*strides[0]*item_bytes,
                        offset+b*strides[0]*item_bytes+width, owner, write) for b in ids)

def verify_live_accesses(accesses):
    """Reject overlap between DIFFERENT layers when either side may write.
    Sorted sweep; distinct physical IDs alone are never a byte-layout proof.
    """
    accesses = tuple(accesses)
    require(all(isinstance(a, Access) and a.start >= 0 and a.end > a.start
                and all(integer(x) for x in (a.storage, a.start, a.end)) and a.storage > 0 and
                isinstance(a.owner, str) and a.owner and type(a.write) is bool
                for a in accesses), "complete actual live footprint required")
    active = []
    for cur in sorted(accesses, key=lambda a: (a.storage, a.start, a.end, a.owner)):
        active = [old for old in active
                  if old.storage == cur.storage and old.end > cur.start]
        require(all(old.owner == cur.owner or not (old.write or cur.write)
                    for old in active), "cross-layer live read/write bytes overlap")
        active.append(cur)
    return True
