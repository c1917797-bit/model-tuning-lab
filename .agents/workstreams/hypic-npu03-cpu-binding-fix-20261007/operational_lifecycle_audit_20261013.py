#!/usr/bin/env python3
"""Independent new operational scope audit; old semantic verdicts unchanged."""
import argparse, hashlib, json, os, re
from pathlib import Path
HERE=Path(__file__).resolve().parent
RAW=Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
ARM="hypic-only"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def need(ok,msg):
    if not ok: raise ValueError(msg)
def activation(events,mode,worker_pids,engine_pids,identifier):
    if mode!="enabled":
        need(not events,"disabled/uninstalled treatment emitted events")
        return dict(disabled_marker_absent=True)
    required=set(worker_pids)|set(engine_pids)
    builds={r["pid"] for r in events if r.get("event")=="plugin_build_active"
            and r.get("module")=="/opt/hypic/hypic_vllm_ascend/__init__.py"
            and r.get("version")=="0.8.5"}
    need(required<=builds,"engine/worker native registration absent")
    sched={r["pid"] for r in events if r.get("event")=="runtime_scheduler_active"}
    need(set(engine_pids)<=sched,"engine scheduler activation absent")
    hot=[r for r in events if r.get("event")=="worker_hot_request_verified"
         and re.fullmatch(re.escape(identifier)+r"-[0-9a-f]{8}",r.get("request_id",""))]
    need({r["pid"] for r in hot}==set(worker_pids),"target four-worker hot proof incomplete")
    need(len({r["request_id"] for r in hot})==1,"cross-worker request disagreement")
    need(all(r.get("complete_hybrid_repair_validated") is True
         and r.get("skipped_prefix_tokens",0)>0 and r.get("expected_full_layers")==16
         and r.get("expected_gdn_layers")==48 for r in hot),"invalid hybrid proof")
    return dict(target_hot_worker_pids=sorted(worker_pids),engine_pids=sorted(engine_pids),
                request_id=hot[0]["request_id"],step_level_proof=False)
