"""Independent restricted feedback + explicit Candidate graph replay.

No production helper is an oracle; native compressed feedback is source-frozen.
No prepare/H2D/oracle is inside capture. No automatic graph or serving opt-in.
"""
import torch
import torch_npu
from graph_contract import STEPS, IDENTICAL_REPEATS, WARMUPS, VARIANTS, metadata_cases
from gate_contract import LIMITS, require
from candidate_adapter import REGIONS, observe, exact, packed_dict, storage_disjoint
from protocols import (restricted, native_step, ValueMajorPacked, restore_state,
    unpack_value_major, errors, tensor_digest, layout_dict, invoke_prepare_guard)

def cpu_packed(arena):
    return ValueMajorPacked(*(x.detach().cpu().contiguous().clone() for x in arena))

def copy_turn(gate, label, buffers, cpu):
    """Copies finish before replay on the graph's captured stream."""
    gate.fixture[label+"_cpu_source"]=[x.clone() for x in cpu]
    _,_,after=observe(gate,label,lambda:_copy(buffers,cpu),buffers)
    gate.require(label+"_all_buffers_installed",
                 all(exact(a,b) for a,b in zip(after,cpu)))
    return after

def _copy(buffers,cpu):
    for dst,src in zip(buffers,cpu): dst.copy_(src)
    torch.npu.synchronize()
    return None

def reset(gate,label,arena,initial):
    sources=[getattr(initial,n) for n in REGIONS]
    copy_turn(gate,label,arena,sources)

def all_args(turn,arena,plans,sr):
    return list(turn[:5])+list(arena)+list(plans)+[sr,turn[5],turn[6]]

def golden_step(gate,label,golden,layout,fixture,native):
    q,k,v,g,beta,ids=fixture
    before=golden.clone()
    gate.fixture.update(reference_before=packed_dict(before),
        fixture_cpu=[x.clone() for x in fixture],layout=layout_dict(layout))
    evidence,cpu_evidence,_=observe(gate,label,
        lambda:native_step(golden,layout,q,k,v,g,beta,ids,native,"npu:0"),[])
    gate.fixture.update(reference_after=packed_dict(evidence["packed"]),
                        native_evidence={k:v for k,v in cpu_evidence.items() if k!="packed"})
    return evidence,before

def audit_result(gate,label,raw,output,cpu_output,after,layout,expected,before,evidence,ids,ptrs):
    actual=ValueMajorPacked(*after[5:8])
    original=restore_state(unpack_value_major(actual,layout),layout)
    golden_original=restore_state(unpack_value_major(expected,layout),layout)
    untouched=[s for s in range(actual.high.shape[0]) if s not in ids.tolist()]
    metrics={
        "selected_state":errors(original.index_select(0,ids.long()),golden_original.index_select(0,ids.long())),
        "complete_state":errors(original,golden_original),
        "output":errors(cpu_output,evidence["original_output_bf16"])}
    guards={
        "untouched_regions_bitwise":all(exact(getattr(actual,n)[untouched],getattr(before,n)[untouched]) for n in REGIONS),
        "reference_untouched_bitwise":evidence["native_fp32_untouched_exact"],
        "all_input_pointers_stable":raw["pointers_before"]==raw["pointers_after"]==ptrs,
        "immutable_inputs_bitwise":all(exact(raw["before"][i],after[i])
                                      for i in list(range(5))+list(range(8,14))),
        "output_ABI":tuple(output.shape)==(ids.numel(),12,128) and output.dtype==torch.bfloat16,
        "output_ND":torch_npu.get_npu_format(output)==2,
        "output_nonalias":all(storage_disjoint(output,x) for x in raw["live_inputs"]),
        "native_scaledV_BF16_exact":evidence["value_cast_exact"],
        "native_restore_BF16_exact":evidence["restored_cast_exact"]}
    passed=all(guards.values()) and all(m["finite"] for m in metrics.values()) and (
        metrics["selected_state"]["max_head_relative_l2"]<=LIMITS["state"] and
        metrics["complete_state"]["max_head_relative_l2"]<=LIMITS["state"] and
        metrics["output"]["max_head_relative_l2"]<=LIMITS["output"])
    # live_inputs is removed BEFORE retention, never used as feedback.
    raw.pop("live_inputs",None)
    gate.fixture[label+"_evaluated"]={"actual":packed_dict(actual),"output":cpu_output,
                                     "metrics":metrics,"guards":guards,"passed":passed}
    return actual,{"passed":passed,"metrics":metrics,"guards":guards}

