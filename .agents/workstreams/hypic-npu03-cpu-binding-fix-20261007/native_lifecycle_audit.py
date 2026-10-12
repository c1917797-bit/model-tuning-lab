#!/usr/bin/env python3
"""Independent lifecycle receipts/activation/request audit; never an adoption gate."""
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
    need(mode in ["enabled","disabled","uninstalled"],"mode")
    root=RAW/("native-lifecycle-20261012-"+mode)
    frozen=read(HERE/"native_lifecycle_contract.json")
    for n,h in frozen["files"].items(): need(sha(HERE/n)==h,"support drift: "+n)
    contract,terminal=read(root/"contract.json"),read(root/"terminal.json")
    need(contract["frozen"]==frozen and contract["preregistration_sha256"]==sha(HERE/"native_lifecycle_contract.json"),"contract drift")
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
         ==frozen['phase_spec_sha256'][mode],'actual command/environment/binds/devices drift')
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
    os.environ.setdefault("HYPIC_HOTPATH_QUALITY_CAMPAIGN","cache10r13")
    os.environ.setdefault("HYPIC_HOTPATH_QUALITY_MODE","full")
    os.environ.setdefault("HYPIC_HOTPATH_QUALITY_ARM",ARM)
    import hotpath_quality_full as existing
    items,evaluator=existing.cases()
    sample=next(x for x in items if x["index"]==59)
    need(all(sample[k]==v for k,v in frozen["sample"].items()),"frozen sample")
    for name,maximum in [("warm1",1),("warm2",1),("target",2048)]:
        row=read(root/(name+".json"));data=row["response"]
        bid="hypic-native-lifecycle-"+mode+"-s059"+("" if name=="target" else "-"+name)
        need(row["request_id"]==data["id"]=="chatcmpl-"+bid and row["max_tokens"]==maximum,"request identity")
        payload=dict(model="qwen36-hypic-e2e-2048",messages=[dict(role="user",content=sample["prompt"])],
            request_id=bid,n=1,max_tokens=maximum,temperature=0,seed=0,ignore_eos=False,stream=False,
            chat_template_kwargs=dict(enable_thinking=False),
            vllm_xargs=dict(hypic_segment_ends=[sample["boundary"],sample["prompt_tokens"]]))
        expected=hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
        need(row["request_sha256"]==expected,"request payload drift")
        need(data["usage"]["prompt_tokens"]==20414 and 1<=data["usage"]["completion_tokens"]<=maximum,"token accounting")
        need(len(data["choices"])==1,"response choice count")
    target=read(root/"target.json")["response"]
    choice=target["choices"][0]
    prediction,correct=evaluator.score_case("longbenchv2",choice["message"]["content"],sample["reference"])
    need(correct and choice["finish_reason"]=="stop","canary semantic or natural finish failed")
    result.update(mode=mode,lifecycle_valid=True,semantic_correct=correct,prediction=prediction,
      completion_tokens=target["usage"]["completion_tokens"],isolation_samples=guard["samples"],
      source_commit=frozen["source_commit"],released=True,quality_or_performance_claim=False,
      all_skill_acceptance=False)
    result["artifact_hashes"]={str(p.relative_to(root)):sha(p) for p in root.rglob("*") if p.is_file()}
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["enabled","disabled","uninstalled"],required=True)
    a=p.parse_args();r=evaluate(a.mode);dest=RAW/("native-lifecycle-20261012-"+a.mode+"-audit.json")
    with dest.open("x") as f: json.dump(r,f,indent=2,sort_keys=True)
    print(json.dumps(dict(path=str(dest),sha256=sha(dest),result={k:v for k,v in r.items() if k!="artifact_hashes"})))
