"""Strict, stdlib-only component admission. Missing authority fails closed.

This validates MAIN-issued expectations, NOT a cryptographic signature. Tests
cannot authenticate AWMCP JSON. Never grants serving, graph or performance.
"""
from dataclasses import dataclass
from collections import Counter
from pathlib import PurePosixPath
import hashlib
import json
import math
import re
import types

REPO = "/opt/host/vnf/austinov/model-tuning-lab"
BASE = "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/gate_v1"
HERE = BASE + "/admission_v1"
RUNTIME_SHA = "7ea60a45ea46f28811c16455885eab46dbd78bce5586a8914f06a701dbcd4ed1"
CONTRACT_SHA = "c77651b97b1aa4e32351afab54e7688bd8fded1df3a989baf3d7a2a281aedcda"
ANCHOR_SHA = "d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8"
REFERENCE_SO = "853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8"
NATIVE_SO = "eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
PEER = "lgw_a6109c51076a4a2c9d2674ca5a8704a0"
SUCCESS_GUARDS = frozenset((
    "immutable_inputs_bitwise", "all_input_pointer_offset_stride_stable",
    "conv_FA_guard_padding_untouched_slots_bitwise", "entire_raw_bitwise",
    "all_views_pointer_storage_stride_stable", "raw_storage_shared", "full_arena_no_sidecar"))
NUMERIC_GUARDS = frozenset((
    "immutable_inputs_bitwise", "all_input_pointer_offset_stride_stable",
    "conv_FA_guard_padding_untouched_slots_bitwise", "all_selected_slots_retired"))
FEEDBACK_GUARDS = frozenset((
    "protected_and_untouched_bitwise", "arena_identity_stable", "output_fresh_nonalias",
    "immutable_inputs_bitwise", "all_pointers_stable", "output_ABI", "output_ND"))
HEALTH = {"dispatch_error": None, "output_copy_errors": [],
          "input_copy_errors": [], "pointer_query_errors": []}

class Pending(RuntimeError):
    """Not enough complete, source-bound actual evidence; keep default OFF."""

def need(ok, message):
    if not ok:
        raise Pending(message)

def digest(data):
    need(type(data) is bytes, "reader must return original bytes")
    return hashlib.sha256(data).hexdigest()

def hex_sha(value):
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None

def absolute(path):
    return (type(path) is str and path.startswith("/") and
            str(PurePosixPath(path)) == path and ".." not in PurePosixPath(path).parts)

@dataclass(frozen=True)
class Ref:
    path: str
    sha256: str
    def __post_init__(self):
        need(absolute(self.path) and hex_sha(self.sha256), "absolute canonical Ref/SHA required")

def as_ref(value):
    need(type(value) is dict and set(value) == {"path", "sha256"}, "exact two-field Ref")
    return Ref(value["path"], value["sha256"])

def ref_dict(ref):
    return {"path": ref.path, "sha256": ref.sha256}

@dataclass(frozen=True)
class TerminalAuthority:
    receipt: Ref
    peer: str
    operation_id: str
    command: str
    args: tuple
    cwd: str

@dataclass(frozen=True)
class RunAuthority:
    stage: str
    report: Ref
    child: Ref
    terminal: TerminalAuthority
    child_command: str
    child_args: tuple
    child_cwd: str
    container_id: str
    physical_card: int
    owner_proof: Ref
    controller_sources: tuple   # tuple[Ref,...], MAIN expected real controller source bytes

@dataclass(frozen=True)
class ComponentAuthority:
    status: str
    reports: tuple
    child_receipts: tuple
    terminal_receipts: tuple
    operation_ids: tuple
    source_manifest: Ref
    runtime_manifest: Ref
    libraries: tuple
    native_anchor: Ref
    physical_cards: tuple
    controller_sources: tuple
    batches: tuple = (1, 16)
    feedback_steps: int = 160
    native_case_count: int = 8
    isolated_case_count: int = 134
    plan_index: object = None
    serving_ready: bool = False
    performance_measurement_admitted: bool = False
    graph_supported: bool = False
    all_prefill_batches_supported: bool = False
    full_model_cache_supported: bool = False
    authority_kind: str = "MAIN-issued-expectation-not-cryptographic-signature"
    scope: str = "standalone-selected-pack-unpack-native-chunk-feedback-B1-B16"

