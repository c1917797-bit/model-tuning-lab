"""MAIN-owned one-shot OFF-A/OFF-B/ON diagnostic. Default only prints a plan."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid
from diag_contract import (ARMS,COLLECTOR,HOST_RESERVE,IMAGE,MODEL,ORDINARY_FLOOR,
    PACKAGE_ROOT,PYTHON,RAW_LIMIT,RESULT_ROOT,ROOT,SECONDS,TRAIN,TRAIN_SHA,budget,
    file_sha,make_manifest,require,source_contract,validated_path,write_new,
    ALLT_OWNER,PRIOR_IDS,BOOTSTRAP_SHA,FORMAL_CPUS,PREFLIGHT_CPUS,PREFLIGHT_MEMORY,GIB,
    bootstrap_command,external_workload,inspect_contract,prior_terminal,
    prior_owned_contract,prior_proof_refs,resource_budget,stats_usage)
from aggregate import compare
from install import install

HELPER=ROOT/"projects/damp-ascend/tools/run_collector_smoke.py"
COMMON=("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")
def current_allT(value):
    """Only the four exact currently supervised IDs, not a historical owner label."""
    ident=value["Id"]
    if ident not in PRIOR_IDS.values():
        return False
    card=next(card for card,known in PRIOR_IDS.items() if known==ident)
    require(value["Image"]==IMAGE and
            value["Name"]=="/qwen36_damp_allt_npu"+str(card)+"_20261006_independent_v1" and
            (value["Config"].get("Labels") or {}).get("model-tuning-lab.owner")==ALLT_OWNER,
            "current allT immutable name/image/owner identity changed")
    return True
def plan(root):
    return {"schema":"damp-fixed-admission-plan/v1","default_enabled":False,
        "output":str(root),"arms":list(ARMS),"batch":1,"input_tokens":1024,"output_tokens":33,
        "physical_cards":[4,5,6,7],"logical_cards":[0,1,2,3],"seconds_including_cold_starts":SECONDS,
        "raw_limit_bytes":RAW_LIMIT,"ordinary_memory_floor":ORDINARY_FLOOR,"host_reserve":HOST_RESERVE,
        "input":{"path":str(TRAIN),"sha256":TRAIN_SHA,"row":"math-fit-02"},
        "enforce_eager":True,"prefix_cache":False,"chunked_prefill":False,
        "source_lock_issued":False,"full_calibration_admitted":False,
        "performance_measurement":False,"task_accuracy_measurement":False,
        "formal_cpus":FORMAL_CPUS,"preflight_cpus":PREFLIGHT_CPUS,
        "preflight_memory":PREFLIGHT_MEMORY,"formal_requires_actual_prior_terminal":True}

class Controller:
    def __init__(self,root):
        self.root=root;self.deadline=time.monotonic()+SECONDS
        self.nonce=uuid.uuid4().hex
        self.phase=0;self.owned=None;self.owned_name=None;self.owned_devices=None
        self.monitors=0;self.external_baseline=None
        self.preflight=False;self.prior=None;self.protected_baseline=None
        spec=importlib.util.spec_from_file_location("_fixed_admission_frozen_idle",HELPER)
        self.helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.helper)
        self.docker=shutil.which("docker");self.smi=shutil.which("npu-smi")
        require(self.docker=="/usr/bin/docker" and self.smi=="/usr/local/sbin/npu-smi","host tools changed")
        # Reuse exact frozen parser, but bound its command timeout to this run.
        self.helper.output=lambda argv,timeout=30:self.output(
            [self.docker if argv[0]=="docker" else self.smi if argv[0]=="npu-smi" else argv[0]]+argv[1:],
            timeout=min(timeout,self.remaining()))

    def remaining(self):
        remaining=self.deadline-time.monotonic()-90  # Reserve owned cleanup within45min.
        require(remaining>0,"45min total deadline reached; no automatic retry")
        return remaining

    def output(self,argv,timeout=30):
        return subprocess.run(argv,text=True,capture_output=True,check=True,
                              timeout=min(timeout,self.remaining())).stdout

    def stage(self,label,argv,timeout=None,monitor=False):
        self.phase+=1
        stem="%02d-%s"%(self.phase,label)
        log=self.root/(stem+".log")
        receipt=self.root/(stem+".receipt.json")
        start=time.monotonic();error=None;code=None;child=None
        try:
            with log.open("x",encoding="utf-8") as out:
                child=subprocess.Popen(argv,stdout=out,stderr=subprocess.STDOUT,text=True)
                limit=start+min(timeout or self.remaining(),self.remaining())
                check_at=0.0
                while child.poll() is None:
                    require(time.monotonic()<limit,label+" stage timeout; do not retry")
                    if monitor and time.monotonic()>=check_at:
                        self.monitor()
                        check_at=time.monotonic()+10
                    time.sleep(0.25)
                code=child.returncode
        except BaseException as exc:
            error={"type":type(exc).__name__,"detail":str(exc)}
            # Only the host docker-exec/create client. Container cleanup is exact
            # owned stop-retain in container.finally; never touch other workloads.
            if child is not None and child.poll() is None:
                try:
                    child.terminate();child.wait(timeout=5)
                except BaseException:
                    try:child.kill();child.wait(timeout=5)
                    except BaseException:pass
            raise
        finally:
            try:
                write_new(receipt,{"argv":argv,"cwd":str(ROOT),"exit_code":code,
                    "elapsed":time.monotonic()-start,"error":error,
                    "log":{"path":str(log),"sha256":file_sha(log) if log.exists() else None}})
            except BaseException:
                if error is None:raise
        require(code==0,label+" failed; retained original log, do not retry")

    def inspect(self,name):
        r=subprocess.run([self.docker,"inspect",name],text=True,capture_output=True,timeout=30)
        if r.returncode:
            return None
        values=json.loads(r.stdout);require(len(values)==1,"ambiguous container identity")
        return values[0]

    def checked(self,name,expected_devices):
        return inspect_contract(self.inspect(name),name,self.nonce,self.root,
                                expected_devices,preflight=not bool(expected_devices))

    def resource_snapshot(self):
        engine=json.loads(self.output([self.docker,"info","--format","{{json .}}"]))
        ids=self.output([self.docker,"ps","--no-trunc","--format","{{.ID}}"]).splitlines()
        values=[];external=[];numeric=[]
        for ident in ids:
            value=self.inspect(ident)
            require(value is not None and value["State"]["Running"],"running container inventory changed")
            if ident==self.owned:
                continue
            stats=json.loads(self.output([self.docker,"stats","--no-stream","--format","{{json .}}",ident]))
            top=self.output([self.docker,"top",ident,"-eo","pid,comm"])
            if current_allT(value):
                h=value["HostConfig"]
                require(value["Image"]==IMAGE and h["NanoCpus"]==10**9 and
                        h["Memory"]==h["MemorySwap"]==8*GIB,
                        "known allT actual quota/image differs")
                numeric.append({"id":ident,"name":value["Name"],"image":value["Image"],
                                "owner":ALLT_OWNER,"stats":stats,"top_process_names":top})
            else:
                external.append(external_workload(value,stats,top,
                    protected_baseline=self.protected_baseline))
            values.append({"id":ident,"name":value["Name"],"image":value["Image"],
                           "stats":stats,"top_process_names":top})
        meminfo=Path("/proc/meminfo").read_text()
        available=int(re.search(r"^MemAvailable:\s*(\d+)",meminfo,re.M)[1])*1024
        return {"engine":engine,"meminfo":meminfo,"mem_available":available,
                "free_disk":shutil.disk_usage(RESULT_ROOT).free,
                "known_allT":numeric,"external":external,"actual_other_running":values}

    def initial_resources(self,preflight):
        self.preflight=preflight
        fresh=self.resource_snapshot()
        receipt=resource_budget(fresh["engine"]["NCPU"],fresh["mem_available"],
             fresh["free_disk"],preflight=preflight,allt_running=len(fresh["known_allT"]))
        protected=[x for x in fresh["external"] if x["known_protected0_3"]]
        require(len(protected)<=1,"ambiguous protected baseline")
        if self.protected_baseline is None and protected:
            self.protected_baseline=protected[0]
        self.external_baseline=tuple(sorted((x["id"],x["image"]) for x in fresh["external"]))
        write_new(self.root/("preflight-resource.json" if preflight else "formal-resource.json"),
                  dict(fresh,budget=receipt,protected_resident_initial=self.protected_baseline))

    def monitor(self):
        self.monitors+=1
        fresh=self.resource_snapshot()
        require(fresh["mem_available"]>=HOST_RESERVE,"ordinary RAM below8GiB reserve; stop only own")
        identity=tuple(sorted((x["id"],x["image"]) for x in fresh["external"]))
        require(identity==self.external_baseline,"external identity changed; stop only own, reschedule")
        require(self.preflight or not fresh["known_allT"],"allT restarted during formal diagnostic")
        value=self.checked(self.owned_name,self.owned_devices)
        require(value is not None and value["State"]["Running"] and not value["State"]["OOMKilled"],
                "owned cgroup unexpectedly stopped/OOM")
        own=json.loads(self.output([self.docker,"stats","--no-stream","--format","{{json .}}",self.owned]))
        _,usage=stats_usage(own)
        require(usage<value["HostConfig"]["Memory"],"owned cgroup memory reached hard cap")
        write_new(self.root/("monitor-%04d.json"%self.monitors),dict(fresh,own_stats=own,
            own_id=self.owned,protected_resident_initial=self.protected_baseline,
            scope="observed current workload; no global cap guarantee"))

    def admit_prior_release(self,receipt_path,receipt_sha,proof_paths,proof_shas):
        require(file_sha(receipt_path)==receipt_sha,"MAIN prior terminal bytes differ")
        release=prior_terminal(json.loads(Path(receipt_path).read_text()))
        refs,proofs=prior_proof_refs(proof_paths,proof_shas)
        actual=prior_owned_contract(proofs,self.inspect)
        self.prior={"terminal":{"path":receipt_path,"sha256":receipt_sha},
                    "device_proofs":refs,"release":release,"actual_stopped_inspects":actual}
        write_new(self.root/"prior-release.json",self.prior)

    def stop_owned(self,name,expected_devices):
        # Exact nonce/id/image only; no unrelated stop/delete. A single inspect may
        # recover a successful create whose stdout was lost; never repeat create.
        value=self.checked(name,expected_devices)
        owned_id=value["Id"]
        r=subprocess.run([self.docker,"stop","--time","30",owned_id],
                         text=True,capture_output=True,timeout=45)
        after=self.checked(name,expected_devices)
        write_new(self.root/(name+"-stop.json"),{"id":owned_id,"exit_code":r.returncode,
            "stdout":r.stdout,"stderr":r.stderr,"retained":True,"running_after":after["State"]["Running"]})
        require(r.returncode==0 and not after["State"]["Running"],"owned stop failed; retain diagnostic")
        self.owned=None;self.owned_name=None;self.owned_devices=None

    def container(self,name,devices,command,label):
        collision=self.inspect(name);require(collision is None,"container name exists; no reuse")
        argv=[self.docker,"create","--name",name,"--label","damp.fixed-admission.owner="+self.nonce,
            "--network","host" if devices else "none","--ipc","private",
            "--memory","64g" if devices else "2g","--memory-swap","64g" if devices else "2g",
            "--cpus","6" if devices else "1","--shm-size","8g" if devices else "1g",
            "--pids-limit","2048","--cap-drop","ALL",
            "--security-opt","no-new-privileges","-e","PYTHONDONTWRITEBYTECODE=1",
            "-e","VLLM_USE_V1=1","-e","VLLM_WORKER_MULTIPROC_METHOD=spawn",
            "-e","OMP_NUM_THREADS=1","-e","TOKENIZERS_PARALLELISM=false",
            "--mount","type=bind,src="+str(ROOT)+",dst="+str(ROOT)+",readonly",
            "--mount","type=bind,src="+MODEL+",dst="+MODEL+",readonly",
            "--mount","type=bind,src="+str(self.root)+",dst="+str(self.root),
            "--mount","type=bind,src="+str(TRAIN.parent)+",dst="+str(TRAIN.parent)+",readonly",
            "--mount","type=bind,src=/usr/local/Ascend/driver,dst=/usr/local/Ascend/driver,readonly"]
        if devices:
            argv+=["-e","ASCEND_RT_VISIBLE_DEVICES=0,1,2,3"]
        for host,logical in devices.items():
            argv+=["--device",host+":"+logical]
        argv+=[IMAGE,"sleep","infinity"]
        primary=None;created=False
        try:
            self.stage(label+"-create",argv,30)
            created=True
            info=self.checked(name,devices)
            write_new(self.root/(name+"-inspect.json"),info)
            self.owned=info["Id"];self.owned_name=name;self.owned_devices=dict(devices)
            self.stage(label+"-start",[self.docker,"start",self.owned],30)
            self.stage(label,[self.docker,"exec",self.owned]+bootstrap_command(self.root,command),monitor=True)
        except BaseException as exc:
            primary=exc
            raise
        finally:
            # Only explicit successful create, or one exact nonce recovery after
            # an ambiguous create timeout. Errors cannot replace original failure.
            try:
                candidate=self.inspect(name)
                if candidate is not None and candidate["Config"]["Labels"].get("damp.fixed-admission.owner")==self.nonce:
                    self.stop_owned(name,devices)
                elif created:
                    raise RuntimeError("created owned container vanished")
            except BaseException as exc:
                try:
                    write_new(self.root/(name+"-stop-failure.json"),
                              {"type":type(exc).__name__,"detail":str(exc),"primary":repr(primary)})
                except BaseException:
                    pass
                if primary is None:
                    raise

    def fresh_idle(self,arm):
        fresh=self.helper.idle_snapshot()
        available=int(re.search(r"^MemAvailable:\s*(\d+)",fresh["meminfo"],re.M)[1])*1024
        budget(available,shutil.disk_usage(RESULT_ROOT).free)
        if self.prior is not None:
            refs=self.prior["device_proofs"]
            _,proofs=prior_proof_refs([x["path"] for x in refs],[x["sha256"] for x in refs])
            prior_owned_contract(proofs,self.inspect)
        write_new(self.root/(arm+"-fresh-idle.json"),fresh)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",default=str(RESULT_ROOT/"fixed-admission-c1-v1"))
    mode=p.add_mutually_exclusive_group()
    mode.add_argument("--execute",action="store_true")
    mode.add_argument("--preflight-only",action="store_true")
    p.add_argument("--prior-operation-receipt");p.add_argument("--prior-operation-sha256")
    p.add_argument("--prior-device-proofs",nargs=4)
    p.add_argument("--prior-device-proof-sha256",nargs=4)
    a=p.parse_args()
    root=Path(a.output).resolve()
    source=source_contract()
    require(Path.cwd().resolve()==ROOT,"canonical cwd required")
    require(root.is_relative_to(RESULT_ROOT) and root!=RESULT_ROOT and
            re.fullmatch("[a-z0-9][a-z0-9_-]{0,60}",root.name),"invalid output root/name")
    if not (a.execute or a.preflight_only):
        print(json.dumps(dict(plan(root),source=source),sort_keys=True));return
    if a.execute:
        require(all((a.prior_operation_receipt,a.prior_operation_sha256,a.prior_device_proofs,
                     a.prior_device_proof_sha256)),"formal execute requires actual MAIN terminal+four immutable owned identities")
    root=validated_path(root)
    root.mkdir(parents=True,exist_ok=False)
    write_new(root/"PLAN.json",dict(plan(root),source=source))
    c=None;error=None
    try:
        install(root/"overlay")
        write_new(root/"manifest.json",make_manifest())
        c=Controller(root)
        image=json.loads(c.output([c.docker,"image","inspect",IMAGE]))[0]
        require(image["Id"]==IMAGE and image["Architecture"]=="arm64","immutable image mismatch")
        if a.execute:
            c.admit_prior_release(a.prior_operation_receipt,a.prior_operation_sha256,
                                  a.prior_device_proofs,a.prior_device_proof_sha256)
            fresh=c.resource_snapshot()
            initial=resource_budget(fresh["engine"]["NCPU"],fresh["mem_available"],
                 fresh["free_disk"],preflight=False,allt_running=len(fresh["known_allT"]))
            write_new(root/"formal-before-preflight-resource.json",dict(fresh,budget=initial))
        c.initial_resources(preflight=True)
        # Dedicated no-device preflight; same overlay, module resolution, transitive
        # mounted files. This must pass before canary or model execution.
        name="qwen36_damp_fixed_c1_"+root.name+"-preflight"
        c.container(name,{},[PYTHON,"-B",str(PACKAGE_ROOT/"preflight.py"),
                    "--report",str(root/"preflight.json")],"preflight")
        if a.preflight_only:
            write_new(root/"RESULT.json",{"schema":"damp-fixed-admission-preflight-controller/v1",
                "status":"no_device_preflight_pass","source":source,"npu_executed":False,
                "actual_native_frame_verified":False,"source_lock_issued":False})
            return
        c.initial_resources(preflight=False)
        devices={**{"/dev/davinci"+str(i):"/dev/davinci"+str(i-4) for i in range(4,8)},
                 **{x:x for x in COMMON}}
        for arm in ARMS:
            c.fresh_idle(arm)
            name="qwen36_damp_fixed_c1_"+root.name+"-"+arm
            # One process only pre-admits one request. No ongoing HTTP arrival
            # simulation, pause/resume, or scheduler patches.
            script="from damp_admission_diagnostic.arm import main;main()"
            command=[PYTHON,"-B","-c",script,"--manifest",str(root/"manifest.json"),
                     "--output-dir",str(root/arm),"--arm",arm]
            c.container(name,devices,command,arm)
            require(sum(p.stat().st_size for p in root.rglob("*.bin"))<=RAW_LIMIT,"total raw exceeds20GiB")
            if arm=="off-b":
                c.remaining()
                result=compare(root/"off-a",root/"off-b")
                c.remaining()
                write_new(root/"OFF_OFF.json",result)
                require(result["status"]=="bitwise_pass","OFF/OFF drift: ON prohibited; evidence retained")
        c.remaining()
        result=compare(root/"off-a",root/"on")
        c.remaining()
        write_new(root/"OFF_ON.json",result)
        require(result["status"]=="bitwise_pass","OFF/ON divergence retained; no full SOURCE_LOCK")
        write_new(root/"RESULT.json",{"schema":"damp-fixed-admission-result/v1",
            "status":"short_diagnostic_bitwise_pass","source":source,
            "not_proven":["full36x4096 capture noninterference","192 calibrated plans","FA/logit full chain",
                          "DAMP compressed recurrence","graph/lifecycle","E2E throughput","task accuracy"],
            "source_lock_issued":False,"full_calibration_admitted":False})
    except BaseException as exc:
        error=exc
        try:
            write_new(root/"FAILURE.json",{"schema":"damp-fixed-admission-failure/v1",
                "type":type(exc).__name__,"detail":str(exc),"evidence_retained":True,
                "source_lock_issued":False})
        except BaseException:
            pass
        raise
if __name__=="__main__":
    main()
