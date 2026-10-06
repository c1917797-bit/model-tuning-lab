#!/usr/bin/env python3
"""Opt-in selected-slot packing gate. MAIN alone may load/execute on NPU4-7."""
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from selected_contract import (NAMESPACE,SELECTED_MANIFEST_SHA,SELECTED_BUILD_SHA,SELECTED_SO_SHA,
    IMAGE,OPP_SHA,COMPILED,LIMITS,REFERENCE,require,sha,bound_json,check_sources,
    validate_build,validate_proof,status_rows,selection,require_decode_admission,
    ALL_BATCH_BUILD_SHA,ALL_BATCH_SO_SHA,ALL_BATCH_MANIFEST_SHA,validate_anchor)

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[5]
PROJECT=REPO/"projects/damp-ascend"

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--stage",choices=("isolated","native_feedback"),default="isolated")
    p.add_argument("--physical-card",type=int,choices=(4,5,6,7),default=4)
    p.add_argument("--preflight",type=Path)
    p.add_argument("--build-receipt",type=Path)
    p.add_argument("--library",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--runtime-manifest",type=Path,default=HERE/"RUNTIME_MANIFEST.json")
    p.add_argument("--runtime-manifest-sha256")
    p.add_argument("--batches",type=int,nargs="+",default=[1,16])
    p.add_argument("--decode-build-receipt",type=Path)
    p.add_argument("--decode-library",type=Path)
    p.add_argument("--decode-library-sha256")
    p.add_argument("--native-anchor-report",type=Path)
    p.add_argument("--reference-library",type=Path)
    p.add_argument("--reference-library-sha256")
    return p

def admission(args):
    require(args.runtime_manifest_sha256 is not None,"external runtime manifest authority required")
    runtime=bound_json(args.runtime_manifest,args.runtime_manifest_sha256)
    require(runtime.get("schema")=="damp-selected-prefill-gate-runtime/v1","runtime schema")
    require(runtime.get("default_enabled") is False,"default OFF")
    check_sources(REPO,runtime["sources"])
    check_sources(REPO,runtime["dependencies"])
    build=validate_build(bound_json(args.build_receipt,SELECTED_BUILD_SHA))
    source=bound_json(HERE.parent/"source_manifest.json",SELECTED_MANIFEST_SHA)
    require(source["compiled_sources"]==COMPILED,"selected manifest/source")
    require(args.library.name=="libqwen36_damp_selected_prefill_v1_ops.so" and
            sha(args.library)==SELECTED_SO_SHA,"explicit selected registration SO")
    for row in build["commands"]:
        require(sha(row["log_path"])==row["log_sha256"],"raw actual build log binding")
    require(sha(build["exported_kernel"]["audit_path"])==build["exported_kernel"]["audit_sha256"],
            "actual exported host symbol audit")
    require(sha(build["cann_identity"]["opp_version_info_path"])==OPP_SHA,"actual runtime OPP9.1")
    proof=json.loads(args.preflight.read_text())
    validate_proof(proof,args.physical_card)
    if args.stage=="native_feedback":
        require(all(getattr(args,name) is not None for name in ("decode_build_receipt","decode_library",
                "decode_library_sha256","native_anchor_report","reference_library","reference_library_sha256")),
                "native authorities must be complete BEFORE Torch/device/load")
        require(set(args.batches)<=set((1,16)), "native feedback actual B1/B16 only")
        decode=bound_json(args.decode_build_receipt,ALL_BATCH_BUILD_SHA)
        decode_manifest=bound_json(PROJECT/"operator/all_batch_wrapper_v3/source_manifest.json",ALL_BATCH_MANIFEST_SHA)
        require_decode_admission(decode,decode_manifest,args.decode_library_sha256)
        require(args.decode_library.name=="libqwen36_gdn_damp_all_batch_v3_decode_ops.so" and
                sha(args.decode_library)==ALL_BATCH_SO_SHA, "actual decode registration SO")
        for row in decode["commands"]:
            require(sha(row["log_path"])==row["log_sha256"],"allbatch actual raw log")
        require(sha(decode["exported_kernel"]["audit_path"])==decode["exported_kernel"]["audit_sha256"],
                "allbatch actual symbol audit")
        anchor=bound_json(args.native_anchor_report,
            "d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8")
        native=validate_anchor(anchor)
        require(args.reference_library_sha256==native["reference_library_sha256"] and
                sha(args.reference_library)==native["reference_library_sha256"] and
                sha(native["native_runtime_library_path"])==native["native_runtime_library_sha256"],
                "actual independent/native binaries before any acquisition")
        for path,digest in runtime["actual_image_sources"].items():
            require(Path(path).is_file() and sha(path)==digest,"actual-image native direct-import source: "+path)
    require(1<=len(args.batches)<=16 and len(set(args.batches))==len(args.batches) and
            all(1<=b<=16 for b in args.batches),"actual unique P1..16 matrix")
    return {"sources":runtime["sources"],"dependencies":runtime["dependencies"],
            "runtime_manifest":{"path":str(args.runtime_manifest),"sha256":sha(args.runtime_manifest)},
            "compiled_sources":COMPILED,"build_receipt":{"path":str(args.build_receipt),
              "sha256":sha(args.build_receipt)},"library":{"path":str(args.library),"sha256":SELECTED_SO_SHA},
            "image_id":IMAGE,"device_proof":proof,"opp_version_info_sha256":OPP_SHA}

def loaded(path):
    wanted=str(path.resolve())
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields=line.split()
        if fields and fields[-1].startswith("/") and Path(fields[-1]).is_file():
            if str(Path(fields[-1]).resolve())==wanted: return sha(wanted)
    return None

def schema(torch,ops):
    names=["dense","hi","lo","scales","pk","pv","sr","indices","use_float_candidate"]
    pack,prepare=ops.pack.default._schema,ops.prepare.default._schema
    require([a.name for a in pack.arguments]==names and
            [a.name for a in prepare.arguments]==names,"actual selected schema")
    require([i for i,a in enumerate(pack.arguments) if a.alias_info and a.alias_info.is_write]==[1,2,3]
            and len(pack.returns)==1 and pack.returns[0].alias_info is None and
            not prepare.returns and not any(a.alias_info for a in prepare.arguments),
            "only three mutable regions/fresh complete status/void prepare")
    require(pack.arguments[-1].default_value is False,"float candidate default OFF")
    return {"pack":str(pack),"prepare":str(prepare)}

def pack_once(torch,npu,gate,ops,arena,dense,plans,indices,golden,label,error=0):
    from evidence import observe,exact
    from packing_oracle import pack,selected_update
    plan,devplans=plans
    # Entire CPU inputs and independently computed expected state precede dispatch.
    cpu_dense=dense.cpu().clone();cpu_indices=indices.cpu().clone()
    if error==0:
        expected=pack(torch,importlib.import_module("independent_oracle"),cpu_dense,plan)
        selected_update(golden,expected,cpu_indices)
    before=arena.raw.cpu().clone()
    gate.fixture={"label":label,"dense":cpu_dense,"indices":cpu_indices,
                  "plan":{"sr":plan.c,"pk":plan.pk,"pv":plan.pv},
                  "raw_before":before,"expected_raw":arena.expected_raw(before,golden)}
    args=[dense,*arena.states,*devplans,indices,False]
    out,cpu_out,after,record=observe(torch,gate,label,lambda:ops.pack(*args),args[:-1]+[arena.raw])
    gate.healthy(record,label+"_dispatch_and_nullable_D2H")
    require(cpu_out is not None,"full status required before feedback")
    rows=status_rows(cpu_out.tolist(),dense.shape[0],error)
    require(out.dtype==torch.int32 and npu.get_npu_format(out)==2 and out.data_ptr()%32==0,
            "physical ND32 full status")
    def interval(x):
        return (x.data_ptr(),x.data_ptr()+x.numel()*x.element_size())
    a,b=interval(out)
    gate.check(label+"_status_fresh_nonalias",all(b<=interval(x)[0] or interval(x)[1]<=a for x in args[:-1]+[arena.raw]))
    immutable=[0,4,5,6,7] # dense, Pk, Pv, SR, dynamic selections
    guards={"immutable_inputs_bitwise":all(exact(torch,record["before"][i],after[i]) for i in immutable),
            "all_input_pointer_offset_stride_stable":record["pointers_before"]==record["pointers_after"]}
    raw_after=after[-1]
    guards["conv_FA_guard_padding_untouched_slots_bitwise"]=arena.outside_selected(before,raw_after,cpu_indices)
    if error in (0,1):
        guards.update(arena.observe(raw_after,before,golden))
    else:
        # Earlier successful groups/tasks may have written. Retire ALL slots,
        # not only the head/group reporting an error; NEVER feed back/retry.
        guards["all_selected_slots_retired"]=True
        gate.report.setdefault("retired_calls",[]).append({"label":label,"slots":cpu_indices.tolist(),
                                                         "retry_allowed":False,"whole_call":True})
    gate.fixture.update(status_raw=cpu_out,raw_after=raw_after,status_rows=rows)
    if error: gate.retain("negative_"+label)
    gate.check(label+"_full_raw_inputs_status",all(guards.values()),guards)
    case={"label":label,"p":dense.shape[0],"indices":cpu_indices.tolist(),"status_rows":rows,
          "guards":guards,"passed":True,"fixture_origin":"CPU-FP32-isolated-not-native",
          "raw_after_sha256":__import__("hashlib").sha256(raw_after.numpy().tobytes()).hexdigest()}
    gate.report["cases"].append(case);gate.save()
    return out

def host_negative(torch,npu,nd,ops,gate,arena,args):
    from evidence import observe,exact
    negatives=[]
    for index in range(8):
        bad=list(args)
        bad[index]=nd(args[index].float()) if args[index].dtype!=torch.float32 else nd(args[index].half())
        negatives.append(("dtype"+str(index),bad))
    for index in range(8):
        bad=list(args)
        target=args[index]
        shape=list(target.shape);shape[-1]-=1
        bad[index]=nd(torch.zeros(shape,dtype=target.dtype))
        negatives.append(("shape"+str(index),bad))
    for p in (0,17):
        bad=list(args);bad[0]=nd(torch.zeros((p,12,128,128),dtype=torch.float32))
        bad[7]=nd(torch.zeros(p,dtype=torch.int32))
        negatives.append(("P"+str(p),bad))
    for index in (0,4,5,6,7):
        bad=list(args)
        target=args[index];expanded=list(target.shape);expanded[-1]*=2
        base=nd(torch.zeros(expanded,dtype=target.dtype))
        bad[index]=base[...,::2]
        negatives.append(("noncontiguous"+str(index),bad))
    bad=list(args);base=nd(torch.zeros(args[7].numel()+8,dtype=torch.int32))
    bad[7]=base[1:1+args[7].numel()];negatives.append(("offset4B",bad))
    bad=list(args);bad[0]=args[0].cpu();negatives.append(("CPU",bad))
    bad=list(args);bad[5]=args[4];negatives.append(("readonly_plan_alias",bad))
    for plan_index,name in ((4,"Pk"),(5,"Pv")):
        bad=list(args);cpu=args[plan_index].cpu().clone();cpu[0,0]=cpu[0,1]
        bad[plan_index]=nd(cpu);negatives.append((name+"duplicate",bad))
    for value,name in ((0.0,"SRzero"),(-1.0,"SRnegative"),(float("nan"),"SRNaN")):
        bad=list(args);cpu=args[6].cpu().clone();cpu[0,0]=value
        bad[6]=nd(cpu);negatives.append((name,bad))
    for name,bad in negatives:
        # static plan value errors are prepare-only: pack without valid prepare
        # rejects missing key, not a claimed value validator.
        methods=("prepare",) if name in ("Pkduplicate","Pvduplicate","SRzero","SRnegative","SRNaN") else ("prepare","pack")
        for method in methods:
            label="host_"+name+"_"+method
            gate.fixture={"stage":"host_negative","label":label}
            tensors=bad[:-1]+[arena.raw]
            _,_,after,record=observe(torch,gate,label,lambda:getattr(ops,method)(*bad),tensors)
            gate.retain("negative_"+label) # original exception + nullable copies BEFORE assertions
            passed=(record["dispatch_error"] is not None and
                not record["output_copy_errors"] and not record["input_copy_errors"] and
                record["pointers_before"]==record["pointers_after"] and
                all(exact(torch,a,b) for a,b in zip(record["before"],after)))
            gate.check(label+"_rejected_all_inputs_raw_unchanged",passed,{"dispatch_error":record["dispatch_error"]})
            gate.report.setdefault("host_negatives",[]).append({"label":label,"passed":passed})

def isolated(torch,npu,nd,ops,gate,batches):
    from arena import Arena
    from evidence import observe,exact
    from packing_oracle import layout,seed,fixture
    independent=importlib.import_module("independent_oracle")
    for p in batches:
        plan=layout(torch,independent,True);s=p+3
        devplans=[nd(x) for x in (plan.pk,plan.pv,plan.c)]
        for kind in ("adjacent","guard_gaps"):
            golden=seed(torch,independent,s,plan)
            arena=Arena(torch,npu,nd,s,kind,golden)
            dense=nd(fixture(torch,p,0));indices=nd(torch.tensor(selection(p,s),dtype=torch.int32))
            args=[dense,*arena.states,*devplans,indices,False]
            gate.fixture={"stage":"cold_prepare","p":p,"layout":kind}
            _,_,_,record=observe(torch,gate,"prepare",lambda:ops.prepare(*args),args[:-1]+[arena.raw])
            gate.healthy(record,"prepare_dispatch")
            gate.check("prepare_all_inputs_full_raw_unchanged",
                record["returns"] is None and record["pointers_before"]==record["pointers_after"] and
                all(exact(torch,a,b) for a,b in zip(record["before"],record["after"])))
            if p==1 and kind=="adjacent":host_negative(torch,npu,nd,ops,gate,arena,args)
            repeats=20 if p in (1,16) else 1
            pointers=(dense.data_ptr(),indices.data_ptr())
            for turn in range(repeats):
                cpu=fixture(torch,p,turn)
                ix=torch.tensor(selection(p,s,turn),dtype=torch.int32)
                # SAME live buffers, changed values and slots; not fresh allocation.
                gate.fixture={"cpu_before_H2D":cpu,"cpu_indices_before_H2D":ix}
                dense.copy_(cpu.to(dense.device));indices.copy_(ix.to(indices.device))
                torch.npu.synchronize()
                require(pointers==(dense.data_ptr(),indices.data_ptr()),"fixture same buffers")
                pack_once(torch,npu,gate,ops,arena,dense,(plan,devplans),indices,golden,
                          "P"+str(p)+"_"+kind+"_changing_"+str(turn))
            baseline=arena.raw.cpu().clone();word_outputs=[]
            for repeat in range(8):
                arena.raw.copy_(baseline.to(arena.raw.device));torch.npu.synchronize()
                pack_once(torch,npu,gate,ops,arena,dense,(plan,devplans),indices,golden,
                          "P"+str(p)+"_"+kind+"_reset_"+str(repeat))
                words=arena.raw.cpu().clone()
                word_outputs.append(words)
                gate.check("identical_reset_determinism",all(exact(torch,words,x) for x in word_outputs))
            # These indices differ on the SAME buffer and are checked on device
            # before any head writer. P1 has no duplicate case by definition.
            bads=[("PAD",[-1]+selection(p,s)[1:]),
                  ("range",[s]+selection(p,s)[1:])]
            if p>1:bads.append(("duplicate",[0,0]+selection(p,s)[2:]))
            for name,ids in bads:
                indices.copy_(torch.tensor(ids,dtype=torch.int32,device=indices.device))
                torch.npu.synchronize()
                pack_once(torch,npu,gate,ops,arena,dense,(plan,devplans),indices,golden,
                          "P"+str(p)+"_"+kind+"_"+name,error=1)
            # Numeric failure has fresh state and no later reuse/feedback.
            for name,error in (("NaN",2),("FP16overflow",2),("scale_underflow",3)):
                fail_golden=seed(torch,independent,s,plan)
                fail_arena=Arena(torch,npu,nd,s,kind,fail_golden)
                x=fixture(torch,p,0)
                if name=="NaN":x[0,0,0,0]=float("nan")
                elif name=="FP16overflow":x[0,0,int(plan.pv[0,0]),int(plan.pk[0,0])]=1e10
                else:
                    x.zero_()
                    for h in range(12):
                        x[:,h,:,plan.pk[h,16:].long()]=torch.tensor(1,dtype=torch.int32).view(torch.float32)
                nx,ni=nd(x),nd(torch.tensor(selection(p,s),dtype=torch.int32))
                ops.prepare(nx,*fail_arena.states,*devplans,ni,False)
                torch.npu.synchronize()
                pack_once(torch,npu,gate,ops,fail_arena,nx,(plan,devplans),ni,fail_golden,
                          "P"+str(p)+"_"+kind+"_"+name,error=error)

def main(argv=None):
    args=parser().parse_args(argv)
    if not args.execute:
        print(json.dumps({"status":"disabled","npu_executed":False,"serving_ready":False}))
        return 0
    require(all(getattr(args,n) is not None for n in ("preflight","build_receipt","library","out")),
            "explicit preflight/build/SO/fresh output required")
    binding=admission(args)
    require(args.out.is_absolute() and args.out.resolve()!=REPO and
            REPO not in args.out.resolve().parents and str(args.out.resolve())!="/",
            "new absolute external experiment output root required")
    args.out.mkdir(parents=True,exist_ok=False)
    report={"schema":"damp-selected-prefill-npu-gate/v1","status":"running","stage":args.stage,
            "bindings":binding,"cases":[],"checks":[],"npu_executed":False,
            "serving_ready":False,"performance_measurement_admitted":False,"graph_supported":False,
            "general_sr":True,"float_candidate_enabled":False,"steps":160,"limits":LIMITS}
    # No Torch auto-load or operator/device acquisition before full CPU checks.
    os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"]="0"
    import torch
    import torch_npu
    from evidence import Recorder
    gate=Recorder(torch,args.out,report)
    try:
        validate_proof(json.loads(args.preflight.read_text()),args.physical_card) # fresh before device
        torch.npu.set_device(0)
        report["actual_runtime_soc"]=torch.npu.get_device_name(0)
        require(report["actual_runtime_soc"]=="Ascend910B4","runtime SoC not guessed from target")
        require(torch.__version__=="2.10.0+cpu" and torch_npu.__version__=="2.10.0.post4","actual image Torch ABI")
        def nd(x):
            value=torch_npu.npu_format_cast(x.contiguous().to("npu:0"),2)
            if value.data_ptr()%32:value=torch_npu.npu_format_cast(value.clone(),2)
            require(torch_npu.get_npu_format(value)==2 and value.is_contiguous() and
                    value.data_ptr()%32==0,"actual operand physical ND32")
            return value
        torch.ops.load_library(str(args.library))
        require(loaded(args.library)==SELECTED_SO_SHA,"actually mapped selected SO")
        ops=getattr(torch.ops,NAMESPACE);report["schemas"]=schema(torch,ops)
        sys.path.insert(0,str(PROJECT/"tests"))
        report["npu_executed"]=True;gate.save()
        if args.stage=="isolated":
            isolated(torch,torch_npu,nd,ops,gate,args.batches)
            report["status"]="isolated_selected_packing_pass"
            report["fixture_origin"]="CPU-FP32-isolated-not-native"
            report["native_prefill_verified"]=False
            report["decode_feedback_verified"]=False
        else:
            from native_feedback import run
            run(args,torch,torch_npu,nd,ops,gate)
            report["status"]="native_chunk_selected_pack_feedback_pass"
            report["native_prefill_verified"]=True
            report["decode_feedback_verified"]=True
        check_sources(REPO,binding["sources"]);check_sources(REPO,binding["dependencies"])
        if args.stage=="native_feedback":
            runtime=bound_json(args.runtime_manifest,args.runtime_manifest_sha256)
            for path,digest in runtime["actual_image_sources"].items():
                require(sha(path)==digest,"end actual-image source identity")
        require(loaded(args.library)==SELECTED_SO_SHA,"end loaded SO identity")
        report["completed_ns"]=time.time_ns();gate.save();print(json.dumps({"status":report["status"]}))
        return 0
    except BaseException as error:
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        gate.retain();gate.save()
        return 1
if __name__=="__main__":raise SystemExit(main())
