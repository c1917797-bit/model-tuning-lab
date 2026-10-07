#!/usr/bin/env python3
"""Bounded copy-only candidate UB trace. Default OFF; no automatic device launch."""
from __future__ import annotations
import argparse,hashlib,json,math,sys,time
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/kvbuffer-parallel-ascend/tools/candidate_ub_trace_v1"
OP=ROOT/"projects/kvbuffer-parallel-ascend/operator/candidate_ub_trace_v1"
NAMESPACE="qwen36_kvbuffer_native_order_trace_v1"
RAW_SHA="ff6c632f7655e396d1f9752591688496791538c6b787a2af24fb2f43f9353f14"
REPLAY_SHA="bf83bb028ef309c826abd1a28dd4b32cbff6fcc390b71f2432c47986064b7e00"
RAW_BYTES=99004309
TRACE_BYTES=49344
SOURCE64=ROOT/"projects/kvbuffer-parallel-ascend/tools/split_gate_v2"
SOURCE64_SHA="508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9"
PRODUCTION_SO_SHA="77b4d61f94b4a8747bd08d2223b11d87702b43186acfd2f1b2e220f7b64a065c"
NATIVE_SO_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
EXPECTED_META=[6,5,4,15,0,1,1,1,1,1,1,16,19,0,0,0]
SCHEMA=("qwen36_kvbuffer_native_order_trace_v1::decode_trace(Tensor query, Tensor key, Tensor value, "
 "Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
 "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, "
 "Tensor actual_seq_lengths, Tensor state_indices, Tensor(g!) trace_states, "
 "Tensor(h!) trace_output, Tensor(i!) trace_meta) -> Tensor")
def require(v,message):
    if not v:raise ValueError(message)
def sha(p):
    p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary exact source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,value):
    with Path(path).open("x") as f:f.write(json.dumps(value,indent=2,allow_nan=False)+"\n")
    return {"path":str(path),"sha256":sha(path)}
def source_admission(manifest_sha):
    require(sha(HERE/"SOURCE_MANIFEST.json")==manifest_sha,"MAIN exact trace source manifest")
    m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
    require(m["schema"]=="kvbp.candidate-ub-trace-source/v1" and m["default_enabled"] is False and
            m["npu_verified"] is False and m["namespace"]==NAMESPACE and m["trace_bytes"]==TRACE_BYTES,
            "trace source scope")
    observed={}
    for rel,item in m["files"].items():
        p=ROOT/rel;require(sha(p)==item["sha256"] and p.stat().st_size==item["bytes"],"NEW source drift")
        observed[str(p)]=item["sha256"]
    for rel,item in m["upstream_files"].items():
        p=ROOT/rel;require(sha(p)==item["sha256"] and p.stat().st_size==item["bytes"],"frozen7 source drift")
    require(m["source64"]=={"path":str(SOURCE64/"SOURCE_MANIFEST.json"),"sha256":SOURCE64_SHA},
            "unchanged complete frozen64 binding")
    sys.path.insert(0,str(SOURCE64));import contract
    _,legacy_sources=contract.source_admission(m["source64"]);require(len(legacy_sources)==64,"full frozen64")
    return m,observed
def check_ranges(ranges,mutable):
    for i in mutable:
        a,n=ranges[i];require(type(a) is int and type(n) is int and a>=0 and n>0,"valid storage byte interval")
        for j,(b,k) in enumerate(ranges):
            if i==j:continue
            require(a+n<=b or b+k<=a,"mutated trace/original storage overlaps another argument")
def original_reproduction(torch,old,fixture,baseline,result):
    bs,bg,bn,bx,by,be=baseline[:6];state,guards,native,x,y,expected=result[:6]
    return {"original_after":all(old.bitwise(torch,bs[n],fixture["after"][n]) for n in bs),
      "original_output":old.bitwise(torch,by,fixture["actual"]),
      "original_native":old.bitwise(torch,bn,fixture["native"]),
      "original_expected_active":old.bitwise(torch,be[:12],fixture["expected"][:12]),
      "trace_after":all(old.bitwise(torch,state[n],bs[n]) for n in state),
      "trace_output_all":old.bitwise(torch,y,by),
      "trace_native_all":old.bitwise(torch,native,bn),
      "trace_expected_active":old.bitwise(torch,expected[:12],be[:12]),
      "trace_guards":all(old.bitwise(torch,guards[n],bg[n]) for n in guards),
      "trace_inputs":all(old.bitwise(torch,x[n],bx[n]) for n in x)}
def invoke(ops,state,x,trace):
    return ops.decode_trace(x["query"],x["key"],x["value"],x["g"],x["beta"],state["base"],
          state["k_log"],state["u_log"],state["lambda_log"],state["decay"],state["length"],
          x["seq"],x["indices"],trace["states"],trace["output"],trace["meta"])
