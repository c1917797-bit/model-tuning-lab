#!/usr/bin/env python3
"""Independent terminal audit of r25retry1 pre-health isolation failure, not a quality test."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r25retry1-state-enabled")
def read(path):
    return json.loads(path.read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok, message):
    if not ok:
        raise ValueError(message)
def evaluate():
    terminal = read(ROOT/"terminal.json")
    guard = read(ROOT/"hypic-only/lane-guard.json")
    stop = read(ROOT/"hypic-only/service-stop.json")
    contract = read(ROOT/"contract.json")
    inspect = read(ROOT/"container-inspect.json")
    frozen = read(HERE/"r25retry1_state_preregistration.json")
    require(contract["frozen"] == frozen and contract["preregistration_sha256"] == sha(HERE/"r25retry1_state_preregistration.json"), "contract drift")
    for name, digest in frozen["files"].items():
        require(sha(HERE/name) == digest, "frozen code drift: "+name)
    cid = terminal["container_id"]
    require(not terminal["completed"] and terminal["error"] == "RuntimeError: quality lane guard detected foreign NPU0-3 process or probe error", "terminal drift")
    require(guard["owned_container_id"] == stop["container_id"] == inspect["Id"] == cid, "owner mismatch")
    require(inspect["Image"] == frozen["image"], "declared image mismatch")
    numbered = [d["PathOnHost"] for d in inspect["HostConfig"]["Devices"] if d["PathOnHost"].removeprefix("/dev/davinci").isdigit()]
    require(numbered == ["/dev/davinci"+str(i) for i in range(4)], "physical declarations")
    require(guard["samples"] == 46 and not guard["probe_errors"] and len(guard["foreign"]) == 2, "guard evidence drift")
    hit = guard["foreign"][0]
    require(hit["at_utc"] == "2026-10-12T12:23:30.776414+00:00", "detection time drift")
    require(hit["processes"] == [dict(container_id="efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6", physical_npu=1, pid=735127)], "foreign evidence drift")
    require(guard["foreign"][1]["at_utc"] == "2026-10-12T12:23:33.089097+00:00" and guard["foreign"][1]["processes"] == hit["processes"], "second detection drift")
    require(not stop["service_reached_health"] and stop["container_removed"] and stop["owned_npus_released"] and stop["port_released"], "release incomplete")
    require(not guard["expected_worker_pids"], "unexpected healthy workers")
    for name in ("warm1", "warm2", "target", "after"):
        require(not (ROOT/(name+".json")).exists(), "unexpected response")
    require(not list((ROOT/"capture").iterdir()), "unexpected captures")
    logs = list((ROOT/"hypic-only").glob("service.full.*.log"))
    require(len(logs) == 1 and sha(logs[0]) == stop["service_log_sha256"], "log identity")
    return dict(schema="hypic-r25retry1-isolation-terminal-audit/v1",
        decision="ISOLATION_FAILED_BEFORE_HEALTH", scored_responses=0,
        capture_seals=0, guard_samples=46, probe_errors=0,
        foreign_event=hit, owned_released=True, declared_physical_npus=[0,1,2,3],
        runtime_source_or_worker_activation_proven=False,
        observer_fix_device_result="not-tested",
        quality_or_performance_claim=False,
        artifact_hashes={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob("*") if p.is_file()})
if __name__ == "__main__":
    result = evaluate()
    out = ROOT.parent/"r25retry1-state-enabled-isolation-failure-audit.json"
    with out.open("x") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(dict(path=str(out),sha256=sha(out),decision=result["decision"])))
