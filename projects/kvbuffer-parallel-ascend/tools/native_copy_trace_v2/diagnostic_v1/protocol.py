#!/usr/bin/env python3
"""Native true-UB copy observation. DEFAULT OFF; four single-step anchors only."""
from __future__ import annotations
import argparse,json,os,struct,sys,time
from pathlib import Path
import native_contract as nc
ROOT=nc.ROOT;HERE=nc.HERE
RAW=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/full-native-order-v2-20261007-1010/b16/gate/raw-step-b16-graph-t0-step37.pt")
RAW_SHA="ff6c632f7655e396d1f9752591688496791538c6b787a2af24fb2f43f9353f14"
NATIVE="/vllm-workspace/vllm-ascend/vllm_ascend/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
NATIVE_SHA="eaa9457a21a45e2cb027c1345ee670b59d10fcd6f4a8be8b0b1bf2fde1d2232a"
OLD=nc.PROJECT/"tools/saved_step_native_order_v2/replay.py"
OLD_SHA="bf83bb028ef309c826abd1a28dd4b32cbff6fcc390b71f2432c47986064b7e00"
require=nc.require;sha=nc.sha
def write(p,obj):
    with Path(p).open("x") as f:
        f.write(json.dumps(obj,indent=2,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    return {"path":str(p),"sha256":sha(p)}
def fixture_metadata(f,torch):
    require((f["schema"],f["batch"],f["mode"],f["trial"],f["step"],f["active"],f["reset_slot"])==
        ("kvbp.raw-step/v1",16,"graph",0,37,12,None),"exact original saved scope")
    require(f["inputs"]["seq"].tolist()==[0]+[1]*12+[0]*4,"real non-cumulative native sequence lengths")
    ids=f["inputs"]["indices"][:12].tolist()
    require(len(set(ids))==12 and all(0<=s<19 for s in ids) and ids[6]==4,"unique valid native state slots")
    require(tuple(f["native_before"].shape)==(19,12,128,128) and f["native_before"].dtype==torch.float32,
            "complete native incoming state")
    require(f["inputs"]["query"].dtype==f["inputs"]["key"].dtype==f["inputs"]["value"].dtype==
        f["inputs"]["beta"].dtype==torch.bfloat16 and f["inputs"]["g"].dtype==torch.float32 and
        f["inputs"]["indices"].dtype==f["inputs"]["seq"].dtype==torch.int32,"actual native ABI")
    return ids
def mapped(required):
    found={}
    for line in Path("/proc/self/maps").read_text().splitlines():
        cols=line.split()
        if len(cols)>=7 and cols[-1]=="(deleted)" and cols[-2] in required:
            raise ValueError("actual required library map is deleted")
        if len(cols)>=6 and cols[-1] in required:found[cols[-1]]=sha(cols[-1])
    require(found==required,"actual mapped native/observation libraries");return found
def call(ops,s,x,tr):
    return ops.decode_trace(x["query"],x["key"],x["value"],x["g"],x["beta"],s,
          x["seq"],x["indices"],tr["precast"],tr["selected"])
def allocate(torch,h,initial,inputs):
    base,bg=h.guarded((19,12,128,128),torch.float32,initial.to("npu:0"))
    state,sg=h.guarded((19,12,128,128),torch.float32,initial.to("npu:0"))
    x={n:h.nd(t.to("npu:0").clone()) for n,t in inputs.items()}
    trace={};guards={"native":bg,"observed":sg}
    for n,shape in [("precast",(16,12,128)),("selected",(16,12,128,128))]:
        trace[n],guards[n]=h.guarded(shape,torch.float32)
        trace[n].fill_(7)
    return base,state,x,trace,guards
def observe(torch,h,old,ops,initial,inputs,out,mode,label,ids):
    base,state,x,tr,guards=allocate(torch,h,initial,inputs)
    ptr={n:t.data_ptr() for n,t in {**guards,**{"x."+n:t for n,t in x.items()}}.items()}
    before_guards={n:t.detach().cpu().clone() for n,t in guards.items()}
    expected=y=None;primary=None;graph=None;tiling=None
    try:
        ops.prepare(x["query"],state);torch.npu.synchronize()
        tiling=ops.tiling_info(x["query"],state).tolist()
        if mode=="graph":
            wb,ws,wx,wt,wg=allocate(torch,h,initial,inputs)
            for _ in range(3):call(ops,ws,wx,wt);torch.npu.synchronize()
            graph=torch.npu.NPUGraph()
            with torch.npu.graph(graph):y=call(ops,state,x,tr)
            torch.npu.synchronize()
            for n,t in guards.items():t.copy_(before_guards[n].to("npu:0"))
            torch.npu.synchronize()
        # Real deployed native FIRST, actual trace second, preserving original ordering.
        expected=h.native(base,x)
        if mode=="graph":torch.npu.synchronize();graph.replay()
        else:y=call(ops,state,x,tr)
        torch.npu.synchronize()
    except BaseException as e:primary=e
    errors={}
    def copy(n,t):
        if t is None:return None
        try:return t.detach().cpu().clone()
        except BaseException as e:errors[n]=repr(e);return None
    raw={"schema":"kvbp.native-copy-trace-raw/v1","mode":mode,"label":label,"source_raw_sha256":RAW_SHA,
        "state_before":initial,"inputs_before":inputs,"guards_before":before_guards,
        "native_after":copy("native_after",base),"observed_after":copy("observed_after",state),
        "native_output":copy("native_output",expected),"observed_output":copy("observed_output",y),
        "trace":{n:copy("trace."+n,t) for n,t in tr.items()},
        "guards":{n:copy("guard."+n,t) for n,t in guards.items()},
        "inputs_after":{n:copy("inputs."+n,t) for n,t in x.items()},
        "pointers_before":ptr,"tiling_bytes":tiling,"copy_errors":errors,
        "dispatch_error":repr(primary) if primary else None}
    try:raw["pointers_after"]={n:t.data_ptr() for n,t in {**guards,**{"x."+n:t for n,t in x.items()}}.items()}
    except BaseException as e:raw["pointers_after"]=None;errors["pointers_after"]=repr(e)
    path=out/(label+"-"+mode+"-raw.pt")
    try:
        require(not path.exists(),"immutable new raw")
        torch.save(raw,path) # before parity/finite/guards; never overwrite failed raw
    except BaseException as e:
        print(json.dumps({"primary":repr(primary),"secondary_raw_save":repr(e)}),flush=True)
        if primary is not None:raise primary
        raise
    if primary is not None:raise primary
    require(not errors,"nullable raw incomplete; retained")
    bits=lambda a,b:old.bitwise(torch,a,b)
    unused=[s for s in range(19) if s not in ids]
    checks={"full19_state_bitwise":bits(raw["native_after"],raw["observed_after"]),
      "active12_output_bitwise":bits(raw["native_output"][:12],raw["observed_output"][:12]),
      "all_inputs_bitwise":all(bits(raw["inputs_after"][n],inputs[n]) for n in x),
      "all_guards_intact":all(bool(torch.all(t[:64]==7)) and bool(torch.all(t[-64:]==7)) for t in raw["guards"].values()),
      "pointers_unchanged":raw["pointers_before"]==raw["pointers_after"],
      "unused_state_bitwise":bits(raw["native_after"][unused],initial[unused]) and bits(raw["observed_after"][unused],initial[unused]),
      "selected12_state_bitwise":all(bits(raw["trace"]["selected"][token],raw["native_after"][slot]) for token,slot in enumerate(ids)),
      "inactive_trace_untouched":bool(torch.all(raw["trace"]["precast"][12:]==7)) and bool(torch.all(raw["trace"]["selected"][12:]==7)),
      "finite":all(bool(torch.isfinite(t).all()) for t in [raw["native_after"],raw["observed_after"],raw["native_output"][:12],
          raw["observed_output"][:12],*raw["trace"].values()])}
    require(tiling is not None and len(tiling)==72,"actual native tiling export")
    fields=list(struct.unpack("<8If8I",bytes(tiling[:68])))
    require(fields[1:8]==[16,4,128,12,128,19,16] and fields[14:17]==[1,0,0],"actual native fixture tiling")
    row={"mode":mode,"arm":label,"raw":{"path":str(path),"sha256":sha(path)},"checks":checks,
         "native_precast_v6":float(raw["trace"]["precast"][6,5,6]),"tiling_fields":fields,
         "native_bf16_bits_v6":int(raw["native_output"][6,5,6].view(torch.int16))&65535,
         "undefined_native_padding_not_compared":4,
         "cpu_cast_diagnostic_only":{"fp32_to_bf16_equals_native":bits(raw["trace"]["precast"][:12].to(torch.bfloat16),raw["native_output"][:12]),
           "not_an_instrumentation_or_original_numeric_gate":True}}
    return row,raw
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
    p.add_argument("--script-sha256");p.add_argument("--identity",type=Path);p.add_argument("--output-dir",type=Path)
    for n in ("trace-library","trace-build","trace-meta"):
        p.add_argument("--"+n,type=Path);p.add_argument("--"+n+"-sha256")
    a=p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"default_enabled":False,"npu_executed":False,"matrix_verified":False,
            "cases":4,"scope":"native source copy anchors and one same-incoming Vtile diagnostic"}));return
    require(all(vars(a).values()),"explicit source/artifact/identity Refs")
    require(sha(__file__)==a.script_sha256,"MAIN exact diagnostic code")
    refs={k:{"path":str(getattr(a,"trace_"+arg)),"sha256":getattr(a,"trace_"+arg+"_sha256")} for k,arg in
          (("library","library"),("build","build"),("meta","meta"))}
    m,s=nc.sources();nc.consume(refs,m,s)
    sys.path.insert(0,str(nc.PROJECT/"tools/split_gate_v2"));import contract
    ident=json.loads(a.identity.read_bytes());c,r,sm,ss=None,None,None,None
    r=ident["source_manifest"];sm,ss=contract.source_admission(r)
    contract.validate_identity(ident,16,6,r,sm,ss,ident["artifact_refs"])
    require(ident["trace_artifact_refs"]==refs and ident["diagnostic_script"]=={"path":str(Path(__file__).resolve()),"sha256":a.script_sha256}
      and ident["trace_source_manifest"]=={"path":str(nc.TOOLS/"SOURCE_MANIFEST_V3.json"),"sha256":nc.MANIFEST_SHA},
      "actual explicitly admitted native source/protocol")
    for path,digest in ident["complete_trace_sources"].items():require(sha(path)==digest,"full diagnostic source closure")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0" and os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0" and
      os.environ.get("PYTHONDONTWRITEBYTECODE")=="1","same one-device environment")
    cg=contract.legacy().cgroup_limit()
    require(sha(RAW)==RAW_SHA and RAW.stat().st_size==99004309,"immutable original failure")
    out=a.output_dir;require(out.parent==Path("/kvbuffer-results") and not out.exists(),"new exclusive output");out.mkdir()
    report={"schema":"kvbp.native-copy-trace-diagnostic/v1","status":"running","cases":[],
      "source_raw_sha256":RAW_SHA,"source_manifest_sha256":nc.MANIFEST_SHA,"sources_before":s,
      "artifact_refs":refs,"cgroup":cg,"identity_sha256":sha(a.identity),"npu_executed":False,
      "matrix_verified":False,"serving_ready":False,"e2e_verified":False,"accuracy_verified":False,"cause_proved":False}
    serial=0;primary=None
    def save():
        nonlocal serial
        serial+=1;return write(out/("report-%03d.json"%serial),report)
    save()
    try:
        import torch
        f=torch.load(RAW,map_location="cpu",weights_only=True);ids=fixture_metadata(f,torch)
        cand=torch.load(nc.CANDIDATE_RAW,map_location="cpu",weights_only=True)
        require(cand["schema"]=="kvbp.candidate-ub-trace-raw/v1" and cand["mode"]=="eager" and
          cand["source_raw_sha256"]==RAW_SHA and tuple(cand["trace"]["states"].shape)==(3,32,128) and
          cand["trace"]["meta"].tolist()==[6,5,4,15,0,1,1,1,1,1,1,16,19,0,0,0],"real copied candidate UB provenance")
        old=nc.module(OLD,OLD_SHA,"_native_copy_frozen_bits")
        require(all(old.bitwise(torch,f["inputs"][n],f["input_before"][n]) for n in f["inputs"]),"immutable original inputs")
        incoming=f["native_before"].clone();same=incoming.clone()
        same[4,5,:32].copy_(cand["trace"]["states"][0]) # ONLY actual candidate reconstructed selected Vtile
        torch.save({"incoming":incoming,"same_incoming_vtile":same,"inputs":f["inputs"],
          "candidate_trace_raw_sha256":nc.CANDIDATE_RAW_SHA,"source_raw_sha256":RAW_SHA},out/"before.pt")
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
        torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
        require(torch.npu.device_count()==1 and torch.npu.get_device_name(0)=="Ascend910B4","actual one910B4")
        require(enable_custom_op(),"actual native op bootstrap");init_device_properties_triton()
        require({path:sha(path) for path in contract.legacy().NATIVE_PINS}==contract.legacy().NATIVE_PINS,"deployed native code")
        h=nc.module(nc.PROJECT/"tools/split_gate_v2/oracle.py",sm["files"]["oracle.py"],"_native_copy_exact_oracle")
        h.torch=torch;h.torch_npu=torch_npu
        torch.ops.load_library(refs["library"]["path"]);ops=getattr(torch.ops,nc.NS)
        report["mapped_libraries"]=mapped({NATIVE:NATIVE_SHA,refs["library"]["path"]:refs["library"]["sha256"]})
        write(out/"attribution-ready.json",{"pid":os.getpid(),"hold_seconds":12,"numerical_matrix_verified":False})
        time.sleep(12)
        report["npu_executed"]=True;save()
        evidence={}
        for label,initial in (("native-before",incoming),("same-candidate-vtile",same)):
            for mode in ("eager","graph"):
                row,raw=observe(torch,h,old,ops,initial,f["inputs"],out,mode,label,ids)
                report["cases"].append(row);save()
                require(all(row["checks"].values()),"native trace instrumentation did not anchor; STOP with raw")
                if label=="native-before":
                    row["saved_native_state_bitwise"]=old.bitwise(torch,raw["native_after"],f["native"])
                    row["saved_native_active_output_bitwise"]=old.bitwise(torch,raw["native_output"][:12],f["expected"][:12])
                    save();require(row["saved_native_state_bitwise"] and row["saved_native_active_output_bitwise"],"deployed native original golden changed")
                evidence[(label,mode)]=raw
        report["mode_anchor_bitwise"]={label:all(old.bitwise(torch,evidence[(label,"eager")][n],evidence[(label,"graph")][n]) for n in
           ("native_after","observed_after")) and all(old.bitwise(torch,evidence[(label,"eager")]["trace"][n],
           evidence[(label,"graph")]["trace"][n]) for n in ("precast","selected")) for label in ("native-before","same-candidate-vtile")}
        save();require(all(report["mode_anchor_bitwise"].values()),"native copy eager/graph differ")
        report["actual_candidate_precast_v6"]=float(cand["trace"]["output"][6])
        report["native_before_precast_v6"]=float(evidence[("native-before","eager")]["trace"]["precast"][6,5,6])
        report["same_candidate_vtile_native_precast_v6"]=float(evidence[("same-candidate-vtile","eager")]["trace"]["precast"][6,5,6])
        report["rounding_midpoint_v6"]=0.0039825439453125
        report["status"]="anchored-native-copy-observation-only"
    except BaseException as e:primary=e;report.update(status="failed",original_error=repr(e));raise
    finally:
        try:
            _,after=nc.sources();report["sources_after"]=after
            require(after==s and sha(RAW)==RAW_SHA,"source/raw drift")
            for path,digest in ident["complete_trace_sources"].items():require(sha(path)==digest,"full diagnostic source closure drift")
            print("MAIN_KVBUFFER_NATIVE_COPY "+json.dumps(save()),flush=True)
        except BaseException as e:
            if primary is None:raise
            print(json.dumps({"primary":repr(primary),"secondary_finalize":repr(e)}),flush=True)
if __name__=="__main__":main()
