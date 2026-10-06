"""Default-OFF observer for actual native builder invocations, not a NPU success.

Only CPU inputs are snapshotted in preview mode. Derived GPU fields are never
presented as observed values. Checked diagnostic mode explicitly reads metadata
(not cache contents) to CPU before any model writer; it is not formal performance.
"""
import contextvars
import functools
import hashlib
import inspect
import json
from dataclasses import dataclass
from pathlib import Path

_ACTIVE = contextvars.ContextVar("damp_cache_metadata_observer_v1", default=None)
HERE = Path(__file__).resolve().parent
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PINS = {
 "/vllm-workspace/vllm/vllm/v1/worker/gpu_input_batch.py": "caeeb20f5010d74663c45f9419237191e3c0a149f4c7aa25bc1b73b1112d67ae",
 "/vllm-workspace/vllm/vllm/v1/attention/backends/utils.py": "f4f2f106ad84aa77cdf0b09d6948878f4e74c56568309312ec47bd190cc710cd",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py": "8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py": "a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3",
 "/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py": "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
 "/vllm-workspace/vllm-ascend/vllm_ascend/attention/utils.py": "6a8c083d632cb745fb57b4bda522c44a2b967f44170be22aa0bc478145ba6dee",
 "/vllm-workspace/vllm/vllm/v1/attention/backend.py": "01e2068470081d2dcf3b676d454ed73d4728798fced35e76ebfa8f0fe4e5dad7",
 "/vllm-workspace/vllm/vllm/v1/worker/block_table.py": "b79a46abf8feb0e2ad9e9de64b55e6fc6d3597eadbd903993cbf4e3e74f1f324",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/utils.py": "e75651c8742650f1bac7dddb5f39b9a636f289b4785864c984837ec12dcdae75",
 "/vllm-workspace/vllm/vllm/v1/worker/utils.py": "36cae980896d5607ce238606ec6c053eff17b7597a0c9185549f94583c1b9de6",
}
FROZEN = {
 "adapter.py": "246648f4ffb59155aa94fc64a6b98128191245d358210af7f64c0cdef31a5cad",
 "contract.py": "8808ca268b73a2b8b07dab8fc8a9b575610db865ee47e44e803e471b902b048c",
}
class Pending(ValueError):
    pass

