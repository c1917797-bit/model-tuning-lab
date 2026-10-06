#!/usr/bin/env python3
"""Raw two-job prerequisite consumer. Stdlib only; default OFF; never launch devices."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT = ROOT / "projects/kvbuffer-parallel-ascend"
BASE = PROJECT / "tools/split_service_consumer_v1"
DISPATCH = PROJECT / "tools/split_dispatch_v1"
PACKET = DISPATCH / "PACKET.json"
PACKET_SHA = "eb2fd0cae186db8b73749255bc8f1ceba5ef1d57f67e2a557126b8bbb37517a9"
OWN = ("consumer.py", "launch.py", "test_consumer.py", "READY.md")
GIB = 1024**3

def require(ok, why):
    if not ok:
        raise ValueError(why)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def clean(data):
    def bad(x):
        raise ValueError("nonfinite JSON: " + x)
    result = json.loads(data, parse_constant=bad)
    def walk(x):
        if isinstance(x, float):
            require(math.isfinite(x), "nonfinite JSON metric")
        elif isinstance(x, dict):
            for y in x.values(): walk(y)
        elif isinstance(x, list):
            for y in x: walk(y)
    walk(result)
    return result

def ref(value):
    require(type(value) is dict and set(value) == {"path", "sha256"}, "exact original Ref")
    p = Path(value["path"])
    require(type(value["path"]) is str and p.is_absolute() and ".." not in p.parts,
            "absolute non-traversing evidence Ref")
    require(re.fullmatch("[0-9a-f]{64}", value["sha256"]) is not None, "SHA256 Ref")
    return value

def read_file(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "ordinary source/evidence file, not symlink")
    return p.read_bytes()

def raw(value, read=read_file):
    value = ref(value)
    data = read(value["path"])
    require(type(data) is bytes and digest(data) == value["sha256"], "raw byte drift")
    return data

def obj(value, read=read_file):
    return clean(raw(value, read))

def actual_ref(path, read=read_file):
    data = read(str(path))
    return {"path": str(path), "sha256": digest(data)}

def write_new(path, value):
    with Path(path).open("xb") as f:
        f.write(canonical(value) + b"\n")

def module(path, wanted, name, read):
    data = read(str(path))
    require(digest(data) == wanted, "imported source drift: " + str(path))
    # A spec preserves __file__; only byte-verified stdlib modules are imported.
    spec = importlib.util.spec_from_file_location(name, str(path))
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    require("torch" not in sys.modules and "torch_npu" not in sys.modules,
            "consumer/source audit must remain stdlib")
    return result

def sources(manifest_ref, read=read_file):
    manifest = obj(manifest_ref, read)
    require(manifest.get("schema") == "kvbp.split-service-consumer-sources/v1" and
            manifest.get("enabled") is False and set(manifest.get("files", {})) == set(OWN),
            "NEW exact four-file source manifest, default OFF")
    for name, wanted in manifest["files"].items():
        require(digest(read(str(BASE/name))) == wanted, "NEW source drift: " + name)
    require(manifest.get("dispatcher_packet") == {"path": str(PACKET), "sha256": PACKET_SHA},
            "exact existing producer packet")
    packet = obj(manifest["dispatcher_packet"], read)
    require(packet["schema"] == "kvbp.split-dispatch-sources/v1" and
            packet["default_enabled"] is False and
            set(packet["sources"]) == {"controller.py", "contracts.py", "test_controller.py", "READY.md"},
            "original producer four-file closure")
    pins = {str(DISPATCH/n): h for n, h in packet["sources"].items()}
    pins.update(packet["frozen_dependencies"])
    require(len(pins) == 49, "actual original 49-file producer closure")
    for path, wanted in pins.items():
        require(digest(read(path)) == wanted, "frozen source drift: " + path)
    for value in packet["artifacts"].values():
        raw(value, read)
    # Do NOT call dispatcher.sources: an image has no authority to execute host npu-smi.
    bridge_path = PROJECT / "tools/split_service_authority_v1/validator.py"
    bridge = module(bridge_path, pins[str(bridge_path)], "kvbp_checked_split_bridge", read)
    dispatch = module(DISPATCH/"contracts.py", pins[str(DISPATCH/"contracts.py")],
                      "kvbp_checked_split_contracts", read)
    host_path = ROOT / "projects/damp-ascend/tools/allT_dispatch_controller_v1/controller.py"
    host = module(host_path, pins[str(host_path)], "kvbp_checked_process_parser", read)
    fp = ROOT / "projects/damp-ascend/tools/prefill_float_dispatch_v1/dispatch.py"
    helper = module(fp, pins[str(fp)], "kvbp_checked_canary_contract", read)
    producer = {str(DISPATCH/n): h for n, h in packet["sources"].items()}
    producer[str(PACKET)] = PACKET_SHA
    return packet, pins, producer, bridge, dispatch, host, helper

def command_receipts(audit, label, read=read_file, listing=None):
    paths = (listing or (lambda p: [str(x) for x in Path(p).glob("*.receipt.json")]))(str(audit))
    found = []
    pattern = re.compile(r"[0-9]{4,6}-" + re.escape(label) + r"\.receipt\.json")
    for path in sorted(paths):
        p = Path(path)
        require(p.parent == audit, "receipt escaped original run-arm audit")
        if not pattern.fullmatch(p.name):
            continue
        receipt_ref = actual_ref(p, read)
        row = obj(receipt_ref, read)
        require(row.get("command") == row.get("argv", [None])[0] and
                row.get("cwd") == str(ROOT) and row.get("exit_code") == 0 and
                row.get("error") is None and row.get("automatic_retry") is False,
                "actual original command receipt, not generated PASS")
        streams = {}
        for k in ("stdout", "stderr"):
            r = {"path": row[k], "sha256": row[k+"_sha256"]}
            require(Path(r["path"]).parent == audit, "command stream escaped original audit")
            streams[k] = raw(r, read)
        found.append((receipt_ref, row, streams))
    return found

def exact_process(observation, waiting, cid, batch, d, h, protected):
    p = observation["process"]
    require(observation.get("physical_card") == d.CARDS[batch] and
            observation.get("canary_same_process") is False and
            waiting.get("observed_role") == "prelaunch_wait_bash_not_native" and
            p.get("observed_role") == "actual_gate_python", "real gate is not prelaunch/canary")
    require(type(p.get("pid")) is int and p["pid"] > 0 and
            type(p.get("start_ticks")) is int and p["start_ticks"] > 0 and
            p["pid"] == waiting.get("pid") and p["start_ticks"] == waiting.get("start_ticks"),
            "exec PID/start-time continuity, not PID reuse")
    require(type(p.get("namespace_pids")) is list and p["namespace_pids"] and
            all(type(n) is int and n > 0 for n in p["namespace_pids"]) and
            p["namespace_pids"][0] == p["pid"], "actual host/NSpid chain")
    for value in (p, waiting):
        require(type(value.get("cgroup")) is str and
                any(x == cid or x == "docker-"+cid+".scope"
                    for line in value["cgroup"].splitlines()
                    for x in line.split(":", 2)[-1].split("/")), "exact real owned cgroup")
    expected = [d.PYTHON, "-B", d.RUNNER, "--batch", str(batch), "--physical-device",
                str(d.CARDS[batch]), "--identity", "/kvbuffer-launch/identity.json",
                "--output-dir", "/kvbuffer-results/gate"]
    require(p.get("argv") == expected, "observed actual gate Python argv")
    rows = h.parse_processes(observation["npu_smi"])
    require([x["pid"] for x in rows[d.CARDS[batch]]] == [p["pid"]], "actual native NPU/PID/card")
    for card in range(4):
        require([x["pid"] for x in rows[card]] == [x["pid"] for x in protected[str(card)]],
                "raw protected0-3 PID set drift")
    return {"host_pid": p["pid"], "namespace_pids": p["namespace_pids"],
            "start_ticks": p["start_ticks"], "physical_card": d.CARDS[batch],
            "scope": "one actual NPU-owner observation, not continuous profiler proof"}

def budget_samples(refs, audit, jobs, execution, d, read=read_file):
    require(type(refs) is list and refs and len(refs) <= 362 and
            len({r["path"] for r in refs}) == len(refs), "actual unique runtime-budget samples")
    last_ns = 0
    for i, value in enumerate(refs, 1):
        require(value["path"] == str(audit/("RUNTIME_BUDGET-%04d.json"%i)),
                "ordered original runtime budget paths")
        result = obj(value, read)
        inputs_ref = result["inputs"]
        require(inputs_ref["path"] == str(audit/("RUNTIME_BUDGET_INPUTS-%04d.json"%i)),
                "original raw budget inputs")
        x = obj(inputs_ref, read)
        require(type(x.get("observed_ns")) is int and x["observed_ns"] > last_ns,
                "actual sampled observation ordering")
        last_ns = x["observed_ns"]
        require(type(x.get("docker_info", {}).get("NCPU")) is int and
                x["docker_info"]["NCPU"] >= 3, "actual joint CPU3 capability")
        m = re.search(r"^MemAvailable:\s*(\d+)\s+kB", x["meminfo"], re.M)
        require(m is not None, "original ordinary RAM MemAvailable")
        require(set(x["cgroups"]) == {"1", "16"}, "both original owned resource groups")
        groups = {int(k): v for k, v in x["cgroups"].items()}
        for b, row in groups.items():
            require(row.get("container_id") == jobs[b]["container_id"], "same-joint exact cgroup owner")
        elapsed = x["own_elapsed_seconds"]
        require(type(elapsed) in (int, float) and math.isfinite(elapsed) and
                0 <= elapsed <= execution["elapsed_seconds"], "actual own sampled phase elapsed")
        own_batch = next(b for b, j in jobs.items() if Path(j["job_root"])/"run-arm" == audit)
        require(x["own_remaining_seconds"] == max(0, jobs[own_batch]["phase_timeout_seconds"]-elapsed) and
                x["peer_remaining_upper_bound_seconds"] == jobs[16 if own_batch == 1 else 1]["phase_timeout_seconds"] and
                x["remaining_seconds"] == max(x["own_remaining_seconds"], x["peer_remaining_upper_bound_seconds"]),
                "unchanged conservative two-arm remaining-time budget")
        expected = d.runtime_budget(int(m[1])*1024, x["free_disk_bytes"], x["remaining_seconds"], groups)
        require({k: result[k] for k in expected} == clean(canonical(expected)),
                "recomputed reserve8GiB/cap-growth/remaining-disk budget differs")
        seen = set()
        for row in result.get("raw_checkpoint_observations", []):
            b = row["batch"]
            p = Path(row["path"])
            require(b in jobs and p.parent == Path(jobs[b]["output_root"])/"gate" and
                    re.fullmatch(r"raw-step-.+\.pt", p.name) and b not in seen and
                    row.get("passed_inferred") is False, "raw checkpoint observation owner/scope")
            seen.add(b)
            if row.get("observation") == "actual_lstat":
                require(type(row["observed_bytes"]) is int and
                        0 <= row["observed_bytes"] <= row["ceiling_bytes"] == d.raw_step_ceiling(b),
                        "unclipped actual raw checkpoint disk ceiling")
            else:
                require(row.get("observation") == "concurrently_disappeared" and
                        "observed_bytes" not in row, "disappearance is not numerical PASS")
    return {"samples": len(refs), "refs": refs,
            "scope": "original sampled cgroups/RAM/disk budgets; not uninterrupted telemetry"}

def strengthen(authority, batch, joint_ref, joint, packet, pins, producer, d, h, helper,
               read=read_file, listing=None):
    child = obj(authority["child"], read)
    report = obj(authority["report"], read)
    jobs = {j["batch"]: j for j in joint["plan"]["jobs"]}
    job = jobs[batch]
    cid = job["container_id"]
    audit = Path(job["job_root"])/"run-arm"
    require(authority["child"]["path"] == str(audit/"CHILD.json") and
            authority["report"]["path"] == str(Path(job["output_root"])/"gate/report.json") and
            authority["identity"]["path"] == str(Path(job["launch_root"])/"identity.json"),
            "actual split host/report/identity mount namespaces")
    require(authority["producer_sources"] == producer and
            child["source_before"] == child["source_after"] == pins and
            obj(actual_ref(audit/"SOURCE_AFTER.json", read), read) == pins,
            "complete actual producer/49-source before-after closure")
    require(child.get("joint") == joint_ref and child.get("separate_canary_not_gate") is True and
            child.get("service_ready") is False and child.get("performance") is False,
            "real shared joint, canary and limited scope")
    args = authority["args"]
    require(authority["command"] == "/usr/bin/python3" and args[:3] ==
            ["-B", str(DISPATCH/"controller.py"), "run-arm"] and args[-1:] == ["--execute"],
            "actual MAIN run-arm original command")
    rest = args[3:-1]
    require(len(rest) == 8 and len(set(rest[::2])) == 4, "four unique actual outer CLI flags")
    require(dict(zip(rest[::2], rest[1::2])) ==
            {"--packet-sha256": PACKET_SHA, "--joint": joint_ref["path"],
             "--joint-sha256": joint_ref["sha256"], "--batch": str(batch)},
            "actual MAIN exact source/joint/batch argv")
    execution = child["execution"]
    require([execution["command"]]+execution["args"] == d.gate_argv(job, cid) and
            obj(actual_ref(audit/"EXECUTION.json", read), read) == execution,
            "original real WAIT/exec command, not a fabricated Python argv")
    d.inspect_proof(obj(child["container_inspect"], read)[0], job, cid)
    proof = obj(child["device_proof"], read)
    require(proof.get("observed_role") == "prelaunch_wait_bash_not_native" and
            proof.get("gate_process_confirmation_required") is True and
            proof["raw_refs"]["mapping"] == child["container_inspect"],
            "do not mistake waiting PID for actual native observation")
    cv = obj(proof["raw_refs"]["canary"], read)
    require(cv.get("status") == "actual_canary_pass" and
            cv.get("expected_physical_card") == job["physical_card"] and
            cv.get("create_argv_sha256") == digest(canonical(job["create_argv"])) and
            cv.get("canary_program_sha256") == helper.CANARY_SHA, "separate actual source canary")
    fresh = obj(proof["raw_refs"]["host_processes"], read)
    require(fresh.get("protected") == joint["protected"] and
            fresh.get("joint_minimum_bytes") == 24*GIB and fresh.get("joint_cpu_with_reserve") == 3,
            "actual same-joint fresh resource identity")
    require(fresh.get("ordinary_available_bytes", 0) >= 24*GIB and
            fresh.get("docker_info", {}).get("NCPU", 0) >= 3, "actual prelaunch joint RAM24GiB/CPU3")
    canary_rows = h.parse_processes(fresh["npu_smi"])
    require(not canary_rows[job["physical_card"]], "own card empty before real gate")
    observations = child.get("actual_gate_process")
    require(type(observations) is list and len(observations) == 1 and
            observations[0]["path"] == str(audit/"ACTUAL_GATE_NPU_PID.json"),
            "one real original gate/PID observation required")
    observation = obj(observations[0], read)
    require(observation["waiting"]["path"] == str(audit/"WAIT_PID.json"), "real saved wait identity")
    waiting = obj(observation["waiting"], read)
    require(waiting["pid"] == proof["same_process_pid"], "waiting PID declaration belongs to real exec")
    process = exact_process(observation, waiting, cid, batch, d, h, joint["protected"])
    claim = obj(actual_ref(Path(job["job_root"])/"ARM_CLAIM.json", read), read)
    release = obj(actual_ref(Path(job["launch_root"])/"RELEASE", read), read)
    require(claim.get("batch") == batch and claim.get("joint") == joint_ref and
            claim.get("automatic_retry") is False and release.get("identity") == authority["identity"] and
            release.get("joint") == joint_ref and release.get("not_a_pass") is True and
            type(claim.get("claimed_ns")) is int and
            claim["claimed_ns"] <= release["approved_release_ns"] <= report["created_ns"],
            "exclusive claim/release/report ordering, not automatic retry")
    budget = budget_samples(child["runtime_resource_budgets"], audit, jobs, execution, d, read)
    parent_rows = command_receipts(audit, "parent-inspect", read, listing)
    require(len(parent_rows) == 4, "actual four original parent stopped-inspect receipts")
    seen = set()
    for _, receipt, streams in parent_rows:
        values = clean(streams["stdout"])
        require(len(values) == 1, "actual one parent inspect")
        e = values[0]; seen.add(e["Id"])
        require(receipt["argv"] == ["/usr/bin/docker", "inspect", e["Id"]] and
                e["Id"] in d.PARENT_IDS and e["Image"] == d.IMAGE and
                e["Config"].get("Labels", {}).get("model-tuning-lab.owner") == "damp-allT-dispatch-v1" and
                e["State"].get("Running") is False and e["State"].get("Pid") == 0,
                "actual stopped original parent ownership, no protected cleanup")
    require(seen == set(d.PARENT_IDS), "four unique exact parent IDs")
    stopped = command_receipts(audit, "stopped-inspect", read, listing)
    released = command_receipts(audit, "release-npu-processes", read, listing)
    require(len(stopped) == len(released) == 1, "one actual own stop/release evidence")
    entry = clean(stopped[0][2]["stdout"])
    require(len(entry) == 1 and stopped[0][1]["argv"] == ["/usr/bin/docker", "inspect", cid],
            "exact own original stop-inspect command")
    d.inspect_proof(entry[0], job, cid)
    require(entry[0]["State"].get("Running") is False and entry[0]["State"].get("Pid") == 0 and
            child.get("cleanup") == {"container_id": cid, "stopped": True, "retained": True, "deleted": False},
            "actual exact stopped/retained container, not cleanup bool alone")
    require(released[0][1]["argv"] == [d.NPU_SMI, "info"], "original verified release npu-smi")
    release_rows = h.parse_processes(released[0][2]["stdout"].decode())
    require(not release_rows[job["physical_card"]], "actual own authorized card released")
    for card in range(4):
        require([x["pid"] for x in release_rows[card]] ==
                [x["pid"] for x in joint["protected"][str(card)]], "protected raw PID set on release")
    refs = [x[0] for x in parent_rows+stopped+released]
    return {"batch": batch, "actual_gate_process": observations, "process": process,
            "runtime_resources": budget, "original_command_receipts": refs,
            "source_after": actual_ref(audit/"SOURCE_AFTER.json", read)}

def validate(inputs, manifest_ref, *, enabled=False, read=read_file, listing=None):
    require(enabled is True, "default OFF; explicit validation only")
    require(type(inputs) is dict and set(inputs) == {"b1", "b16", "source_manifest"},
            "exact original two-run bridge inputs")
    packet, pins, producer, bridge, d, h, helper = sources(manifest_ref, read)
    require(inputs["source_manifest"] == packet["bridge_manifest"], "actual original bridge manifest")
    component = bridge.validate_complete(inputs["b1"], inputs["b16"], inputs["source_manifest"],
                                         read, enabled=True, testing=False)
    require(component["npu_verified"] is True and component["evidence_kind"] == "actual-main-execution",
            "synthetic contract cannot authorize actual model diagnostic")
    children = [obj(inputs[k]["child"], read) for k in ("b1", "b16")]
    joint_ref = children[0]["joint"]
    require(joint_ref == children[1]["joint"], "one actual joint admission for both jobs")
    joint = obj(joint_ref, read)
    require(joint.get("schema") == "kvbp.split-joint-prepared/v1" and
            joint["packet_sha256"] == PACKET_SHA and joint["producer_sources"] == producer and
            joint["source_pins"] == pins, "actual frozen joint source identity")
    prepared = joint["prepared_ns"]
    require(type(prepared) is int and prepared > 0, "actual prepare timestamp")
    predicted = d.plan(joint["inputs"], datetime.fromtimestamp(prepared/1e9, timezone.utc))
    plan = dict(joint["plan"])
    jobs = plan["jobs"]
    require(len(jobs) == 2 and {j["batch"] for j in jobs} == {1,16} and
            len({j["container_id"] for j in jobs}) == 2, "two distinct actual prepared containers")
    plan["jobs"] = [{k: v for k, v in j.items() if k != "container_id"} for j in jobs]
    require(plan == predicted, "unchanged true two-job create/mount/CPU/RAM/phase plan")
    parent = d.parent_terminal(obj(joint["inputs"]["parent_operation"], read), joint["inputs"]["parent_expected"])
    require(joint["parent"]["original_operation"] == joint["inputs"]["parent_operation"] and
            joint["parent"]["terminal"] == parent, "failed previous operation is release evidence only")
    details = [strengthen(inputs[k], b, joint_ref, joint, packet, pins, producer, d, h, helper, read, listing)
               for k, b in (("b1", 1), ("b16", 16))]
    return {"schema": "kvbp.checked-split-service-prerequisite/v1",
            "status": "actual_raw_two_job_prerequisite_checked", "source_manifest": ref(manifest_ref),
            "original_inputs": inputs, "component": component, "joint": joint_ref, "details": details,
            "native_gate_kind": "split-kernel-prerequisite", "legacy_pass_fabricated": False,
            "service_ready": False, "model_lifecycle_verified": False, "other_batches_verified": False,
            "matched_e2e_verified": False, "task_accuracy_verified": False,
            "limitations": ["sampled resource observations are not continuous telemetry",
                            "protected PID/cgroup-start invariants remain source-bound producer observations",
                            "initial packed/native state and true model lifecycle need separate numeric evidence",
                            "B1/B16 isolated matrix does not admit T2-15/C16/formal performance"]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", nargs="?", choices=("plan", "freeze", "check"), default="plan")
    p.add_argument("--manifest"); p.add_argument("--manifest-sha256")
    p.add_argument("--inputs"); p.add_argument("--inputs-sha256")
    p.add_argument("--output"); p.add_argument("--enable", action="store_true")
    a = p.parse_args()
    if a.mode == "plan":
        print(json.dumps({"enabled": False, "launches_npu": False, "service_ready": False,
                          "requires": ["two original MAIN RunAuthority records", "raw joint/PID/budget/cleanup",
                                       "MAIN-reviewed NEW source manifest", "fresh TP4 MAIN identity later"]}))
        return
    if a.mode == "freeze":
        packet = obj({"path": str(PACKET), "sha256": PACKET_SHA})
        for path, wanted in packet["frozen_dependencies"].items():
            require(digest(read_file(path)) == wanted, "old source drift during freeze")
        result = {"schema": "kvbp.split-service-consumer-sources/v1", "enabled": False,
                  "files": {n: digest(read_file(BASE/n)) for n in OWN},
                  "dispatcher_packet": {"path": str(PACKET), "sha256": PACKET_SHA}}
        print(canonical(result).decode())
        return
    require(a.enable and all((a.manifest, a.manifest_sha256, a.inputs, a.inputs_sha256, a.output)),
            "explicit MAIN raw input/source Refs/new output")
    input_ref = {"path": a.inputs, "sha256": a.inputs_sha256}
    result = validate(obj(input_ref), {"path": a.manifest, "sha256": a.manifest_sha256}, enabled=True)
    result["input_ref"] = input_ref
    write_new(a.output, result)
    print(json.dumps({"checked": actual_ref(a.output), "service_ready": False, "launches_npu": False}))

if __name__ == "__main__":
    main()
