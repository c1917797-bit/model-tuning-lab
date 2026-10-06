"""Parent-owned one-shot TRAIN FP32 reference pair; no performance/accuracy claim."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

REPO = Path("/opt/host/vnf/austinov/model-tuning-lab")
RESULT = Path("/cache/cch/qwen36-damp-20261006")
INPUT = RESULT/"calibration-inputs"
MODEL = "/cache/efim/Qwen3.6-27B"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MANIFEST = INPUT/"full-training-36x1024-v3.json"
MANIFEST_SHA = "f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33"
MANIFEST_SEMANTIC_SHA = "6791283f69290789555d4391312e8d8511fee7787d2ea4257599302486f34bb7"
HELPER = REPO/"projects/damp-ascend/tools/run_collector_smoke.py"
HELPER_SHA = "da541917ebd8764a81624a215a157b6d4e18fbaaa53d9310be54a104d2fbbf92"
NAME = "qwen36_damp_full_capture_tp4_20261006_v1"
AUDIT = RESULT/"full-capture-v1-launch"
ARMS = {arm:RESULT/("full-capture-v1-"+arm) for arm in ("off","on")}
LABEL = "model-tuning-lab.full-capture-owner"
TIMEOUTS = dict(create=90,start=90,import_source=120,manifest_identity=120,canary=90,
               off=10800,on=10800,validate=900)
GiB = 1024**3

def require(value,message):
    if not value:raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def helper():
    require(HELPER.resolve()==HELPER and sha(HELPER)==HELPER_SHA,"frozen smoke safety helper changed")
    spec=importlib.util.spec_from_file_location("damp_full_safety",HELPER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Only configure this fresh process's helper object; never edit its source.
    module.NAME, module.AUDIT, module.MANIFEST = NAME,AUDIT,MANIFEST
    return module

def resources(snapshot,usage):
    match=re.search(r"^MemAvailable:\s*(\d+)",snapshot["meminfo"],re.M)
    require(match is not None and int(match[1])>=64*1024*1024,
            "ordinary MemAvailable below64GiB; never reclaim HugeTLB")
    require(usage.free>=40*GiB,"result filesystem free space below40GiB")
    return dict(mem_available_kib=int(match[1]),result_free_bytes=usage.free,
                minimum_memory_gib=64,minimum_result_disk_gib=40)

def shape(manifest):
    require(manifest["mode"]=="full" and len(manifest["rows"])==36 and
        all(len(row["input_ids"])==1024 for row in manifest["rows"]) and
        manifest["generation"]==dict(temperature=0,seed=0,thinking=False,
            ignore_eos=True,min_tokens=4096,max_tokens=4096) and
        manifest["tp_size"]==4 and manifest["physical_npus"]==[4,5,6,7] and
        manifest["anchors"]==[256,512,768,2304,2560,2816] and manifest["horizon"]==256 and
        manifest["layers"]==[i for i in range(64) if i%4!=3],
        "full36 TRAIN reference protocol changed")

def absent(paths):
    require(all(not Path(p).exists() for p in paths),"output already exists; no overwrite/retry")

def container_proof(entry,expected_id,owner):
    require(entry["Id"]==expected_id and re.fullmatch(r"[0-9a-f]{64}",expected_id) is not None and
        entry["Name"]=="/"+NAME and entry["Image"]==IMAGE and
        entry["Config"]["Labels"].get(LABEL)==owner and entry["HostConfig"]["Privileged"] is False and
        entry["HostConfig"]["NetworkMode"]=="host" and
        not entry["HostConfig"].get("DeviceRequests"),"owned container identity/privilege drift")
    mappings={d["PathOnHost"]:d["PathInContainer"] for d in entry["HostConfig"]["Devices"]}
    wanted={**{f"/dev/davinci{p}":f"/dev/davinci{p-4}" for p in range(4,8)},
            **{p:p for p in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")}}
    require(mappings==wanted and len(entry["HostConfig"]["Devices"])==len(wanted),
            "unexpected device mapping; protected0-3 forbidden")
    mounts={m["Destination"]:m for m in entry["Mounts"]}
    for path,writable in ((str(REPO),False),(MODEL,False),(str(RESULT),True),
                          (str(INPUT),False),("/usr/local/Ascend/driver",False)):
        require(path in mounts and mounts[path]["Type"]=="bind" and mounts[path]["RW"] is writable and
            Path(mounts[path]["Source"]).resolve()==Path(path).resolve(),"mount/source mutability drift")
    return dict(id=entry["Id"],image=entry["Image"],devices=entry["HostConfig"]["Devices"],
        mounts=entry["Mounts"],privileged=False,network="host",owner=owner)

def stage(safety,label,argv):
    started=time.monotonic()
    try:safety.logged(label,argv,TIMEOUTS[label])
    except Exception as error:
        receipt=AUDIT/(label+".receipt.json")
        if not receipt.exists():
            safety.write_new(receipt,dict(argv=argv,exit_code=None,seconds=time.monotonic()-started,
                status="failed",error_type=type(error).__name__,detail=str(error),
                timeout_seconds=TIMEOUTS[label],automatic_retry=False))
        raise

def fresh(safety,label):
    snapshot=safety.idle_snapshot()
    snapshot["full_reference_resources"]=resources(snapshot,shutil.disk_usage(RESULT))
    safety.write_new(AUDIT/(label+".precheck.json"),snapshot)

def stop_owned(safety,container_id,owner):
    entry=json.loads(safety.output(["docker","inspect",container_id]))[0]
    container_proof(entry,container_id,owner)
    result=subprocess.run(["docker","stop","--time","30",container_id],
        capture_output=True,text=True,timeout=45)
    receipt=dict(id=container_id,name=NAME,exit_code=result.returncode,
                 stdout=result.stdout,stderr=result.stderr,deleted=False)
    safety.write_new(AUDIT/"stop.json",receipt)
    require(result.returncode==0,"owned stop failed; retained container needs parent attention")
    after=json.loads(safety.output(["docker","inspect",container_id]))[0]
    container_proof(after,container_id,owner)
    require(after["State"]["Status"]=="exited" and not after["State"]["Running"],
            "owned container not stopped")
    safety.write_new(AUDIT/"stopped.json",dict(id=container_id,status="exited",retained=True))
    print("STOPPED AND RETAINED "+NAME,flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id",choices=["full-v1"])
    parser.add_argument("--self-test",action="store_true",help="stdlib only: no Docker or NPU calls")
    args=parser.parse_args()
    if args.self_test:return self_test()
    require(args.run_id=="full-v1","explicit parent full-v1 execution required")
    require(Path.cwd().resolve()==REPO and REPO.is_dir() and RESULT.is_dir(),
            "canonical repository cwd/results required")
    safety=helper()
    absent([AUDIT,*ARMS.values()])
    require(sha(MANIFEST)==MANIFEST_SHA,"full TRAIN manifest file changed")
    manifest=json.loads(MANIFEST.read_text())
    semantic=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":"),
        ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    require(semantic==MANIFEST_SEMANTIC_SHA,"manifest semantic hash changed");shape(manifest)
    collision=subprocess.run(["docker","container","inspect",NAME],capture_output=True,text=True,timeout=30)
    require(collision.returncode!=0,"full-v1 container already exists")
    require(("No such object: "+NAME in collision.stderr or "No such container: "+NAME in collision.stderr),
            "cannot prove container name absent")
    image=json.loads(safety.output(["docker","image","inspect",IMAGE]))[0]
    require(image["Id"]==IMAGE and image["Architecture"]=="arm64","image identity/architecture changed")
    snapshot=safety.idle_snapshot()
    snapshot["full_reference_resources"]=resources(snapshot,shutil.disk_usage(RESULT))
    AUDIT.mkdir(parents=False,exist_ok=False)
    safety.write_new(AUDIT/"prelaunch.json",snapshot)
    code={}
    for p in sorted((REPO/"projects/damp-ascend/collector").rglob("*")):
        if p.is_file():
            require("__pycache__" not in p.parts,"unexpected generated collector files")
            code[str(p.relative_to(REPO))]=sha(p)
    code[str(HELPER.relative_to(REPO))]=sha(HELPER)
    code[str(Path(__file__).resolve().relative_to(REPO))]=sha(__file__)
    owner=uuid.uuid4().hex
    safety.write_new(AUDIT/"source.json",dict(commit=safety.output(["git","rev-parse","HEAD"]).strip(),
        dirty=safety.output(["git","status","--short"]),files=code,owner=owner,
        manifest_file_sha256=MANIFEST_SHA,manifest_semantic_sha256=semantic,image=IMAGE))
    safety.write_new(AUDIT/"PROTOCOL.json",dict(schema="damp.full-reference-launch/v1",
        purpose="FP32 TRAIN calibration reference only",prompts=36,input_tokens=1024,
        output_tokens=4096,batch_size=4,arms=["native-off","capture-on"],enforce_eager=True,
        prefix_cache=False,chunked_prefill=False,physical_npus=[4,5,6,7],tp=4,
        minimum_memory_gib=64,minimum_result_disk_gib=40,timeouts=TIMEOUTS,
        automatic_retry=False,source_lock_issued=False,
        not_proven=["compressed recurrence","graph","E2E throughput","task accuracy"]))
    create=["docker","create","--name",NAME,"--label",LABEL+"="+owner,
        "--network","host","--shm-size","8g","-e","ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
        "-e","PYTHONDONTWRITEBYTECODE=1","-e","VLLM_USE_V1=1",
        "-e","VLLM_WORKER_MULTIPROC_METHOD=spawn","-e","OMP_NUM_THREADS=1",
        "-e","TOKENIZERS_PARALLELISM=false","-e","DAMP_CAPTURE_ENABLE=0",
        "-e","VLLM_PLUGINS=ascend,ascend_kv_connector,ascend_model,ascend_model_loader,damp_capture"]
    for path,writable in (("/usr/local/Ascend/driver",False),(str(REPO),False),
                          (MODEL,False),(str(RESULT),True),(str(INPUT),False)):
        create+=["-v",path+":"+path+(":rw" if writable else ":ro")]
    for p in range(4,8):create+=["--device",f"/dev/davinci{p}:/dev/davinci{p-4}"]
    for p in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc"):create+=["--device",p]
    create += [IMAGE,"sleep","infinity"]
    safety.write_new(AUDIT/"create-command.json",dict(argv=create))
    container_id=None;failure=None;create_attempted=False
    try:
        create_attempted=True
        stage(safety,"create",create)
        returned_id=(AUDIT/"create.log").read_text().strip()
        require(re.fullmatch(r"[0-9a-f]{64}",returned_id) is not None,
                "unknown docker-create output; recover exact owner once, never retry")
        container_id=returned_id
        entry=json.loads(safety.output(["docker","inspect",container_id]))[0]
        safety.write_new(AUDIT/"container.json",container_proof(entry,container_id,owner))
        stage(safety,"start",["docker","start",container_id])
        stage(safety,"import_source",safety.python_in_container("-c",
            "import acl,torch,torch_npu,importlib.metadata as m; import vllm_ascend.ops; "
            "import vllm_ascend.ops.gdn as g; import vllm_ascend.worker.model_runner_v1 as r; "
            "import damp_capture.patch as p; from vllm_ascend.utils import enable_custom_op; assert enable_custom_op(); "
            "from damp_capture.contract import file_digest,GDN_SHA,RUNNER_SHA; "
            "assert file_digest(g.__file__)==GDN_SHA and file_digest(r.__file__)==RUNNER_SHA; "
            "assert len([e for e in m.entry_points(group='vllm.general_plugins') if e.name=='damp_capture'])==1; "
            "print(g.__file__,r.__file__,p.__file__,torch.__version__,torch_npu.__version__); "
            "print(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)"))
        stage(safety,"manifest_identity",safety.python_in_container("-c",
            "from damp_capture.contract import load_manifest,digest,file_digest; "
            "from damp_capture.identity import source_identity,ENGINE_SOURCE; "
            "import inspect; from pathlib import Path; from vllm.v1.engine.llm_engine import LLMEngine; "
            "assert Path(inspect.getsourcefile(LLMEngine.add_request)).resolve()==Path(ENGINE_SOURCE); "
            "assert LLMEngine.add_request.__qualname__=='LLMEngine.add_request'; "
            "p="+repr(str(MANIFEST))+"; m=load_manifest(p); "
            "assert file_digest(p)=="+repr(MANIFEST_SHA)+"; "
            "assert digest(m)=="+repr(MANIFEST_SEMANTIC_SHA)+"; "
            "print({'manifest_file':file_digest(p),'semantic':digest(m),'request_identity':source_identity()})"))
        fresh(safety,"canary")
        stage(safety,"canary",safety.python_in_container("-c",
            "import torch,torch_npu; assert torch.npu.device_count()==4; "
            "[(torch.npu.set_device(i),print('logical',i,'sum',torch.ones(16,device='npu').sum().cpu().item())) for i in range(4)]; "
            "torch.npu.synchronize()"))
        for arm in ("off","on"):
            top=safety.output(["docker","top",container_id,"-eo","pid,args"])
            require("python" not in top,"orphaned model process between paired arms")
            fresh(safety,arm)
            stage(safety,arm,safety.python_in_container("-m","damp_capture.run",
                "--manifest",str(MANIFEST),"--output-dir",str(ARMS[arm]),"--capture",arm,
                "--batch-size","4","--memory-utilization","0.80"))
        top=safety.output(["docker","top",container_id,"-eo","pid,args"])
        require("python" not in top,"orphaned model process before offline validation")
        stage(safety,"validate",safety.python_in_container("-m","damp_capture.validate",
            "--manifest",str(MANIFEST),"--output-dir",str(ARMS["on"]),
            "--dense-output-dir",str(ARMS["off"])))
    except Exception as error:
        failure=error
        safety.write_new(AUDIT/"FAILURE.json",dict(error_type=type(error).__name__,detail=str(error),
            automatic_retry=False,partial_reference_not_accepted=True))
    finally:
        try:
            # A timed-out create is an unknown outcome, never permission to create again.
            # A single read may recover only the fresh nonce-labelled exact owned ID.
            if container_id is None and create_attempted:
                probe=subprocess.run(["docker","inspect",NAME],capture_output=True,text=True,timeout=30)
                if probe.returncode==0:
                    candidate=json.loads(probe.stdout)[0]
                    container_proof(candidate,candidate["Id"],owner);container_id=candidate["Id"]
            if container_id is not None:stop_owned(safety,container_id,owner)
        except Exception as cleanup:
            safety.write_new(AUDIT/"STOP_FAILURE.json",dict(error_type=type(cleanup).__name__,
                detail=str(cleanup),parent_attention_required=True,no_delete=True))
            if failure is None:failure=cleanup
    if failure is not None:raise failure
    safety.write_new(AUDIT/"RESULT.json",dict(status="pass",scope="FP32-full-TRAIN-reference-only",
        requests=36,ranks=4,layers=48,output_tokens_per_request=4096,batch_size=4,
        source_lock_issued=False,owned_container_stopped_and_retained=True,
        not_proven=["compressed recurrence","graph","E2E throughput","task accuracy"]))
    print("PASS FULL FP32 REFERENCE ONLY; NO PERFORMANCE/ACCURACY CLAIM",flush=True)

def self_test():
    """Embedded software checks because this task owns exactly one new file."""
    import tempfile
    from types import SimpleNamespace
    import unittest
    class Checks(unittest.TestCase):
        def test_resources_boundaries(self):
            self.assertEqual(resources(dict(meminfo="MemAvailable: 67108864 kB\n"),SimpleNamespace(free=40*GiB))["minimum_memory_gib"],64)
            for memory,disk in (("MemAvailable: 67108863 kB\n",40*GiB),
                                ("unknown",40*GiB),("MemAvailable: 67108864 kB\n",40*GiB-1)):
                with self.assertRaises(RuntimeError):resources(dict(meminfo=memory),SimpleNamespace(free=disk))
        def test_nonoverwrite(self):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);absent([p/"new"])
                with self.assertRaises(RuntimeError):absent([p])
        def test_container_exact_mapping_mounts_and_nonce(self):
            cid="a"*64;nonce="n"*32
            entry=dict(Id=cid,Name="/"+NAME,Image=IMAGE,Config=dict(Labels={LABEL:nonce}),
                HostConfig=dict(Privileged=False,NetworkMode="host",Devices=[
                    dict(PathOnHost=f"/dev/davinci{p}",PathInContainer=f"/dev/davinci{p-4}") for p in range(4,8)]+[
                    dict(PathOnHost=p,PathInContainer=p) for p in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")]),
                Mounts=[dict(Source=p,Destination=p,RW=rw,Type="bind") for p,rw in (
                    (str(REPO),False),(MODEL,False),(str(RESULT),True),(str(INPUT),False),("/usr/local/Ascend/driver",False))])
            self.assertEqual(container_proof(entry,cid,nonce)["id"],cid)
            for case in range(6):
                fake=copy.deepcopy(entry)
                if case==0:fake["HostConfig"]["Privileged"]=True
                if case==1:fake["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci0"
                if case==2:fake["Mounts"][0]["RW"]=True
                if case==3:fake["Config"]["Labels"][LABEL]="foreign"
                if case==4:fake["Image"]="sha256:"+"0"*64
                if case==5:fake["Mounts"][3]["RW"]=True
                with self.subTest(case=case),self.assertRaises(RuntimeError):container_proof(fake,cid,nonce)
        def test_no_modified_smoke_helper(self):
            self.assertEqual(sha(HELPER),HELPER_SHA)
        def test_protocol_dimensions(self):
            m=dict(mode="full",rows=[dict(input_ids=[1]*1024) for _ in range(36)],tp_size=4,
                physical_npus=[4,5,6,7],anchors=[256,512,768,2304,2560,2816],horizon=256,
                layers=[i for i in range(64) if i%4!=3],generation=dict(temperature=0,seed=0,
                thinking=False,ignore_eos=True,min_tokens=4096,max_tokens=4096))
            shape(m);m["generation"]["max_tokens"]=1024
            with self.assertRaises(RuntimeError):shape(m)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    require(result.wasSuccessful(),"full launcher software checks failed")
    print("SOFTWARE ONLY; Docker/NPU not invoked")

if __name__=="__main__":main()