def require(value, message):
    if not value:
        raise Pending(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verify_sources(image_id):
    require(image_id == IMAGE, "actual image identity missing")
    for path, digest in PINS.items():
        require(sha(path) == digest, "actual source drift: "+path)
    for path, digest in FROZEN.items():
        require(sha(HERE.parent/path) == digest, "frozen cache helper drift: "+path)

def native_function(fn, path, name, parameters):
    require(inspect.isfunction(fn) and fn.__name__ == name and
            str(Path(inspect.getfile(fn)).resolve()) == path and sha(path) == PINS[path] and
            tuple(inspect.signature(fn).parameters) == tuple(parameters),
            "native callable/source/signature mismatch: "+name)

def cpu_list(tensor, dtype=None):
    require(str(tensor.device) == "cpu", "CPU input missing; no implicit D2H allowed")
    if dtype is not None:
        require(str(tensor.dtype) == dtype, "CPU metadata dtype drift")
    values = tensor.tolist()
    return json.loads(json.dumps(values, allow_nan=False))

def ints(values):
    require(isinstance(values, (list, tuple)) and all(type(x) is int for x in values),
            "exact integer list required")
    return tuple(values)

def descriptor(tensor):
    require(str(tensor.device).startswith(("npu:", "privateuseone:")),
            "original native NPU metadata buffer missing")
    storage = tensor.untyped_storage()
    return {"object_id": id(tensor), "storage_ptr": int(storage.data_ptr()),
            "storage_bytes": int(storage.nbytes()), "data_ptr": int(tensor.data_ptr()),
            "shape": list(tensor.shape), "stride": list(tensor.stride()),
            "dtype": str(tensor.dtype), "device": str(tensor.device)}

def same_storage(a, b):
    da, db = descriptor(a), descriptor(b)
    require(da["storage_ptr"] == db["storage_ptr"] and
            da["storage_bytes"] == db["storage_bytes"],
            "native builder field left original buffer storage")

def derived_fa_slots(rows, starts, logical_tables, block_size):
    require(type(block_size) is int and block_size > 0, "logical block size missing")
    require(len(starts) == len(rows)+1 and starts[0] == 0, "actual query boundary missing")
    result = []
    for i, row in enumerate(rows):
        computed, query = row
        require(type(computed) is int and computed >= 0 and type(query) is int and query > 0
                and starts[i+1]-starts[i] == query, "actual computed/query drift")
        blocks = ints(logical_tables[i])
        for position in range(computed, computed+query):
            index, offset = divmod(position, block_size)
            require(index < len(blocks) and blocks[index] >= 0, "FA allocated CPU table incomplete")
            result.append(blocks[index]*block_size+offset)
    return result

def gdn_mirror(turn, conv_slots):
    rows = turn.rows
    value = {
        "provenance": "derived_not_device_observed",
        "spec_sequence_masks": None,
        "num_actual_tokens": turn.starts[-1],
        "num_decodes": turn.num_decodes,
        "num_decode_tokens": turn.decode_tokens,
        "num_prefills": len(turn.prefill_rows),
        "non_spec_state_indices": [r.slot for r in rows],
        "conv_starts": list(turn.starts), "conv_slots": conv_slots,
    }
    if turn.prefill_rows:
        value.update(conv_has_initial=[r.computed_tokens > 0 for r in rows],
                     prefill_starts=list(turn.prefill_starts),
                     prefill_slots=list(turn.prefill_slots),
                     prefill_has_initial=list(turn.has_initial))
    if turn.num_decodes:
        value["decode_actual_seq_lengths"] = [0]+[1]*turn.num_decodes
    return value

@dataclass(frozen=True)
class Commit:
    table_id: int
    rows: tuple
    counts: tuple
    gpu: dict
    physical_block_size: int
    logical_block_size: int
    ratio: int

@dataclass(frozen=True)
class Event:
    kind: str
    builder_id: int
    names: tuple
    metadata: object
    common: object
    values: dict
    bindings: dict

@dataclass(frozen=True)
class Preview:
    serial: int
    runner_id: int
    ticket: object
    turns: dict
    events: tuple
    by_layer: dict
    native_mapping: dict
    status: str = "derived_not_device_observed"
    ready: bool = False
    npu_executed: bool = False
    performance_measurement_admitted: bool = False

class Producer:
    """Actual per-runner invocation collector; no fake per-layer builder calls.

    Native-only preview can run without candidate admission. Candidate path must
    call checked_admission before its first model writer; formal performance is
    deliberately pending until independent mirror/lifecycle gates are supplied.
    """
    def __init__(self, owner, image_id):
        verify_sources(image_id)
        self.owner = owner
        self.commits = {}
        self.events, self.turns, self.active = [], {}, False
        self.runner, self.ticket, self.serial = None, None, 0
        self.preview = None
        self.last_comparison, self.last_failure = None, None
        self.native_runner_build, self.native_gdn_build = None, None

    def observe_commit(self, table, num_reqs):
        require(type(num_reqs) is int and num_reqs > 0, "actual commit row count missing")
        cpu = table.get_cpu_tensor()
        values = cpu_list(cpu[:num_reqs], "torch.int32")
        counts = tuple(int(x) for x in table.num_blocks_per_row[:num_reqs])
        require(str(table.num_blocks_per_row.dtype) == "int32" and
                len(values) == len(counts) == num_reqs and all(x > 0 for x in counts),
                "actual CPU committed table/counts missing")
        ratio, pbs, lbs = int(table.blocks_per_phys_block), int(table.physical_block_size), int(table.logical_block_size)
        require(ratio >= 1 and pbs == ratio*lbs and bool(table.use_hybrid_blocks) == (ratio > 1),
                "physical/kernel block ratio changed")
        rows = tuple(ints(row) for row in values)
        require(all(n <= len(row) for n, row in zip(counts, rows)), "CPU logical row overflow")
        self.commits[id(table)] = Commit(id(table), rows, counts, descriptor(table.get_device_tensor()),
                                         pbs, lbs, ratio)

    def begin(self, runner, bound):
        require(not self.active and self.preview is None and self.owner.ticket is not None,
                "pending previous preview or missing pre-zero scheduler ticket")
        self.owner._runner(runner)
        count = len(runner.input_batch.req_ids)
        require(1 <= count <= 16 and bound["num_reqs"] == count and
                bound["num_reqs_padded"] in (None, count) and
                bound["num_tokens_padded"] in (None, bound["num_tokens"]) and
                bound["ubatch_slices"] is None and not bound["use_spec_decode"] and
                not bound["for_cudagraph_capture"],
                "graph/padding/ubatch/spec metadata path pending")
        self.runner, self.ticket = runner, self.owner.ticket
        self.events, self.turns, self.active = [], {}, True
        self.serial += 1

    def input(self, builder, common, kind, kwargs):
        require(self.active and kind in ("gdn", "fa") and kwargs.get("common_prefix_len") == 0
                and not kwargs.get("fast_build", False),
                "builder invocation outside active non-cascade/eager scope")
        if kind == "gdn":
            require(kwargs.get("num_accepted_tokens") is None and
                    kwargs.get("num_decode_draft_tokens_cpu") is None, "spec inputs pending")
        names = tuple(builder.layer_names)
        require(names and len(set(names)) == len(names) and
                all(self.owner.layers.get(n, (None,))[0] == kind for n in names),
                "actual builder layer/group ownership missing")
        gids = {self.owner.layers[n][1] for n in names}
        require(len(gids) == 1, "native builder straddles cache groups")
        gid = next(iter(gids))
        table = self.runner.input_batch.block_table[gid]
        commit = self.commits.get(id(table))
        n = len(self.runner.input_batch.req_ids)
        require(commit is not None and len(commit.rows) == n and
                descriptor(table.get_device_tensor()) == commit.gpu,
                "actual prior CPU->GPU BlockTable commit not observed")
        require(int(common.num_reqs) == n and int(common.num_actual_tokens) > 0 and
                int(common.num_input_tokens) == int(common.num_actual_tokens),
                "padded/common token cardinality pending")
        starts = ints(cpu_list(common.query_start_loc_cpu[:n+1], "torch.int32"))
        computed = ints([int(x) for x in self.runner.input_batch.num_computed_tokens_cpu[:n]])
        prompts = ints([int(x) for x in self.runner.input_batch.num_prompt_tokens[:n]])
        seq = ints(cpu_list(common._seq_lens_cpu[:n], "torch.int32"))
        is_prefilling = cpu_list(common.is_prefilling[:n], "torch.bool")
        require(len(starts) == n+1 and starts[0] == 0 and starts[-1] == int(common.num_actual_tokens)
                and seq == tuple(computed[i]+starts[i+1]-starts[i] for i in range(n))
                and is_prefilling == [computed[i] < prompts[i] for i in range(n)],
                "actual CPU query/sequence/prefill drift")
        same_storage(common.block_table_tensor, table.get_device_tensor())
        same_storage(common.slot_mapping, table.slot_mapping.gpu)
        tables = tuple(row[:count] for row, count in zip(commit.rows, commit.counts))
        for i, rid in enumerate(self.runner.input_batch.req_ids):
            request = self.runner.requests[rid]
            # Physical conversion belongs to frozen cache contract, not the continuous helper.
            physical = ints(request.block_ids[gid])
            logical = tuple(p*commit.ratio+k for p in physical for k in range(commit.ratio))
            require(logical == tables[i], "committed logical table differs from actual request allocation")
        bindings = {"cpu_origin": "native_builder_common_and_blocktable_commit",
                    "query": descriptor(common.query_start_loc), "seq": descriptor(common.seq_lens),
                    "block_table": descriptor(common.block_table_tensor),
                    "slot_mapping": descriptor(common.slot_mapping),
                    "block_commit": {"table_id": commit.table_id, "rows": [list(x) for x in commit.rows],
                                     "counts": list(commit.counts), "gpu": commit.gpu},
                    "computed": list(computed), "prompt": list(prompts),
                    "starts": list(starts), "seq_lens": list(seq),
                    "names": list(names), "group": gid, "ratio": commit.ratio,
                    "logical_block_size": commit.logical_block_size}
        if kind == "gdn":
            require(commit.ratio == 1 and all(len(x) == 1 for x in tables), "mamba-none single slots missing")
            for name in names:
                rows = tuple(self.owner.cont.Row(rid, tables[i][0], starts[i+1]-starts[i],
                            computed[i], prompts[i], id(self.runner.requests[rid]))
                            for i, rid in enumerate(self.runner.input_batch.req_ids))
                turn = self.owner.cont.plan(rows, starts, self.owner.views[name][0].shape[0])
                self.turns[name] = turn
            mirror = gdn_mirror(self.turns[names[0]], [list(x) for x in tables])
        else:
            mirror = {"provenance": "derived_not_device_observed",
                      "request_ids": list(self.runner.input_batch.req_ids),
                      "query_start_loc": list(starts), "seq_lens": list(seq),
                      "slot_mapping": derived_fa_slots(tuple((computed[i], starts[i+1]-starts[i])
                                         for i in range(n)), starts, tables, commit.logical_block_size)}
        return names, mirror, bindings

    def output(self, builder, common, metadata, kind, prepared):
        names, mirror, bindings = prepared
        require(not any(set(e.names) & set(names) for e in self.events), "duplicate native group build")
        if kind == "gdn":
            require(metadata.spec_sequence_masks is None and int(metadata.num_spec_decodes) == 0 and
                    int(metadata.num_spec_decode_tokens) == 0, "spec native metadata pending")
            for key in ("num_actual_tokens", "num_decodes", "num_decode_tokens", "num_prefills"):
                require(type(getattr(metadata, key)) is int and getattr(metadata, key) == mirror[key],
                        "native GDN counts disagree with CPU source mirror")
            conv = (metadata.non_spec_prefill_metadata.causal_conv1d if mirror["num_prefills"]
                    else metadata.non_spec_decode_metadata.causal_conv1d)
            same_storage(conv.query_start_loc, common.query_start_loc)
            same_storage(conv.cache_indices, common.block_table_tensor)
            bindings["conv_query"], bindings["conv_slots"] = descriptor(conv.query_start_loc), descriptor(conv.cache_indices)
            same_storage(metadata.non_spec_state_indices_tensor, common.block_table_tensor)
            bindings["state_indices"] = descriptor(metadata.non_spec_state_indices_tensor)
            if mirror["num_prefills"]:
                require(list(metadata.non_spec_prefill_metadata.chunk.cu_seqlens_host) == mirror["prefill_starts"],
                        "actual CPU chunk boundary disagrees with prefill suffix")
        else:
            require(int(metadata.num_actual_tokens) == common.num_actual_tokens and
                    metadata.actual_seq_lengths_q == mirror["query_start_loc"][1:] and
                    metadata.seq_lens_list == mirror["seq_lens"],
                    "actual FA CPU result fields disagree")
            same_storage(metadata.block_tables, common.block_table_tensor)
            same_storage(metadata.slot_mapping, common.slot_mapping)
            bindings["fa_query"] = descriptor(metadata.query_start_loc)  # Native copies CPU starts to a new GPU buffer.
        self.events.append(Event(kind, id(builder), names, metadata, common, mirror, bindings))

    def finish(self, result):
        require(self.active and isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict),
                "actual per-layer metadata mapping missing")
        mapping = result[0]
        observed = {n: e for e in self.events for n in e.names}
        require(set(observed) == set(self.owner.layers) == set(mapping) and
                len(self.turns) == 48 and sum(self.owner.layers[n][0] == "fa" for n in mapping) == 16 and
                all(mapping[n] is observed[n].metadata for n in mapping),
                "complete actual native builder/group->48GDN/16FA mapping missing")
        self.preview = Preview(self.serial, id(self.runner), self.ticket, dict(self.turns),
                               tuple(self.events), observed, dict(mapping))
        self.active = False
        self.commits = {}  # A later turn needs a newly observed native commit, not a stale CPU table.
        return self.preview

    def pending_formal(self):
        raise Pending("formal admission pending: independent checked mirror, lifecycle and native output gates")

    def checked_admission(self, preview, *, mode="off", formal_perf=False):
        require(mode == "checked-diagnostic" and formal_perf is False and
                preview is self.preview and preview.ticket is self.owner.ticket,
                "only explicit non-performance checked diagnostic may read device metadata")
        receipts, comparisons = {}, []
        try:
            for event in preview.events:
                self.last_comparison = {"names": list(event.names), "kind": event.kind,
                                        "expected": event.values, "actual": None,
                                        "bindings": event.bindings}
                actual = device_values(event)
                self.last_comparison["actual"] = actual
                compare_values(event.values, actual)
                comparisons.append({"names": list(event.names), "kind": event.kind,
                                    "metadata_id": id(event.metadata), "status": "equal",
                                    "device_observed": True, "bindings": event.bindings})
                for name in event.names:
                    producer = self.native_gdn_build if event.kind == "gdn" else self.native_runner_build
                    receipts[name] = self.owner.native_receipt(event.kind, name, event.metadata,
                        dict(actual, provenance="checked_device_metadata_diagnostic"), producer)
            admitted = self.owner.before_model(self.runner, preview.turns, receipts, preview.ticket)
            report = {"schema": "damp-native-mirror-check/v1", "status": "checked_metadata_equal",
                      "npu_metadata_read": True, "cache_contents_read": False,
                      "performance_measurement_admitted": False, "ready": False,
                      "source_sha256": PINS, "runner_id": preview.runner_id,
                      "serial": preview.serial, "native_builder_calls": len(preview.events),
                      "gdn_layers": 48, "fa_layers": 16, "comparisons": comparisons}
            self.preview = None
            return admitted, report
        except BaseException as error:
            self.last_failure = {"schema": "damp-native-mirror-failure/v1",
                                 "status": "failed", "ready": False,
                                 "performance_measurement_admitted": False,
                                 "serial": preview.serial,
                                 "comparison": self.last_comparison,
                                 "error_type": type(error).__name__, "error": str(error)}
            self.owner.retire()
            raise

    def discard_native_preview(self):
        require(self.preview is not None, "no preview")
        # Native-only observer arm must not fabricate DAMP LeaseBook commits.
        self.preview = None

