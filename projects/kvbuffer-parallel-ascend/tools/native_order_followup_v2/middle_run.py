#!/usr/bin/env python3
"""NEW explicit true-T middle entry; frozen v2 oracle/math, no PAD/no automatic retry."""
from __future__ import annotations
import argparse,json,os,time
from datetime import datetime,timezone
from pathlib import Path
import binding as b
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true");p.add_argument("--audit-only",action="store_true")
    p.add_argument("--batches",nargs="+",type=int);p.add_argument("--physical-device",type=int,choices=tuple(b.GROUPS))
    for n in ("followup-manifest","library","build-receipt","meta-receipt","middle-meta"):
        p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
    p.add_argument("--identity");p.add_argument("--output-dir");a=p.parse_args(argv)
    if not a.execute and not a.audit_only:
        print(json.dumps(dict(status="OFF",groups=b.GROUPS,namespace=b.NS,npu_executed=False,serving_ready=False)));return 0
    b.require(not (a.execute and a.audit_only),"one explicit mode")
    b.require(a.batches and a.physical_device and a.followup_manifest and a.followup_manifest_sha256,
              "exact real-T group/source Ref")
    pp=b.protocol(a.batches,a.physical_device)
    fr=dict(path=a.followup_manifest,sha256=a.followup_manifest_sha256)
    packet,gm,pins,own,finite,bridge,legacy=b.sources(fr);before={**pins,**own}
    oracle=b.load_oracle(gm)
    b.require(oracle.OUT_LIMIT==.00303 and oracle.STATE_LIMIT==2e-6
              and tuple(oracle.PADDING_ACTIVE)==(0,1,3,7,12,15,16,16),"original numerical gates")
    if a.audit_only:
        print(json.dumps(dict(status="source_audit_pass",protocol=pp,sources=before,
                              npu_executed=False,serving_ready=False,loaded_runtime_verified=False)));return 0
    names=("library","build_receipt","meta_receipt","middle_meta")
    b.require(all(getattr(a,n) and getattr(a,n+"_sha256") for n in names)
              and a.identity and a.output_dir,"MAIN actual artifacts/identity/fresh output")
    r={n:dict(path=getattr(a,n),sha256=getattr(a,n+"_sha256")) for n in names}
    ar=dict(library=r["library"],build=r["build_receipt"],meta=r["meta_receipt"])
    checked,meta=b.artifacts(ar,gm,pins)
    mm=b.validate_meta14(r["middle_meta"],ar,packet["v2_gate_manifest"],pins,own)
    b.require(mm["followup_manifest"]==fr and mm["schema"]==meta["schema"] and mm["prepare_schema"]==meta["prepare_schema"],
              "actual v2 fourteen-T Meta schema")
    ident=json.loads(Path(a.identity).read_bytes())
    b.require(ident.get("schema")=="kvbp.native-order-middle-launch/v2"
              and ident.get("image_id")==b.IMAGE and ident.get("protocol")==pp
              and ident.get("physical_devices")==[a.physical_device]
              and ident.get("logical_to_physical")=={"0":a.physical_device}
              and all(ident.get(k) is True for k in ("fresh_idle_verified","nonprivileged","source_canary_passed"))
              and ident.get("memory_cgroup_bytes")==8*b.GIB,"fresh actual MAIN single-card identity")
    b.require(ident.get("sources")==before and ident.get("source_manifest")==packet["v2_gate_manifest"]
              and ident.get("followup_manifest")==fr and ident.get("artifact_refs")==ar
              and ident.get("middle_meta")==r["middle_meta"],"complete actual source/Meta/artifact identity")
    b.require(type(ident.get("evidence")) is dict and ident["evidence"],"MAIN raw proof refs")
    for value in ident["evidence"].values():b.raw(value)
    start=datetime.fromisoformat(ident["preflight_utc"].replace("Z","+00:00"))
    b.require(start.tzinfo is not None and 0<=(datetime.now(timezone.utc)-start).total_seconds()<=600,"fresh <=600s")
    b.require(os.environ.get("KVBUFFER_NATIVE_ORDER_MIDDLE_EXECUTE")=="1"
              and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0"
              and os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","explicit MAIN opt-in/logical0/no bytecode")
    native={path:b.digest(b.read_file(path)) for path in legacy.NATIVE_PINS}
    b.require(native==legacy.NATIVE_PINS and b.digest(b.read_file(b.NATIVE_SO))==b.NATIVE_SHA,"actual native bytes")
    cg=legacy.cgroup_limit();out=Path(a.output_dir).resolve()
    b.require(Path("/kvbuffer-results") in out.parents and not out.exists(),"fresh bounded output only")
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema="kvbp.intermediate-native-gate/v2",status="running",claim="kernel-only",
        created_ns=time.time_ns(),script_sha256=own[str(b.BASE/"middle_run.py")],driver_sources=own,
        source_manifest=packet["v2_gate_manifest"],followup_manifest=fr,
        sources_before=before,artifact_refs=ar,middle_meta=r["middle_meta"],
        launch_identity=ident,launch_identity_sha256=b.digest(Path(a.identity).read_bytes()),protocol=pp,
        frozen_receipts=checked,native_sources=native,cgroup=cg,candidate_namespace=b.NS,
        finite_scope=finite.FINITE_SCOPE,cases=[],serving_ready=False,performance_measurement_admitted=False,
        npu_executed=False)
    def save():(out/"report.json").write_text(
        json.dumps(oracle.finite_json(report),indent=2,allow_nan=False)+"\n")
    primary=None
    try:
        save()
        import torch,torch_npu
        oracle.torch=torch;oracle.torch_npu=torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        b.require(torch.npu.device_count()==1 and torch.npu.current_device()==0,"actual one logical device")
        b.require(enable_custom_op(),"native custom op unavailable");init_device_properties_triton()
        torch.ops.load_library(ar["library"]["path"]);ops=getattr(torch.ops,b.NS);oracle.bind_candidate(ops)
        report["candidate_schema"]=str(ops.decode.default._schema)
        report["native_schema"]=str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
        b.require(report["candidate_schema"]==meta["schema"],"actual candidate schema matches Meta")
        mapped={}
        for line in Path("/proc/self/maps").read_text().splitlines():
            fields=line.split()
            if len(fields)>=6 and fields[-1].startswith("/") and ".so" in fields[-1]:
                path=fields[-1]
                if Path(path).is_file() and any(w in path.lower() for w in ("kvbuffer","vllm","cust_op","opapi","torch_npu")):
                    mapped[path]=b.digest(b.read_file(path))
        b.require(mapped.get(ar["library"]["path"])==ar["library"]["sha256"]
                  and mapped.get(b.NATIVE_SO)==b.NATIVE_SHA,"actual candidate/native mappings")
        report["loaded_libraries"]=mapped
        report["runtime"]=dict(torch=torch.__version__,torch_npu=torch_npu.__version__,
            logical_device=0,logical_device_count=1,device_name=torch.npu.get_device_name(0))
        save()
        for t in a.batches:
            for mode,trials in (("eager",1),("graph",3)):
                for trial in range(trials):oracle.run_case(t,mode,trial,report,save,out)
            b.require(b.validate_batch([x for x in report["cases"] if x["batch"]==t],t,finite,bridge)==640,
                      "complete original 4x160 numerical/log/slot/flush/finite protocol")
        b.require(len(report["cases"])==4*len(a.batches),"no duplicated/extra true-T cases")
        report.update(status="intermediate_batches_kernel_native_eager_graph_pass",npu_executed=True)
        report["not_validated"]=["other-shards","48-layer-model-lifecycle","mixed-prefill","matched-E2E",
                                 "TTFT/TPOT","GSM8K/LongBench","formal-performance"]
    except BaseException as error:
        primary=error;report.update(status="failed",error=repr(error));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,_,pins2,own2,_,_,_=b.sources(fr);report["sources_after"]={**pins2,**own2}
            b.require(report["sources_after"]==before,"source drift during actual run");save()
        except BaseException as secondary:
            report["secondary_finalize_error"]=repr(secondary)
            try:save()
            except BaseException as save_error:
                print(json.dumps(dict(original_error=repr(primary or secondary),secondary_error=repr(secondary),
                                      save_error=repr(save_error),report_path=str(out/"report.json"))))
            if primary is None:raise
    return 0
if __name__=="__main__":raise SystemExit(main())
