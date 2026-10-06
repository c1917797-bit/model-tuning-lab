#!/usr/bin/env python3
"""Source-bound two-process kernel prerequisite; never launch or fabricate legacy PASS."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import re

ROOT = "/opt/host/vnf/austinov/model-tuning-lab"
PROJECT = ROOT + "/projects/kvbuffer-parallel-ascend"
RUNNER = PROJECT + "/tools/split_gate_v1/run.py"
IMAGE_PYTHON = "/usr/local/python3.12.13/bin/python3"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LIBRARY = "0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b"
BUILD = "25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4"
META = "2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727"
NATIVE_PATH = "/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA = "eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
PREFIX = "MAIN_KVBUFFER_SPLIT_CHILD "
CGROUP = 8 * 1024**3
MODES = (("eager", 0), ("graph", 0), ("graph", 1), ("graph", 2))
GUARDS = ("untouched_slots_bitwise", "nonflush_base_bitwise", "guards", "pointers",
          "input_immutable", "zero_length_output_zero", "finite", "metric_finite")
LOGS = ("k_log", "u_log", "lambda_log", "decay", "length")

def require(ok, why):
    if not ok:
        raise ValueError(why)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def clean_json(raw):
    def bad(value):
        raise ValueError("nonfinite JSON constant: " + value)
    value = json.loads(raw, parse_constant=bad)
    def walk(x):
        if isinstance(x, float):
            require(math.isfinite(x), "nonfinite JSON metric")
        elif isinstance(x, dict):
            for y in x.values():
                walk(y)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(value)
    return value

def ref(value):
    require(type(value) is dict and set(value) == {"path", "sha256"}, "exact raw Ref keys")
    require(type(value["path"]) is str and value["path"].startswith("/") and
            ".." not in Path(value["path"]).parts, "absolute bounded evidence path")
    require(type(value["sha256"]) is str and
            re.fullmatch("[0-9a-f]{64}", value["sha256"]), "Ref SHA256")
    return value

def raw(value, read_bytes):
    value = ref(value)
    data = read_bytes(value["path"])
    require(type(data) is bytes and digest(data) == value["sha256"], "original evidence byte drift")
    return data

def obj(value, read_bytes):
    return clean_json(raw(value, read_bytes))

def frozen(manifest_ref, read_bytes):
    m = obj(manifest_ref, read_bytes)
    require(m.get("schema") == "kvbp.split-service-authority-sources/v1", "source manifest schema")
    require(set(m.get("files", {})) == {"validator.py", "test_validator.py", "READY.md"},
            "NEW three-file source closure")
    here = Path(__file__).resolve().parent
    for name, sha in m["files"].items():
        require(digest(read_bytes(str(here / name))) == sha, "NEW source drift: " + name)
    require(type(m.get("frozen_dependencies")) is dict and m["frozen_dependencies"],
            "frozen consumer/producer sources required")
    for path, sha in m["frozen_dependencies"].items():
        require(digest(read_bytes(path)) == sha, "frozen source drift: " + path)
    for key, wanted in (("build", BUILD), ("meta", META), ("library", LIBRARY)):
        require(ref(m["artifacts"][key])["sha256"] == wanted, "artifact authority SHA")
        raw(m["artifacts"][key], read_bytes)
    build, meta = obj(m["artifacts"]["build"], read_bytes), obj(m["artifacts"]["meta"], read_bytes)
    require(build["status"] == "compiled_no_device" and build["npu_executed"] is False and
            build["image_id"] == IMAGE and build["library_sha256"] == LIBRARY and
            all(c["exit_code"] == 0 for c in build["commands"]), "original actual build receipt")
    require(meta["status"] == "pass" and meta["npu_executed"] is False and
            meta["library_sha256"] == LIBRARY and meta["build_receipt_sha256"] == BUILD,
            "original actual no-device Meta receipt")
    return m, meta

def terminal(authority, read_bytes):
    d = obj(authority["operation"], read_bytes)
    d = d.get("structuredContent", d)
    op = d.get("operation")
    route = op if isinstance(op, dict) else d
    result = op.get("result") if isinstance(op, dict) else d.get("result")
    require(isinstance(result, dict), "actual AWMCP execution result absent")
    record = result.get("record")
    require(isinstance(record, dict), "original AWMCP exec record absent")
    require(route.get("routeDecision") in ("peer_direct", "upstream_local_peer") and
            route.get("targetPeerId") == authority["peer_id"], "original operation peer/route")
    require(record.get("id") == authority["operation_id"] and
            record.get("command") == authority["command"] and
            record.get("args") == authority["args"] and record.get("cwd") == authority["cwd"],
            "MAIN exact original operation/command/argv/cwd")
    require(authority["cwd"] == ROOT and type(authority["args"]) is list and
            authority["command"].startswith("/"), "absolute original MAIN command/canonical cwd")
    require(record.get("state") == "completed" and record.get("exitCode") == 0 and
            record.get("error") is None and record.get("cancelled") is False and
            record.get("timedOut") is False, "original operation nonzero/nonterminal/cancel/timeout")
    require(raw(authority["stdout"], read_bytes) == record.get("stdout", "").encode() and
            raw(authority["stderr"], read_bytes) == record.get("stderr", "").encode(),
            "original MAIN stdout/stderr mismatch")
    markers = [line[len(PREFIX):] for line in record["stdout"].splitlines() if line.startswith(PREFIX)]
    require(len(markers) == 1, "one actual MAIN child marker required, not self-ready")
    marker = clean_json(markers[0])
    require(marker == {k: ref(authority[k]) for k in ("report", "identity", "child")},
            "original stdout does not bind exact child/report/identity")
    return record

def child(authority, report, identity, batch, read_bytes, testing):
    c = obj(authority["child"], read_bytes)
    require(c.get("schema") == "kvbp.split-child-execution/v1", "MAIN actual child sidecar missing")
    require(c.get("report") == authority["report"] and c.get("identity") == authority["identity"],
            "child binds original report/identity")
    require(c.get("evidence_kind") == ("synthetic-software-contract" if testing else "actual-main-execution"),
            "synthetic evidence is not actual NPU authority")
    ex = c["execution"]
    require(ex.get("command") in ("/usr/bin/docker", "docker") and ex.get("cwd") == ROOT and
            ex.get("exit_code") == 0 and ex.get("error") is None and
            ex.get("cancelled") is False and ex.get("timed_out") is False,
            "actual original docker child outcome")
    argv = ex["args"]
    require(type(argv) is list and argv[:1] == ["exec"] and argv.count(RUNNER) == 1 and
            argv.count(IMAGE_PYTHON) == 1, "original docker exec/image-Python/runner boundary")
    runner_at = argv.index(RUNNER)
    python_at = argv.index(IMAGE_PYTHON)
    require(python_at < runner_at and argv[python_at + 1:runner_at] in ([], ["-B"]),
            "true image Python command, not fabricated host Python")
    flags = argv[runner_at + 1:]
    require(len(flags) % 2 == 0 and len(set(flags[::2])) == len(flags[::2]), "unique inner runner flags")
    pairs = dict(zip(flags[::2], flags[1::2]))
    allowed = {"--batch", "--physical-device", "--identity", "--output-dir",
               "--library", "--build-receipt", "--meta-receipt"}
    require(set(pairs) <= allowed and {"--batch", "--physical-device", "--identity", "--output-dir"} <= set(pairs),
            "original real runner CLI")
    require(pairs["--batch"] == str(batch) and pairs["--physical-device"] == str({1:5,16:6}[batch]) and
            pairs["--identity"] == c["image_identity_path"] and
            pairs["--output-dir"] == c["image_output_dir"] and
            c["image_output_dir"].startswith("/kvbuffer-results/") and
            ".." not in Path(c["image_output_dir"]).parts, "child true batch/card/evidence namespace")
    for key in ("stdout", "stderr"):
        raw(ex[key], read_bytes)
    require(type(c.get("producer_sources")) is dict and c["producer_sources"] == authority["producer_sources"] and
            bool(c["producer_sources"]), "MAIN expected actual producer source closure")
    for path, sha in c["producer_sources"].items():
        require(digest(read_bytes(path)) == sha, "actual parent/shim source drift")
    inspect = obj(c["container_inspect"], read_bytes)
    require(type(inspect) is list and len(inspect) == 1, "original one-container Docker inspect")
    inspect = inspect[0]
    cid = inspect["Id"]
    require(re.fullmatch("[0-9a-f]{64}", cid) and cid in argv[:python_at] and inspect["Image"] == IMAGE,
            "exact child container ID/image/argv")
    host = inspect["HostConfig"]
    require(host.get("Privileged") is False and host.get("Memory") == CGROUP and
            host.get("MemorySwap") == CGROUP, "nonprivileged actual 8GiB cgroup inspect")
    card_nodes = []
    for device in host.get("Devices", []):
        match = re.fullmatch("/dev/davinci([0-9]+)", device["PathOnHost"])
        if match:
            card_nodes.append(int(match.group(1)))
    require(card_nodes == [{1:5,16:6}[batch]], "only authorized physical card, protect0-3")
    proof = obj(c["device_proof"], read_bytes)
    require(proof.get("schema") == "kvbp.split-main-device-binding/v1" and
            proof.get("container_id") == cid and proof.get("image_id") == IMAGE and
            proof.get("physical_devices") == card_nodes and
            proof.get("logical_to_physical") == {"0":card_nodes[0]} and
            type(proof.get("same_process_pid")) is int and proof["same_process_pid"] > 0,
            "MAIN actual same-process physical proof; not logical0 inference")
    require(proof.get("evidence_kind") == c["evidence_kind"], "device evidence scope mismatch")
    require(set(proof.get("raw_refs", {})) == {"canary", "mapping", "host_processes", "cgroup"},
            "MAIN fresh device proof raw reference closure")
    for value in proof["raw_refs"].values():
        require(len(raw(value, read_bytes)) > 0, "missing MAIN device evidence bytes")
    require(proof.get("preflight_utc") == identity["preflight_utc"] and
            identity.get("evidence", {}).get("device_proof") == c["device_proof"] and
            identity.get("evidence", {}).get("container_inspect") == c["container_inspect"],
            "original MAIN proof/inspect/preflight temporal binding")
    native = ref(c["native_library"])
    require(native["sha256"] == NATIVE_SHA, "verified same-image native binary identity")
    raw(native, read_bytes)
    require(report["loaded_libraries"].get(NATIVE_PATH) == NATIVE_SHA,
            "actual mapped native library missing/drift, not merely source schema")
    return {"container_id": cid, "physical_device": card_nodes[0], "child": authority["child"],
            "device_proof": c["device_proof"], "container_inspect": c["container_inspect"],
            "native_library": native, "producer_sources": c["producer_sources"]}

def validate_cases(report, batch):
    cases = report["cases"]
    require(len(cases) == 4 and {(c.get("batch"), c.get("mode"), c.get("trial")) for c in cases} ==
            {(batch, mode, trial) for mode, trial in MODES}, "four unique actual mode/trial cases")
    for case in cases:
        require(case.get("status") == "passed" and "error" not in case and "pending_raw_step" not in case,
                "failed/pending raw evidence cannot be promoted")
        rows = case["steps"]
        require(len(rows) == 160 and [r["step"] for r in rows] == list(range(1,161)),
                "160 unique ordered changing feedback steps")
        lengths = [0] * (batch + 3)
        merges = 0
        for i, row in enumerate(rows):
            active = (0,1,3,7,12,15,16,16)[i % 8] if batch == 16 and case["mode"] == "graph" else batch
            reset = (i // 16) % (batch + 3) if i in (64,112) else None
            require(row.get("active") == active and row.get("reset_slot") == reset,
                    "true active schedule/reset-slot protocol")
            if reset is not None:
                lengths[reset] = 0
            for token in range(active):
                slot = (token + i) % (batch + 3)
                if lengths[slot] == 15:
                    merges += 1
                    lengths[slot] = 0
                else:
                    lengths[slot] += 1
            require(row.get("passed") is True and all(row.get(k) is True for k in GUARDS),
                    "raw per-step finite/guard/pointer/input/untouched/base gate")
            logs = row.get("all_logs_bitwise_outside_new_U")
            require(type(logs) is dict and set(logs) == set(LOGS) and
                    all(v is True for v in logs.values()), "complete log invariant gate")
            for key, limit in (("output_error", .00303), ("complete_state_l2", 2e-6),
                               ("max_per_head_l2", 2e-6)):
                value = row.get(key)
                require(type(value) in (int,float) and math.isfinite(value) and 0 <= value <= limit,
                        "frozen numerical bound: " + key)
            receipt = row["raw_step"]
            name = "raw-step-b%d-%s-t%d-step%d.pt" % (batch, case["mode"], case["trial"], i+1)
            require(receipt.get("file") == name and receipt.get("step") == i+1 and
                    receipt.get("retained") is False and type(receipt.get("bytes")) is int and
                    receipt["bytes"] > 0 and re.fullmatch("[0-9a-f]{64}", receipt.get("sha256", "")),
                    "each original raw checkpoint identity/passed cleanup")
        require(case.get("resets") == 2 and case.get("merges") == merges and merges > 0,
                "source-replayed reset/flush coverage")
        for maximum, key in (("max_output_error", "output_error"), ("max_state_l2", "complete_state_l2"),
                             ("max_head_l2", "max_per_head_l2")):
            require(case.get(maximum) == max(r[key] for r in rows), "original metric maximum mismatch")
    return 640

def validate_run(authority, batch, manifest, meta, read_bytes, testing=False):
    required = {"report", "identity", "operation", "stdout", "stderr", "child", "peer_id",
                "operation_id", "command", "args", "cwd", "producer_sources"}
    require(type(authority) is dict and set(authority) == required, "MAIN raw RunAuthority exact fields")
    report = obj(authority["report"], read_bytes)
    identity = obj(authority["identity"], read_bytes)
    terminal(authority, read_bytes)
    require(report.get("schema") == "kvbp.split-native-gate/v1" and
            report.get("status") == "single_batch_kernel_native_eager_graph_pass" and
            report.get("claim") == "kernel-only" and "error" not in report, "original real split PASS only")
    require(report.get("launch_identity") == identity and
            report.get("launch_identity_sha256") == authority["identity"]["sha256"], "original identity bytes")
    expected_protocol = dict(batch=batch,physical_device={1:5,16:6}[batch],logical_device=0,slots=batch+3,
        eager_trials=1,graph_trials=3,steps_per_case=160,feedback=True,output_limit=.00303,
        complete_and_per_head_l2_limit=2e-6,graph_active_schedule=[0,1,3,7,12,15,16,16] if batch==16 else [1],
        reset_steps=[64,112],required_flushes=True,retry="none",scope="kernel-only-not-model-E2E-or-task-accuracy")
    require(report["protocol"] == expected_protocol and identity["protocol"] == expected_protocol,
            "original unchanged preregistered protocol")
    require(identity.get("schema") == "kvbp.split-launch-identity/v1" and identity.get("image_id") == IMAGE and
            identity.get("physical_devices") == [{1:5,16:6}[batch]] and
            identity.get("logical_to_physical") == {"0":{1:5,16:6}[batch]} and
            all(identity.get(k) is True for k in ("fresh_idle_verified","nonprivileged","source_canary_passed")),
            "original MAIN launch identity")
    require(identity.get("memory_cgroup_bytes") == CGROUP and report["cgroup"]["bytes"] == CGROUP,
            "original/actual 8GiB cgroup")
    split = PROJECT + "/tools/split_gate_v1/"
    drivers = {k[len(split):]:v for k,v in manifest["frozen_dependencies"].items() if k.startswith(split)}
    require(report["driver_sources"] == drivers and identity["driver_sources"] == drivers and
            report["script_sha256"] == drivers["run.py"], "original immutable split driver closure")
    repo_pins, native_pins = manifest["repo_pins"], manifest["native_pins"]
    expected_receipts = dict(build_receipt_sha256=BUILD,meta_receipt_sha256=META,library_sha256=LIBRARY,
                            repo_sources=repo_pins,meta_is_not_npu_proof=True)
    require(report["frozen_receipts"] == expected_receipts and identity["repo_sources"] == repo_pins and
            report["native_sources"] == native_pins and identity["native_sources"] == native_pins and
            identity["library_sha256"] == LIBRARY and identity["build_receipt_sha256"] == BUILD and
            identity["meta_receipt_sha256"] == META, "original complete source/artifact binding")
    require(report["candidate_schema"] == meta["schema"] and
            digest(report["candidate_schema"].encode()) == report["candidate_schema_sha256"] and
            digest(report["native_schema"].encode()) == report["native_schema_sha256"] and
            all(x in report["native_schema"] for x in ("npu_recurrent_gated_delta_rule", "beta", "scale",
                                                    "actual_seq_lengths", "ssm_state_indices")),
            "actual schemas and original schema digests")
    maps = report["loaded_libraries"]
    require(type(maps) is dict and any("kvbuffer" in p and s == LIBRARY for p,s in maps.items()) and
            all(p.startswith("/") and "(deleted)" not in p for p in maps), "actual loaded candidate binding")
    runtime = report["runtime"]
    require(runtime.get("logical_device_count") == 1 and runtime.get("logical_device") == 0 and
            type(runtime.get("device_name")) is str and runtime["device_name"], "original observed device runtime")
    require(type(report["created_ns"]) is int and type(report["completed_ns"]) is int and
            report["created_ns"] < report["completed_ns"], "original completed timestamps")
    preflight = datetime.fromisoformat(identity["preflight_utc"].replace("Z", "+00:00"))
    require(preflight.tzinfo is not None and
            0 <= report["created_ns"] / 1e9 - preflight.timestamp() <= 600,
            "original launch freshness, not current historical-report TTL")
    steps = validate_cases(report,batch)
    detail = child(authority,report,identity,batch,read_bytes,testing)
    return dict(batch=batch,steps=steps,cases=4,raw_authority=authority,**detail)

def validate_complete(b1, b16, source_manifest, read_bytes=Path.read_bytes, *, enabled=False, testing=False):
    require(enabled is True, "default OFF: explicit enabled=True is required")
    if read_bytes is Path.read_bytes:
        read_bytes = lambda path: Path(path).read_bytes()
    manifest, meta = frozen(source_manifest,read_bytes)
    runs = [validate_run(a,b,manifest,meta,read_bytes,testing) for a,b in ((b1,1),(b16,16))]
    require(runs[0]["container_id"] != runs[1]["container_id"] and
            b1["operation_id"] != b16["operation_id"] and b1["report"] != b16["report"],
            "two distinct original jobs/container/operations required")
    r1,r16 = (obj(a["report"],read_bytes) for a in (b1,b16))
    require(r1["native_schema"] == r16["native_schema"] and
            r1["loaded_libraries"] == r16["loaded_libraries"] and
            r1["native_sources"] == r16["native_sources"], "same-image/native/code drift between jobs")
    return dict(schema="kvbp.split-kernel-prerequisite/v1",
        status="synthetic_contract_pass" if testing else "checked_actual_split_kernel_prerequisite",
        evidence_kind="synthetic-software-contract" if testing else "actual-main-execution",
        source_manifest=ref(source_manifest),image_id=IMAGE,library_sha256=LIBRARY,
        unique_cases=8,changing_feedback_steps=1280,batches=[1,16],runs=runs,
        native_eager_graph_prerequisite=True,npu_verified=not testing,
        service_ready=False,model_lifecycle_verified=False,other_batches_verified=False,
        matched_e2e_verified=False,task_accuracy_verified=False,
        legacy_single_process_pass_fabricated=False,
        limitations=["raw passed tensors hash-recorded then lawfully removed by frozen producer",
                     "MAIN external device proof raw bytes bound, not independently reparsed as device telemetry",
                     "whole FP32 native input/output guard is not added by this bridge",
                     "old service launcher still rejects this new schema; explicit new adapter required"])

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--enable",action="store_true",help="stdlib evidence validation only; never NPU or serving")
    p.add_argument("--inputs",type=Path,help="MAIN JSON: b1, b16, source_manifest (raw Ref)")
    p.add_argument("--output",type=Path,help="new prerequisite JSON; never overwrite")
    a = p.parse_args()
    if not a.enable:
        print(json.dumps(dict(enabled=False,launches_npu=False,service_ready=False,
                              required=["b1","b16","source_manifest"],actual_evidence_pending=True)))
        return
    require(a.inputs is not None and a.output is not None,"enabled evidence input/new output required")
    inputs = clean_json(a.inputs.read_bytes())
    require(set(inputs) == {"b1","b16","source_manifest"},"complete exact two-run input")
    result = validate_complete(inputs["b1"],inputs["b16"],inputs["source_manifest"],enabled=True)
    with a.output.open("xb") as stream:
        stream.write(canonical(result)+b"\n")
    print(json.dumps({"output":str(a.output),"sha256":digest(a.output.read_bytes()),"service_ready":False}))
if __name__ == "__main__":
    main()