def read_metadata(tensor):
    require(str(tensor.device).startswith(("npu:", "privateuseone:")),
            "checked gate must read actual NPU metadata, not CPU fixture")
    # Deliberate diagnostic D2H. Never called by preview or formal performance.
    return tensor.detach().cpu().tolist()

def device_values(event):
    md = event.metadata
    if event.kind == "fa":
        # In this pinned eager builder md.seq_lens is the original CPU tensor.
        # Observe it as CPU; independently check the CommonMetadata GPU seq_lens.
        native_cpu_seq = cpu_list(md.seq_lens, "torch.int32")
        device_seq = read_metadata(event.common.seq_lens)
        require(native_cpu_seq == device_seq, "actual FA CPU result/GPU common sequence lengths differ")
        return {"request_ids": event.values["request_ids"],
                "query_start_loc": read_metadata(md.query_start_loc),
                "seq_lens": device_seq,
                "slot_mapping": read_metadata(md.slot_mapping)}
    result = {k: getattr(md, k) for k in ("num_actual_tokens", "num_decodes", "num_decode_tokens", "num_prefills")}
    result["spec_sequence_masks"] = md.spec_sequence_masks
    result["non_spec_state_indices"] = read_metadata(md.non_spec_state_indices_tensor)
    conv = (md.non_spec_prefill_metadata.causal_conv1d if md.num_prefills
            else md.non_spec_decode_metadata.causal_conv1d)
    result.update(conv_starts=read_metadata(conv.query_start_loc), conv_slots=read_metadata(conv.cache_indices))
    if md.num_prefills:
        result.update(conv_has_initial=read_metadata(conv.initial_state_mode),
                      prefill_starts=read_metadata(md.prefill_query_start_loc),
                      prefill_slots=read_metadata(md.prefill_state_indices),
                      prefill_has_initial=read_metadata(md.prefill_has_initial_state))
    if md.num_decodes:
        result["decode_actual_seq_lengths"] = read_metadata(md.non_spec_decode_metadata.actual_seq_lengths)
    return result