def checked(ref, read_bytes):
    try:
        data = read_bytes(ref.path)
    except (OSError, KeyError) as error:
        raise Pending("original bytes unavailable: " + ref.path) from error
    need(digest(data) == ref.sha256, "byte SHA mismatch: " + ref.path)
    return data

def json_bytes(data):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, "duplicate JSON key: " + key)
            out[key] = value
        return out
    def nonfinite(value):
        raise Pending("nonfinite JSON: " + value)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    except Pending:
        raise
    except Exception as error:
        raise Pending("invalid JSON bytes") from error

def json_ref(ref, read_bytes):
    value = json_bytes(checked(ref, read_bytes))
    need(type(value) is dict, "object JSON required")
    return value

def source_map(rows, read_bytes):
    need(type(rows) is dict and rows, "nonempty source identity")
    for path, sha in rows.items():
        target = path if absolute(path) else REPO + "/" + path
        checked(Ref(target, sha), read_bytes)

def frozen_contract(read_bytes):
    raw = checked(Ref(REPO + "/" + BASE + "/selected_contract.py", CONTRACT_SHA), read_bytes)
    # Only a byte-pinned, already reviewed stdlib module is executed here.
    module = types.ModuleType("_damp_selected_frozen_contract")
    exec(compile(raw, REPO + "/" + BASE + "/selected_contract.py", "exec"), module.__dict__)
    return module

def schemas():
    args = ("Tensor dense, Tensor hi, Tensor lo, Tensor scales, Tensor pk, Tensor pv, Tensor sr, "
            "Tensor indices, bool use_float_candidate=False")
    mutable = args.replace("Tensor hi", "Tensor(a!) hi").replace("Tensor lo", "Tensor(b!) lo").replace(
        "Tensor scales", "Tensor(c!) scales")
    ns = "qwen36_damp_selected_prefill_v1::"
    return {"pack": ns + "pack(" + mutable + ") -> Tensor",
            "prepare": ns + "prepare(" + args + ") -> ()"}

def pack_matrix(c):
    rows = {}
    for p in (1, 16):
        for kind in ("adjacent", "guard_gaps"):
            prefix = "P" + str(p) + "_" + kind
            for turn in range(20):
                rows[prefix + "_changing_" + str(turn)] = (p, 0, c.selection(p, p + 3, turn))
            for turn in range(8):
                rows[prefix + "_reset_" + str(turn)] = (p, 0, c.selection(p, p + 3, 19))
            rows[prefix + "_PAD"] = (p, 1, [-1] + c.selection(p, p + 3)[1:])
            rows[prefix + "_range"] = (p, 1, [p + 3] + c.selection(p, p + 3)[1:])
            if p == 16:
                rows[prefix + "_duplicate"] = (p, 1, [0, 0] + c.selection(p, p + 3)[2:])
            for label, error in (("NaN", 2), ("FP16overflow", 2), ("scale_underflow", 3)):
                rows[prefix + "_" + label] = (p, error, c.selection(p, p + 3))
    return rows

def host_labels():
    names = (["dtype" + str(i) for i in range(8)] +
             ["shape" + str(i) for i in range(8)] + ["P0", "P17"] +
             ["noncontiguous" + str(i) for i in (0, 4, 5, 6, 7)] +
             ["offset4B", "CPU", "readonly_plan_alias"])
    return (["host_" + n + "_" + m for n in names for m in ("prepare", "pack")] +
            ["host_" + n + "_prepare" for n in ("Pkduplicate", "Pvduplicate", "SRzero", "SRnegative", "SRNaN")])

def native_matrix(c):
    return {"native_P" + str(p) + "_" + kind + "_" + mode:
            (p, 0, c.selection(p, p + 3, 1))
            for p in (1, 16) for kind in ("adjacent", "guard_gaps") for mode in ("fresh", "continuation")}

