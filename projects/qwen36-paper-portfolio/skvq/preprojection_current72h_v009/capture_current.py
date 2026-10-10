"""DEFAULT OFF. MAIN-owned SAME-image container entry, not a host/NPU lease.
Real LLM + native named collective_rpc scheduler; complete256 inputs only.
Must be launched by MAIN's fresh owned resource controller, never by preparer.
"""
import argparse,datetime,json,os,shutil,sys,time,traceback
from pathlib import Path
import hashlib
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
if hashlib.sha256((BASE/"SOURCE_MANIFEST.sha256").read_bytes()).hexdigest()!="ecc5065c34b63029e44ba2be227d725c67f6437b2023aeb0e8a9916d3dbab711":
    raise ValueError("original frozen capture001 source manifest")
sys.path.insert(0,str(BASE))
from io_contract import *
PROJECTION=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-capture-adapter-v1-001")
sys.path.insert(0,str(PROJECTION))
import rpc_extension as rpc
import current_contract as C
from model_kwargs import kwargs
import spawn_startup as startup
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LLM_PATH="/vllm-workspace/vllm/vllm/entrypoints/llm.py"
LLM_SHA="fd28c3f53740d196689ac97ca566bd23879d082b3e9c7eb9ca20f0a88caf6e7e"
DEADLINE=C.CUT
def admission(ref_path,root,max_total):
    """Consume actual MAIN pre-create/in-container binding. Fields below are a
    new explicit required raw receipt schema, not a claim a receipt exists.
    MAIN must originate this from real inspect/cgroup/SMI/clock, independently
    consume it before launch, and continuously supervise CPU/RAM/ownership.
    """
    require(os.environ.get("QWEN36_SKVQ_CAPTURE_ENABLE")=="1" and
      os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1" and os.environ.get("QWEN36_SKVQ_PROJECTION_CAPTURE_ENABLE")=="1","three explicit opt-ins")
    p=Path(ref_path);v=json.loads(p.read_text())
    require(v["current_source_ref"]==C.source() and v["current_clock"]["protocol_ref"]==C.clock()["protocol_ref"] and
      v["current_clock"]["portfolio_cutoff_epoch"]==C.CUT,"actual current source/unchanged72h authorization")
    C.checked(v["n1_ref"]);n1=json.loads(Path(v["n1_ref"]["path"]).read_bytes())
    require(n1["status"]=="SKVQ_ALL4_TINY_N1_CHECKED" and n1["source_ref"]==C.source() and
      n1["effective_capture_configuration_checked"]is True and len(n1["ranks"])==4,"actual same-source all4 tiny/config before model")
    require(v["schema"]=="MAIN_SKVQ_FRESH_CAPTURE_ADMISSION_V1" and v["image"]==IMAGE and
      v["physical_npus"]==[4,5,6,7] and v["owned_cid"]==os.environ.get("MAIN_OWNED_CID") and
      v["inside_output_root"]==str(root),"actual source/mount/CID scope binding")
    require(time.time()-v["observed_epoch"]>=0 and time.time()-v["observed_epoch"]<=60 and
      v["max_total_seconds"]==max_total and v["cleanup_included_seconds"]==180,"fresh total clock includes180cleanup")
    require(600<=max_total<=7200 and time.time()+max_total<=DEADLINE,"portfolio complete budget not reset")
    require(v["memory_guest_bytes"]==64*2**30 and v["memory_host_bytes"]==512*2**20 and
      v["memory_reserve_bytes"]==8*2**30 and v["ordinary_available_bytes"]>=v["memory_guest_bytes"]+v["memory_host_bytes"]+v["memory_reserve_bytes"],"same-budget ordinary memory pre-create, HugeTLB untouched")
    require(v["guest_cpu_effective"]>=4 and v["host_cpu_effective"]>=1 and
      v["joint_ancestor_cpu_budget"]>=7 and v["reserve_cpu"]==2 and
      v["cpu_all_ancestors_checked"] is True and v["daemon_ancestors_checked"] is True,"actual shared ancestor summed CPU")
    require(v["mounts_exact_semantic_set_checked"] is True and v["devices_exact_checked"] is True and
      v["source_manifest_consumed"] is True and v["input_raw_consumed"] is True,"actual mounts/source/input consumer receipt")
    require(v["disk_available_bytes"]>=320*2**30 and shutil.disk_usage(root.parent).free>=320*2**30,"256GiBQKV+32GiBpreK+32GiB reserve; real filesystem free")
    require(v["foreign_physical_npus_protected"]==[0,1,2,3] and v["protected_services_untouched"] is True,
      "MAIN owner protects foreign0-3/OVS, never releases additional hugepages")
    for r in v["raw_refs"]:
        require(reference(r["path"])==r,"actual raw admission refs, no flags alone")
    require(v["raw_refs"],"inspect+SMI+host/daemon cgroup raw refs mandatory")
    return reference(p)
def run(inputs,out,receipt,max_total):
    start=time.monotonic();out=Path(out)
    consumed_input=load_inputs(inputs);input_ref=reference(inputs)
    require(sha_file(LLM_PATH)==LLM_SHA,"actual public LLM source before import/launch")
    receipt_ref=admission(receipt,out,max_total)
    out=safe_root(out,"run-skvq-capture-projection-001-")
    llm=None;primary=None;secondary=[];rank_results=None;completed=[];startup_ref=None;install=[];spawn_refs=[]
    try:
        from vllm.entrypoints.llm import LLM
        from vllm import SamplingParams
        from tp_provider import module_origin
        module_origin(sys.modules["vllm.entrypoints.llm"],"vllm.entrypoints.llm",LLM_SHA)
        startup_ref=startup.parent(C.source(),out)
        llm=LLM(**kwargs())
        install=llm.collective_rpc(rpc.METHODS[0],timeout=60,args=(str(Path(inputs)),str(out),C.source()["sha256"]))
        require(len(install)==4 and {r["rank"] for r in install}==set(range(4)),"actual all4 installed receivers")
        spawn_refs=startup.consume_installs(install,startup_ref,C.source())
        publish_json(out/"INSTALL.json",install)
        params=SamplingParams(temperature=0,max_tokens=1,min_tokens=1,ignore_eos=True)
        for i in range(256):
            require(time.monotonic()-start<max_total-180 and time.time()+180<DEADLINE,"full fixed budget, retain remaining180cleanup")
            arms=llm.collective_rpc(rpc.METHODS[1],timeout=30,args=(i,))
            require(len(arms)==4 and {r["rank"] for r in arms}==set(range(4)) and
              all(r["sample_id"]==i and r["input_token_sha256"]==consumed_input["samples"][i]["token_ids_sha256"] for r in arms),"all actual4 ranks same current frozen input")
            tokens=sample_ids(inputs,i)
            outputs=llm.generate([{"prompt_token_ids":tokens}],params,use_tqdm=False)
            require(len(outputs)==1 and outputs[0].finished and outputs[0].prompt_token_ids==tokens and
              len(outputs[0].outputs)==1 and len(outputs[0].outputs[0].token_ids)==1,"real unchanged single request, only one native output")
            record={"sample_id":i,"actual_input_sha256":consumed_input["samples"][i]["token_ids_sha256"],
              "request_id":outputs[0].request_id,"native_output_token_ids":list(outputs[0].outputs[0].token_ids),
              "arms":arms,"elapsed_seconds":time.monotonic()-start}
            completed.append(publish_json(out/("SAMPLE-%03d.json"%i),record))
        rank_results=llm.collective_rpc(rpc.METHODS[2],timeout=60)
        require(len(rank_results)==4,"all4 actual complete/restored rank manifests")
        require(reference(inputs)==input_ref,"frozen actual input after all256")
    except BaseException as e:
        primary={"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
    finally:
        # This restoration path never runs numerical/source/resource admission
        # checks that could block already failed exact-owned cleanup. The MAIN
        # host remains responsible for bounded owned stop/retain on RPC failure.
        if llm is not None:
            try:secondary=llm.collective_rpc(rpc.METHODS[3],timeout=30)
            except BaseException as e:secondary=[{"type":type(e).__name__,"message":str(e),"scope":"restore_rpc"}]
        result={"schema":"SKVQ_CAPTURE_PRODUCER_RESULT_V1",
          "status":"ALL256_CAPTURED_PENDING_INDEPENDENT_CONSUMER" if primary is None else "FAILED",
          "primary":primary,"secondary":secondary,"rank_results":rank_results,"sample_records":completed,
          "current_source_ref":C.source(),"current_clock":C.clock(),
          "spawn_parent_ref":startup_ref,"worker_install_results":install,"worker_spawn_install_refs":spawn_refs,
          "input_ref":input_ref,"admission_ref":receipt_ref,"elapsed_seconds":time.monotonic()-start,
          "max_total_seconds_including_cleanup":max_total,"cleanup_reserved_seconds":180,
          "actual_native_baseline_capture_only":True,"author_calibration_not_run":True,
          "formal_start_utc":None,"formal_deadline_utc":None,"portfolio_deadline_utc":"2026-10-12T07:00:25Z",
          "native_ready":False,"model_ready":False}
        publish_json(out/"PRODUCER_RESULT.json",result)
    require(primary is None and all(not r.get("secondary") and not r.get("primary") for r in secondary),"actual producer/cleanup failure; no calibration promotion")
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");p.add_argument("--inputs");p.add_argument("--output")
    p.add_argument("--source-manifest-sha256");p.add_argument("--admission");p.add_argument("--max-total-seconds",type=int,default=7200);a=p.parse_args()
    if not a.execute:print(json.dumps({"default_enabled":False,"Torch_imported":"torch" in sys.modules,"model_launched":False,"native_ready":False}));return
    require(a.inputs and a.output and a.admission,"exact input/newoutput/actual MAIN admission required")
    C.configure(a.source_manifest_sha256)
    print(json.dumps(run(a.inputs,a.output,a.admission,a.max_total_seconds),sort_keys=True))
if __name__=="__main__":main()
