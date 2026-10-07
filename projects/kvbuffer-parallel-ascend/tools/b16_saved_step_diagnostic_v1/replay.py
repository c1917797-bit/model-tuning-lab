#!/usr/bin/env python3
"""Explicit saved B16 failure diagnostic. Reproduction is NOT numerical PASS."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,math,os,sys,time
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
GATE=PROJECT/"tools/split_gate_v2"
OLD=PROJECT/"tools/saved_step_native_order_v2/replay.py"
OLD_SHA="bf83bb028ef309c826abd1a28dd4b32cbff6fcc390b71f2432c47986064b7e00"
SOURCE_SHA="508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9"
RAW=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/full-native-order-v2-20261007-1010/b16/gate/raw-step-b16-graph-t0-step37.pt")
RAW_SHA="ff6c632f7655e396d1f9752591688496791538c6b787a2af24fb2f43f9353f14"
RAW_BYTES=99004309
NATIVE="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
NATIVE_HEADER=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/native-source-snapshot-20261007-1052/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h")
NATIVE_HEADER_SHA="96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b"
def require(value,message):
    if not value:raise ValueError(message)
def sha(path):
    p=Path(path);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def module(path,digest,name):
    require(sha(path)==digest,"frozen helper drift")
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def write(path,value):
    with Path(path).open("x") as f:
        f.write(json.dumps(value,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(path),"sha256":sha(path)}
def metadata(f):
    require((f["schema"],f["batch"],f["mode"],f["trial"],f["step"],f["active"],f["reset_slot"])==
            ("kvbp.raw-step/v1",16,"graph",0,37,12,None),"exact saved failure metadata")
    require(set(f["before"])=={"base","k_log","u_log","lambda_log","decay","length"} and
            set(f["after"])==set(f["before"]) and set(f["guards_before"])==set(f["before"]) and
            set(f["guards"])==set(f["before"]),"all six state/guard fields")
def cpu_difference(torch,f):
    a,e=f["actual"][:12],f["expected"][:12]
    require(a.dtype==e.dtype==torch.bfloat16 and tuple(a.shape)==tuple(e.shape)==(12,12,128),
            "actual BF16 defined active output geometry")
    different=a.contiguous().view(torch.int16)!=e.contiguous().view(torch.int16)
    diff=(a.float()-e.float()).abs();flat=int(diff.flatten().argmax())
    coord=[flat//1536,(flat//128)%12,flat%128]
    def value(t,b,h,v):
        q=t[b,h,v]
        return {"value":float(q),"bits16":int(q.view(torch.int16))&65535}
    b,h,v=coord
    return {"scope":"original saved CPU BF16 active rows only",
            "different_bf16_points":int(different.sum()),"maximum_absolute_difference":float(diff.max()),
            "maximum_coordinate":coord,"actual":value(a,b,h,v),"expected":value(e,b,h,v),
            "neighborhood":[{"coordinate":[b,h,j],"actual":value(a,b,h,j),"expected":value(e,b,h,j)}
                            for j in range(max(0,v-2),min(128,v+3))],
            "maximum_expected_absolute":float(e.float().abs().max()),
            "slot_lengths_before":f["before"]["length"][:,:,0].tolist(),
            "slot_lengths_after":f["after"]["length"][:,:,0].tolist(),
            "indices":f["inputs"]["indices"].tolist(),"native_undefined_padding_not_compared":4,
            "precast_or_exact_candidate_reconstruction_observed":False}
def metrics(torch,h,result):
    state,guards,native,x,y,expected,before,immutable,pointers=result[:9]
    active=12;slots=19
    require(tuple(state["base"].shape)==(slots,12,128,128),"complete S19 geometry")
    complete=h.logical(state)
    eout=h.output_error(y[:active],expected[:active]);estate=h.rel(complete,native)
    ehead=max(h.rel(complete[s,v],native[s,v]) for s in range(slots) for v in range(12))
    ids=x["indices"][:active].cpu().tolist();unused=[s for s in range(slots) if s not in ids]
    logs=h.check_logs(state,before,x,active)
    checks={"untouched_slots_bitwise":all(torch.equal(state[n][unused],before[n][unused]) for n in h.NAMES),
      "nonflush_base_bitwise":all(torch.equal(state["base"][s],before["base"][s])
                                for s in ids if int(before["length"][s,0,0])!=15),
      "guards":all(bool(torch.all(g[:64]==7).cpu()) and bool(torch.all(g[-64:]==7).cpu()) for g in guards.values()),
      "pointers":h.all_pointers(state,guards,native,x)==pointers,
      "input_immutable":all(torch.equal(x[n],immutable[n]) for n in x),
      "zero_length_output_zero":bool(torch.all(y[active:]==0).cpu())}
    finite=h.finite_receipt(state,y,expected,complete,native,active,(eout,estate,ehead),
                           lambda t:bool(torch.isfinite(t).all().cpu()))
    return h.finite_json({"output_error":eout,"complete_state_l2":estate,"max_per_head_l2":ehead,
        "logs":logs,**checks,**finite,"original_thresholds":{"output":h.OUT_LIMIT,"state":h.STATE_LIMIT},
        "original_numeric_pass":eout<=h.OUT_LIMIT and estate<=h.STATE_LIMIT and ehead<=h.STATE_LIMIT
            and all(checks.values()) and all(logs.values()) and finite["finite"]})
def reproduction(torch,old,f,result):
    state,guards,native,x,y,expected=result[:6]
    return {"after":all(old.bitwise(torch,state[n],f["after"][n]) for n in state),
            "actual_all":old.bitwise(torch,y,f["actual"]),
            "native_all":old.bitwise(torch,native,f["native"]),
            "expected_active":old.bitwise(torch,expected[:12],f["expected"][:12]),
            "guards_all":all(old.bitwise(torch,guards[n],f["guards"][n]) for n in guards),
            "inputs_all":all(old.bitwise(torch,x[n],f["inputs"][n]) for n in x),
            "undefined_native_padding_not_compared":True}
def mapped(required):
    found={}
    for line in Path("/proc/self/maps").read_text().splitlines():
        p=line.split()
        if len(p)>=6 and p[-1]=="(deleted)" and p[-2] in required:
            raise ValueError("deleted actual mapped library; cannot prove bytes")
        if len(p)>=6 and p[-1] in required:found[p[-1]]=sha(p[-1])
    require(found==required,"actual mapped native/candidate exact binaries");return found
def history_branch(torch,h,old,f,out):
    state,guards,native,x=old.allocate_from_fixture(torch,h,f)
    logical=h.nd(h.logical(state));torch.npu.synchronize()
    logical_before=logical.detach().cpu().clone()
    expected=actual=None;primary=None
    try:
        expected=h.native(native,x);actual=h.native(logical,x);torch.npu.synchronize()
    except BaseException as e:primary=e
    raw=old.collect(torch,h,state,guards,native,x,actual,expected)
    raw.update(schema="kvbp.b16-history-raw/v1",logical_before=logical_before,
               original_native_before=f["native_before"],input_before=f["inputs"],
               source="independent Torch equation reconstruction, not exact candidate UB trace",
               dispatch_error=repr(primary) if primary else None)
    p=out/"historical-branch-raw.pt"
    try:torch.save(raw,p)
    except BaseException as e:
        if primary is not None:
            print(json.dumps({"primary":repr(primary),"secondary_save":repr(e)}),flush=True);raise primary
        raise
    if primary is not None:raise primary
    require(not raw["copy_errors"],"history raw incomplete")
    return {"raw":{"path":str(p),"sha256":sha(p)},
            "output_active_error":h.output_error(actual[:12],expected[:12]),
            "incoming_logical_vs_native_l2":h.rel(logical_before,f["native_before"]),
            "after_native_l2":h.rel(logical,native),"precise_candidate_trace":False,
            "attribution_closed":False,"diagnostic_only":True}
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    for n in ("script-sha256","source-manifest-sha256","library-sha256","build-receipt-sha256","meta-receipt-sha256"):
        p.add_argument("--"+n)
    for n in ("identity","output-dir","source-manifest","library","build-receipt","meta-receipt"):
        p.add_argument("--"+n,type=Path)
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
             "scope":"B16 graph0 step37 single saved-step diagnostic; never matrix PASS"}));return
    require(all(vars(a).values()),"explicit complete MAIN Refs")
    require(sha(__file__)==a.script_sha256 and a.source_manifest_sha256==SOURCE_SHA,"exact diagnostic/source64")
    require(sha(RAW)==RAW_SHA and RAW.stat().st_size==RAW_BYTES,"immutable original raw")
    require(sha(NATIVE_HEADER)==NATIVE_HEADER_SHA,"actual native header bytes")
    old=module(OLD,OLD_SHA,"_kvbp_b16_frozen_replay")
    sys.path.insert(0,str(GATE));import contract
    ref=contract.ref({"path":str(a.source_manifest),"sha256":a.source_manifest_sha256})
    manifest,sources=contract.source_admission(ref)
    refs={k:contract.ref({"path":str(path),"sha256":digest}) for k,path,digest in
        (("library",a.library,a.library_sha256),("build",a.build_receipt,a.build_receipt_sha256),
         ("meta",a.meta_receipt,a.meta_receipt_sha256))}
    contract.artifacts(refs,manifest)
    ident=json.loads(a.identity.read_bytes());contract.validate_identity(ident,16,6,ref,manifest,sources,refs)
    require(ident["diagnostic_script"]=={"path":str(Path(__file__).resolve()),"sha256":a.script_sha256},
            "actual explicitly admitted diagnostic source")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and
            os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
            os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","same single-logical0 environment")
    cg=contract.legacy().cgroup_limit()
    out=a.output_dir;require(out.parent==Path("/kvbuffer-results") and not out.exists(),"fresh exclusive diagnostic")
    out.mkdir()
    report={"schema":"kvbp.b16-saved-step-diagnostic/v1","status":"running","created_ns":time.time_ns(),
        "raw":{"path":str(RAW),"sha256":RAW_SHA,"bytes":RAW_BYTES},
        "sources_before":sources,"source_manifest":ref,"artifacts":refs,"cgroup":cg,
        "identity_sha256":sha(a.identity),"native_header_sha256":NATIVE_HEADER_SHA,"results":[],
        "matrix_verified":False,"e2e_verified":False,"accuracy_verified":False,"serving_ready":False,
        "precise_trace_observed":False}
    serial=0;helper=None;primary=None
    def save():
        nonlocal serial
        serial+=1;v=helper.finite_json(report) if helper else report
        return write(out/("report-%03d.json"%serial),v)
    save()
    try:
        import torch
        fixture=torch.load(RAW,map_location="cpu",weights_only=True);metadata(fixture)
        require(tuple(fixture["before"]["base"].shape)==(19,12,128,128),"original S19")
        require(all(old.bitwise(torch,fixture["inputs"][n],fixture["input_before"][n]) for n in fixture["inputs"]),
                "original inputs immutable")
        # First report actual CPU BF16 bits before any device import/bootstrap.
        report["original_cpu_difference"]=cpu_difference(torch,fixture);save()
        torch.save({"fixture":fixture,"source_raw_sha256":RAW_SHA},out/"before.pt")
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4","actual910B4")
        require(enable_custom_op(),"original native bootstrap");init_device_properties_triton()
        require({n:sha(n) for n in contract.legacy().NATIVE_PINS}==contract.legacy().NATIVE_PINS,"native sources")
        helper=module(GATE/"oracle.py",manifest["files"]["oracle.py"],"_kvbp_b16_oracle")
        helper.torch=torch;helper.torch_npu=torch_npu
        torch.ops.load_library(str(a.library));ops=getattr(torch.ops,contract.NAMESPACE);helper.bind_candidate(ops)
        report["mapped_libraries"]=mapped({str(a.library):a.library_sha256,NATIVE:NATIVE_SHA})
        write(out/"attribution-ready.json",{"pid":os.getpid(),"hold_seconds":12,"separate_canary_not_gate":True,
             "source_raw_sha256":RAW_SHA,"candidate_matrix_verified":False})
        time.sleep(12) # bounded host actual-PID attribution, never performance.
        for mode in ("eager","graph"):
            result=old.step(torch,helper,fixture,ops,out,mode,"current-"+mode)
            row={"mode":mode,"raw":{"path":str(result[-1]),"sha256":sha(result[-1])},
                 "reproduction":reproduction(torch,old,fixture,result)}
            report["results"].append(row);save()
            require(all(row["reproduction"].values()),"single saved-step bytes do not reproduce; retain and STOP")
            row["metrics"]=metrics(torch,helper,result);save()
            require(row["metrics"]["original_numeric_pass"] is False and
                    row["metrics"]["output_error"]==0.003048780487804878,
                    "original output failure no longer exact; diagnosis changed, not PASS")
        report["history_branch"]=history_branch(torch,helper,old,fixture,out);save()
        report["status"]="reproduced-original-failure-diagnostic-only"
    except BaseException as e:
        primary=e;report.update(status="failed",original_error=repr(e));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,after=contract.source_admission(ref);report["sources_after"]=after
            require(after==sources and sha(RAW)==RAW_SHA and sha(__file__)==a.script_sha256,
                    "source/evidence drift")
            final=save();print("MAIN_KVBUFFER_B16_DIAGNOSTIC "+json.dumps(final),flush=True)
        except BaseException as e:
            if primary is None:raise
            try:print(json.dumps({"primary":repr(primary),"secondary_finalize":repr(e)}),flush=True)
            except BaseException:pass
if __name__=="__main__":main()