def pack_cases(report, expected, c, origin):
    need(type(report.get("cases")) is list and len(report["cases"]) == len(expected),
         "complete exact pack-case count")
    by_label = {}
    for row in report["cases"]:
        label = row.get("label")
        need(label in expected and label not in by_label, "missing/duplicate/extra packing case")
        p, error, slots = expected[label]
        need(type(row.get("p")) is int and row["p"] == p and row.get("indices") == slots and
             all(type(n) is int for n in row["indices"]), "packing batch/slot identity")
        need(row.get("passed") is True and row.get("fixture_origin") == origin and
             hex_sha(row.get("raw_after_sha256")), "packing result/origin/raw identity")
        guards = row.get("guards")
        wanted = NUMERIC_GUARDS if error in (2, 3) else SUCCESS_GUARDS
        need(type(guards) is dict and set(guards) == wanted and all(v is True for v in guards.values()),
             "all complete-state/input/shared-arena guards required")
        rows = row.get("status_rows")
        need(type(rows) is list and len(rows) == p * 12 and
             all(type(r) is list and len(r) == 8 and all(type(x) is int for x in r) for r in rows),
             "all twelve P status rows required")
        # Successful report serializes rows, not the original guarded full status
        # tensor. Source-pinned pack_once validated the complete raw status first.
        raw = [c.GUARD] * 8 + [x for r in rows for x in r] + [c.GUARD] * 8
        try:
            c.status_rows(raw, p, error)
        except Exception as failure:
            raise Pending("packing status ABI or pre-writer rejection") from failure
        by_label[label] = row
    return by_label

def checks(report, expected):
    rows = report.get("checks")
    need(type(rows) is list and Counter(r.get("name") for r in rows) == expected,
         "exact source-bound check multiset incomplete/duplicate/extra")
    for row in rows:
        need(row.get("passed") is True, "check failed")
        name, detail = row["name"], row.get("details")
        if name.endswith("_dispatch") or name.endswith("_dispatch_and_nullable_D2H"):
            need(detail == HEALTH, "poisoned dispatch/copy/pointer evidence")
        elif name.endswith("_rejected_all_inputs_raw_unchanged"):
            need(type(detail) is dict and type(detail.get("dispatch_error")) is dict and
                 type(detail["dispatch_error"].get("error")) is str and
                 type(detail["dispatch_error"].get("traceback")) is str,
                 "host rejection must retain ORIGINAL exception")
    return rows

def expected_pack_checks(labels):
    out = Counter()
    for label in labels:
        for suffix in ("_dispatch_and_nullable_D2H", "_status_fresh_nonalias", "_full_raw_inputs_status"):
            out[label + suffix] += 1
    return out

def isolated(report, c):
    matrix = pack_matrix(c)
    cases = pack_cases(report, matrix, c, "CPU-FP32-isolated-not-native")
    need(report.get("native_prefill_verified") is False and report.get("decode_feedback_verified") is False and
         report.get("fixture_origin") == "CPU-FP32-isolated-not-native", "isolated must not claim native")
    wanted_hosts = host_labels()
    hosts = report.get("host_negatives")
    need(type(hosts) is list and len(hosts) == len(wanted_hosts) and
         Counter(r.get("label") for r in hosts) == Counter(wanted_hosts) and
         all(r.get("passed") is True for r in hosts), "all 57 host pre-dispatch rejections")
    retired = report.get("retired_calls")
    wanted_retired = {label: {"label": label, "slots": value[2], "retry_allowed": False, "whole_call": True}
                      for label, value in matrix.items() if value[1] in (2, 3)}
    need(type(retired) is list and len(retired) == 12 and
         {r.get("label"): r for r in retired} == wanted_retired, "retire ENTIRE numeric call; no retry")
    expected = expected_pack_checks(matrix)
    expected.update({"prepare_dispatch": 4, "prepare_all_inputs_full_raw_unchanged": 4,
                     "identical_reset_determinism": 32})
    expected.update({label + "_rejected_all_inputs_raw_unchanged": 1 for label in wanted_hosts})
    rows = checks(report, expected)
    for row in rows:
        if row["name"].endswith("_full_raw_inputs_status"):
            label = row["name"][:-len("_full_raw_inputs_status")]
            need(row["details"] == cases[label]["guards"], "guard record/result mismatch")
    for p in (1, 16):
        for kind in ("adjacent", "guard_gaps"):
            prefix = "P" + str(p) + "_" + kind
            hashes = [cases[prefix + "_reset_" + str(i)]["raw_after_sha256"] for i in range(8)]
            need(len(set(hashes)) == 1, "eight reset replays not bitwise deterministic")
            changing = [cases[prefix + "_changing_" + str(i)]["raw_after_sha256"] for i in range(20)]
            need(len(set(changing)) >= 2, "same-buffer changing matrix not observed")
    need(not report.get("feedback_cases") and not report.get("native_bindings"), "isolated scope inflated")
    negatives = {label for label, value in matrix.items() if value[1]} | set(wanted_hosts)
    return {"negative_" + label + ".pt" for label in negatives}