def evaluate(mode):
    need(mode in ["disabled","uninstalled"],"mode")
    root=RAW/("operational-lifecycle-20261013-"+mode)
    new=read(HERE/"operational_lifecycle_20261013.json")
    frozen=read(HERE/"native_lifecycle_contract.json")
    need(sha(HERE/"native_lifecycle_contract.json")==new["legacy_contract_sha256"],"legacy contract drift")
    for n,h in new["files"].items(): need(sha(HERE/n)==h,"new support drift: "+n)
    for n,h in frozen["files"].items(): need(sha(HERE/n)==h,"support drift: "+n)
    contract,terminal=read(root/"contract.json"),read(root/"terminal.json")
    need(contract["frozen"]==new and contract["preregistration_sha256"]==sha(HERE/"operational_lifecycle_20261013.json"),"contract drift")
    need(terminal["completed"] and terminal["error"] is None and terminal["mode"]==mode,"execution incomplete")
    item,start,stop,ns,source=[read(root/p) for p in ["container-inspect.json",ARM+"/service-start.json",
        ARM+"/service-stop.json",ARM+"/worker-namespace-map.json",ARM+"/source-attestation.json"]]
    cid=terminal["container_id"]
    need(item["Id"]==cid and all(x["container_id"]==cid for x in [start,stop,ns,source]),"container identity")
    need(item["Image"]==frozen["image"] and item["HostConfig"]["CpusetCpus"]=="112-191"
         and item["HostConfig"]["NetworkMode"]=="host","container runtime")
    spec=dict(binds=sorted(item['HostConfig']['Binds']),env=sorted(item['Config']['Env']),
       command=item['Config']['Cmd'],devices=item['HostConfig']['Devices'],
       image=item['Image'],cpuset=item['HostConfig']['CpusetCpus'])
    need(hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()
         ==new['phase_spec_sha256'][mode],'actual command/environment/binds/devices drift')
    mapped=[x["PathOnHost"] for x in item["HostConfig"]["Devices"] if re.fullmatch(r"/dev/davinci\d+",x["PathOnHost"])]
    need(mapped==["/dev/davinci"+str(i) for i in range(4)],"physical device scope")
    need(start["source_attestation_sha256"]==sha(root/ARM/"source-attestation.json"),"source receipt hash")
    need(source["selected_source_commit"]==frozen["source_commit"],"source commit")
    need(source["actual_command"]==item["Config"]["Cmd"] and source["actual_binds"]==sorted(item["HostConfig"]["Binds"]),"actual spec")
    env=dict(x.split("=",1) for x in item["Config"]["Env"])
    need(env["VLLM_ASCEND_HYPIC_ENABLE"]==("1" if mode=="enabled" else "0"),"switch identity")
    need(env["ASCEND_RT_VISIBLE_DEVICES"]=="0,1,2,3","logical map")
    probe=read(root/"installed.json")
    need(probe["installed"] and probe["expect"]=="installed"
         and probe["manifest_sha256"]==frozen["package_assets"]["MANIFEST.json"]
         and probe["framework_runner_sha256"]==frozen["framework_runner_sha256"],"installed source identity")
    for field,name in [("npu_smi_sha256","npu-smi-at-health.txt"),("docker_top_sha256","docker-top-at-health.txt"),
                       ("worker_namespace_map_sha256","worker-namespace-map.json")]:
        need(start[field]==sha(root/ARM/name),"physical proof hash")
    need(set(start["worker_pid_by_physical_npu"])=={"0","1","2","3"}
         and ns["physical_npu_to_host_pid"]==start["worker_pid_by_physical_npu"],"physical PID map")
    need(stop["container_removed"] and stop["owned_npus_released"] and stop["port_released"],"owned release incomplete")
    guard=read(root/ARM/"lane-guard.json")
    need(guard["samples"]>0 and not guard["foreign"] and not guard["probe_errors"]
         and guard["owned_container_id"]==cid,"isolation")
    need(set(guard["expected_worker_pids"])==set(start["worker_pid_by_physical_npu"].values()),"guard workers")
    logs=list((root/ARM).glob("service.full.*.log"))
    need(len(logs)==1 and sha(logs[0])==stop["service_log_sha256"],"logs identity")
    text=logs[0].read_text(errors="replace")
    need("Failed to load plugin hypic_vllm_ascend" not in text,"plugin swallowed startup failure")
    pairs=set((int(r),int(p)) for r,p in re.findall(r"\(Worker_TP([0-3]) pid=(\d+)\)",text))
    need(len(pairs)==4 and {r for r,p in pairs}==set(range(4)),"rank map")
    workers={p for r,p in pairs}
    need(workers==set(ns["physical_npu_to_namespace_pid"].values()),"rank/physical PID mapping")
    engines={int(p) for p in re.findall(r"\(EngineCore[^)]*pid=(\d+)\)",text)}
    need(len(engines)==1,"engine inventory")
    events=[json.loads(x) for x in (root/ARM/"hypic-evidence.jsonl").read_text().splitlines() if x]
    result=activation(events,mode,workers,engines,"chatcmpl-hypic-native-lifecycle-"+mode+"-s059")
    if mode=="uninstalled":
        for name in ["uninstalled.json","absent-at-health.json"]:
            absent=read(root/name)
            need(absent["expect"]=="absent" and not absent["installed"]
                 and absent["module_origin"] is None and absent["entrypoints"]==[],"uninstall absent proof")
        need(source["plugin_absent"] is True,"uninstalled serving identity")
        result["rollback_scope"]="stop/remove previous owned container; uninstall in replacement instance before official restart, not hot uninstall or same writable-layer restoration"
    else:
        need(source["python_tree_sha256"]==frozen["source_tree_sha256"] and source["python_files"]==32,"serving bytes")
        need("exec bash /opt/hypic/run_with_native_plugin.sh vllm serve " in item["Config"]["Cmd"][2],"same native wrapper")
    row=read(root/"smoke.json")
    smoke(row,mode,frozen["sample"],new["smoke_request_sha256"][mode])
    result.update(mode=mode,lifecycle_valid=True,semantic_quality_evaluated=False,
      requests_completed=1,isolation_samples=guard["samples"],
      source_commit=frozen["source_commit"],released=True,quality_or_performance_claim=False,
      all_skill_acceptance=False,canary_semantic_pass=False,
      scope="operational disable/uninstall/replacement restart only; old quality/canary failures unchanged")
    result["artifact_hashes"]={str(p.relative_to(root)):sha(p) for p in root.rglob("*") if p.is_file()}
    return result
def smoke(row,mode,sample,expected_hash):
    data=row["response"]
    identifier="chatcmpl-operational-lifecycle-20261013-"+mode+"-smoke"
    need(row["request_id"]==data["id"]==identifier,"request identity")
    need(row["max_tokens"]==1 and row["request_sha256"]==expected_hash,"bounded request")
    need(data["usage"]["prompt_tokens"]==sample["prompt_tokens"]
        and data["usage"]["completion_tokens"]==1,"token accounting")
    need(len(data["choices"])==1,"choice count")
    choice=data["choices"][0]
    need(choice["finish_reason"] in ("stop","length") and
         isinstance(choice["message"]["content"],str) and
         bool(choice["message"]["content"]),"valid nonempty operational response")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["disabled","uninstalled"],required=True)
    p.add_argument("--write",action="store_true");a=p.parse_args();r=evaluate(a.mode)
    if a.write:
        dest=RAW/("operational-lifecycle-20261013-"+a.mode+"-audit.json")
        with dest.open("x") as f:json.dump(r,f,indent=2,sort_keys=True)
    print(json.dumps({k:v for k,v in r.items() if k!="artifact_hashes"}))
