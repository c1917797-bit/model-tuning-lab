#!/usr/bin/env python3
"""One new NPU matrix; never auto-retry. Kernel correctness, not E2E throughput."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"plugin"))
from kvbuffer_parallel.contract import (IMAGE,SOURCES,admit_lengths,source_identity,aux_bytes,require,sha)
from kvbuffer_parallel.patch import EXPECTED_SCHEMA as ORIGINAL_SCHEMA
CANDIDATE_NAMESPACE = "qwen36_kvbuffer_native_order_v2"
EXPECTED_SCHEMA = ORIGINAL_SCHEMA.replace("qwen36_kvbuffer_parallel_fp32", CANDIDATE_NAMESPACE)
candidate_ops = None

def bind_candidate(ops):
    """Explicit injection into this NEW oracle only; no global torch.ops mutation."""
    global candidate_ops
    require(str(ops.decode.default._schema) == EXPECTED_SCHEMA, "new candidate schema differs")
    candidate_ops = ops

from finite_contract import finite_receipt, FINITE_SCOPE

OUT_LIMIT, STATE_LIMIT = .00303, 2e-6
PADDING_ACTIVE = (0,1,3,7,12,15,16,16)
NAMES = ("base","k_log","u_log","lambda_log","decay","length")
SHAPES = lambda s: ((s,12,128,128),(s,4,16,128),(s,12,16,128),
                    (s,12,32),(s,12,32),(s,12,32))

def nd(t):
    t=torch_npu.npu_format_cast(t,2)
    require(torch_npu.get_npu_format(t)==2 and t.is_contiguous(),"physical ND failed")
    return t

def guarded(shape,dtype,initial=None):
    count=math.prod(shape)
    raw=nd(torch.full((count+128,),7,dtype=dtype,device="npu:0"))
    view=raw[64:64+count].view(shape)
    if initial is None: view.zero_()
    else: view.copy_(initial)
    return view,raw

def allocate(initial):
    dtypes=(torch.float32,torch.bfloat16,torch.float32,torch.float32,torch.float32,torch.int32)
    state,guards={},{}
    for name,shape,dtype in zip(NAMES,SHAPES(initial.shape[0]),dtypes):
        state[name],guards[name]=guarded(shape,dtype,initial if name=="base" else None)
    state["lambda_log"][:,:,:16].fill_(1e30) # dead exponent must not be evaluated
    require(sum(t.numel()*t.element_size() for n,t in state.items() if n!="base") ==
            aux_bytes(int(initial.shape[0]))//48,"auxiliary byte ledger differs")
    return state,guards

def reset_slot(state,native,slot,initial):
    native[slot].copy_(initial[slot]);state["base"][slot].copy_(initial[slot])
    for n in NAMES[1:]: state[n][slot].zero_()
    state["lambda_log"][slot,:,:16].fill_(1e30)

def logical(state):
    # Independent FP32 Torch equation. Dead mask is BEFORE exp, not NaN*0.
    k=state["k_log"].float().repeat_interleave(3,dim=1)
    u=state["u_log"]
    lam=state["lambda_log"][:,:,:16]
    c=state["decay"][:,:,0]
    live=torch.arange(16,device=c.device).view(1,1,16)<state["length"][:,:,0,None]
    safe=torch.where(live,lam,c[:,:,None])
    r=torch.exp(c[:,:,None]-safe)*live.float()
    return torch.exp(c)[:,:,None,None]*state["base"]+torch.einsum("shl,shlv,shlk->shvk",r,u,k)

def inputs(batch,slots,step,gen,active):
    def put(t): return nd(t.to("npu:0"))
    q=torch.nn.functional.normalize(torch.randn((batch,4,128),generator=gen),dim=-1)
    k=torch.nn.functional.normalize(torch.randn((batch,4,128),generator=gen),dim=-1)
    ids=((torch.arange(batch,dtype=torch.int32)+step)%slots)
    ids[active:]=0 # native graph padding aliases real slot0, but length is0
    seq=[0]+[1]*active+[0]*(batch-active)
    admit_lengths(seq,ids.tolist(),batch,slots,active)
    return dict(query=put(q.bfloat16()),key=put(k.bfloat16()),
                value=put((torch.randn((batch,12,128),generator=gen)*.2).bfloat16()),
                g=put(-(0.002+.18*torch.rand((batch,12),generator=gen))),
                beta=put(torch.sigmoid(torch.randn((batch,12),generator=gen)).bfloat16()),
                indices=put(ids),seq=put(torch.tensor(seq,dtype=torch.int32)))

def candidate(state,x):
    return candidate_ops.decode(
        x["query"],x["key"],x["value"],x["g"],x["beta"],state["base"],
        state["k_log"],state["u_log"],state["lambda_log"],state["decay"],state["length"],
        x["seq"],x["indices"])

def native(state,x):
    # Native schema is keyword-only after the four positional tensors.
    return torch.ops._C_ascend.npu_recurrent_gated_delta_rule(
        x["query"],x["key"],x["value"],state,beta=x["beta"],scale=128**-.5,
        g=x["g"],actual_seq_lengths=x["seq"],ssm_state_indices=x["indices"])

def rel(a,e):
    a,e=a.detach().cpu().double(),e.detach().cpu().double()
    return math.sqrt(float((a-e).square().sum())/max(float(e.square().sum()),1e-30))

def output_error(a,e):
    if not a.numel(): return 0.
    a,e=a.detach().cpu().float(),e.detach().cpu().float()
    return float((a-e).abs().max())/max(float(e.abs().max()),1e-30)

def finite_json(value):
    """Diagnostic-only: keep JSON valid even when original tensors/metrics fail."""
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {k:finite_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [finite_json(v) for v in value]
    return value

def cpu_tensors(tensors):
    # Copy first, never perform FP64 or diagnostic arithmetic on the NPU.
    return {n:t.detach().cpu().clone() for n,t in tensors.items()}

def all_pointers(state,guards,native_state,x,actual=None,expected=None):
    result={"state":{n:t.data_ptr() for n,t in state.items()},
            "guards":{n:t.data_ptr() for n,t in guards.items()},
            "native_state":native_state.data_ptr(),
            "inputs":{n:t.data_ptr() for n,t in x.items()}}
    if actual is not None:result["actual"]=actual.data_ptr()
    if expected is not None:result["expected"]=expected.data_ptr()
    return result

def metric_max(previous,current):
    if previous is None or not math.isfinite(current):return None
    return max(previous,current)

def copy_inputs(source,target):
    for n in source: target[n].copy_(source[n])

def check_logs(state,before,x,active):
    expected={n:t.clone() for n,t in before.items()}
    ids=x["indices"][:active].cpu().tolist()
    for i,slot in enumerate(ids):
        lengths=before["length"][slot,:,0].cpu().tolist()
        require(len(set(lengths))==1 and 0<=lengths[0]<16,"head lengths not lock-step")
        l=lengths[0]
        if l==15:
            expected["length"][slot,:,0]=0
            expected["decay"][slot,:,0]=0
        else:
            expected["length"][slot,:,0]=l+1
            expected["decay"][slot,:,0]=before["decay"][slot,:,0]+x["g"][i]
            expected["lambda_log"][slot,:,l]=expected["decay"][slot,:,0]
            expected["k_log"][slot,:,l]=x["key"][i]
            # New U is checked by complete/per-head logical-state parity.
            # All old U, all other slots and all padding must remain bitwise.
            expected["u_log"][slot,:,l]=state["u_log"][slot,:,l]
    return {n:bool(torch.equal(expected[n],state[n])) for n in NAMES[1:]}

def run_case(batch,mode,trial,report,save,output):
    slots=batch+3
    gen=torch.Generator().manual_seed(260519050+batch+trial*100003+(mode=="graph")*17)
    initial=(torch.randn((slots,12,128,128),generator=gen)*.005).float().to("npu:0")
    initial=nd(initial)
    state,guards=allocate(initial)
    native_state=nd(initial.clone())
    pointers={n:t.data_ptr() for n,t in state.items()}
    candidate_ops.prepare(
        nd(torch.empty((batch,4,128),dtype=torch.bfloat16,device="npu:0")),state["base"])
    graph=None; static=None; graph_out=None
    case={"batch":batch,"mode":mode,"trial":trial,"status":"running","steps":[],
          "merges":0,"resets":0,"max_output_error":0.,"max_state_l2":0.,"max_head_l2":0.}
    report["cases"].append(case);save()
    if mode=="graph":
        static=inputs(batch,slots,0,gen,batch)
        warm,warm_guards=allocate(initial)
        for _ in range(3): candidate(warm,static);torch.npu.synchronize()
        graph=torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_out=candidate(state,static)
        torch.npu.synchronize()
        for slot in range(slots): reset_slot(state,native_state,slot,initial)
        torch.npu.synchronize()
    try:
        for step in range(160):
            active=PADDING_ACTIVE[step%len(PADDING_ACTIVE)] if mode=="graph" and batch==16 else batch
            reset=None
            if step in (64,112):
                reset=(step//16)%slots
                reset_slot(state,native_state,reset,initial);case["resets"]+=1
            x=inputs(batch,slots,step,gen,active)
            if static is not None: copy_inputs(x,static);x=static
            # Snapshot complete sources before either mutating operator.
            before={n:t.clone() for n,t in state.items()}
            immutable={n:t.clone() for n,t in x.items()}
            native_before=native_state.clone()
            guards_before={n:t.clone() for n,t in guards.items()}
            pointers_before=all_pointers(state,guards,native_state,x)
            torch.npu.synchronize()
            expected=native(native_state,x)
            if graph is None: actual=candidate(state,x)
            else:
                torch.npu.synchronize() # input copies + oracle read visible on captured stream
                graph.replay();actual=graph_out
            torch.npu.synchronize()
            # Persist the COMPLETE unanalysed step before logical reconstruction,
            # finite checks, log checks, metrics or assertions can themselves fail.
            raw_path=output/("raw-step-b%d-%s-t%d-step%d.pt"%(batch,mode,trial,step+1))
            require(not raw_path.exists(),"raw step must never overwrite evidence")
            raw_receipt={"file":raw_path.name,"step":step+1,"retained":True}
            case["pending_raw_step"]=raw_receipt
            torch.save({"schema":"kvbp.raw-step/v1","batch":batch,"mode":mode,
                        "trial":trial,"step":step+1,"active":active,"reset_slot":reset,
                        "before":cpu_tensors(before),"after":cpu_tensors(state),
                        "native_before":native_before.detach().cpu().clone(),
                        "native":native_state.detach().cpu().clone(),
                        "inputs":cpu_tensors(x),"input_before":cpu_tensors(immutable),
                        "actual":actual.detach().cpu().clone(),
                        "expected":expected.detach().cpu().clone(),
                        "guards_before":cpu_tensors(guards_before),"guards":cpu_tensors(guards),
                        "pointers":{"before":pointers_before,
                                    "after":all_pointers(state,guards,native_state,x,actual,expected)}},
                       raw_path)
            raw_receipt.update(sha256=sha(raw_path),bytes=raw_path.stat().st_size)
            save()
            complete=logical(state)
            eout=output_error(actual[:active],expected[:active])
            estate=rel(complete,native_state)
            perhead=[]
            for slot in range(slots):
                for h in range(12):
                    perhead.append(rel(complete[slot,h],native_state[slot,h]))
            ehead=max(perhead)
            ids=x["indices"][:active].cpu().tolist()
            unused=[s for s in range(slots) if s not in ids]
            untouched=all(torch.equal(state[n][unused],before[n][unused]) for n in NAMES)
            no_write=all(torch.equal(state["base"][s],before["base"][s])
                         for s in ids if int(before["length"][s,0,0])!=15)
            logs=check_logs(state,before,x,active)
            guard_ok=all(bool(torch.all(raw[:64]==7).cpu()) and
                         bool(torch.all(raw[-64:]==7).cpu()) for raw in guards.values())
            pointer_ok=pointers=={n:t.data_ptr() for n,t in state.items()}
            input_ok=all(torch.equal(x[n],immutable[n]) for n in x)
            pad_ok=bool(torch.all(actual[active:]==0).cpu()) if active<batch else True
            finite_parts=finite_receipt(state,actual,expected,complete,native_state,
                    active,(eout,estate,ehead),
                    lambda tensor: bool(torch.isfinite(tensor).all().cpu()))
            metric_finite=finite_parts["metric_finite"]
            finite=finite_parts["finite"]
            merged=sum(int(before["length"][s,0,0])==15 for s in ids)
            case["merges"]+=merged
            passed=(eout<=OUT_LIMIT and estate<=STATE_LIMIT and ehead<=STATE_LIMIT and
                    untouched and no_write and all(logs.values()) and guard_ok and
                    pointer_ok and input_ok and pad_ok and finite)
            row={"step":step+1,"active":active,"reset_slot":reset,"output_error":eout,
                 "complete_state_l2":estate,"max_per_head_l2":ehead,
                 "all_logs_bitwise_outside_new_U":logs,"untouched_slots_bitwise":untouched,
                 "nonflush_base_bitwise":no_write,"guards":guard_ok,"pointers":pointer_ok,
                 "input_immutable":input_ok,"zero_length_output_zero":pad_ok,"finite":finite,
                 "metric_finite":metric_finite,"raw_step":raw_receipt,"passed":passed,
                 "finite_scope":FINITE_SCOPE,"finite_buffer_checks":finite_parts["finite_buffer_checks"],
                 "native_expected_defined_rows":active,
                 "native_expected_undefined_padding_rows":batch-active,
                 "native_padding_values_rewritten":False}
            row=finite_json(row)
            case["steps"].append(row)
            case["max_output_error"]=metric_max(case["max_output_error"],eout)
            case["max_state_l2"]=metric_max(case["max_state_l2"],estate)
            case["max_head_l2"]=metric_max(case["max_head_l2"],ehead)
            save()
            if not passed:
                # The raw file already exists, including nonfinite original tensors.
                # Never remove/replace failed evidence and never let JSON NaN mask it.
                raise RuntimeError("first numerical failure: "+json.dumps(row,allow_nan=False))
            # Only this already-passed step's fresh, hash-checked temporary raw file
            # may be removed. No glob/recursive cleanup and no previous results.
            require(raw_path.parent==output and not raw_path.is_symlink() and
                    raw_path.is_file() and sha(raw_path)==raw_receipt["sha256"],
                    "passed raw-step identity changed; retain it")
            raw_path.unlink()
            row["raw_step"]["retained"]=False
            case.pop("pending_raw_step")
            save()
        require(case["merges"]>0 and case["resets"]==2,"flush/reset coverage missing")
        case["status"]="passed"
    except BaseException as error:
        case.update(status="failed",error=repr(error));raise
    finally: save()
