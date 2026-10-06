#!/usr/bin/env python3
"""Pure stdlib argv generator. Never executes Docker, Git, Torch or NPU."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import time

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
REPO=PROJECT.parents[1]
ROOT=Path("/cache/cch/qwen36-damp-20261006")
GATE=PROJECT/"tests/all_batch_gate_v1"
BUILD=ROOT/"all-batch-wrapper-v3-build-v1"
NATIVE=ROOT/"production-integer-compaction-graph-v1/native-source-manifest.json"
NATIVE_REFERENCE=Path("/cache/austinov/src/vllm-ascend")
NATIVE_HEADER=NATIVE_REFERENCE/"csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h"
META=ROOT/"all-batch-gate-v1-preflight-v1/report.json"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LIBRARY=BUILD/"cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so"
LIBRARY_SHA="a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade"
RECEIPT_SHA="a9c8a6824f3f0948d4395eabcc731a0b4e0da6a7f94d6053d3159cf008e23d36"
SOURCE_SHA="a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958"
RUNTIME_SHA="1755f39069b18b10aaabfb7ff341e6879ba741af3cbb72703b64ffe1070f38d5"
META_SHA="131824824ae447f6c26bb53abf49c01a418f08bd30738c2d24f7c55a5cd0ccd0"
NATIVE_SHA="6eb9c6d5dbad6f4d5a9507708ab3ac80d4533ed9b3aaa0897aa4270baa7edc54"
NATIVE_COMMIT="5cb98caaadeff42b5b62b996e34bb2aaa29d20fd"
NATIVE_HEADER_SHA="96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b"
NATIVE_SO="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SO_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
GIB=1024**3
PER_CARD_CPU_QUOTA=1
NUMERIC_CPU_QUOTA=4*PER_CARD_CPU_QUOTA
OPTIONAL_SELECTOR_CPU_QUOTA=2
JOINT_CPU_QUOTA=NUMERIC_CPU_QUOTA+OPTIONAL_SELECTOR_CPU_QUOTA
PER_CARD_BYTES=8*GIB
AGGREGATE_MIN_BYTES=4*PER_CARD_BYTES+8*GIB
DISK_MIN_BYTES=8*GIB
CAPTURE_OPERATION="exec-0000000000000455"
PYTHON="/usr/local/python3.12.13/bin/python3"
BOOTSTRAP=('set -e; source /usr/local/Ascend/ascend-toolkit/set_env.sh; '
 'source /usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh; '
 'source /usr/local/Ascend/nnal/atb/set_env.sh --cxx_abi=1; '
 'export ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0; exec "$@"')
CANARY_CODE='''import json,os,sys,time
import torch,torch_npu
assert os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0"
assert torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4"
torch_npu.npu.set_compile_mode(jit_compile=False)
torch.npu.set_device(0)
assert torch.npu.get_device_name("npu:0")=="Ascend910B4"
x=torch.tensor([1.,2.,3.],dtype=torch.float32,device="npu:0")
y=x*x
torch.npu.synchronize()
value=y.cpu().tolist()
assert value==[1.,4.,9.]
print(json.dumps({"schema":"damp_allT_canary_v1","status":"actual_canary_pass",
 "npu_executed":True,"expected_physical_card":int(sys.argv[1]),"logical_device":0,
 "runtime_soc":torch.npu.get_device_name("npu:0"),"result":value,
 "create_argv_sha256":sys.argv[2],"canary_program_sha256":sys.argv[3],
 "completed_at_unix_ns":time.time_ns(),
 "scope":"actual tiny NPU mul only; physical mapping comes from MAIN inspect, not this program"}))
'''
CANARY_SHA=hashlib.sha256(CANARY_CODE.encode()).hexdigest()

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def argv_sha(argv):
    return hashlib.sha256(json.dumps(argv,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()

def read_bound(path,digest):
    p=Path(path)
    require(isinstance(digest,str) and re.fullmatch(r"[a-f0-9]{64}",digest),"lowercase SHA256 required")
    require(p.is_absolute() and p.is_file(),"missing absolute artifact: "+str(p))
    require(sha(p)==digest,"artifact drift: "+str(p))
    return json.loads(p.read_text())

def gate_contract():
    spec=importlib.util.spec_from_file_location("damp_allT_dispatch_frozen_gate_contract",GATE/"contract.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(module.SOURCE_SHA==SOURCE_SHA and module.IMAGE==IMAGE,"wrong frozen gate contract")
    return module

def source_admission():
    module=gate_contract()
    args=SimpleNamespace(library=LIBRARY,library_sha256=LIBRARY_SHA,
        source_manifest=module.WRAPPER/"source_manifest.json",source_manifest_sha256=SOURCE_SHA,
        runtime_manifest=GATE/"runtime_manifest.json",runtime_manifest_sha256=RUNTIME_SHA,
        build_receipt=BUILD/"build-receipt.json",build_receipt_sha256=RECEIPT_SHA)
    binding=module.source_bindings(args)
    meta=read_bound(META,META_SHA)
    require(meta.get("schema")=="damp_allT_runner_meta_preflight_v1" and
            meta.get("status")=="actual_full_runner_meta_pass" and meta.get("npu_executed") is False,
            "actual full runner NO-device preflight required")
    require(meta["meta"].get("passed") is True and meta["meta"].get("positive_calls")==32 and
            meta["meta"].get("negative_calls")==46 and
            [x["batch"] for x in meta["meta"]["positives"]]==list(range(1,17)),
            "real allT Meta coverage required, not an old B1/B16 receipt")
    for key,value in (("library_sha256",LIBRARY_SHA),("source_manifest_sha256",SOURCE_SHA),
                      ("runtime_manifest_sha256",RUNTIME_SHA),("build_receipt_sha256",RECEIPT_SHA)):
        require(meta["source_bindings"].get(key)==value,"Meta/source identity drift: "+key)
    return {"compiled_sources":len(binding["compiled_sources"]),
            "runtime_sources":len(binding["runtime_sources"]),
            "library":str(LIBRARY),"library_sha256":LIBRARY_SHA,
            "build_receipt":str(BUILD/"build-receipt.json"),"build_receipt_sha256":RECEIPT_SHA,
            "meta_report":str(META),"meta_report_sha256":META_SHA,
            "source_manifest_sha256":SOURCE_SHA,"runtime_manifest_sha256":RUNTIME_SHA,
            "scope":"actual existing NO-device evidence only; not NPU admission"}

def native_identity(path=NATIVE):
    try:
        manifest=read_bound(path,NATIVE_SHA)
        require(manifest.get("image_id")==IMAGE and manifest.get("native_commit")==NATIVE_COMMIT and
                manifest.get("native_header_sha256")==NATIVE_HEADER_SHA and
                manifest.get("native_runtime_library_path")==NATIVE_SO and
                manifest.get("native_runtime_library_sha256")==NATIVE_SO_SHA and
                manifest.get("source_contract_passed") is True,"native_bindings identity mismatch")
        require(NATIVE_REFERENCE.is_dir() and NATIVE_HEADER.is_file() and
                sha(NATIVE_HEADER)==NATIVE_HEADER_SHA,"readonly exact native reference source missing/drifted")
        return {"path":str(Path(path)),"sha256":NATIVE_SHA,
                "native_reference":str(NATIVE_REFERENCE),"native_header_sha256":NATIVE_HEADER_SHA,
                "scope":"existing identity document; image SO/GDN/proc maps rechecked by real gate"},[]
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        return None,[{"stage":"native_identity","path":str(path),"error":str(error)}]

def shard(run_id,physical,output_root,native_path=NATIVE):
    require(isinstance(run_id,str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}",run_id),"safe bounded run_id")
    require(type(physical) is int and physical in (4,5,6,7),"authorized card only")
    root=Path(output_root)
    require(root.is_absolute() and root.parent==ROOT and root.name=="allT-dispatch-"+run_id,
            "exact fresh experiment output child underROOT")
    require(not root.is_symlink(),"output root cannot be a symlink")
    directory=root/("physical"+str(physical))
    require(not directory.is_symlink(),"shard output mount cannot be a symlink")
    name="qwen36_damp_allt_npu"+str(physical)+"_20261006_"+run_id
    create=["docker","create","--name",name,"--label","model-tuning-lab.owner=damp-allT-dispatch-v1",
            "--label","model-tuning-lab.run="+run_id,"--network","none","--cpus",str(PER_CARD_CPU_QUOTA),
            "--memory","8g","--memory-swap","8g","--cap-drop","ALL",
            "--security-opt","no-new-privileges","--device",
            "/dev/davinci"+str(physical)+":/dev/davinci0"]
    for control in ("davinci_manager","devmm_svm","hisi_hdc"):
        create+=["--device","/dev/"+control]
    for path in (REPO,BUILD,NATIVE_REFERENCE,Path(native_path),Path("/usr/local/Ascend/driver")):
        create+=["--mount","type=bind,source="+str(path)+",target="+str(path)+",readonly"]
    create+=["--mount","type=bind,source="+str(directory)+",target="+str(directory)]
    for env in ("ASCEND_RT_VISIBLE_DEVICES=0","ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0",
                "DAMP_RUN_ALL_BATCH_GATE_V1=1","DAMP_ENABLE_ALL_BATCH_WRAPPER_V3=1",
                "PYTHONDONTWRITEBYTECODE=1"):
        create+=["-e",env]
    create+=["-w",str(REPO),"--entrypoint","/bin/bash",IMAGE,"-c",BOOTSTRAP,
             "damp-allT-idle","sleep","infinity"]
    digest=argv_sha(create)
    gate=[PYTHON,"-B",str(GATE/"run_all_batch_gate.py"),"--physical-card",str(physical),
        "--library",str(LIBRARY),"--library-sha256",LIBRARY_SHA,
        "--source-manifest",str(PROJECT/"operator/all_batch_wrapper_v3/source_manifest.json"),
        "--source-manifest-sha256",SOURCE_SHA,"--runtime-manifest",str(GATE/"runtime_manifest.json"),
        "--runtime-manifest-sha256",RUNTIME_SHA,"--build-receipt",str(BUILD/"build-receipt.json"),
        "--build-receipt-sha256",RECEIPT_SHA,"--native-source-manifest",str(native_path),
        "--native-source-manifest-sha256",NATIVE_SHA,"--output-dir",str(directory/"gate")]
    return {"physical_card":physical,"batches":list(range(1+4*(physical-4),5+4*(physical-4))),
        "container_name":name,"host_output_mount":str(directory),"gate_output":str(directory/"gate"),
        "expected_device_proof_path":str(directory/"device-proof.json"),
        "expected_canary_path":str(directory/"canary.json"),
        "docker_create_argv":create,"create_argv_sha256":digest,
        "docker_start_argv":["docker","start",name],
        "docker_canary_exec_argv":["docker","exec",name,"/bin/bash","-c",BOOTSTRAP,"damp-allT-canary",
                                  PYTHON,"-B","-c",CANARY_CODE,str(physical),digest,CANARY_SHA],
        "gate_argv_source_bound_incomplete":gate,"gate_argv":None,"docker_gate_exec_argv":None,
        "pending_mandatory_arguments":["--device-proof","--device-proof-sha256"],
        "cgroup_memory_limit_bytes":PER_CARD_BYTES,"cpu_quota":PER_CARD_CPU_QUOTA,
        "no_overwrite":"MAIN creates only new output/control dirs and new container; gate subdir must stay nonexistent"}

def validate_live_admission(admission,entries,module,now_ns):
    require(admission.get("schema")=="damp_allT_MAIN_live_admission_v1","MAIN live record schema")
    observed=admission.get("observed_at_unix_ns")
    require(type(observed) is int and 0<=now_ns-observed<=300*10**9,"fresh <=5min host resource record")
    require(admission.get("capture_operation_id")==CAPTURE_OPERATION and
            admission.get("capture_terminal") is True and admission.get("owned_TP4_lease_released") is True,
            "original TP4 capture must be terminal and owned lease released")
    require(admission.get("physical_npu_ids")==[4,5,6,7] and
            admission.get("exclusive_resource_check_passed") is True and
            admission.get("protected_NPU0_3_unchanged") is True,"MAIN real card/protected workload check")
    require(type(admission.get("ordinary_mem_available_bytes")) is int and
            admission["ordinary_mem_available_bytes"]>=AGGREGATE_MIN_BYTES and
            admission.get("per_card_cgroup_limit_bytes")==PER_CARD_BYTES and
            type(admission.get("free_disk_bytes")) is int and admission["free_disk_bytes"]>=DISK_MIN_BYTES,
            "aggregate four8GiB+8GiBreserve ordinaryRAM /8GiB disk admission")
    cpu=admission.get("docker_cpu_capacity",{})
    when=cpu.get("observed_at_unix_ns")
    require(type(when) is int and 0<=now_ns-when<=300*10**9,
            "fresh <=5min actual Docker NCPU capability observation required")
    engine=read_bound(cpu.get("info_path",""),cpu.get("info_sha256",""))
    require(type(engine.get("NCPU")) is int and engine["NCPU"]>=JOINT_CPU_QUOTA,
            "Docker NCPU must admit four1CPU numerical shards + optional2CPU selector")
    require(cpu.get("per_numeric_shard_cpu_quota")==PER_CARD_CPU_QUOTA and
            cpu.get("numeric_shards_cpu_quota")==NUMERIC_CPU_QUOTA and
            cpu.get("optional_selector_cpu_quota")==OPTIONAL_SELECTOR_CPU_QUOTA and
            cpu.get("joint_cpu_quota")==JOINT_CPU_QUOTA and
            cpu.get("formal_performance_exclusive") is True,
            "MAIN joint CPU quota and formal-performance exclusivity record required")
    require(set(admission.get("cards",{}))=={"4","5","6","7"},"all four actual card records")
    for entry in entries:
        card=entry["physical_card"];row=admission["cards"][str(card)]
        require(row.get("container_name")==entry["container_name"] and
                isinstance(row.get("container_id"),str) and
                re.fullmatch(r"[a-f0-9]{64}",row["container_id"]) and
                row.get("container_image_id")==IMAGE and
                row.get("create_argv_sha256")==entry["create_argv_sha256"] and
                row.get("fresh_created_from_this_plan") is True and row.get("inspect_single_card_scope_passed") is True,
                "actual owned new container/image/argv/scope inspect required")
        require(row.get("device_proof")==entry["expected_device_proof_path"] and
                row.get("canary")==entry["expected_canary_path"],"exact new single-shard evidence paths")
        proof=read_bound(row["device_proof"],row["device_proof_sha256"])
        module.validate_device(proof,card,now_ns)
        canary=read_bound(row["canary"],row["canary_sha256"])
        when=canary.get("completed_at_unix_ns")
        require(canary.get("schema")=="damp_allT_canary_v1" and canary.get("status")=="actual_canary_pass" and
                canary.get("npu_executed") is True and canary.get("expected_physical_card")==card and
                canary.get("logical_device")==0 and canary.get("runtime_soc")=="Ascend910B4" and
                canary.get("result")==[1.,4.,9.] and canary.get("create_argv_sha256")==entry["create_argv_sha256"] and
                canary.get("canary_program_sha256")==CANARY_SHA and type(when) is int and
                0<=now_ns-when<=300*10**9,"actual fresh canary from this exact container plan required")
        require(not Path(entry["gate_output"]).exists(),"gate output already exists: never overwrite/retry")
        entry["gate_argv"]=entry["gate_argv_source_bound_incomplete"]+[
            "--device-proof",row["device_proof"],"--device-proof-sha256",row["device_proof_sha256"]]
        entry["docker_gate_exec_argv"]=["docker","exec",entry["container_name"],
            "/bin/bash","-c",BOOTSTRAP,"damp-allT-gate"]+entry["gate_argv"]
        entry["pending_mandatory_arguments"]=[]
    return {"authority":"MAIN-recorded actual fresh inspections/canaries; generator does not measure host truth",
            "resource_observed_at_unix_ns":observed,"reserve_bytes":8*GIB,"total_cgroup_bytes":4*PER_CARD_BYTES,
            "docker_ncpu":engine["NCPU"],"numeric_cpu_quota":NUMERIC_CPU_QUOTA,
            "optional_selector_cpu_quota":OPTIONAL_SELECTOR_CPU_QUOTA,"joint_cpu_quota":JOINT_CPU_QUOTA}

def make_plan(run_id,output_root,admission_path=None,native_path=NATIVE):
    source=source_admission()
    native,missing=native_identity(native_path)
    entries=[shard(run_id,p,output_root,native_path) for p in (4,5,6,7)]
    require(all(not Path(e["gate_output"]).exists() for e in entries),"no existing gate results")
    if admission_path is None:
        require(not Path(output_root).exists(),"new launch/outputroot required before MAIN creates evidence")
    result={"schema":"damp_allT_dispatch_plan_v1","status":"waiting_native_identity" if missing else "waiting_MAIN_live_admission",
        "created_at_unix_ns":time.time_ns(),"executed":False,"npu_executed":False,"source":source,
        "native_identity":native,"missing_evidence":missing,
        "image_id":IMAGE,"capture_operation_id":CAPTURE_OPERATION,"deadline_utc":"2026-10-07T08:48:03Z",
        "aggregate_ram_min_bytes":AGGREGATE_MIN_BYTES,"per_card_limit_bytes":PER_CARD_BYTES,
        "minimum_free_disk_bytes":DISK_MIN_BYTES,"shards":entries,
        "cpu_policy":{"per_numeric_shard_cpu_quota":PER_CARD_CPU_QUOTA,
            "numeric_shards_cpu_quota":NUMERIC_CPU_QUOTA,
            "optional_selector_cpu_quota":OPTIONAL_SELECTOR_CPU_QUOTA,"joint_cpu_quota":JOINT_CPU_QUOTA,
            "needs_MAIN_fresh_actual_Docker_NCPU":True,
            "formal_performance_exclusive":True,
            "scope":"quota feasibility only, not free CPU measurement or formal performance admission"},
        "requires_MAIN_before_any_Docker_create":["capture terminal/ownedlease released",
            "freshprocess/HBM/nodeholders+mappings on4-7; protected0-3 untouched",
            "fresh aggregate ordinaryRAM>=40GiB and disk>=8GiB",
            "fresh Docker NCPU>=6; four1CPU quotas + optional selector2CPU; account for other work",
            "formal performance never overlaps CPU selector or numerical shards",
            "all planned names absent from fresh docker ps -a",
            "new exclusive result directories; no overwrite","actual same immutable image and native/source checks"],
        "scope":"pure argv plan; no container/NPU/idle fact is created; not numerical/E2E/task success"}
    if admission_path is not None:
        require(not missing,"cannot admit incomplete native identity")
        path=Path(admission_path)
        require(path.is_absolute() and path.is_file(),"actual MAIN admission JSON required")
        admission=json.loads(path.read_text())
        result["live_admission"]=validate_live_admission(admission,entries,gate_contract(),time.time_ns())
        result["admission_artifact"]={"path":str(path),"sha256":sha(path)}
        result["status"]="complete_gate_argv_for_MAIN_final_recheck_only"
        result["commands_now"]="only docker_gate_exec_argv; containers already created/canary-tested by MAIN"
    else:
        result["missing_evidence"]+= [{"stage":"live_admission","needed":"actual MAIN resource/card/container/proof/canary JSON"}]
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id",default="v1")
    parser.add_argument("--output-root",type=Path)
    parser.add_argument("--native-source-manifest",type=Path,default=NATIVE)
    parser.add_argument("--admission-file",type=Path)
    args=parser.parse_args()
    output=args.output_root or ROOT/("allT-dispatch-"+args.run_id)
    try:
        result=make_plan(args.run_id,output,args.admission_file,args.native_source_manifest)
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        result={"schema":"damp_allT_dispatch_plan_v1","status":"blocked_source_or_admission",
                "error":repr(error),"executed":False,"npu_executed":False}
        print(json.dumps(result,indent=2,allow_nan=False));return 1
    print(json.dumps(result,indent=2,allow_nan=False));return 0
if __name__=="__main__":raise SystemExit(main())
