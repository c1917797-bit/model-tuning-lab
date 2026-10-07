"""NEW source-bound three-repair driver. Default is plan-only, no artifacts."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
from v2_contract import HERE,OLD,ROOT,file_sha,frozen_run,inventory,require,source_contract,v1
import v2_release as release
from v2_peak import Peak

OLD_RUN=frozen_run()
# A private import namespace, never the shared v1 module. This single source-bound
# policy injection classifies only actual current070e IDs; all other safety code
# remains the byte-frozen v1 Controller.
OLD_RUN.current_allT=release.current_allT
D=v1()

def install(root):
    source_contract();root=Path(root);root.mkdir(parents=True,exist_ok=False)
    (root/"damp_capture").symlink_to(D.COLLECTOR/"damp_capture",target_is_directory=True)
    (root/"damp_admission_diagnostic").symlink_to(OLD/"damp_admission_diagnostic",target_is_directory=True)
    for name in ("damp_fixed_v2.py","v2_contract.py","v2_bindings.py","v2_observer.py"):
        (root/name).symlink_to(HERE/name)
    meta=root/"damp_fixed_admission_v2-0.2.0.dist-info";meta.mkdir()
    with (meta/"METADATA").open("x") as out:
        out.write("Metadata-Version: 2.1\nName: damp-fixed-admission-v2\nVersion: 0.2.0\n")
    with (meta/"entry_points.txt").open("x") as out:
        out.write("[vllm.general_plugins]\ndamp_capture = damp_fixed_v2:register\n")
    return inventory([e for d in importlib.metadata.distributions(path=[str(root)]) for e in d.entry_points])

def target_preflight(report):
    packet=source_contract()
    env=D.runtime_environment(Path(report).parent)  # same exact reviewed CANN shell/PYTHONPATH.
    require(sys.version_info[:2]==(3,12) and callable(getattr(threading,"getprofile",None)),
            "actual target3.12 public profile API required")
    require(sys.getprofile() is None and threading.getprofile() is None,"foreign profile hook")
    require(not Path("/dev/davinci0").exists() and not Path("/dev/davinci4").exists(),"unexpected device exposure")
    require(os.environ.get("DAMP_ADMISSION_TRACE_ENABLE")!="1","preflight must defaultOFF")
    actual=inventory(importlib.metadata.entry_points())
    import damp_fixed_v2
    require(Path(damp_fixed_v2.__file__).resolve()==HERE/"damp_fixed_v2.py","wrong NEW entry module")
    before=set(sys.modules);require(damp_fixed_v2.register() is None,"defaultOFF changed behavior")
    require(not any(x=="torch" or x.startswith("torch.") for x in sys.modules),"defaultOFF imported Torch")
    from damp_capture import run as collector_run
    require(Path(collector_run.__file__).resolve()==D.COLLECTOR/"damp_capture/run.py","frozen collector runner mismatch")
    for path,digest in D.RUNTIME.items(): require(file_sha(path)==digest,"actual image source drift")
    D.write_new(report,{"schema":"damp-fixed-admission-preflight/v2","status":"source_import_pass",
        "packet":packet,"entrypoint":actual,"actual_environment":env,
        "prior_v1_target48_test_scope":"unchanged source-only helper tests, not nativeOFF first forward",
        "npu_executed":False,"actual_native_model_forward_verified":False,"source_lock_issued":False})

class Controller(OLD_RUN.Controller):
    def __init__(self,root):
        super().__init__(root)
        self.peak=None;self.peak_count=0;self.peak_completed=False

    def peak_record(self,stage,*,completed=False):
        require(self.peak is not None,"own kernel peak observer not attached before model")
        value=self.checked(self.owned_name,self.owned_devices)
        row=self.peak.sample(value,model_completed=completed)
        self.peak_count+=1
        D.write_new(self.root/("cgroup-peak-%04d.json"%self.peak_count),dict(row,stage=stage))
        require(row["failcnt"]==0 and row["kernel_peak_bytes"]<row["limit_bytes"],
                "own cgroup reached/failed hard cap; retained kernel peak")

    def stage(self,label,argv,timeout=None,monitor=False):
        result=super().stage(label,argv,timeout,monitor)
        if len(argv)>=2 and argv[:2]==[self.docker,"start"]:
            value=self.checked(self.owned_name,self.owned_devices)
            self.peak=Peak(value);self.peak_completed=False
            self.peak_record("started-before-model")
        elif len(argv)>=2 and argv[:2]==[self.docker,"exec"]:
            self.peak_completed=bool(self.owned_devices)
            self.peak_record("exec-completed-before-stop",completed=bool(self.owned_devices))
        return result

    def monitor(self):
        super().monitor()  # exact original external/own caps; no policy relaxation.
        self.peak_record("periodic")

    def stop_owned(self,name,devices):
        error=None
        try:
            if self.peak is not None:
                self.peak_record("last-pre-stop",completed=self.peak_completed)
        except BaseException as exc:
            error=exc
            try:
                D.write_new(self.root/(name+"-peak-incomplete.json"),
                    {"type":type(exc).__name__,"detail":str(exc),"peak_coverage_incomplete":True})
            except BaseException: pass
        stop_error=None
        try:
            # Always exact owned stop-retain, even when telemetry failed.
            return super().stop_owned(name,devices)
        except BaseException as exc:
            stop_error=exc
            raise
        finally:
            self.peak=None
            # Keep native failure via v1 container.finally, and never replace a
            # cleanup failure with a telemetry failure.
            if error is not None and stop_error is None: raise error

    def admit_prior_release(self,path,digest,paths,shas,*,host_cleanup=False):
        if host_cleanup:
            authority=release.host_job()
        else:
            require(D.file_sha(path)==digest,"actual original MAIN terminal bytes differ")
            authority=release.terminal(json.loads(Path(path).read_text()))
        refs,proofs=release.references(paths,shas)
        actual=release.stopped(proofs,self.inspect)
        clients=release.no_exec_clients()
        self.prior={"terminal":None if host_cleanup else {"path":path,"sha256":digest},
                    "device_proofs":refs,"release":authority,
                    "actual_stopped_inspects":actual,"fresh_host_clients":clients}
        D.write_new(self.root/"prior-release.json",self.prior)

    def fresh_idle(self,arm):
        require(self.prior is not None,"current070e release admission required")
        refs=self.prior["device_proofs"]
        _,proofs=release.references([x["path"] for x in refs],[x["sha256"] for x in refs])
        release.stopped(proofs,self.inspect);release.no_exec_clients()
        fresh=self.helper.idle_snapshot()
        available=int(re.search(r"^MemAvailable:\s*(\d+)",fresh["meminfo"],re.M)[1])*1024
        D.budget(available,shutil.disk_usage(D.RESULT_ROOT).free)
        D.write_new(self.root/(arm+"-fresh-idle.json"),fresh)

def plan(root,source):
    return dict(OLD_RUN.plan(root),schema="damp-fixed-admission-plan/v2",source=source,
        release_operation_context=release.OP,
        original_aw_terminal_or_explicit_host_job_cleanup_required=True,
        own_kernel_peak_required=True,default_enabled=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",default=str(D.RESULT_ROOT/"fixed-admission-c1-v2"))
    mode=p.add_mutually_exclusive_group()
    mode.add_argument("--execute",action="store_true")
    mode.add_argument("--preflight-only",action="store_true")
    mode.add_argument("--target-preflight-report")
    prior=p.add_mutually_exclusive_group()
    prior.add_argument("--prior-operation-receipt")
    prior.add_argument("--prior-host-job-cleanup",action="store_true")
    p.add_argument("--prior-operation-sha256")
    p.add_argument("--prior-device-proofs",nargs=4)
    p.add_argument("--prior-device-proof-sha256",nargs=4)
    a=p.parse_args()
    if a.target_preflight_report:
        return target_preflight(a.target_preflight_report)
    root=Path(a.output).resolve();source=source_contract()
    require(Path.cwd().resolve()==ROOT,"canonical cwd required")
    require(root.is_relative_to(D.RESULT_ROOT) and root!=D.RESULT_ROOT and
            re.fullmatch("[a-z0-9][a-z0-9_-]{0,60}",root.name),"invalid new output")
    if not (a.execute or a.preflight_only):
        print(json.dumps(plan(root,source),sort_keys=True));return
    if a.execute:
        require(a.prior_device_proofs and a.prior_device_proof_sha256 and
                (a.prior_host_job_cleanup or (a.prior_operation_receipt and a.prior_operation_sha256)),
                "actual current070e release+four immutable identities required")
    root=D.validated_path(root);root.mkdir(parents=True,exist_ok=False)
    D.write_new(root/"PLAN.json",plan(root,source));c=None
    try:
        install(root/"overlay");D.write_new(root/"manifest.json",D.make_manifest())
        c=Controller(root)
        image=json.loads(c.output([c.docker,"image","inspect",D.IMAGE]))[0]
        require(image["Id"]==D.IMAGE and image["Architecture"]=="arm64","actual immutable image differs")
        if a.execute:
            c.admit_prior_release(a.prior_operation_receipt,a.prior_operation_sha256,
                a.prior_device_proofs,a.prior_device_proof_sha256,host_cleanup=a.prior_host_job_cleanup)
            fresh=c.resource_snapshot()
            budget=D.resource_budget(fresh["engine"]["NCPU"],fresh["mem_available"],
                fresh["free_disk"],preflight=False,allt_running=len(fresh["known_allT"]))
            D.write_new(root/"formal-before-preflight-resource.json",dict(fresh,budget=budget))
        c.initial_resources(preflight=True)
        c.container("qwen36_damp_fixed_c1_"+root.name+"-preflight",{},
            [D.PYTHON,"-B",str(HERE/"run.py"),"--target-preflight-report",str(root/"preflight.json")],"preflight")
        if a.preflight_only:
            D.write_new(root/"RESULT.json",{"schema":"damp-fixed-admission-result/v2",
                "status":"no_device_preflight_pass","npu_executed":False,
                "actual_native_model_forward_verified":False,"source_lock_issued":False});return
        c.initial_resources(preflight=False)
        devices={**{"/dev/davinci"+str(i):"/dev/davinci"+str(i-4) for i in range(4,8)},
                 **{x:x for x in OLD_RUN.COMMON}}
        for arm in D.ARMS:
            c.fresh_idle(arm)
            command=[D.PYTHON,"-B","-c","from damp_admission_diagnostic.arm import main;main()",
                "--manifest",str(root/"manifest.json"),"--output-dir",str(root/arm),"--arm",arm]
            c.container("qwen36_damp_fixed_c1_"+root.name+"-"+arm,devices,command,arm)
            require(sum(x.stat().st_size for x in root.rglob("*.bin"))<=D.RAW_LIMIT,"total raw exceeds20GiB")
            if arm=="off-b":
                c.remaining();result=OLD_RUN.compare(root/"off-a",root/"off-b");c.remaining()
                D.write_new(root/"OFF_OFF.json",result)
                require(result["status"]=="bitwise_pass","OFF/OFF drift; ON prohibited")
        c.remaining();result=OLD_RUN.compare(root/"off-a",root/"on");c.remaining()
        D.write_new(root/"OFF_ON.json",result)
        require(result["status"]=="bitwise_pass","OFF/ON divergence; no SOURCE_LOCK")
        D.write_new(root/"RESULT.json",{"schema":"damp-fixed-admission-result/v2",
            "status":"short_diagnostic_bitwise_pass","source":source,
            "source_lock_issued":False,"full_calibration_admitted":False,
            "performance_measurement":False,"task_accuracy_measurement":False,
            "not_proven":["full36 capture parity","192 plans","FA/logit full chain",
                          "compressed recurrence","graph/lifecycle","E2E","task accuracy"]})
    except BaseException as exc:
        try:
            D.write_new(root/"FAILURE.json",{"type":type(exc).__name__,"detail":str(exc),
                "evidence_retained":True,"source_lock_issued":False})
        except BaseException: pass
        raise

if __name__=="__main__": main()