def compare_values(expected, actual):
    expected = {k: v for k, v in expected.items() if k != "provenance"}
    require(expected == actual, "derived mirror differs from independently read native NPU metadata")
    return True

def wrap_commit(original, producer_for_table):
    @functools.wraps(original)
    def commit(table, num_reqs):
        producer = producer_for_table(table)
        if producer is None:
            return original(table, num_reqs)
        try:
            producer.observe_commit(table, num_reqs)  # Exact CPU input before native nonblocking copy.
            return original(table, num_reqs)
        except BaseException:
            producer.owner.retire()
            raise
    return commit

def wrap_builder(original, kind):
    sig = inspect.signature(original)
    @functools.wraps(original)
    def build(builder, *args, **kwargs):
        producer = _ACTIVE.get()
        if producer is None:
            return original(builder, *args, **kwargs)
        bound = sig.bind(builder, *args, **kwargs); bound.apply_defaults()
        common = bound.arguments["common_attn_metadata"]
        prepared = producer.input(builder, common, kind, bound.arguments)
        result = original(builder, *args, **kwargs)
        producer.output(builder, common, result, kind, prepared)
        return result
    return build

def wrap_runner(original, producer_for_runner, after_preview=None):
    sig = inspect.signature(original)
    @functools.wraps(original)
    def build(runner, *args, **kwargs):
        producer = producer_for_runner(runner)
        if producer is None:
            return original(runner, *args, **kwargs)
        bound = sig.bind(runner, *args, **kwargs); bound.apply_defaults()
        producer.begin(runner, bound.arguments)
        token = _ACTIVE.set(producer)
        try:
            result = original(runner, *args, **kwargs)
            preview = producer.finish(result)
            if after_preview is not None:
                after_preview(producer, preview)  # Diagnostic/admission policy is explicit outside this observer.
            return result
        except BaseException:
            producer.owner.retire()
            raise
        finally:
            _ACTIVE.reset(token)
    return build