def allocate_trace(torch,helper):
    trace,guards={},{}
    for name,shape,dtype in (("states",(3,32,128),torch.float32),("output",(32,),torch.float32),("meta",(16,),torch.int32)):
        trace[name],guards[name]=helper.guarded(shape,dtype)
    require(sum(t.numel()*t.element_size() for t in trace.values())==TRACE_BYTES,"bounded trace ledger")
    trace["states"].fill_(float("nan"));trace["output"].fill_(float("nan"));trace["meta"].zero_()
    return trace,guards
def reset_trace(torch,trace,guards):
    for root in guards.values():root.fill_(7)
    trace["states"].fill_(float("nan"));trace["output"].fill_(float("nan"));trace["meta"].zero_()
def trace_step(torch,helper,old,fixture,ops,out,mode):
    # Same frozen step call order; only additional independent mutable trace outputs.
    state,guards,native,x=old.allocate_from_fixture(torch,helper,fixture)
    trace,trace_guards=allocate_trace(torch,helper)
    original_pointers=helper.all_pointers(state,guards,native,x)
    trace_pointers={n:t.data_ptr() for n,t in trace.items()}
    y=expected=None;primary=None
    try:
        ops.prepare(x["query"],state["base"]);torch.npu.synchronize()
        if mode=="graph":
            warm,warm_guards,_,wx=old.allocate_from_fixture(torch,helper,fixture)
            wt,wg=allocate_trace(torch,helper)
            for _ in range(3):invoke(ops,warm,wx,wt);torch.npu.synchronize()
            graph=torch.npu.NPUGraph()
            with torch.npu.graph(graph):y=invoke(ops,state,x,trace)
            torch.npu.synchronize()
            for n in helper.NAMES:guards[n].copy_(fixture["guards_before"][n].to("npu:0"))
            reset_trace(torch,trace,trace_guards);torch.npu.synchronize()
        expected=helper.native(native,x) # original independent native FIRST
        if mode=="graph":torch.npu.synchronize();graph.replay()
        else:y=invoke(ops,state,x,trace)
        torch.npu.synchronize()
    except BaseException as e:primary=e
    raw=old.collect(torch,helper,state,guards,native,x,y,expected);copy_errors={}
    def copy(name,t):
        try:return t.detach().cpu().clone()
        except BaseException as e:copy_errors[name]=repr(e);return None
    try:trace_pointers_after={n:t.data_ptr() for n,t in trace.items()}
    except BaseException as e:
        trace_pointers_after=None;copy_errors["trace_pointers_after"]=repr(e)
    raw.update(schema="kvbp.candidate-ub-trace-raw/v1",mode=mode,
       trace={n:copy("trace."+n,t) for n,t in trace.items()},
       trace_guards={n:copy("trace_guard."+n,t) for n,t in trace_guards.items()},
       before=fixture["before"],native_before=fixture["native_before"],inputs_before=fixture["input_before"],
       pointers_before=original_pointers,trace_pointers_before=trace_pointers,
       trace_pointers_after=trace_pointers_after,trace_copy_errors=copy_errors,
       original_dispatch_error=repr(primary) if primary else None,source_raw_sha256=RAW_SHA)
    p=out/("trace-"+mode+"-raw.pt")
    try:
        require(not p.exists(),"trace raw cannot overwrite");torch.save(raw,p)
    except BaseException as e:
        if primary is not None:
            print(json.dumps({"primary":repr(primary),"secondary_raw_save":repr(e)}),flush=True);raise primary
        raise
    if primary is not None:raise primary
    require(not raw["copy_errors"] and not copy_errors,"trace raw incomplete")
    checks={"original_pointers":helper.all_pointers(state,guards,native,x)==original_pointers,
       "trace_pointers":raw["trace_pointers_before"]==raw["trace_pointers_after"],
       "trace_guards":all(bool(torch.all(t[:64]==7).cpu()) and bool(torch.all(t[-64:]==7).cpu()) for t in trace_guards.values()),
       "meta":raw["trace"]["meta"].tolist()==EXPECTED_META,
       "trace_finite":bool(torch.isfinite(trace["states"]).all().cpu()) and bool(torch.isfinite(trace["output"]).all().cpu())}
    return (state,guards,native,x,y,expected),raw,{"path":str(p),"sha256":sha(p)},checks