def dispatch_valid(gate,label,dispatch,args,layout,expected,before,evidence,ids,ptrs):
    output,cpu_output,after=observe(gate,label,dispatch,args)
    raw=gate.fixture[label]; raw["live_inputs"]=args
    actual,record=audit_result(gate,label,raw,output,cpu_output,after,layout,
                               expected,before,evidence,ids,ptrs)
    return actual,cpu_output,output,record

def pair_exact(outputs,states):
    return (all(exact(outputs[0],x) for x in outputs[1:]) and
            all(exact(getattr(states[0],n),getattr(s,n)) for s in states[1:] for n in REGIONS))

def capture_one(gate,label,candidate,args):
    graph=torch.npu.NPUGraph()
    def capture():
        with torch.npu.graph(graph):
            output=candidate.decode(*args)
        return output
    output,_,after=observe(gate,label,capture,args)
    raw=gate.fixture[label]
    guards={
        "capture_immutable_inputs":all(exact(raw["before"][i],after[i])
                                      for i in list(range(5))+list(range(8,14))),
        "capture_pointers_stable":raw["pointers_before"]==raw["pointers_after"],
        "output_ABI":tuple(output.shape)==(args[0].shape[0],12,128) and output.dtype==torch.bfloat16,
        "output_ND":torch_npu.get_npu_format(output)==2,
        "output_nonalias":all(storage_disjoint(output,x) for x in args)}
    gate.require(label+"_capture_contract",all(guards.values()),guards)
    return graph,output

def replay(graph,output):
    # Required captured-stream visibility boundary, even when source was CPU.
    torch.npu.synchronize()
    graph.replay()
    return output

def invalid_turn(gate,label,dispatch,args,ptrs):
    output,cpu_output,after=observe(gate,label,dispatch,args)
    raw=gate.fixture[label]
    guards={
        "all_output_nan":tuple(output.shape)==(args[0].shape[0],12,128) and
                          output.dtype==torch.bfloat16 and bool(torch.isnan(cpu_output).all()),
        "complete_state_bitwise_unchanged":all(exact(raw["before"][i],after[i]) for i in (5,6,7)),
        "every_input_bitwise_unchanged":all(exact(a,b) for a,b in zip(raw["before"],after)),
        "every_pointer_stable":raw["pointers_before"]==raw["pointers_after"]==ptrs,
        "output_ND":torch_npu.get_npu_format(output)==2,
        "output_nonalias":all(storage_disjoint(output,x) for x in args)}
    gate.fixture[label+"_invalid_guards"]=guards
    return {"passed":all(guards.values()),"guards":guards}

