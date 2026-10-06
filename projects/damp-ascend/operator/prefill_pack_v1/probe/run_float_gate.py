"""Opt-in, isolated real-NPU/Meta gate. MAIN owns execution; no pack/state writes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
BASE=Path(__file__).resolve().parent
REPO=BASE.parents[4]
PROJECT=REPO/"projects/damp-ascend"
NAMESPACE="qwen36_damp_prefill_float_probe"
LIBRARY="libqwen36_damp_prefill_float_probe_ops.so"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OPP_PATH=Path("/usr/local/Ascend/cann-9.1.0/opp/version.info")
OPP_SHA="841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6"
def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked(path,digest):
    p=Path(path)
    require(p.is_absolute() and p.is_file() and sha(p)==digest,"missing/drifted absolute file "+str(p))
    return p.resolve()
def read_bound(path,digest):return json.loads(checked(path,digest).read_text())
def source_bindings(args):
    source=read_bound(args.source_manifest,args.source_manifest_sha256)
    runtime=read_bound(args.runtime_manifest,args.runtime_manifest_sha256)
    require(source["schema"]=="damp-prefill-float-compiled-source/v1" and
            source["namespace"]==NAMESPACE and source["target_library"]==LIBRARY,"compiled identity")
    require(len(source["compiled_sources"])==9,"compiled9 required")
    require(runtime["schema"]=="damp-prefill-float-runtime-source/v1" and
            runtime["default_execute"] is False and runtime["npu_executed"] is False,"runtime preparation")
    for table in (source["compiled_sources"],runtime["sources"]):
        for name,digest in table.items():
            p=(REPO/name).resolve()
            require(p.is_relative_to(PROJECT.resolve()),"source escaped project")
            checked(p,digest)
    lib=checked(args.library,args.library_sha256)
    require(lib.name==LIBRARY,"wrong independent library")
    receipt=read_bound(args.build_receipt,args.build_receipt_sha256)
    require(receipt.get("status")=="compiled_no_device" and receipt.get("npu_executed") is False and
            receipt.get("sources")==source["compiled_sources"] and receipt.get("image_id")==IMAGE and
            receipt.get("npu_arch")=="dav-2201" and receipt.get("library_sha256")==args.library_sha256,
            "actual no-device build receipt/source/library/arch/image required")
    commands=receipt.get("commands",[])
    require(len(commands)>=2 and all(c.get("exit_code")==0 and c.get("command") and
            len(c.get("log_sha256",""))==64 for c in commands),"actual successful build logs")
    exported=receipt.get("exported_kernel",{})
    require(exported.get("name")=="qwen36_damp_prefill_float_div_bits_kernel" and
            exported.get("defined") is True and exported.get("type") in ("T","W") and
            len(exported.get("audit_sha256",""))==64,"exported non-UND host launcher required")
    checked(exported["audit_path"],exported["audit_sha256"])
    require(receipt.get("cann_version_info_sha256")==OPP_SHA,"actual OPP identity required")
    checked(OPP_PATH,OPP_SHA)
    require("Version=9.1.0" in OPP_PATH.read_text().splitlines(),"actual OPP9.1 line")
    return dict(compiled_sources=source["compiled_sources"],runtime_sources=runtime["sources"],
                source_manifest_sha256=args.source_manifest_sha256,
                runtime_manifest_sha256=args.runtime_manifest_sha256,
                library=str(lib),library_sha256=args.library_sha256,
                build_receipt=args.build_receipt,build_receipt_sha256=args.build_receipt_sha256)
def nullable_copy(tensors):
    out=[];errors=[]
    for i,t in enumerate(tensors):
        try:out.append(t.detach().cpu().clone())
        except BaseException as error:out.append(None);errors.append(dict(index=i,error=repr(error)))
    return out,errors
def parse(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("meta","npu"),required=True)
    p.add_argument("--execute",action="store_true")
    for name in ("source-manifest","runtime-manifest","library","build-receipt"):
        p.add_argument("--"+name,required=True);p.add_argument("--"+name+"-sha256",required=True)
    p.add_argument("--output-dir",required=True)
    p.add_argument("--preflight");p.add_argument("--preflight-sha256")
    p.add_argument("--physical-card",type=int,choices=(4,5,6,7),default=4)
    return p.parse_args(argv)
def main(argv=None):
    a=parse(argv)
    require(a.execute,"no execution without explicit --execute")
    out=Path(a.output_dir)
    require(out.is_absolute() and not out.exists(),"NEW absolute non-overwrite output required")
    bindings=source_bindings(a)
    out.mkdir(parents=True,exist_ok=False)
    report=dict(schema="damp-prefill-exact-float-gate/v1",namespace=NAMESPACE,status="started",
                mode=a.mode,npu_executed=False,graph_supported=False,packing_supported=False,
                serving_ready=False,bindings=bindings,cases=[],negative=[],error=None)
    def save_report():
        (out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    save_report()
    try:
        import torch
        if a.mode=="npu":
            require(a.preflight and a.preflight_sha256,"fresh actual device proof required")
            proof=read_bound(a.preflight,a.preflight_sha256)
            contract_path=PROJECT/"tests/all_batch_gate_v1/contract.py"
            checked(contract_path,"f42a42ce36dc18cb65381f00ac3a4737cb8b50dbf50b22bf90a719dd800d87fd")
            old=list(sys.path)
            try:
                sys.path.insert(0,str(contract_path.parent))
                spec=importlib.util.spec_from_file_location("prefill_float_device_contract",contract_path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                module.validate_device(proof,a.physical_card,time.time_ns())
            finally:sys.path[:]=old
            import torch_npu
            torch.npu.set_device(0)
            require(torch.npu.get_device_name(0)=="Ascend910B4","actual runtime SoC mismatch")
            report.update(npu_executed=True,physical_card=a.physical_card,actual_runtime_soc="Ascend910B4",
                          device_proof=dict(path=a.preflight,sha256=a.preflight_sha256,content=proof))
        torch.ops.load_library(bindings["library"])
        op=getattr(torch.ops,NAMESPACE)
        report["schemas"]={name:str(getattr(op,name).default._schema) for name in ("prepare","divide_bits")}
        if a.mode=="meta":
            for n in (64,896):
                inputs=[torch.empty(n,dtype=torch.int32,device="meta") for _ in range(3)]
                for enabled in (False,True):
                    op.prepare(*inputs,enabled);actual=op.divide_bits(*inputs,enabled)
                    require(len(actual)==4 and all(t.shape==(n+16,) and t.dtype==torch.int32 and
                            t.device.type=="meta" for t in actual),"actual Meta outputs")
                    report["cases"].append(dict(count=n,use_candidate=enabled,status="passed"))
            for n in (0,63,65,897,1792):
                inputs=[torch.empty(n,dtype=torch.int32,device="meta") for _ in range(3)]
                try:op.divide_bits(*inputs,False)
                except BaseException as error:report["negative"].append(dict(count=n,error=repr(error),passed=True))
                else:raise RuntimeError("invalid Meta N admitted")
            report["status"]="load_schema_meta_pass";save_report();return
        from cases import GUARDS,INPUT_GUARDS,signed,matrix_chunks,changing_rows
        def one(name,rows,enabled,prepared=False):
            n=len(rows)
            cpu_roots=[torch.tensor([INPUT_GUARDS[j]]*8+[signed(r[k]) for r in rows]+
                        [INPUT_GUARDS[j]]*8,dtype=torch.int32) for j,k in enumerate(("x","c","proposal"))]
            expected=[torch.tensor([GUARDS[j]]*8+
                        [signed(r["bits"]) if j==0 else r[("valid","finite","accepted")[j-1]]
                         if j<3 or enabled else 0 for r in rows]+[GUARDS[j]]*8,dtype=torch.int32)
                      for j in range(4)]
            artifact=dict(name=name,rows=rows,use_candidate=enabled,before=cpu_roots,golden=expected,
                          raw_actual=None,after=None,dispatch_error=None,copy_errors=[],replays=[])
            torch.save(artifact,out/(name+".before.pt")) # BEFORE H2D, poisoned context cannot erase fixture
            roots=[];device_out=[]
            try:
                roots=[torch_npu.npu_format_cast(t.to("npu:0"),2) for t in cpu_roots]
                inputs=[t[8:8+n] for t in roots]
                ptrs=[(t.data_ptr(),t.untyped_storage().data_ptr()) for t in roots]
                before,_=nullable_copy(roots)
                op.prepare(*inputs,enabled);torch.npu.synchronize()
                prepare_after,errors=nullable_copy(roots);artifact["copy_errors"]+=errors
                require(all(x is not None and torch.equal(x,y) for x,y in zip(prepare_after,before)),
                        "prepare mutated raw inputs")
                for replay in range(8):
                    device_out=op.divide_bits(*inputs,enabled);torch.npu.synchronize()
                    repeated,errors=nullable_copy(device_out)
                    artifact["replays"].append(repeated);artifact["copy_errors"]+=errors
                require(ptrs==[(t.data_ptr(),t.untyped_storage().data_ptr()) for t in roots],
                        "input storage moved")
                require(len({t.untyped_storage().data_ptr() for t in [*roots,*device_out]})==7,
                        "output/input storage alias")
            except BaseException as error:artifact["dispatch_error"]=repr(error)
            artifact["raw_actual"],errors=nullable_copy(device_out);artifact["copy_errors"]+=errors
            artifact["after"],errors=nullable_copy(roots);artifact["copy_errors"]+=errors
            torch.save(artifact,out/(name+".pt")) # raw full outputs/guards saved BEFORE assertions
            require(artifact["dispatch_error"] is None and not artifact["copy_errors"],
                    "dispatch/copy failure; raw artifact retained")
            require(len(artifact["raw_actual"])==4 and all(torch.equal(x,y) for x,y in
                    zip(artifact["raw_actual"],expected)),"full raw bits/status/guards mismatch")
            require(len(artifact["replays"])==8 and all(len(replay)==4 and all(
                    x is not None and torch.equal(x,y) for x,y in zip(replay,expected))
                    for replay in artifact["replays"]),"identical-repeat nondeterminism")
            require(len(artifact["after"])==3 and all(torch.equal(x,y) for x,y in
                    zip(artifact["after"],cpu_roots)),"raw input/guard mutation")
            report["cases"].append(dict(name=name,count=n,use_candidate=enabled,status="passed",
                identical_repeats=8,artifact=str(out/(name+".pt")),artifact_sha256=sha(out/(name+".pt"))))
            save_report()
        for name,rows in matrix_chunks(896):
            for enabled in (False,True):one(name+("-certificate" if enabled else "-exact"),rows,enabled)
        for n in (64,896):
            for turn in range(20):
                for enabled in (False,True):
                    one("changing-%d-%d-%d"%(n,turn,enabled),changing_rows(n,turn),enabled)
        # Actual host rejection guards, freshly saved before each potentially invalid dispatch.
        for bad in ("N0","N63","N65","N897","N1792","wrongdtype","noncontiguous","offset","alias","cpu"):
            count=int(bad[1:]) if bad.startswith("N") else 64
            roots=[torch_npu.npu_format_cast(torch.zeros(max(count,128)+16,dtype=torch.int32,
                    device="npu:0"),2) for _ in range(3)]
            before,errors=nullable_copy(roots);artifact=dict(name=bad,before=before,error=None,
                                                           copy_errors=errors,after=None)
            torch.save(artifact,out/("reject-"+bad+".before.pt"))
            inputs=[t[8:8+count] for t in roots]
            if bad=="wrongdtype":inputs[1]=inputs[1].to(torch.int64)
            if bad=="noncontiguous":inputs[1]=roots[1][8:136:2]
            if bad=="offset":inputs[1]=roots[1][9:73]
            if bad=="alias":inputs[1]=inputs[0]
            if bad=="cpu":inputs[1]=inputs[1].cpu()
            try:op.divide_bits(*inputs,False);torch.npu.synchronize()
            except BaseException as error:artifact["error"]=repr(error)
            artifact["after"],errors=nullable_copy(roots);artifact["copy_errors"]+=errors
            torch.save(artifact,out/("reject-"+bad+".pt"))
            require(artifact["error"] is not None and not artifact["copy_errors"] and
                    all(torch.equal(x,y) for x,y in zip(artifact["after"],before)),
                    "negative must reject without input mutation")
            report["negative"].append(dict(name=bad,passed=True));save_report()
        require(bindings==source_bindings(a),"source drift during gate")
        report["status"]="exact_float_numerical_pass";save_report()
    except BaseException as error:
        report.update(status="failed",error=repr(error));save_report();raise
if __name__=="__main__":main()