def diagnostic(torch,helper,old,fixture,production_ops,trace_ops,out,*,enabled=False,
               raw_path=None,source_manifest_sha256=None,libraries=None):
    require(enabled is True,"trace default OFF")
    require(raw_path is not None and source_manifest_sha256 and type(libraries) is dict and
            set(libraries)=={"production","trace","native"},"MAIN actual immutable raw/source/library Refs")
    source_manifest,source_before=source_admission(source_manifest_sha256)
    require(sha(raw_path)==RAW_SHA and Path(raw_path).stat().st_size==RAW_BYTES,"actual immutable saved bytes")
    require(libraries["production"]["sha256"]==PRODUCTION_SO_SHA and
            libraries["native"]["sha256"]==NATIVE_SO_SHA,"actual original production/native binaries")
    required={r["path"]:r["sha256"] for r in libraries.values()}
    for path,digest in required.items():require(sha(path)==digest,"actual binary bytes drift")
    old.mapped(required) # known frozen helper has no deleted map support; reject deleted explicitly first below
    for line in Path("/proc/self/maps").read_text().splitlines():
        parts=line.split()
        require(not(len(parts)>=7 and parts[-1]=="(deleted)" and parts[-2] in required),
                "deleted mapped library cannot prove actual bytes")
    require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4","actual one910B4")
    require((fixture["schema"],fixture["batch"],fixture["trial"],fixture["step"],fixture["active"])==
            ("kvbp.raw-step/v1",16,0,37,12),"fixed saved fixture scope")
    require(str(trace_ops.decode_trace.default._schema)==SCHEMA,"actual loaded trace ABI differs")
    require(tuple(fixture["before"]["base"].shape)==(19,12,128,128) and
       int(fixture["inputs"]["indices"][6])==4 and int(fixture["before"]["length"][4,5,0])==15,
       "actual failure selector/flush differs")
    require(not out.exists(),"exclusive NEW trace output");out.mkdir()
    report={"schema":"kvbp.candidate-ub-trace-diagnostic/v1","status":"running","source_raw_sha256":RAW_SHA,
      "scope":"token6/head5/slot4/Vtile0/step37 only","cases":[],"trace_bytes":TRACE_BYTES,
      "candidate_numeric_pass":False,"cause_proved":False,"serving_ready":False,"matrix_verified":False,
      "native_precast_observed":False,"created_ns":time.time_ns(),
      "source_manifest_sha256":source_manifest_sha256,"sources_before":source_before,"libraries":libraries}
    serial=0
    def save():
        nonlocal serial
        serial+=1;return write(out/("report-%03d.json"%serial),helper.finite_json(report))
    save();primary=None
    try:
        for mode in ("eager","graph"):
            baseline=old.step(torch,helper,fixture,production_ops,out,mode,"production-"+mode)
            result,raw,ref,checks=trace_step(torch,helper,old,fixture,trace_ops,out,mode)
            compare=original_reproduction(torch,old,fixture,baseline,result)
            row={"mode":mode,"raw":ref,"baseline_raw":{"path":str(baseline[-1]),"sha256":sha(baseline[-1])},
                 "non_interference":compare,"trace_checks":checks}
            report["cases"].append(row);save()
            require(all(compare.values()) and all(checks.values()),"trace does not anchor production bytes; STOP")
            trace=raw["trace"]
            # merge=true: actual UB update must bitwise equal exact candidate base store.
            row["updated_ub_equals_actual_flush_base"]=old.bitwise(torch,trace["states"][2],raw["after"]["base"][4,5,:32])
            # Do not substitute Torch equation for reconstruction. All below are actual copied UB values.
            row["selected_reconstructed_vs_native_before_l2"]=helper.rel(trace["states"][0],fixture["native_before"][4,5,:32])
            row["selected_updated_vs_native_after_l2"]=helper.rel(trace["states"][2],fixture["native"][4,5,:32])
            row["precast_values"]=trace["output"].tolist()
            row["actual_bf16_bits"]=(raw["actual"][6,5,:32].view(torch.int16).to(torch.int32)&65535).tolist()
            row["native_bf16_bits"]=(raw["expected"][6,5,:32].view(torch.int16).to(torch.int32)&65535).tolist()
            row["selected_coordinate"]=[6,5,6]
            row["candidate_precast_v6"]=float(trace["output"][6])
            row["original_bf16_rounding_midpoint_v6"]=(0.00396728515625+0.003997802734375)/2
            row["native_precast"]="unobserved; cannot give exact native distance"
            save();require(row["updated_ub_equals_actual_flush_base"],"UB/store seam differs")
        report["status"]="anchored-copy-only-trace-diagnostic"
    except BaseException as e:primary=e;report.update(status="failed",original_error=repr(e));raise
    finally:
        report["completed_ns"]=time.time_ns()
        try:
            _,after=source_admission(source_manifest_sha256);report["sources_after"]=after
            require(after==source_before and sha(raw_path)==RAW_SHA,"source/raw drift during trace")
            print("MAIN_KVBUFFER_UB_TRACE "+json.dumps(save()),flush=True)
        except BaseException as e:
            if primary is None:raise
            try:print(json.dumps({"primary":repr(primary),"secondary_report":repr(e)}),flush=True)
            except BaseException:pass
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source-audit-only",action="store_true")
    p.add_argument("--source-manifest-sha256");a=p.parse_args(argv)
    if not a.source_audit_only:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"serving_ready":False,
                         "trace_bytes":TRACE_BYTES,"loaded_abi_verified":False}));return
    require(a.source_manifest_sha256,"MAIN published source manifest SHA")
    _,s=source_admission(a.source_manifest_sha256)
    print(json.dumps({"status":"source-only","source_count":len(s),"npu_executed":False}))
if __name__=="__main__":main()
