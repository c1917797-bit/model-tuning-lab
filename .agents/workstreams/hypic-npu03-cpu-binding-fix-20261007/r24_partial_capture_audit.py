#!/usr/bin/env python3
"""Post-terminal partial audit; never relabel the failed r24 lifecycle as success."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from numerical_state_writer import read_sealed
from numerical_state_audit import audit, join_step_receipts

HERE = Path(__file__).resolve().parent
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
ARM = "hypic-only"
BASE = "quality-context-41984-hotpath-cache10r24-state-"
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text())
def require(condition, message):
    if not condition:
        raise ValueError(message)

def evaluate(mode):
    root = RAW/(BASE+mode)
    contract, terminal = read(root/"contract.json"), read(root/"terminal.json")
    frozen = read(HERE/"r24_state_preregistration.json")
    require(contract["frozen"] == frozen, "frozen contract mismatch")
    require(contract["preregistration_sha256"] == sha(HERE/"r24_state_preregistration.json"),
            "preregistration digest mismatch")
    for name, digest in frozen["files"].items():
        require(sha(HERE/name) == digest, "audit/controller code changed: "+name)
    require(terminal["completed"] is False and terminal["error"] == "HTTPError: HTTP Error 500: Internal Server Error", "unexpected failure identity")
    start, stop = read(root/ARM/"service-start.json"), read(root/ARM/"service-stop.json")
    namespace = read(root/ARM/"worker-namespace-map.json")
    source = read(root/ARM/"source-attestation.json")
    item = read(root/"container-inspect.json")
    cid = terminal["container_id"]
    require(all(x["container_id"] == cid for x in [start,stop,namespace,source]), "container mismatch")
    require(item["Id"] == cid and item["Image"] == frozen["image"], "image identity mismatch")
    mapped = [x["PathOnHost"] for x in item["HostConfig"]["Devices"]
              if re.fullmatch(r"/dev/davinci\d+",x["PathOnHost"])]
    require(mapped == ["/dev/davinci"+str(i) for i in range(4)], "physical device mapping mismatch")
    require(source["selected_source_commit"] == frozen["source_commit"]
            and source["python_tree_sha256"] == frozen["source_tree_sha256"], "runtime source mismatch")
    require(start["source_attestation_sha256"] == sha(root/ARM/"source-attestation.json"),
            "source receipt hash mismatch")
    for field,name in [("npu_smi_sha256","npu-smi-at-health.txt"),
                       ("docker_top_sha256","docker-top-at-health.txt"),
                       ("worker_namespace_map_sha256","worker-namespace-map.json")]:
        require(start[field] == sha(root/ARM/name), "worker receipt hash mismatch")
    require(set(start["worker_pid_by_physical_npu"]) == {"0","1","2","3"}
            and namespace["physical_npu_to_host_pid"] == start["worker_pid_by_physical_npu"],
            "physical worker inventory mismatch")
    require(stop["container_removed"] and stop["owned_npus_released"] and stop["port_released"],
            "owned release incomplete")
    guard = read(root/ARM/"lane-guard.json")
    require(guard["samples"] > 0 and not guard["foreign"] and not guard["probe_errors"]
            and guard["owned_container_id"] == cid, "isolation invalid")
    require(set(guard["expected_worker_pids"]) == set(start["worker_pid_by_physical_npu"].values()),
            "guard worker mapping mismatch")
    for name,maximum in [("warm1",1),("warm2",1),("target",2048)]:
        response = read(root/(name+".json"))
        bodyid = frozen["body_request_id"] + ("" if name=="target" else "-"+name)
        require(response["request_id"] == "chatcmpl-"+bodyid
                and response["response"]["id"] == response["request_id"]
                and response["max_tokens"] == maximum, "response identity mismatch")
        usage = response["response"]["usage"]
        require(usage["prompt_tokens"] == 20414 and 1 <= usage["completion_tokens"] <= maximum,
                "response token accounting mismatch")
    logs = list((root/ARM).glob("service.full.*.log"))
    require(len(logs)==1 and sha(logs[0]) == stop["service_log_sha256"], "service log identity")
    text = logs[0].read_text(errors="replace")
    framework_pairs = set((int(rank),int(pid)) for rank,pid in re.findall(
        r"\(Worker_TP([0-3]) pid=(\d+)\)", text))
    require(len(framework_pairs)==4 and {r for r,p in framework_pairs}==set(range(4)),
            "independent framework rank/PID map incomplete")
    bindings = dict(framework_pairs)
    physical_pids = namespace["physical_npu_to_namespace_pid"]
    require(set(bindings.values()) == set(physical_pids.values()), "rank/PID/physical mismatch")
    registrations = []
    for line in text.splitlines():
        if '"schema": "hypic-state-observer-installed/v2"' in line:
            registrations.append(json.loads(line[line.index("{"):line.rindex("}")+1]))
    selected = [x for x in registrations if x["pid"] in bindings.values()]
    if mode == "enabled":
        require({x["pid"] for x in selected} == set(bindings.values()),
                "four worker registration absent")
        for row in selected:
            require(row["request_id"] == "chatcmpl-"+frozen["body_request_id"]
                    and row["manifest_sha256"] == frozen["files"]["state-observer-package-v2/MANIFEST.json"]
                    and row["kv_layer"] == frozen["kv_layer"] and row["gdn_layer"] == frozen["gdn_layer"],
                    "registered observer identity drift")
    else:
        require(not selected, "disabled registration present")
    require("Failed to load plugin hypic_vllm_ascend" not in text, "swallowed plugin failure")
    require(not (root/"after.json").exists(), "post-uninstall response unexpectedly present")
    require("NameError: name '_hypic_diagnostic_state_observer' is not defined" in text,
            "post-uninstall failure not corroborated")
    report = dict(frozen_experiment_verdict="FAILED_POST_UNINSTALL",
                  partial_capture_only=True, post_uninstall_passed=False, mode=mode, physical_npus=[0,1,2,3], isolation_samples=guard["samples"],
                  source_valid=True, released=True, quality_or_performance_claim=False)
    directories = list((root/"capture").iterdir())
    if mode=="disabled":
        require(not directories, "disabled control captured data")
        report["disabled_capture_absent"] = True
    else:
        require(len(directories)==4, "four raw workers required")
        captures,receipts,request_ids = [],[],set()
        manifest_sha = frozen["files"]["state-observer-package-v2/MANIFEST.json"]
        for path in directories:
            seal, events = read_sealed(path)
            meta=seal["metadata"]
            require(meta["manifest_sha256"]==manifest_sha and bindings[meta["rank"]]==meta["pid"],
                    "capture worker/manifest mismatch")
            require(physical_pids[str(meta["container_visible_device"])]==meta["pid"],
                    "capture device/physical mapping mismatch")
            request_ids.add(meta["request_id"])
            captures += [x for x in events if x["schema"]=="hypic-state-capture/v1"]
            receipts += [x for x in events if x["schema"]=="hypic-state-step-receipt/v1"]
            require(len(events)==5, "unexpected bounded event count")
        require(len(request_ids)==1, "cross-worker request mismatch")
        request_id=next(iter(request_ids))
        require(re.fullmatch(re.escape("chatcmpl-"+frozen["body_request_id"])+r"-[0-9a-f]{8}",
                             request_id), "internal request suffix mismatch")
        state=audit(captures,request_id=request_id,kv_layer=frozen["kv_layer"],gdn_layer=frozen["gdn_layer"])
        report["step_join"]=join_step_receipts(state,receipts,bindings,
            runtime_sha256=frozen["runner_sha256"],kv_layer=frozen["kv_layer"],gdn_layer=frozen["gdn_layer"])
        report["state"]=state
        report["limited_device_capture_valid"]=True
    report["artifact_hashes"]={str(p.relative_to(root)):sha(p) for p in root.rglob("*")
                               if p.is_file() and p.name != "controller.lock"}
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["enabled","disabled"],required=True)
    a=p.parse_args()
    report=evaluate(a.mode)
    destination=RAW/("r24-state-"+a.mode+"-partial-capture-audit.json")
    with destination.open("x") as stream:
        json.dump(report,stream,indent=2,sort_keys=True);stream.write("\n")
    print(json.dumps(dict(path=str(destination),sha256=sha(destination),
                          mode=a.mode,evidence_valid=True,quality_claim=False)))