def native_feedback(report, c):
    matrix = native_matrix(c)
    cases = pack_cases(report, matrix, c, "actual_native_chunk_FP32_final")
    need(report.get("native_prefill_verified") is True and report.get("decode_feedback_verified") is True and
         not report.get("retired_calls") and not report.get("host_negatives"), "native scope/error retirement")
    rows = report.get("feedback_cases")
    need(type(rows) is list and len(rows) == 8, "eight fresh/continuation own-feedback cases")
    seen = set()
    expected = expected_pack_checks(matrix)
    for name in ("actual_native_chunk_dispatch", "native_chunk_all_inputs_and_packed_arena_immutable",
                 "native_pack_prepare_dispatch", "native_pack_prepare_entire_inputs_raw_immutable",
                 "decode_prepare_dispatch", "decode_prepare_all_inputs_raw_immutable"):
        expected[name] += 8
    for name in ("selected_unpack_dispatch", "selected_unpack_all_inputs_raw_immutable",
                 "service_unpack_vs_independent_FP32_bitwise"):
        expected[name] += 4
    for case in rows:
        label = case.get("label")
        pack_label = label[:-9] if type(label) is str and label.endswith("_feedback") else ""
        need(pack_label in matrix and pack_label not in seen and case.get("stage") == "prefill_seeded_decode" and
             type(case.get("p")) is int and case["p"] == matrix[pack_label][0] and case.get("status") == "passed",
             "exact native feedback identity")
        seen.add(pack_label)
        steps = case.get("steps")
        need(type(steps) is list and len(steps) == 160, "complete 160-step own-feedback trajectory")
        slots_seen = set()
        for i, step in enumerate(steps, 1):
            p = case["p"]
            slots = step.get("indices")
            need(type(slots) is list and len(slots) == p and all(type(n) is int and 0 <= n < p + 3 for n in slots)
                 and len(set(slots)) == p, "dynamic distinct feedback indices")
            slots_seen.add(tuple(slots))
            need(type(step.get("step")) is int and step["step"] == i and step.get("passed") is True,
                 "missing/reordered/failed feedback step")
            guard = step.get("guards")
            need(type(guard) is dict and set(guard) == FEEDBACK_GUARDS and all(v is True for v in guard.values()),
                 "full feedback state/input/ND/output guards")
            metrics = step.get("metrics")
            need(type(metrics) is dict and set(metrics) == {"selected_state", "complete_state", "output"},
                 "all selected/complete state + output metrics")
            for key, limit in (("selected_state", 1e-5), ("complete_state", 1e-5), ("output", .00303)):
                metric = metrics[key]
                error = metric.get("max_head_relative_l2")
                need(set(metric) == {"finite", "relative_l2", "max_head_relative_l2", "max_absolute", "expected_norm"} and
                     metric.get("finite") is True and all(type(metric[k]) in (int, float) and
                     math.isfinite(metric[k]) and metric[k] >= 0 for k in
                     ("relative_l2", "max_head_relative_l2", "max_absolute", "expected_norm")) and
                     error <= limit, "frozen numerical limit/all finite metric evidence")
            diag = step.get("packed_bitwise_diagnostic")
            need(type(diag) is dict and set(diag) == {"high", "low", "scales"} and
                 all(type(v) is bool for v in diag.values()), "packed diagnostic ABI")
            # Diagnostic bitwise fields are NOT an additional acceptance threshold.
            expected[pack_label + "_step_" + str(i)] += 1
        need(len(slots_seen) >= 2, "changing slot feedback missing")
    expected["decode_dispatch"] += 8 * 160
    check_rows = checks(report, expected)
    by_step = {case["label"][:-9] + "_step_" + str(row["step"]): row
               for case in rows for row in case["steps"]}
    for row in check_rows:
        if row["name"].endswith("_full_raw_inputs_status"):
            label = row["name"][:-len("_full_raw_inputs_status")]
            need(row["details"] == cases[label]["guards"], "native packing guard mismatch")
        if row["name"] in by_step:
            need(row["details"] == by_step[row["name"]], "step check differs from actual complete row")
    return set()

