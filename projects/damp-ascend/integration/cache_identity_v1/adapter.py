"""Default-OFF CPU observer at actual Ascend runner/zeroer seams.

This preserves native arguments/returns; it never reads, copies, or modifies
device cache contents. A successful ticket is CPU pre-writer admission only.
"""
import functools
import hashlib
import importlib.util
import inspect
import json
import sys
from dataclasses import dataclass
from pathlib import Path

_DIR = Path(__file__).resolve().parent
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

c = _load("damp_cache_identity_contract_v1", _DIR/"contract.py")
ROOT = _DIR.parents[3]
CONTINUOUS = ROOT/"projects/damp-ascend/integration/continuous_metadata_v1/contract.py"
CONTINUOUS_SHA = "113f37c597e8b062b217217a48e7f087d885c3456b5efe53305264d9c7b64a1b"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCES = {
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
    "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py": "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/utils.py": "e75651c8742650f1bac7dddb5f39b9a636f289b4785864c984837ec12dcdae75",
    "/vllm-workspace/vllm/vllm/v1/worker/utils.py": "36cae980896d5607ce238606ec6c053eff17b7597a0c9185549f94583c1b9de6",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py": "8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py": "a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3",
    "/vllm-workspace/vllm/vllm/v1/kv_cache_interface.py": "8d6be98bbf75b3d55007b64ccf5afef047ca01790a432522f70a196412c103d9",
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_sources(image_id):
    c.require(image_id == IMAGE, "actual immutable image receipt missing")
    for path, sha in SOURCES.items():
        c.require(digest(path) == sha, "deployed source mismatch: "+path)
    c.require(digest(CONTINUOUS) == CONTINUOUS_SHA, "frozen continuous helper changed")

def native_callable(fn, path, name, names=None):
    c.require(inspect.isfunction(fn) and fn.__name__ == name and
              str(Path(inspect.getfile(fn)).resolve()) == path and digest(path) == SOURCES[path],
              "foreign/wrapped native callable owns seam: "+name)
    if names is not None:
        c.require(tuple(inspect.signature(fn).parameters) == tuple(names), "native seam signature changed")

def view_of(tensor, layer, region, kind, group):
    storage = tensor.untyped_storage()
    c.require(str(tensor.device).startswith(("npu:", "privateuseone:")), "actual NPU typed allocation missing")
    # All methods below return host-side tensor metadata; no .cpu/.clone/.tolist.
    item = int(tensor.element_size())
    base, pointer = int(storage.data_ptr()), int(tensor.data_ptr())
    return c.View(layer, region, kind, group, base, int(storage.nbytes()), pointer-base,
                  tuple(int(x) for x in tensor.shape), tuple(int(x) for x in tensor.stride()),
                  item, str(tensor.dtype), str(tensor.device)).validate()

@dataclass(frozen=True)
class Ticket:
    owner: int
    serial: int
    scheduler: int
    finished: frozenset
    predicted: dict
    zero_count: int

@dataclass(frozen=True)
class NativeReceipt:
    owner: int
    kind: str
    layer: str
    metadata_id: int
    values: dict
    producer_path: str
    producer_sha256: str

class AdmittedTurn:
    ready = False
    npu_executed = False
    performance_measurement_admitted = False
    status = "cpu-pre-writer-admitted-not-lifecycle-proof"
    def __init__(self, owner, ticket, turns, receipts):
        self.owner, self.ticket, self.turns, self.receipts = owner, ticket, dict(turns), dict(receipts)
        self.prechecked, self.started, self.consumed = set(), set(), set()
        self.closed = False

    def require_layer(self, prefix, native_metadata):
        c.require(not self.closed and not self.owner.retired and prefix in self.turns
                  and id(native_metadata) == self.receipts[prefix].metadata_id,
                  "stale/foreign actual GDN metadata")
        return self.turns[prefix]

    def before_writer(self, prefix, turn, native_metadata):
        c.require(turn == self.require_layer(prefix, native_metadata)
                  and prefix not in self.prechecked, "duplicate/foreign layer writer admission")
        self.prechecked.add(prefix)

    def writer_started(self, prefix):
        c.require(not self.closed and not self.owner.retired and prefix in self.prechecked
                  and prefix not in self.started, "writer before complete CPU admission or duplicate writer")
        self.started.add(prefix)

    def layer_succeeded(self, prefix):
        c.require(not self.closed and not self.owner.retired and prefix in self.started
                  and prefix not in self.consumed, "unstarted/duplicate layer success")
        self.consumed.add(prefix)

    def retire(self, prefix, reason, retry_allowed=False):
        c.require(retry_allowed is False and prefix in self.turns and isinstance(reason, str),
                  "partial writers never permit native fallback/retry")
        self.abort()

    def commit(self):
        self.owner.commit(self)

    def abort(self):
        self.closed = True
        self.owner.retire()

class Owner:
    """One actual runner. Retained LeaseBooks supplied by the core owner.

    Default source-bound scope: TP4 text/eager/prefix-off/mamba-none, no
    speculative/async/transfer/preemption relocation. Missing receipt => Pending.
    """
    def __init__(self, image_id, full_attention_type, mamba_type, leases):
        verify_sources(image_id)
        spec_path = "/vllm-workspace/vllm/vllm/v1/kv_cache_interface.py"
        c.require(all(str(Path(inspect.getfile(cls)).resolve()) == spec_path
                      for cls in (full_attention_type, mamba_type)), "foreign native cache spec classes")
        self.fa_type, self.mamba_type = full_attention_type, mamba_type
        self.cont = _load("damp_cache_identity_continuous_v1", CONTINUOUS)
        self.leases = leases
        self.runner_id = None
        self.views, self.groups, self.layers, self.refs = {}, {}, {}, {}
        self.zeroer, self.zero_segments, self.zero_page_bytes = None, (), None
        self.zero_meta_signature, self.native_zero = None, None
        self.serial, self.ticket, self.retired = 0, None, False
        self.admitted = None
        self.cold = False

    def retire(self):
        self.retired = True
        for book in self.leases.values():
            book.retire()

    def _runner(self, runner):
        c.require(not self.retired and self.cold and self.runner_id == id(runner),
                  "missing/retired/foreign cold cache identity")
        config = runner.vllm_config
        c.require(not config.cache_config.enable_prefix_caching and
                  config.cache_config.mamba_cache_mode == "none" and
                  config.model_config.enforce_eager and config.speculative_config is None and
                  config.kv_transfer_config is None and not runner.use_async_scheduling and
                  int(runner.pcp_size) == 1 and int(runner.dcp_size) == 1,
                  "unverified graph/prefix/async/spec/CP/cache-transfer path")
        for name, tensors in self.refs.items():
            for old, tensor in zip(self.views[name], tensors):
                c.require(view_of(tensor, name, old.region, old.kind, old.group) == old,
                          "actual typed geometry/storage changed")
        c.require(getattr(runner, "_kv_block_zeroer", None) is self.zeroer,
                  "native zeroer identity missing/changed")
        c.require(type(self.zeroer).__dict__.get("zero_block_ids") is self.native_zero,
                  "native zero writer callable changed")
        self.after_zeroer_init()

    def observe_cold(self, runner, config, raw, typed):
        c.require(not self.cold and not self.retired, "cold geometry can be registered once")
        native_callable(runner._get_layer_kv_cache_specs.__func__,
                        "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py",
                        "_get_layer_kv_cache_specs", ("self", "kv_cache_config"))
        specs = runner._get_layer_kv_cache_specs(config)
        skipped = runner.runner_only_attn_layers
        names = {n for group in config.kv_cache_groups for n in group.layer_names if n not in skipped}
        c.require(names == set(typed), "incomplete native typed group table")
        self.runner_id = id(runner)
        raw_regions = {}
        for allocation in config.kv_cache_tensors:
            owners = tuple(allocation.shared_by)
            c.require(owners and all(n in raw for n in owners), "actual shared_by/raw map missing")
            observed = []
            for name in owners:
                parts = raw[name] if isinstance(raw[name], (tuple, list)) else (raw[name],)
                observed.append(tuple((int(t.untyped_storage().data_ptr()), int(t.untyped_storage().nbytes()),
                                      int(t.data_ptr()), int(t.numel())*int(t.element_size())) for t in parts))
            c.require(all(x == observed[0] for x in observed), "shared_by does not alias declared native raw allocation")
            c.require(sum(x[3] for x in observed[0]) == int(allocation.size), "raw allocation budget/size changed")
            for name in owners:
                raw_regions[name] = observed[0]
        for gid, group in enumerate(config.kv_cache_groups):
            table = runner.input_batch.block_table[gid]
            c.require(str(Path(inspect.getfile(type(table))).resolve()) ==
                      "/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py",
                      "foreign native block-table producer")
            ratio = int(table.blocks_per_phys_block)
            bs = int(table.logical_block_size)
            physical_bs = int(table.physical_block_size)
            c.require(ratio >= 1 and bs*ratio == physical_bs and
                      bool(table.use_hybrid_blocks) == (ratio > 1),
                      "actual block-table physical/logical geometry drift")
            layer_names = tuple(n for n in group.layer_names if n not in skipped)
            self.groups[gid] = (layer_names, ratio, bs, physical_bs)
            for name in layer_names:
                spec = specs[name]
                kind = "fa" if isinstance(spec, self.fa_type) else (
                    "gdn" if isinstance(spec, self.mamba_type) else None)
                c.require(kind is not None and int(spec.block_size) == physical_bs,
                          "unsupported native cache spec/group block size")
                tensors = tuple(typed[name])
                regions = ("K", "V") if kind == "fa" else ("conv", "high", "low", "scales")
                c.require(len(tensors) == len(regions), "typed region cardinality changed")
                views = tuple(view_of(t, name, region, kind, gid) for t, region in zip(tensors, regions))
                if kind == "gdn":
                    c.require(ratio == 1 and len(spec.shapes) == len(spec.dtypes) == 4 and
                              [v.dtype for v in views[1:]] == ["torch.float16", "torch.int8", "torch.float32"],
                              "actual four-state GDN format/none slot ratio missing")
                    c.require(all(v.shape[1:] == tuple(sh) and v.dtype == str(dt)
                                  for v, sh, dt in zip(views, spec.shapes, spec.dtypes)),
                              "typed GDN shapes/dtypes disagree with native spec")
                c.require(len({v.shape[0] for v in views}) == 1, "region slot cardinalities differ")
                for v in views:
                    c.require(any(pointer <= v.storage+v.offset and
                                  v.storage+v.offset+(v.shape[0]-1)*v.pitch+v.width <= pointer+size and
                                  v.storage == base and v.storage_bytes == total
                                  for base, total, pointer, size in raw_regions[name]),
                              "typed region not inside original source-bound raw allocation")
                # Validate each layer's distinct regions, but cross-group sharing
                # is resolved per live request rather than forbidden by pointer alone.
                c.check_spans(tuple(s for v in views for s in v.blocks((0,), name+":"+v.region, True)))
                self.layers[name] = (kind, gid)
                self.views[name], self.refs[name] = views, tensors
        gdn = {n for n, (kind, _) in self.layers.items() if kind == "gdn"}
        fa = {n for n, (kind, _) in self.layers.items() if kind == "fa"}
        c.require(len(gdn) == 48 and len(fa) == 16 and set(self.leases) == gdn,
                  "actual Qwen3.6 48GDN/16FA and all-layer lease coverage required")
        c.require(all(type(book).__name__ == "LeaseBook" and
                      str(Path(inspect.getfile(type(book))).resolve()) == str(CONTINUOUS)
                      for book in self.leases.values()),
                  "frozen continuous LeaseBook identity required")
        self.cold = True

    def before_zeroer_init(self, zeroer, groups, kernel_sizes, skipped, context):
        c.require(self.cold and self.zeroer is None, "cold views required before one native zeroer init")
        segments, seen, page_bytes = [], set(), None
        for group in groups:
            spec = group.kv_cache_spec
            if not isinstance(spec, self.fa_type):
                continue
            gid = group.kv_cache_group_id
            if gid >= len(kernel_sizes):
                continue  # Exact native skip, coverage below prevents silent loss.
            kernel_bs = kernel_sizes[gid][0]
            c.require(c.integer(kernel_bs) and kernel_bs > 0 and spec.block_size % kernel_bs == 0,
                      "native zeroer first kernel block size invalid")
            for name in group.layer_names:
                if name in skipped:
                    continue
                c.require(name in self.views and self.layers[name] == ("fa", gid),
                          "zeroer group not in cold FA table")
                actual = context[name].kv_cache
                c.require(len(actual) == 2 and all(a is b for a, b in zip(actual, self.refs[name])),
                          "zeroer did not receive actual cold K/V views")
                for view, tensor in zip(self.views[name], actual):
                    address = int(tensor.data_ptr())
                    if address in seen:
                        continue
                    seen.add(address)
                    width = view.pitch*(spec.block_size//kernel_bs)
                    c.require(width % 4 == 0 and (page_bytes is None or width == page_bytes),
                              "native zeroer non-uniform int32 page")
                    page_bytes = width
                    segments.append((view, address))
        c.require(segments and {v.layer for v, _ in segments} ==
                  {n for n, (kind, _) in self.layers.items() if kind == "fa"},
                  "complete exact native FA zero segment coverage missing")
        self.zeroer, self.zero_segments, self.zero_page_bytes = zeroer, tuple(segments), page_bytes

    def after_zeroer_init(self):
        zero_path = "/vllm-workspace/vllm-ascend/vllm_ascend/worker/utils.py"
        zero_fn = type(self.zeroer).__dict__.get("zero_block_ids")
        native_callable(zero_fn, zero_path, "zero_block_ids", ("self", "block_ids"))
        if self.native_zero is None:
            self.native_zero = zero_fn
        c.require(zero_fn is self.native_zero, "native zero writer rebound")
        meta = self.zeroer._meta
        c.require(isinstance(meta, tuple) and len(meta) == 4 and meta[1]*4 == self.zero_page_bytes
                  and meta[3] == len(self.zero_segments) and
                  tuple(meta[0].shape) == (len(self.zero_segments),) and str(meta[0].dtype) == "torch.uint64",
                  "native zero metadata scalar/shape binding mismatch")
        signature = (id(meta[0]), int(meta[0].data_ptr()), tuple(meta[0].shape),
                     str(meta[0].dtype), str(meta[0].device), meta[1], meta[2], meta[3])
        if self.zero_meta_signature is None:
            self.zero_meta_signature = signature
        c.require(signature == self.zero_meta_signature, "native device zero table identity/scalars changed")
        # Contents are established by the pinned original init_meta receiving
        # these exact arguments; no device-table D2H is performed here.

    def _requests(self, runner, scheduler):
        finished = scheduler.finished_req_ids
        c.require(isinstance(finished, (set, frozenset)) and all(isinstance(x, str) for x in finished),
                  "native exact finished ID set missing")
        cached = scheduler.scheduled_cached_reqs
        c.require(not cached.resumed_req_ids and not scheduler.scheduled_spec_decode_tokens,
                  "preemption relocation/speculative path pending")
        predicted = {}
        for rid, request in runner.requests.items():
            if rid in finished:
                continue
            c.prompt_only(request)
            blocks = tuple(c.ids(x) for x in request.block_ids)
            c.require(len(blocks) == len(self.groups), "retained request group table incomplete")
            predicted[rid] = (id(request), blocks, None)
        c.require(len(set(cached.req_ids)) == len(cached.req_ids) and
                  len(cached.req_ids) == len(cached.new_block_ids) == len(cached.num_computed_tokens),
                  "cached scheduler arrays differ")
        for rid, new, computed in zip(cached.req_ids, cached.new_block_ids, cached.num_computed_tokens):
            c.require(rid in predicted and c.integer(computed) and computed >= 0 and
                      computed >= int(runner.requests[rid].num_computed_tokens),
                      "unknown cached identity/rewind length")
            generation, blocks, _ = predicted[rid]
            if new is not None:
                c.require(len(new) == len(blocks), "appended cache group table incomplete")
                blocks = tuple(c.ids(list(old)+list(extra)) for old, extra in zip(blocks, new))
            predicted[rid] = (generation, blocks, computed)
        for request in scheduler.scheduled_new_reqs:
            rid = request.req_id
            c.require(rid not in predicted and request.num_computed_tokens == 0,
                      "streaming/new-prefix/recompute request pending")
            c.prompt_only(request)
            blocks = tuple(c.ids(x) for x in request.block_ids)
            c.require(len(blocks) == len(self.groups), "new request group table incomplete")
            predicted[rid] = (None, blocks, 0)
        c.require(set(scheduler.num_scheduled_tokens) <= set(predicted) and
                  all(c.integer(x) and x > 0 for x in scheduler.num_scheduled_tokens.values()),
                  "actual scheduler token map invalid")
        return frozenset(finished), predicted

    def _retained(self, runner, finished):
        spans = []
        for name, book in self.leases.items():
            _, gid = self.layers[name]
            for slot, (rid, generation, computed) in book.records.items():
                if rid in finished:
                    continue
                request = runner.requests.get(rid)
                c.require(request is not None and id(request) == generation and computed > 0,
                          "paused/live GDN lease disappeared/recycled")
                logical = c.physical_to_logical(request.block_ids[gid], self.groups[gid][1])
                c.require(len(logical) == 1 and logical[0] == slot,
                          "retained GDN request moved or none-cache not single-slot")
                spans.extend(s for view in self.views[name] for s in view.blocks((slot,), name+":"+view.region+":"+rid, False))
        # Conservatively protect every retained allocated FA block, including
        # paused requests and allocation beyond currently computed sequence.
        for rid, request in runner.requests.items():
            if rid in finished:
                continue
            for name, (kind, gid) in self.layers.items():
                if kind == "fa":
                    blocks = c.physical_to_logical(request.block_ids[gid], self.groups[gid][1])
                    spans.extend(s for view in self.views[name] for s in view.blocks(blocks, name+":"+view.region+":"+rid, False))
        return spans

    def before_update(self, runner, scheduler_output):
        self._runner(runner)
        c.require(self.ticket is None, "previous CPU ticket not consumed/committed")
        finished, predicted = self._requests(runner, scheduler_output)
        spans = self._retained(runner, finished)
        # Include prospective GDN writes, before the native early FA zero writer.
        for name, (kind, gid) in self.layers.items():
            if kind == "gdn":
                for rid in scheduler_output.num_scheduled_tokens:
                    blocks = c.physical_to_logical(predicted[rid][1][gid], self.groups[gid][1])
                    c.require(len(blocks) == 1, "mamba-none requires one exact slot")
                    generation, _, computed = predicted[rid]
                    c.require(c.integer(computed), "active request absent from native scheduler cached/new rows")
                    records = {slot: record for slot, record in self.leases[name].records.items()
                               if record[0] not in finished}
                    previous = records.get(blocks[0])
                    if computed == 0:
                        c.require(previous is None and all(r[0] != rid for r in records.values()),
                                  "fresh prefill would overwrite/move a retained GDN lease")
                    else:
                        c.require(previous == (rid, generation, computed),
                                  "active GDN state uninitialized/recycled/relocated/rewound before cache-zero")
                    spans.extend(s for view in self.views[name] for s in view.blocks(blocks, name+":"+view.region+":"+rid, True))
        zero_ids = () if scheduler_output.new_block_ids_to_zero is None else scheduler_output.new_block_ids_to_zero
        spans.extend(c.zero_spans(self.zero_segments, self.zero_page_bytes, zero_ids))
        c.check_spans(spans)
        self.serial += 1
        self.ticket = Ticket(id(self), self.serial, id(scheduler_output), finished, predicted,
                             len(zero_ids))
        return self.ticket

    def after_update(self, runner, scheduler_output):
        c.require(self.ticket is not None and self.ticket.scheduler == id(scheduler_output),
                  "native update lost source-bound ticket")
        if not scheduler_output.num_scheduled_tokens:
            for book in self.leases.values():
                book.finish(self.ticket.finished)
            self.ticket = None

    def native_receipt(self, kind, layer, metadata, cpu_values, producer):
        c.require(kind in ("fa", "gdn") and self.layers.get(layer, (None,))[0] == kind
                  and type(cpu_values) is dict, "complete actual CPU metadata receipt required")
        path = ("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py" if kind == "gdn"
                else "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py")
        native_callable(producer, path, "build" if kind == "gdn" else "_build_attention_metadata")
        values = json.loads(json.dumps(cpu_values, allow_nan=False))  # CPU metadata only, no cache copies.
        return NativeReceipt(id(self), kind, layer, id(metadata), values, path, SOURCES[path])

    def before_model(self, runner, turns, native_cpu_receipts, ticket):
        self._runner(runner)
        c.require(ticket is self.ticket and ticket.owner == id(self) and self.admitted is None, "foreign/stale scheduler ticket")
        gdn = set(self.leases)
        c.require(set(turns) == gdn and set(native_cpu_receipts) == set(self.layers),
                  "complete 48GDN+16FA CPU/native receipt coverage missing (pending)")
        batch = runner.input_batch
        req_ids = tuple(batch.req_ids)
        c.require(req_ids and len(req_ids) <= 16 and len(set(req_ids)) == len(req_ids),
                  "exact eager post-reorder active rows missing")
        first = next(iter(turns.values()))
        c.require(tuple(row.request_id for row in first.rows) == req_ids,
                  "turn rows do not match actual reordered input batch")
        spans = self._retained(runner, ticket.finished)
        all_slots = []
        for name, (kind, gid) in self.layers.items():
            receipt = native_cpu_receipts[name]
            c.require(isinstance(receipt, NativeReceipt) and receipt.owner == id(self) and
                      receipt.layer == name and receipt.kind == kind, "foreign native metadata receipt")
            table = batch.block_table[gid]
            cpu = table.get_cpu_tensor()
            c.require(str(cpu.device) == "cpu" and str(cpu.dtype) == "torch.int32" and
                      getattr(cpu, "ndim", None) == 2 and str(table.num_blocks_per_row.dtype) == "int32",
                      "native block-table CPU mirror missing")
            for i, rid in enumerate(req_ids):
                request = runner.requests[rid]
                c.require(rid in ticket.predicted and (ticket.predicted[rid][0] is None or
                          ticket.predicted[rid][0] == id(request)),
                          "native request object generation drift")
                c.require(tuple(c.ids(x) for x in request.block_ids) == ticket.predicted[rid][1],
                          "native update changed predicted cache allocation")
                expected = c.physical_to_logical(request.block_ids[gid], self.groups[gid][1])
                count = int(table.num_blocks_per_row[i])
                actual = tuple(int(cpu[i, j]) for j in range(count))
                c.require(actual == expected, "actual CPU logical block table differs from request allocation")
                row = first.rows[i]
                c.require(id(request) == row.generation and
                          int(batch.num_computed_tokens_cpu[i]) == row.computed_tokens and
                          int(batch.num_prompt_tokens[i]) == row.prompt_tokens,
                          "native CPU request length/generation drift")
                if kind == "gdn":
                    turn = turns[name]
                    c.require(turn.starts == first.starts and
                              tuple(r.request_id for r in turn.rows) == req_ids and
                              tuple((r.generation, r.query_tokens, r.computed_tokens, r.prompt_tokens)
                                    for r in turn.rows) ==
                              tuple((r.generation, r.query_tokens, r.computed_tokens, r.prompt_tokens)
                                    for r in first.rows) and len(actual) == 1 and actual[0] == turn.rows[i].slot,
                              "all-layer GDN rows/slot identity differ")
                else:
                    readable, writable, slots = c.fa_blocks(actual, self.groups[gid][2],
                                                            row.computed_tokens, row.query_tokens)
                    all_slots.append((name, i, slots))
                    spans.extend(s for view in self.views[name]
                                 for s in view.blocks(readable, name+":"+view.region+":"+rid, False))
                    spans.extend(s for view in self.views[name]
                                 for s in view.blocks(writable, name+":"+view.region+":"+rid, True))
            if kind == "gdn":
                turn = turns[name]
                for key in ("non_spec_state_indices", "conv_starts"):
                    c.require(isinstance(receipt.values.get(key), list) and
                              all(c.integer(x) for x in receipt.values[key]),
                              "actual GDN CPU index/boundary dtype drift")
                self.cont.verify_native(turn, receipt.values)
                records = {slot: record for slot, record in self.leases[name].records.items()
                           if record[0] not in ticket.finished}
                temp = self.cont.LeaseBook()
                temp.records = records
                temp.check(turn)
                spans.extend(s for row in turn.rows for view in self.views[name]
                             for s in view.blocks((row.slot,), name+":"+view.region+":"+row.request_id, True))
            else:
                expected_slots = [slot for n, _, slots in all_slots if n == name for slot in slots]
                values = receipt.values
                c.require(all(isinstance(values.get(k), list) and
                              all(c.integer(x) for x in values[k])
                              for k in ("query_start_loc", "seq_lens", "slot_mapping")) and
                          values.get("request_ids") == list(req_ids) and
                          values.get("query_start_loc") == list(first.starts) and
                          values.get("seq_lens") == [r.computed_tokens+r.query_tokens for r in first.rows] and
                          values.get("slot_mapping") == expected_slots and
                          all(c.integer(x) for x in values["slot_mapping"]),
                          "source-bound actual FA read/write CPU receipt missing/drift")
        c.check_spans(spans)
        self.admitted = AdmittedTurn(self, ticket, turns, {n: native_cpu_receipts[n] for n in gdn})
        return self.admitted

    def commit(self, admitted):
        c.require(isinstance(admitted, AdmittedTurn) and admitted is self.admitted and admitted.owner is self and
                  not admitted.closed and not self.retired and admitted.ticket is self.ticket and
                  admitted.consumed == set(self.leases), "all48 cores must complete exactly once")
        for book in self.leases.values():
            book.finish(admitted.ticket.finished)
        for name, turn in admitted.turns.items():
            self.leases[name].commit(turn)
        admitted.closed, self.ticket, self.admitted = True, None, None

def wrap_update(original, owner_for):
    @functools.wraps(original)
    def update(runner, scheduler_output):
        owner = owner_for(runner)
        if owner is None:
            return original(runner, scheduler_output)
        try:
            owner.before_update(runner, scheduler_output)
            result = original(runner, scheduler_output)
            owner.after_update(runner, scheduler_output)
            return result
        except BaseException:
            owner.retire()
            raise
    return update

def install_runner_update(runner_cls, owner_for, enabled=False):
    if enabled is not True:
        return False
    fn = runner_cls.__dict__.get("_update_states")
    native_callable(fn, "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py",
                    "_update_states", ("self", "scheduler_output"))
    base = runner_cls.__mro__[1].__dict__.get("_update_states")
    native_callable(base, "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py",
                    "_update_states", ("self", "scheduler_output"))
    runner_cls._update_states = wrap_update(fn, owner_for)
    return True

def wrap_zeroer_init(original, owner_for_zeroer):
    @functools.wraps(original)
    def init(zeroer, attn_groups_iter, kernel_block_sizes, cache_dtype,
             runner_only_attn_layers, static_forward_context):
        owner = owner_for_zeroer(zeroer)
        if owner is None:
            return original(zeroer, attn_groups_iter, kernel_block_sizes, cache_dtype,
                            runner_only_attn_layers, static_forward_context)
        groups = tuple(attn_groups_iter)  # Native consumes this iterable exactly once.
        try:
            owner.before_zeroer_init(zeroer, groups, kernel_block_sizes,
                                     runner_only_attn_layers, static_forward_context)
            result = original(zeroer, groups, kernel_block_sizes, cache_dtype,
                              runner_only_attn_layers, static_forward_context)
            owner.after_zeroer_init()
            return result
        except BaseException:
            owner.retire()
            raise
    return init

def install_zeroer_init(zeroer_cls, owner_for_zeroer, enabled=False):
    if enabled is not True:
        return False
    fn = zeroer_cls.__dict__.get("init_meta")
    native_callable(fn, "/vllm-workspace/vllm-ascend/vllm_ascend/worker/utils.py", "init_meta",
                    ("self", "attn_groups_iter", "kernel_block_sizes", "cache_dtype",
                     "runner_only_attn_layers", "static_forward_context"))
    zeroer_cls.init_meta = wrap_zeroer_init(fn, owner_for_zeroer)
    return True
