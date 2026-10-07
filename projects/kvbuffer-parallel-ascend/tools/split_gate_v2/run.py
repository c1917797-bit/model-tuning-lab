#!/usr/bin/env python3
"""Independent NEW v2 gate. Default OFF; no old PASS or global ops reassignment."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
import time
from contract import (NAMESPACE,CGROUP_BYTES,legacy,require,sha,ref,source_admission,
                      artifacts,validate_identity,validate_cases)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--source-audit-only",action="store_true")
    p.add_argument("--batch",choices=(1,16),type=int)
    p.add_argument("--physical-device",choices=(5,6),type=int)
    p.add_argument("--source-manifest",type=Path);p.add_argument("--source-manifest-sha256")
    p.add_argument("--identity",type=Path);p.add_argument("--output-dir",type=Path)
    p.add_argument("--library",type=Path);p.add_argument("--library-sha256")
    p.add_argument("--build-receipt",type=Path);p.add_argument("--build-receipt-sha256")
    p.add_argument("--meta-receipt",type=Path);p.add_argument("--meta-receipt-sha256")
    a=p.parse_args(argv)
    if not a.execute and not a.source_audit_only:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                          "namespace":NAMESPACE,"new_build_meta_and_MAIN_identity_pending":True}))
        return
    require(a.source_manifest is not None and a.source_manifest_sha256,"actual source Ref required")
    source_ref=ref({"path":str(a.source_manifest),"sha256":a.source_manifest_sha256})
    manifest,sources=source_admission(source_ref)
    if a.source_audit_only:
        require(not a.execute,"source audit cannot dispatch")
        print(json.dumps({"source_audit_passed":True,"sources":sources,"namespace":NAMESPACE,
                          "npu_executed":False,"serving_ready":False}))
        return
    require(all((a.batch,a.physical_device,a.identity,a.output_dir,a.library,a.library_sha256,
                 a.build_receipt,a.build_receipt_sha256,a.meta_receipt,a.meta_receipt_sha256)),
            "MAIN explicit artifact/proof/input/output fields required")
    refs={k:ref({"path":str(path),"sha256":digest}) for k,path,digest in
          (("library",a.library,a.library_sha256),("build",a.build_receipt,a.build_receipt_sha256),
           ("meta",a.meta_receipt,a.meta_receipt_sha256))}
    checked=artifacts(refs,manifest)
    ident=json.loads(a.identity.read_bytes())
    pp=validate_identity(ident,a.batch,a.physical_device,source_ref,manifest,sources,refs)
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
            os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","logical0/no bytecode")
    native=legacy().NATIVE_PINS
    require({n:sha(n) for n in native}==native,"real same-image native source drift")
    cg=legacy().cgroup_limit()
    out=a.output_dir.resolve()
    require(Path("/kvbuffer-results") in out.parents and not out.exists(),"fresh independent output")
    out.mkdir(parents=True,exist_ok=False)
    report={"schema":"kvbp.split-native-gate/v2","status":"running","claim":"kernel-only",
            "created_ns":time.time_ns(),"script_sha256":sha(__file__),"sources_before":sources,
            "source_manifest":source_ref,"artifact_refs":refs,"launch_identity":ident,
            "launch_identity_sha256":sha(a.identity),"protocol":pp,"cgroup":cg,
            "frozen_receipts":checked,"native_sources":native,"candidate_namespace":NAMESPACE,
            "finite_scope":pp["finite_scope"],"cases":[]}
    oracle=None
    def save():
        val=oracle.finite_json(report) if oracle is not None else report
        (out/"report.json").write_text(json.dumps(val,indent=2,allow_nan=False)+"\n")
    save()
    primary=None
    try:
        import torch,torch_npu
        import oracle as oracle_module
        oracle=oracle_module;oracle.torch=torch;oracle.torch_npu=torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual logical0")
        require(enable_custom_op(),"native operators unavailable");init_device_properties_triton()
        torch.ops.load_library(str(a.library.resolve()))
        ops=getattr(torch.ops,NAMESPACE);oracle.bind_candidate(ops)
        report["native_schema"]=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
        report["candidate_schema"]=str(ops.decode.default._schema)
        require(report["candidate_schema"]==checked["meta_schema"],"actual loaded/Meta schema")
        loaded={}
        for line in Path("/proc/self/maps").read_text().splitlines():
            fields=line.split()
            if len(fields)>=6 and fields[-1].startswith("/") and ".so" in fields[-1]:
                path=fields[-1]
                if any(w in path.lower() for w in ("kvbuffer","vllm","cust_op","opapi","torch_npu")):
                    if Path(path).is_file():loaded[path]=sha(path)
        require(loaded.get(str(a.library.resolve()))==refs["library"]["sha256"],"actual candidate maps")
        native_path="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
        require(loaded.get(native_path)=="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a",
                "actual native mapped library")
        report["loaded_libraries"]=loaded
        report["runtime"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
                           "logical_device":torch.npu.current_device(),
                           "logical_device_count":torch.npu.device_count(),
                           "device_name":torch.npu.get_device_name(0)}
        save()
        for mode,trials in (("eager",1),("graph",3)):
            for trial in range(trials):oracle.run_case(a.batch,mode,trial,report,save,out)
        report["status"]="single_batch_kernel_native_eager_graph_pass"
        report["report_completeness"]=validate_cases(report,a.batch)
        report["not_validated"]=["other-batches","48-layer-lifecycle","matched-E2E","task-accuracy",
                                 "MAIN raw operation/child/PID/stop authority separate"]
    except BaseException as error:
        primary=error;report.update(status="failed",error=repr(error));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,after=source_admission(source_ref)
            report["sources_after"]=after
            require(after==sources,"source drift during real numerical run")
            save()
        except BaseException as secondary:
            if primary is None:
                report.update(status="failed",error=repr(secondary))
                try:save()
                except BaseException as save_error:
                    print(json.dumps({"original_error":repr(secondary),
                                      "save_error":repr(save_error),"report_path":str(out/"report.json")}))
                raise
            report["secondary_finalize_error"]=repr(secondary)
            try:save()
            except BaseException as save_error:
                print(json.dumps({"original_error":repr(primary),"secondary_error":repr(secondary),
                                  "save_error":repr(save_error),"report_path":str(out/"report.json")}))
if __name__=="__main__":main()