def argv(authority, report):
    args = authority.child_args
    need(type(args) is tuple and all(type(s) is str for s in args), "exact child args tuple")
    def one(flag):
        need(args.count(flag) == 1 and args.index(flag) + 1 < len(args), "child flag missing/duplicate: " + flag)
        return args[args.index(flag) + 1]
    need(args.count("--execute") == 1 and one("--stage") == authority.stage and
         one("--physical-card") == str(authority.physical_card) and
         one("--runtime-manifest-sha256") == RUNTIME_SHA and
         one("--runtime-manifest") == report["bindings"]["runtime_manifest"]["path"] and
         one("--library") == report["bindings"]["library"]["path"] and
         one("--build-receipt") == report["bindings"]["build_receipt"]["path"] and
         one("--preflight") == authority.owner_proof.path and
         one("--out") == str(PurePosixPath(authority.report.path).parent), "actual child report/arguments binding")
    need(args.count("--batches") == 1, "explicit full B1/B16 child matrix")
    pos = args.index("--batches")
    end = next((i for i in range(pos + 1, len(args)) if args[i].startswith("--")), len(args))
    need(args[pos + 1:end] in (("1", "16"), ("16", "1")), "no shrunken or inflated native matrix")
    need(REPO + "/" + BASE + "/run.py" in args, "actual frozen gate entrypoint")
    if authority.stage == "native_feedback":
        native = report["native_bindings"]
        need(one("--native-anchor-report") == native["anchor_path"] and
             one("--reference-library") == native["reference_library"] and
             one("--reference-library-sha256") == REFERENCE_SO and
             one("--decode-library") == native["decode_library"] and
             one("--decode-library-sha256") == c_all_batch_so() and
             one("--decode-build-receipt") in args, "native binary/anchor argv binding")
        return one("--decode-build-receipt")
    return None

def c_all_batch_so():
    return "a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade"