def install(runner_cls, gdn_builder_cls, fa_builder_cls, block_table_cls,
            producer_for_runner, producer_for_table, after_preview=None, *, enabled=False):
    if enabled is not True:
        return False
    sources = [
      (runner_cls, "_build_attention_metadata", "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py",
       ("self","num_tokens","num_reqs","max_query_len","num_tokens_padded","num_reqs_padded","ubatch_slices",
        "logits_indices","use_spec_decode","for_cudagraph_capture","num_scheduled_tokens","num_scheduled_tokens_np",
        "cascade_attn_prefix_lens")),
      (gdn_builder_cls, "build", "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py",
       ("self","common_prefix_len","common_attn_metadata","num_accepted_tokens","num_decode_draft_tokens_cpu","fast_build")),
      (fa_builder_cls, "build", "/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py",
       ("self","common_prefix_len","common_attn_metadata","fast_build")),
      (block_table_cls, "commit_block_table", "/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py", ("self","num_reqs")),
    ]
    originals = []
    for cls, name, path, params in sources:
        original = cls.__dict__.get(name)
        native_function(original, path, name, params)
        originals.append(original)
    runner_original, gdn_original, fa_original, block_original = originals
    # Producer accessors bind frozen original functions; do not inspect newly wrapped aliases.
    def for_runner(runner):
        p = producer_for_runner(runner)
        if p is not None:
            p.native_runner_build, p.native_gdn_build = runner_original, gdn_original
        return p
    runner_cls._build_attention_metadata = wrap_runner(runner_original, for_runner, after_preview)
    gdn_builder_cls.build = wrap_builder(gdn_original, "gdn")
    fa_builder_cls.build = wrap_builder(fa_original, "fa")
    block_table_cls.commit_block_table = wrap_commit(block_original, producer_for_table)
    return True
