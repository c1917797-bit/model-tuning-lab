#!/usr/bin/env python3
"""ONE saved valid step45 on two independent arenas; diagnostic, not a new gate."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import torch

HERE = Path(__file__).resolve().parent
TESTS = HERE.parents[1]/"tests"
sys.path.insert(0, str(TESTS))
from independent_oracle import (OracleLayout, ValueMajorPacked, errors, f32_bits,
    pack_value_major, restore_state, scalar_div_f32)
FIELD_NAMES = ("high", "low", "scales")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def finite_json(value):
    if isinstance(value, dict): return {str(k): finite_json(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [finite_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    return value

def cpu(tensor):
    return tensor.detach().cpu().contiguous()

def exact(a, b):
    a,b=cpu(a),cpu(b)
    return a.shape==b.shape and a.dtype==b.dtype and torch.equal(a.view(torch.uint8),b.view(torch.uint8))

def packed_dict(p):
    return {n:cpu(getattr(p,n)) for n in FIELD_NAMES}

def packed(d):
    if set(d)!=set(FIELD_NAMES): raise ValueError("unexpected packed fields")
    return ValueMajorPacked(*(d[n] for n in FIELD_NAMES))

def subset(p, ids):
    return ValueMajorPacked(*(getattr(p,n).index_select(0,ids) for n in FIELD_NAMES))

def summary(a,b):
    d={}
    for n in FIELD_NAMES:
        x,y=getattr(a,n),getattr(b,n)
        if x.shape!=y.shape or x.dtype!=y.dtype: raise ValueError("packed ABI changed")
        d[n]={"bitwise":exact(x,y),"numeric_differences":int((x!=y).sum()),
              "max_absolute":float((x.double()-y.double()).abs().max())}
    return d

def all_exact(d):
    return all(x["bitwise"] for x in d.values())

def loaded_libraries():
    paths=set()
    for line in Path("/proc/self/maps").read_text().splitlines():
        item=line.split()[-1]
        if item.startswith("/") and ".so" in item and Path(item).is_file():
            paths.add(item)
    return [{"path":p,"sha256":sha(p)} for p in sorted(paths)]

def checked_file(p, expected):
    if not p.is_absolute() or not p.is_file() or sha(p)!=expected:
        raise ValueError("frozen absolute input identity mismatch: "+str(p))

def nd(t, device):
    # Explicit test-side preparation, not a wrapper's silent format conversion.
    return torch_npu.npu_format_cast(t.to(device).contiguous(), 2)

def audit_fixture(f, source):
    # Frozen gate saves variant as int0 and does not save constant lengths.
    # Source-bound reconstruction is [0] + [1]*B, exactly candidate_setup().
    gate=TESTS/"restricted_native_golden_gate.py"
    if sha(gate)!=source["source_hashes"]["restricted_native_golden_gate.py"]:
        raise ValueError("frozen metadata recipe source changed")
    expected={"q":((1,4,128),torch.bfloat16),"k":((1,4,128),torch.bfloat16),
              "v":((1,12,128),torch.bfloat16),"g":((1,12),torch.float32),
              "beta":((1,12),torch.bfloat16),"indices":((1,),torch.int32)}
    for n,(shape,dtype) in expected.items():
        if tuple(f[n].shape)!=shape or f[n].dtype!=dtype or f[n].device.type!="cpu":
            raise ValueError("frozen CPU input ABI changed: "+n)
        if not bool(torch.isfinite(f[n].float()).all()):
            raise ValueError("nonfinite frozen input: "+n)
    if f["indices"].min()<0 or f["indices"].max()>=4:
        raise ValueError("frozen selected slot outside B1+3 slots")
    for side in ("actual_before","golden_before","actual_after","golden_after"):
        p=packed(f[side])
        for n,shape,dtype in (("high",(4,12,128,16),torch.float16),
                             ("low",(4,12,128,112),torch.int8),
                             ("scales",(4,12,4,112),torch.float32)):
            x=getattr(p,n)
            if tuple(x.shape)!=shape or x.dtype!=dtype or not bool(torch.isfinite(x.float()).all()):
                raise ValueError("frozen packed state ABI changed: "+side+"/"+n)
    if not bool((f["layout"]["c"]==1).all()):
        raise ValueError("fixture is not identity SR")
    native=f["native_evidence"]["native_updated_selected_fp32"]
    if native.shape!=(1,12,128,128) or native.dtype!=torch.float32 or not bool(torch.isfinite(native).all()):
        raise ValueError("frozen native updated ABI changed")
    ld=f["layout"]
    layout=OracleLayout(ld["c"],ld["pv"],ld["pk"],ld["khi"],ld["group"])
    selected=pack_value_major(native,layout)
    ids=f["indices"].long()
    if not all_exact(summary(selected,subset(packed(f["golden_after"]),ids))):
        raise ValueError("native updated does not independently repack to saved golden")
    if not all_exact(summary(packed(f["actual_before"]),packed(f["golden_before"]))):
        raise ValueError("saved before differs")
    if not exact(f["actual_output"],f["native_evidence"]["original_output_bf16"]):
        raise ValueError("saved output not exact as pre-registered")
    return {"status":"PASS","fixture_variant_code":0,"variant_semantics":"identity",
            "metadata_recipe":"[0]+[1]*B INT32, pinned original candidate_setup()",
            "metadata_recipe_source_sha256":sha(gate),
            "lengths":[0,1],"selected_slots":f["indices"].tolist(),
            "independent_native_repack_exact":True}

def check_preflight(proof):
    physical=proof.get("physical_npu_ids",[])
    mapping=proof.get("logical_to_physical",{})
    observed=proof.get("observed_at_unix_ns",0)
    if (not physical or any(x not in (4,5,6,7) for x in physical) or
        mapping.get("0")!=4 or any(x not in physical for x in mapping.values()) or
        proof.get("privileged") is not False or
        proof.get("exclusive_resource_check_passed") is not True or
        not 0<=time.time_ns()-observed<=1800*10**9):
        raise ValueError("fresh physical4->logical0, nonprivileged/exclusive proof required")

def native_boundary(updated, scales, row, h, v, lk):
    x=float(updated[row,h,v,lk+16])
    s=float(scales[row,h,v//32,lk])
    q=scalar_div_f32(x,s)
    return {"x":x,"x_bits":hex(f32_bits(x)),"scale":s,"scale_bits":hex(f32_bits(s)),
            "ieee_rne_fp32_quotient":q,"quotient_bits":hex(f32_bits(q)),
            "rne_clipped_code":max(-127,min(127,round(q)))}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for field in ("fixture","source-report","oracle","production-library","trace-library","preflight-receipt"):
        p.add_argument("--"+field,type=Path,required=True)
        p.add_argument("--"+field+"-sha256",required=True)
    p.add_argument("--logical-device",type=int,required=True)
    p.add_argument("--physical-device",type=int,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--audit-only",action="store_true",
                   help="CPU frozen-fixture/source contract only; no torch_npu/library/NPU load")
    args=p.parse_args()
    out=args.output_dir.resolve()
    repo=HERE.parents[3]
    if out.exists() or out==repo or repo in out.parents:
        p.error("require NEW output root outside repository")
    if args.physical_device!=4 or args.logical_device!=0:
        p.error("this single-card diagnostic is restricted to physical4 -> logical0")
    try:
        for field in ("fixture","source_report","oracle","production_library","trace_library","preflight_receipt"):
            checked_file(getattr(args,field),getattr(args,field+"_sha256"))
        if args.oracle.resolve()!=(TESTS/"independent_oracle.py").resolve():
            raise ValueError("wrong independently authored oracle location")
    except Exception as exc:
        p.error(str(exc))
    out.mkdir(parents=True)
    result={"schema":"damp-native-failure-npu-single-trace/v1","status":"RUNNING",
        "created_ns":time.time_ns(),"script_sha256":sha(__file__),
        "scope":"one immutable saved-valid-fixture attribution only; not a closed-loop "
                "PASS, generalSR, graph, serving, calibration, performance or quality result",
        "mapping":{"physical":args.physical_device,"logical":args.logical_device,
                   "proof_scope":"hashed parent preflight, not inferred from Torch logical ordinal"},
        "input_hashes":{f:getattr(args,f+"_sha256") for f in
            ("fixture","source_report","oracle","production_library","trace_library","preflight_receipt")}}
    artifacts={}
    def save():
        (out/"report.json").write_text(json.dumps(finite_json(result),indent=2,allow_nan=False)+"\n")
    save()
    try:
        source=json.loads(args.source_report.read_text())
        if source.get("schema")!="damp-restricted-native-compressed-golden/v1":
            raise ValueError("source gate schema mismatch")
        if source.get("first_failure_fixture",{}).get("sha256")!=args.fixture_sha256:
            raise ValueError("report does not bind fixture")
        if source.get("source_hashes",{}).get("independent_oracle.py")!=args.oracle_sha256:
            raise ValueError("independent oracle differs from saved gate")
        f=torch.load(args.fixture,map_location="cpu",weights_only=True)
        if f.get("stage")!="closed_loop" or f.get("batch")!=1 or f.get("step")!=45 or f.get("variant")!=0:
            raise ValueError("not the frozen restricted B1 identity step45 fixture")
        if args.fixture_sha256!="59795deab9d00328df79dfeeefa08ff6d917f455bfe9d7565d0fd9c3cbf70598":
            raise ValueError("this diagnostic was pre-registered for one exact fixture")
        if args.production_library_sha256!="22f522cf5befcf6afa12560dd2624fd6ddb1c99cc8d9bf04a4b08502363b3937":
            raise ValueError("must replay exact production v4")
        result["source_gate_status"]=source["status"]
        result["source_native_manifest"]=source.get("native_source_manifest")
        result["parent_preflight"]=json.loads(args.preflight_receipt.read_text())
        check=subprocess.run([sys.executable,str(HERE/"check_source_parity.py")],
                              capture_output=True,text=True,check=False)
        result["source_parity_command"]={"returncode":check.returncode,"stderr":check.stderr}
        if check.returncode: raise ValueError("production/trace source parity check failed")
        result["source_parity"]=json.loads(check.stdout)
        torch.set_num_threads(1)
        result["cpu_fixture_audit"]=audit_fixture(f,source)
        if args.audit_only:
            result["status"]="CPU_FIXTURE_AUDIT_PASS"
            result["scope"]="CPU-only exact saved-fixture/source contract; no NPU or algorithm acceptance"
            save()
            print(json.dumps({"status":result["status"],"report":str(out/"report.json")}))
            return 0
        check_preflight(result["parent_preflight"])
        global torch_npu
        import torch_npu
        torch.npu.set_device(args.logical_device)
        device=torch.device("npu:"+str(args.logical_device))
        result["runtime"]={"torch":torch.__version__,"torch_npu":torch_npu.__version__,
            "device_name":torch.npu.get_device_name(device),
            "ascend_rt_visible_devices":os.environ.get("ASCEND_RT_VISIBLE_DEVICES"),
            "pid":os.getpid()}
        torch.ops.load_library(str(args.production_library.resolve()))
        torch.ops.load_library(str(args.trace_library.resolve()))
        result["schemas"]={"production_prepare":str(torch.ops.qwen36_damp.prepare.default._schema),
            "production_decode":str(torch.ops.qwen36_damp.decode.default._schema),
            "trace_prepare":str(torch.ops.qwen36_damp_trace.prepare.default._schema),
            "trace_decode":str(torch.ops.qwen36_damp_trace.decode_trace.default._schema)}
        for schema in (torch.ops.qwen36_damp.decode.default._schema,
                       torch.ops.qwen36_damp_trace.decode_trace.default._schema):
            writes=[i for i,a in enumerate(schema.arguments) if a.alias_info and a.alias_info.is_write]
            if len(schema.arguments)!=14 or writes!=[5,6,7] or any(x.alias_info for x in schema.returns):
                raise ValueError("decode argument count/state aliases/output alias changed")
        for schema in (torch.ops.qwen36_damp.prepare.default._schema,
                       torch.ops.qwen36_damp_trace.prepare.default._schema):
            if len(schema.arguments)!=6 or len(schema.returns)!=0:
                raise ValueError("prepare schema changed")
        trace_schema=torch.ops.qwen36_damp_trace.decode_trace.default._schema
        if len(trace_schema.returns)!=3:
            raise ValueError("trace must return output, updated, quotient")
        result["loaded_libraries"]=loaded_libraries()
        mapped={x["path"]:x["sha256"] for x in result["loaded_libraries"]}
        for path,expected in ((args.production_library,args.production_library_sha256),
                              (args.trace_library,args.trace_library_sha256)):
            if mapped.get(str(path.resolve()))!=expected:
                raise ValueError("expected actual loaded .so not found with exact hash")
        ld=f["layout"]
        layout=OracleLayout(ld["c"],ld["pv"],ld["pk"],ld["khi"],ld["group"])
        gb,ab=packed(f["golden_before"]),packed(f["actual_before"])
        aa=packed(f["actual_after"])
        ids=f["indices"].long()
        result["same_before"]=summary(ab,gb)
        if not all_exact(result["same_before"]):
            raise ValueError("saved before arenas differ; trace attribution disallowed")
        # The oracle plan uses logical indices; INT32 ABI conversion is explicit.
        pk=ld["pk"].to(torch.int32).contiguous()
        pv=ld["pv"].to(torch.int32).contiguous()
        inv=torch.argsort(ld["pv"].long(),dim=-1).to(torch.int32).contiguous()
        c=ld["c"]
        if c.dtype!=torch.float32 or not bool((c==1).all()):
            raise ValueError("restricted identity SR changed")
        plans=[nd(x,device) for x in (pk,pv,inv,c)]
        q,k,v,g,beta=[nd(f[n],device) for n in ("q","k","v","g","beta")]
        lengths=nd(torch.tensor([0]+[1]*f["batch"],dtype=torch.int32),device)
        indices=nd(f["indices"],device)
        if lengths.dtype!=torch.int32 or indices.dtype!=torch.int32:
            raise ValueError("dynamic metadata dtype changed")
        immutable=[q,k,v,g,beta,*plans,lengths,indices]
        immutable_before=[cpu(x).clone() for x in immutable]
        immutable_ptr=[x.data_ptr() for x in immutable]
        def arena():
            return ValueMajorPacked(*(nd(getattr(ab,n).clone(),device) for n in FIELD_NAMES))
        prod,traced=arena(),arena()
        prod_ptr=[getattr(prod,n).data_ptr() for n in FIELD_NAMES]
        trace_ptr=[getattr(traced,n).data_ptr() for n in FIELD_NAMES]
        all_npu=immutable+[getattr(x,n) for x in (prod,traced) for n in FIELD_NAMES]
        result["nd_formats_before"]=[int(torch_npu.get_npu_format(x)) for x in all_npu]
        if any(x!=2 for x in result["nd_formats_before"]):
            raise ValueError("test tensors not physical ND")
        torch.ops.qwen36_damp.prepare(q,prod.high,*plans)
        torch.ops.qwen36_damp_trace.prepare(q,traced.high,*plans)
        prod_out=torch.ops.qwen36_damp.decode(q,k,v,g,beta,prod.high,prod.low,prod.scales,
                                            *plans,lengths,indices)
        trace_out,updated,quotient=torch.ops.qwen36_damp_trace.decode_trace(
            q,k,v,g,beta,traced.high,traced.low,traced.scales,*plans,lengths,indices)
        torch.npu.synchronize()
        pp=ValueMajorPacked(*(cpu(getattr(prod,n)) for n in FIELD_NAMES))
        tp=ValueMajorPacked(*(cpu(getattr(traced,n)) for n in FIELD_NAMES))
        po,to,up,qu=[cpu(x) for x in (prod_out,trace_out,updated,quotient)]
        artifacts={"production_after":packed_dict(pp),"trace_after":packed_dict(tp),
                   "production_output":po,"trace_output":to,"updated_trace":up,
                   "quotient_trace":qu}
        result["production_vs_saved_actual"]=summary(pp,aa)
        result["production_output_vs_saved_actual_bitwise"]=exact(po,f["actual_output"])
        result["trace_vs_production"]=summary(tp,pp)
        result["trace_output_vs_production_bitwise"]=exact(to,po)
        untouched=torch.tensor([i for i in range(ab.high.shape[0]) if i not in ids.tolist()],dtype=torch.long)
        result["production_untouched"]=summary(subset(pp,untouched),subset(ab,untouched))
        result["trace_untouched"]=summary(subset(tp,untouched),subset(ab,untouched))
        result["immutable_bitwise"]=all(exact(x,y) for x,y in zip(immutable,immutable_before))
        result["immutable_pointers_unchanged"]=[x.data_ptr() for x in immutable]==immutable_ptr
        result["state_pointers_unchanged"]=all([getattr(a,n).data_ptr() for n in FIELD_NAMES]==ptrs
                                               for a,ptrs in ((prod,prod_ptr),(traced,trace_ptr)))
        result["nd_formats_after"]=[int(torch_npu.get_npu_format(x)) for x in all_npu+[updated,quotient]]
        if up.shape!=(1,12,128,128) or qu.shape!=(1,12,128,112) or up.dtype!=torch.float32 or qu.dtype!=torch.float32:
            raise ValueError("trace ABI changed")
        result["trace_fields_finite"]=bool(torch.isfinite(up).all() and torch.isfinite(qu).all())
        result["attribution_ready"]=(all_exact(result["production_vs_saved_actual"]) and
            result["production_output_vs_saved_actual_bitwise"] and
            all_exact(result["trace_vs_production"]) and result["trace_output_vs_production_bitwise"] and
            all_exact(result["production_untouched"]) and all_exact(result["trace_untouched"]) and
            result["immutable_bitwise"] and result["immutable_pointers_unchanged"] and
            result["state_pointers_unchanged"] and result["trace_fields_finite"] and
            all(x==2 for x in result["nd_formats_after"]))
        if not result["attribution_ready"]:
            raise ValueError("trace changed production or a guard; attribution disallowed")
        native=f["native_evidence"]["native_updated_selected_fp32"]
        if native.shape!=up.shape or native.dtype!=torch.float32:
            raise ValueError("saved native FP32 ABI changed")
        result["updated_vs_native"]={"bitwise":exact(up,native),
            "differences":int((up.view(torch.int32)!=native.view(torch.int32)).sum()),
            "transformed_metrics":errors(up,native),
            "original_coordinate_metrics":errors(restore_state(up,layout),restore_state(native,layout))}
        independent_pack=pack_value_major(up,layout)
        result["independent_updated_repack_vs_trace"]=summary(independent_pack,subset(tp,ids))
        quantizer=torch.round(qu).clamp(-127,127).to(torch.int8)
        result["traced_quotient_rne_clamp_vs_codes_bitwise"]=exact(quantizer,subset(tp,ids).low)
        changes=(subset(tp,ids).low!=subset(packed(f["golden_after"]),ids).low).nonzero(as_tuple=False)
        result["native_golden_low_code_differences"]=len(changes)
        boundaries=[]
        selected_scale=subset(tp,ids).scales
        native_scale=subset(packed(f["golden_after"]),ids).scales
        for row,h,vv,lk in changes[:64].tolist():
            details={"indices":[row,h,vv,lk],"original_V":int(layout.pv[h,vv]),
                "original_K":int(layout.pk[h,lk+16]),"trace_updated":native_boundary(up,selected_scale,row,h,vv,lk),
                "native_updated":native_boundary(native,native_scale,row,h,vv,lk),
                "actual_npu_quotient":float(qu[row,h,vv,lk]),
                "actual_npu_quotient_bits":hex(f32_bits(float(qu[row,h,vv,lk]))),
                "trace_code":int(tp.low[int(ids[row]),h,vv,lk]),
                "native_golden_code":int(f["golden_after"]["low"][int(ids[row]),h,vv,lk])}
            details["quotient_matches_ieee_on_trace_updated"]=(
                details["actual_npu_quotient_bits"]==details["trace_updated"]["quotient_bits"])
            boundaries.append(details)
        result["boundaries"]=boundaries
        torch.save(artifacts,out/"trace_evidence.pt")
        result["trace_evidence"]={"path":str(out/"trace_evidence.pt"),"sha256":sha(out/"trace_evidence.pt")}
        result["status"]="PASS"
        result["interpretation"]="diagnostic identity/guards passed; inspect actual updated and quotient evidence; original numerical gate not overturned"
        save()
        print(json.dumps(finite_json({"status":result["status"],"report":str(out/"report.json"),
              "updated_vs_native":result["updated_vs_native"],"boundaries":boundaries}),allow_nan=False))
        return 0
    except Exception as exc:
        result["status"]="FAIL"
        result["error"]={"type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
        try:
            torch.save(artifacts,out/"first_failure.pt")
            result["first_failure"]={"path":str(out/"first_failure.pt"),"sha256":sha(out/"first_failure.pt")}
        except Exception as saving:
            result["failure_save_error"]={"type":type(saving).__name__,"message":str(saving)}
        try: save()
        except Exception as saving:
            print(json.dumps({"status":"FAIL","report_save_error":str(saving)},allow_nan=False),file=sys.stderr)
        print(json.dumps({"status":"FAIL","error":str(exc),"report":str(out/"report.json")},allow_nan=False))
        return 1

if __name__=="__main__":
    raise SystemExit(main())