def run_authority(authority, runtime, c, read_bytes):
    need(type(authority) is RunAuthority and authority.stage in ("isolated", "native_feedback"),
         "MAIN expected run authority required")
    need(type(authority.physical_card) is int and authority.physical_card in (4, 5, 6, 7) and
         type(authority.container_id) is str and re.fullmatch("[0-9a-f]{64}", authority.container_id) is not None,
         "actual owned nonprivileged container/card identity")
    need(absolute(authority.child_cwd) and type(authority.child_command) is str and authority.child_command,
         "exact child execution identity")
    report = json_ref(authority.report, read_bytes)
    terminal = json_ref(authority.terminal.receipt, read_bytes)
    child = json_ref(authority.child, read_bytes)
    t = authority.terminal
    need(t.peer == PEER and type(t.operation_id) is str and t.operation_id.startswith("exec-") and
         type(t.args) is tuple and all(type(a) is str for a in t.args) and absolute(t.cwd), "expected actual peer/op/argv")
    op = terminal.get("operation", {})
    record = op.get("result", {}).get("record", {})
    need(terminal.get("schema") == "agentweb.operation/v1" and terminal.get("kind") == "exec" and
         terminal.get("operationId") == t.operation_id and terminal.get("terminal") is True and
         terminal.get("status") == "completed" and terminal.get("succeeded") is True and terminal.get("error") is None and
         op.get("routeDecision") == "peer_direct" and op.get("targetPeerId") == t.peer,
         "original MAIN outer operation_get completed/direct receipt")
    need({"id", "state", "exitCode", "error", "cancelled", "timedOut", "command", "args", "cwd",
          "stdout", "stderr", "durationMs"} <= set(record) and record.get("id") == t.operation_id and record.get("state") == "completed" and
         type(record.get("exitCode")) is int and record["exitCode"] == 0 and record.get("error") is None and
         record.get("cancelled") is False and record.get("timedOut") is False and
         record.get("command") == t.command and record.get("args") == list(t.args) and record.get("cwd") == t.cwd and
         type(record.get("stdout")) is str and type(record.get("stderr")) is str and
         type(record.get("durationMs")) in (int, float) and math.isfinite(record["durationMs"]) and record["durationMs"] >= 0,
         "actual outer exit/cancel/timeout/command raw result")
    refs = authority.controller_sources
    need(type(refs) is tuple and refs and all(type(r) is Ref for r in refs) and
         len({r.path for r in refs}) == len(refs), "MAIN-issued controller source identity")
    controller = {r.path: r.sha256 for r in refs}
    source_map(controller, read_bytes)
    need(any(r.path in t.args for r in refs), "outer command must execute a bound actual controller")
    markers = [line[len("MAIN_SELECTED_PREFILL_CHILD "):] for line in record["stdout"].splitlines()
               if line.startswith("MAIN_SELECTED_PREFILL_CHILD ")]
    need(len(markers) == 1 and json_bytes(markers[0].encode()) ==
         {"child": ref_dict(authority.child), "report": ref_dict(authority.report), "stage": authority.stage},
         "actual outer raw stdout must bind child receipt/report SHA")
    need(child.get("schema") == "damp-selected-prefill-child/v1" and child.get("stage") == authority.stage and
         child.get("report") == ref_dict(authority.report) and child.get("controller_sources") == controller and
         child.get("owner_proof") == ref_dict(authority.owner_proof), "future actual child contract/MAIN expectations")
    execution = child.get("execution", {})
    need({"command", "args", "cwd", "state", "returncode", "error", "cancelled", "timed_out",
          "stdout", "stderr", "started_ns", "completed_ns", "duration_ms"} <= set(execution) and
         execution.get("command") == authority.child_command and execution.get("args") == list(authority.child_args) and
         execution.get("cwd") == authority.child_cwd and execution.get("state") == "completed" and
         type(execution.get("returncode")) is int and execution["returncode"] == 0 and
         execution.get("error") is None and execution.get("cancelled") is False and execution.get("timed_out") is False and
         type(execution.get("stdout")) is str and type(execution.get("stderr")) is str,
         "actual subprocess raw exit/timeout/cancellation evidence")
    start, end = execution.get("started_ns"), execution.get("completed_ns")
    duration = execution.get("duration_ms")
    need(type(start) is int and type(end) is int and 0 < start <= end and
         type(duration) in (int, float) and math.isfinite(duration) and duration >= 0 and
         abs(duration - (end - start) / 1e6) <= 1000, "actual timed execution interval")
    need(child.get("container") == {"id": authority.container_id, "image_id": c.IMAGE,
         "physical_npu_ids": [authority.physical_card], "logical_to_physical": {"0": authority.physical_card},
         "privileged": False}, "actual container/image/nonprivileged single-card mapping")
    proof = json_ref(authority.owner_proof, read_bytes)
    try:
        c.validate_proof(proof, authority.physical_card, start)
    except Exception as error:
        raise Pending("fresh fail-closed proof at actual acquisition") from error
    need(child.get("runtime") == {"soc": "Ascend910B4", "torch": "2.10.0+cpu",
         "torch_npu": "2.10.0.post4", "opp_version_info_sha256": c.OPP_SHA},
         "actual runtime identity, not compiler target")
    status = ("isolated_selected_packing_pass" if authority.stage == "isolated"
              else "native_chunk_selected_pack_feedback_pass")
    need(report.get("schema") == "damp-selected-prefill-npu-gate/v1" and report.get("status") == status and
         report.get("stage") == authority.stage and report.get("npu_executed") is True and
         report.get("steps") == 160 and report.get("limits") == c.LIMITS and report.get("general_sr") is True and
         report.get("actual_runtime_soc") == "Ascend910B4" and report.get("schemas") == schemas() and
         type(report.get("completed_ns")) is int and start <= report["completed_ns"] <= end,
         "actual full numerical gate terminal/scope/runtime/schema")
    need(all(report.get(key) is False for key in ("serving_ready", "performance_measurement_admitted",
         "graph_supported", "float_candidate_enabled")), "component must NOT promote serving/graph/performance")
    need(not any(k in report for k in ("error", "traceback", "failure_save_error")), "failed/poisoned report")
    b = report.get("bindings", {})
    runtime_ref = Ref(REPO + "/" + BASE + "/RUNTIME_MANIFEST.json", RUNTIME_SHA)
    need(b.get("runtime_manifest") == ref_dict(runtime_ref) and child.get("runtime_manifest") == ref_dict(runtime_ref) and
         b.get("sources") == runtime["sources"] and b.get("dependencies") == runtime["dependencies"] and
         b.get("compiled_sources") == c.COMPILED and b.get("image_id") == c.IMAGE and
         b.get("opp_version_info_sha256") == c.OPP_SHA and b.get("device_proof") == proof,
         "actual complete source/runtime/proof closure")
    build_ref, so_ref = as_ref(b.get("build_receipt")), as_ref(b.get("library"))
    need(build_ref.sha256 == c.SELECTED_BUILD_SHA and so_ref.sha256 == c.SELECTED_SO_SHA,
         "immutable actual selected build/SO")
    build = json_ref(build_ref, read_bytes)
    try:
        c.validate_build(build)
    except Exception as error:
        raise Pending("actual selected compiler/export receipt") from error
    checked(so_ref, read_bytes)
    for command in build["commands"]:
        checked(Ref(command["log_path"], command["log_sha256"]), read_bytes)
    exported = build["exported_kernel"]
    checked(Ref(exported["audit_path"], exported["audit_sha256"]), read_bytes)
    expected_loaded = {so_ref.path: so_ref.sha256}
    decode_receipt_path = argv(authority, report)
    if authority.stage == "native_feedback":
        nb = report["native_bindings"]
        anchor = json_ref(Ref(nb["anchor_path"], ANCHOR_SHA), read_bytes)
        try:
            native = c.validate_anchor(anchor)
        except Exception as error:
            raise Pending("six actual independently source-bound native/reference anchors") from error
        need(nb.get("anchor_sha256") == ANCHOR_SHA and nb.get("native_runtime") == native and
             nb.get("reference_library_sha256") == REFERENCE_SO and
             native.get("reference_library_sha256") == REFERENCE_SO and
             native.get("native_runtime_library_sha256") == NATIVE_SO and
             nb.get("decode_library_sha256") == c.ALL_BATCH_SO_SHA and
             nb.get("decode_build_receipt_sha256") == c.ALL_BATCH_BUILD_SHA, "actual native/reference/decode identity")
        decode_ref = Ref(decode_receipt_path, c.ALL_BATCH_BUILD_SHA)
        decode = json_ref(decode_ref, read_bytes)
        dm = json_ref(Ref(REPO + "/projects/damp-ascend/operator/all_batch_wrapper_v3/source_manifest.json",
                         c.ALL_BATCH_MANIFEST_SHA), read_bytes)
        try:
            c.require_decode_admission(decode, dm, c.ALL_BATCH_SO_SHA)
        except Exception as error:
            raise Pending("actual all-batch build/export identity") from error
        for command in decode["commands"]:
            checked(Ref(command["log_path"], command["log_sha256"]), read_bytes)
        ex = decode["exported_kernel"]
        checked(Ref(ex["audit_path"], ex["audit_sha256"]), read_bytes)
        for path, sha in ((nb["reference_library"], REFERENCE_SO), (nb["decode_library"], c.ALL_BATCH_SO_SHA),
                          (native["native_runtime_library_path"], NATIVE_SO)):
            checked(Ref(path, sha), read_bytes)
            expected_loaded[path] = sha
        need(child.get("runtime_image_sources") == runtime["actual_image_sources"], "23 actual image source checks")
    else:
        need(child.get("runtime_image_sources") == {}, "isolated no native-image execution claim")
    need(child.get("loaded_libraries") == expected_loaded, "actual mapped SOs, not merely files present")
    wanted_artifacts = isolated(report, c) if authority.stage == "isolated" else native_feedback(report, c)
    artifacts = report.get("artifacts", [])
    need(type(artifacts) is list and len(artifacts) == len(wanted_artifacts) and
         {PurePosixPath(r.get("path", "")).name for r in artifacts} == wanted_artifacts and
         all(r.get("copy_errors") == [] for r in artifacts), "complete retained negative evidence/no poisoned copies")
    child_artifacts = child.get("artifacts")
    need(type(child_artifacts) is list and len(child_artifacts) == len(artifacts), "actual artifact byte hashes")
    refs_by_path = {as_ref(r).path: as_ref(r) for r in child_artifacts}
    need(len(refs_by_path) == len(artifacts) and set(refs_by_path) == {r["path"] for r in artifacts},
         "exact negative artifact set")
    parent = PurePosixPath(authority.report.path).parent
    for ref in refs_by_path.values():
        need(PurePosixPath(ref.path).parent == parent, "same experiment negative output root")
        checked(ref, read_bytes)  # never unpickle untrusted .pt
    return report, tuple(Ref(path, sha) for path, sha in expected_loaded.items())