def graph_case(gate,candidate,native,nd,batch,variant):
    layout,initial,generator=restricted.layouts(batch,variant)
    fixtures=[restricted.turn(batch,batch+3,i,generator) for i in range(STEPS)]
    lenses=torch.tensor([0]+[1]*batch,dtype=torch.int32)
    # Only metadata and dynamic Q/K/V/g/beta are overwritten on replay.
    buffers=[nd(x) for x in (*fixtures[0][:5],lenses,fixtures[0][5])]
    plans=[nd(x.int()) for x in (layout.pk,layout.pv,layout.pv.argsort(1))]
    sr=nd(layout.c)
    arenas=[[nd(getattr(initial,n)) for n in REGIONS] for _ in range(3)]
    args=[all_args(buffers,a,plans,sr) for a in arenas]
    ptrs=[[x.data_ptr() for x in a] for a in args]
    gate.start_case("graph_restricted",batch,VARIANTS[variant])
    gate.case.update(steps_expected=STEPS,identical_repeats_expected=IDENTICAL_REPEATS,
                     initial_fixture_sha256=tensor_digest([getattr(initial,n) for n in REGIONS]+[layout.c,layout.pk,layout.pv]),
                     graph_outputs_static=True,static_plan_scope="SR1/power2 only")
    gate.fixture={"stage":"cold_prepare","batch":batch,"variant":variant,
                  "initial":packed_dict(initial),"layout":layout_dict(layout)}
    # Separate resettable warmup state is NEVER one of the captured arenas.
    warm=[nd(getattr(initial,n)) for n in REGIONS]
    warm_args=all_args(buffers,warm,plans,sr)
    invoke_prepare_guard(gate,candidate.prepare,[buffers[0],warm[0],*plans,sr],warm)
    warm_ptrs=[x.data_ptr() for x in warm_args]
    warm_golden=initial.clone()
    for i in range(WARMUPS):
        fixture=fixtures[i]
        gate.fixture={"stage":"warmup","batch":batch,"variant":variant,"step":i+1}
        copy_turn(gate,"warmup_input_install",buffers,[*fixture[:5],lenses,fixture[5]])
        evidence,golden_before=golden_step(gate,"warmup_native",warm_golden,layout,fixture,native)
        before=cpu_packed(warm); warm_golden=evidence["packed"]
        _,_,_,record=dispatch_valid(gate,"warmup_candidate",lambda:candidate.decode(*warm_args),
            warm_args,layout,warm_golden,before,evidence,fixture[5],warm_ptrs)
        gate.require("warmup_"+str(i+1)+"_numerical_guard",record["passed"],record)
    gate.fixture={"stage":"capture_prepare","batch":batch,"variant":variant,"initial":packed_dict(initial)}
    copy_turn(gate,"capture_input_install",buffers,[*fixtures[0][:5],lenses,fixtures[0][5]])
    for i,arena in enumerate(arenas):
        invoke_prepare_guard(gate,candidate.prepare,[buffers[0],arena[0],*plans,sr],arena)
    # No cold tiling upload, Python constants, CPU copies or native oracle in graph.
    graphs=[];graph_outputs=[]
    for i in (0,1):
        graph,output=capture_one(gate,"capture_graph_"+str(i),candidate,args[i])
        graphs.append(graph); graph_outputs.append(output)
    gate.require("both_graph_outputs_disjoint",storage_disjoint(*graph_outputs))
    gate.require("all_three_arenas_disjoint",all(storage_disjoint(a,b)
        for i,arena in enumerate(arenas) for earlier in arenas[:i] for a in arena for b in earlier))
    output_ptrs=[x.data_ptr() for x in graph_outputs]
    # Capture can modify state; reset explicitly and synchronize outside capture.
    for i,arena in enumerate(arenas): reset(gate,"capture_reset_"+str(i),arena,initial)
    gate.fixture={"stage":"identical_native","batch":batch,"variant":variant}
    evidence,_=golden_step(gate,"identical_native",initial.clone(),layout,fixtures[0],native)
    repeated_digest=None
    for repeat in range(IDENTICAL_REPEATS):
        gate.fixture={"stage":"identical_replay","batch":batch,"variant":variant,"repeat":repeat+1,
                      "expected":packed_dict(evidence["packed"]),"native_output":evidence["original_output_bf16"]}
        for i,arena in enumerate(arenas): reset(gate,"identical_reset_"+str(i),arena,initial)
        copy_turn(gate,"identical_input_install",buffers,[*fixtures[0][:5],lenses,fixtures[0][5]])
        states=[];outputs=[];records=[]
        for i in range(3):
            fn=(lambda i=i:replay(graphs[i],graph_outputs[i])) if i<2 else lambda:candidate.decode(*args[2])
            actual,out,_,record=dispatch_valid(gate,"identical_path_"+str(i),fn,args[i],layout,
                evidence["packed"],initial,evidence,fixtures[0][5],ptrs[i])
            states.append(actual);outputs.append(out);records.append(record)
        digest=tensor_digest(outputs+[getattr(states[0],n) for n in REGIONS])
        checks={"both_graphs_vs_eager_bitwise":pair_exact(outputs,states),
                "all_eight_identical_snapshots_bitwise":repeated_digest is None or digest==repeated_digest,
                "graph_output_pointers_stable":output_ptrs==[x.data_ptr() for x in graph_outputs]}
        gate.require("identical_replay_"+str(repeat+1),all(x["passed"] for x in records) and all(checks.values()),
                     {"paths":records,"guards":checks,"actual_digest":digest})
        repeated_digest=digest
    for i,arena in enumerate(arenas): reset(gate,"feedback_reset_"+str(i),arena,initial)
    golden=initial.clone()
    for index,fixture in enumerate(fixtures):
        q,k,v,g,beta,ids=fixture
        gate.fixture={"stage":"changed_graph_feedback","batch":batch,"variant":variant,"step":index+1}
        copy_turn(gate,"dynamic_input_install",buffers,[q,k,v,g,beta,lenses,ids])
        before=[cpu_packed(a) for a in arenas]
        evidence,golden_before=golden_step(gate,"independent_native_feedback",golden,layout,fixture,native)
        golden=evidence["packed"]
        states=[];outputs=[];records=[]
        for i in range(3):
            fn=(lambda i=i:replay(graphs[i],graph_outputs[i])) if i<2 else lambda:candidate.decode(*args[2])
            actual,out,_,record=dispatch_valid(gate,"feedback_path_"+str(i),fn,args[i],layout,
                golden,before[i],evidence,ids,ptrs[i])
            states.append(actual);outputs.append(out);records.append(record)
        checks={"both_graphs_vs_same_eager_bitwise":pair_exact(outputs,states),
                "graph_output_pointers_stable":output_ptrs==[x.data_ptr() for x in graph_outputs]}
        # Some modulo turns intentionally repeat the captured slots. The whole
        # case must have observed changed IDs, not every step (index0 is equal).
        gate.step({"step":index+1,"passed":all(r["passed"] for r in records) and
                   checks["both_graphs_vs_same_eager_bitwise"] and checks["graph_output_pointers_stable"],
                   "guards":checks,"paths":records,"indices":ids.tolist(),
                   "slot_changed_from_capture_diagnostic":ids.tolist()!=fixtures[0][5].tolist(),
                   "turn_fixture_sha256":tensor_digest(list(fixture)),
                   "packed_bitwise_vs_independent_native":{n:exact(getattr(states[0],n),getattr(golden,n)) for n in REGIONS}})
    gate.require("real_changed_slot_and_input_coverage",
        len({tuple(f[5].tolist()) for f in fixtures})==batch+3 and
        len({tensor_digest(list(f[:5])) for f in fixtures})==STEPS)
    # Reuse the very same captured graphs: changing only device metadata must
    # select atomic NaN/no-state-write, then recover with independent feedback.
    negative_records=[]
    for index,(name,bad_lens,bad_ids) in enumerate(metadata_cases(batch,batch+3)):
        fixture=fixtures[(index+7)%STEPS]
        gate.fixture={"stage":"invalid_dynamic_metadata","batch":batch,"variant":variant,"label":name,
                      "reference_before":packed_dict(golden),"fixture_cpu":list(fixture),
                      "malformed_lengths":bad_lens,"malformed_indices":bad_ids}
        copy_turn(gate,"invalid_input_install",buffers,[*fixture[:5],
                  torch.tensor(bad_lens,dtype=torch.int32),torch.tensor(bad_ids,dtype=torch.int32)])
        records=[]
        for i in range(3):
            fn=(lambda i=i:replay(graphs[i],graph_outputs[i])) if i<2 else lambda:candidate.decode(*args[2])
            records.append(invalid_turn(gate,"invalid_path_"+str(i),fn,args[i],ptrs[i]))
        gate.require("invalid_"+name,all(r["passed"] for r in records),records)
        negative_records.append({"name":name,"paths":records,"passed":True})
        # Invalid metadata was rejected before ANY state writer. This recovery
        # is legal only after all-state byte invariance proved, never after a
        # quantizer internal failure which may have partially stored groups.
        gate.fixture={"stage":"valid_after_invalid","batch":batch,"variant":variant,"label":name}
        copy_turn(gate,"recovery_input_install",buffers,[*fixture[:5],lenses,fixture[5]])
        before=[cpu_packed(a) for a in arenas]
        evidence,_=golden_step(gate,"recovery_native_feedback",golden,layout,fixture,native)
        golden=evidence["packed"]
        states=[];outputs=[];records=[]
        for i in range(3):
            fn=(lambda i=i:replay(graphs[i],graph_outputs[i])) if i<2 else lambda:candidate.decode(*args[2])
            actual,out,_,record=dispatch_valid(gate,"recovery_path_"+str(i),fn,args[i],layout,
                golden,before[i],evidence,fixture[5],ptrs[i])
            states.append(actual);outputs.append(out);records.append(record)
        gate.require("valid_recovery_after_"+name,all(r["passed"] for r in records) and pair_exact(outputs,states),
                     {"paths":records,"bitwise_graph_eager":pair_exact(outputs,states)})
    gate.case.update(invalid_dynamic_cases=negative_records,identical_repeats=IDENTICAL_REPEATS,
                     warmups=WARMUPS,changed_replays=STEPS,
                     final_packed_sha256=tensor_digest([getattr(golden,n) for n in REGIONS]))
    gate.end_case()