def validate_complete(isolated_run, native_run, read_bytes, *, source_manifest, enabled=False):
    """Validate both full actual stages; absent evidence raises Pending.

    read_bytes(path)->bytes must read actual original bytes without projection.
    source_manifest is MAIN's frozen Ref, not report-supplied self-authorization.
    The returned descriptor is immutable and NEVER a service-ready capability.
    """
    need(enabled is True, "default OFF")
    manifest = json_ref(source_manifest, read_bytes)
    wanted_sources = {HERE + "/contract.py", HERE + "/tests/test_admission.py", HERE + "/READY.md"}
    need(manifest.get("schema") == "damp-selected-prefill-component-admission-sources/v1" and
         manifest.get("default_enabled") is False and set(manifest.get("sources", {})) == wanted_sources and
         manifest.get("gate_runtime") == ref_dict(Ref(REPO + "/" + BASE + "/RUNTIME_MANIFEST.json", RUNTIME_SHA)),
         "MAIN-issued exact admission sources/default OFF")
    source_map(manifest["sources"], read_bytes)
    runtime = json_ref(Ref(REPO + "/" + BASE + "/RUNTIME_MANIFEST.json", RUNTIME_SHA), read_bytes)
    need(runtime.get("schema") == "damp-selected-prefill-gate-runtime/v1" and runtime.get("default_enabled") is False,
         "frozen gate runtime identity")
    source_map(runtime["sources"], read_bytes)
    source_map(runtime["dependencies"], read_bytes)
    for ref in runtime["actual_snapshot_manifests"]:
        checked(as_ref(ref), read_bytes)
    c = frozen_contract(read_bytes)
    need(type(isolated_run) is RunAuthority and isolated_run.stage == "isolated" and
         type(native_run) is RunAuthority and native_run.stage == "native_feedback", "both exact actual stages required")
    isolated_report, isolated_libs = run_authority(isolated_run, runtime, c, read_bytes)
    native_report, native_libs = run_authority(native_run, runtime, c, read_bytes)
    libraries = tuple(sorted(set(isolated_libs + native_libs), key=lambda r: r.path))
    return ComponentAuthority(
        status="standalone_component_chain_evidence_admitted",
        reports=(isolated_run.report, native_run.report),
        child_receipts=(isolated_run.child, native_run.child),
        terminal_receipts=(isolated_run.terminal.receipt, native_run.terminal.receipt),
        operation_ids=(isolated_run.terminal.operation_id, native_run.terminal.operation_id),
        source_manifest=source_manifest,
        runtime_manifest=Ref(REPO + "/" + BASE + "/RUNTIME_MANIFEST.json", RUNTIME_SHA),
        libraries=libraries,
        native_anchor=Ref(native_report["native_bindings"]["anchor_path"], ANCHOR_SHA),
        physical_cards=(isolated_run.physical_card, native_run.physical_card),
        controller_sources=tuple(sorted(set(isolated_run.controller_sources + native_run.controller_sources),
                                        key=lambda r: r.path)))
