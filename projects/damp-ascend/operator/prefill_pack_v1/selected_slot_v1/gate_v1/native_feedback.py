"""Actual source-bound native chunk -> selected pack -> compressed own-feedback.

Standalone PCP1 eager operation gate, NOT native model-builder/mixed/FA service.
No mutation of original globals/functions/torch.ops. Explicit registration SOs.
"""
from contextlib import contextmanager
import importlib
import inspect
import json
from pathlib import Path
import sys
from selected_contract import (require,sha,bound_json,validate_anchor,require_decode_admission,
    REFERENCE,LIMITS,status_rows,selection,REGIONS,ALL_BATCH_BUILD_SHA,ALL_BATCH_MANIFEST_SHA)
from evidence import observe,exact
from packing_oracle import layout,seed,pack,selected_update
from arena import Arena

ANCHOR_SHA="d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8"
REFERENCE_SO="853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8"

@contextmanager
def native_context(torch,out):
    # Public APIs from ACTUAL pinned image. No MagicMock/global replacement.
    from vllm.config import VllmConfig,set_current_vllm_config
    from vllm.config.vllm import OptimizationLevel
    from vllm.forward_context import ForwardContext,override_forward_context,is_forward_context_available
    from vllm.distributed.parallel_state import (init_distributed_environment,initialize_model_parallel,
        get_pcp_group,destroy_model_parallel,destroy_distributed_environment)
    from vllm.platforms import current_platform
    require(not torch.distributed.is_initialized() and not is_forward_context_available(),
            "standalone process owns new distributed/forward context only")
    require(current_platform.device_name=="npu","actual Ascend platform selected")
    config=VllmConfig(optimization_level=OptimizationLevel.O0)
    require(config.model_config is None and config.parallel_config.data_parallel_size==1 and
            config.parallel_config.tensor_parallel_size==1 and
            config.parallel_config.pipeline_parallel_size==1,"model-free actual config/PCP1 only")
    rendezvous=out/"owned-gloo-rendezvous"
    require(not rendezvous.exists(),"fresh file rendezvous, no external port")
    context=ForwardContext(no_compile_layers={},attn_metadata={},slot_mapping={})
    with set_current_vllm_config(config):
        try:
            init_distributed_environment(world_size=1,rank=0,local_rank=0,
                distributed_init_method="file://"+str(rendezvous.resolve()),backend="gloo")
            initialize_model_parallel(tensor_model_parallel_size=1,pipeline_model_parallel_size=1,
                prefill_context_model_parallel_size=1,decode_context_model_parallel_size=1,backend="gloo")
            require(get_pcp_group().world_size==1,"real PCP1, not fake group")
            with override_forward_context(context):yield context
        finally:
            # Only newly owned standalone groups; never caller model groups.
            destroy_model_parallel()
            destroy_distributed_environment()

def continuation_initial(torch,independent,nd,golden,plan,indices,p):
    # Independent restore from its OWN packed feedback to P transient states.
    packed=independent.ValueMajorPacked(*(getattr(golden,n).index_select(0,indices.long()).clone()
                                         for n in REGIONS))
    transformed=independent.unpack_value_major(packed,plan)
    original=independent.restore_state(transformed,plan)
    return nd(original.transpose(-1,-2).contiguous())

def actual_unpack(torch,npu,gdn,decode_ops,pack_ops,arena,plan,devplans,indices,p,nd,gate):
    # Exercise frozen service's ACTUAL selected-unpack implementation, without
    # pretending the fake layer fixture is an initialized model/cache authority.
    from types import SimpleNamespace
    from run import PROJECT
    core_parent=PROJECT/"integration/service_continuous_core_v1"
    sys.path.insert(0,str(PROJECT/"integration"))
    sys.path.insert(0,str(core_parent))
    from damp_continuous_core.torch_backend import TorchBackend,Cold
    prefix="standalone-unpack-probe"
    holder=SimpleNamespace(kv_cache=(arena.views["conv"],*arena.states),prefix=prefix)
    devplan=SimpleNamespace(pk=devplans[0],pv=devplans[1],inv_pv=nd(plan.pv.argsort(1).int()),sr=devplans[2])
    backend=TorchBackend(torch,npu,gdn,decode_ops,pack_ops,None,None,None,enabled=True,formal_perf=False)
    # This test injects a resource to call selected-unpack only. It does NOT
    # certify prepare_layer, native allocator, receipts or service admission.
    backend.resource=lambda layer:backend.cold[prefix]
    backend.cold[prefix]=Cold(devplan,nd(plan.pk.argsort(1).int()),(),(),
                             frozenset((1,16)),frozenset((1,16)))
    md=SimpleNamespace(prefill_state_indices=nd(indices))
    turn=SimpleNamespace(prefill_rows=tuple(range(p)))
    inputs=[*arena.states,*devplans,devplan.inv_pv,backend.cold[prefix].inv_pk,md.prefill_state_indices]
    out,cpu,after,record=observe(torch,gate,"service_selected_unpack",
        lambda:backend.unpack_selected(holder,md,turn,tuple(range(p))),inputs+[arena.raw])
    gate.healthy(record,"selected_unpack_dispatch")
    gate.check("selected_unpack_all_inputs_raw_immutable",
        record["pointers_before"]==record["pointers_after"] and
        all(exact(torch,a,b) for a,b in zip(record["before"],after)))
    return out,cpu

def run(args,torch,npu,nd,pack_ops,gate):
    from run import REPO,PROJECT,pack_once,loaded
    from selected_contract import check_sources
    require(all(getattr(args,name) is not None for name in ("decode_build_receipt","decode_library",
            "decode_library_sha256","native_anchor_report","reference_library","reference_library_sha256")),
            "explicit decode/native/reference authority required for native feedback")
    require(set(args.batches)<=set((1,16)),"native feedback first B1/B16 only; no C16 scheduler claim")
    anchor=bound_json(args.native_anchor_report,ANCHOR_SHA)
    native_binding=validate_anchor(anchor)
    require(args.reference_library_sha256==REFERENCE_SO and sha(args.reference_library)==REFERENCE_SO,
            "independently anchored reference SO")
    require(native_binding["reference_library_sha256"]==REFERENCE_SO,"anchor reference identity")
    check_sources(REPO,{"projects/damp-ascend/operator/reference/"+k:v for k,v in REFERENCE.items()})
    decode_manifest=bound_json(PROJECT/"operator/all_batch_wrapper_v3/source_manifest.json",ALL_BATCH_MANIFEST_SHA)
    decode_receipt=bound_json(args.decode_build_receipt,ALL_BATCH_BUILD_SHA)
    require_decode_admission(decode_receipt,decode_manifest,args.decode_library_sha256)
    require(sha(args.decode_library)==args.decode_library_sha256,"explicit decode SO")
    native_library=Path(native_binding["native_runtime_library_path"])
    require(sha(native_library)==native_binding["native_runtime_library_sha256"],"actual native runtime binary")
    require(__import__("os").environ.get("DAMP_ENABLE_NATIVE_REFERENCE")=="1",
            "independent test-only reference explicit opt-in")
    torch.ops.load_library(str(args.reference_library))
    torch.ops.load_library(str(args.decode_library))
    decode_ops=torch.ops.qwen36_damp_all_batch_v3
    ref=torch.ops.qwen36_damp_reference.decode
    require(loaded(args.reference_library)==REFERENCE_SO and
            loaded(args.decode_library)==args.decode_library_sha256,"actual mapped injected libraries")
    sys.path.insert(0,str(PROJECT/"operator/production_integer_compaction_v1/tests"))
    from protocols import invoke_reference
    from general_sr_native_gate import turn
    independent=importlib.import_module("independent_oracle")
    gdn=importlib.import_module("vllm_ascend.ops.gdn")
    source=Path(inspect.getsourcefile(gdn.chunk_gated_delta_rule))
    require(sha(source)=="6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5",
            "native chunk callable actual-image source")
    gate.report["native_bindings"]={"anchor_path":str(args.native_anchor_report),"anchor_sha256":ANCHOR_SHA,
        "native_runtime":native_binding,"reference_library":str(args.reference_library),
        "reference_library_sha256":REFERENCE_SO,"decode_library":str(args.decode_library),
        "decode_library_sha256":args.decode_library_sha256,"decode_build_receipt_sha256":sha(args.decode_build_receipt)}
    # Public context/group API setup is itself an untested runtime seam.
    with native_context(torch,args.out):
        for p in args.batches:
            s=p+3;plan=layout(torch,independent,True)
            devplans=[nd(x) for x in (plan.pk,plan.pv,plan.c)]
            inv_pv=nd(plan.pv.argsort(1).int())
            for kind in ("adjacent","guard_gaps"):
                golden=seed(torch,independent,s,plan)
                arena=Arena(torch,npu,nd,s,kind,golden)
                ids=torch.tensor(selection(p,s,1),dtype=torch.int32)
                for continuation in (False,True):
                    # True branch checks actual service selected unpack against
                    # independently restored previous packed state, not itself.
                    initial_cpu=torch.zeros((p,12,128,128),dtype=torch.float32)
                    initial=nd(initial_cpu)
                    if continuation:
                        initial=continuation_initial(torch,independent,nd,golden,plan,ids,p)
                        expected_initial=initial.cpu().clone()
                        actual,actual_cpu=actual_unpack(torch,npu,gdn,decode_ops,pack_ops,
                                      arena,plan,devplans,ids,p,nd,gate)
                        gate.check("service_unpack_vs_independent_FP32_bitwise",
                                   exact(torch,actual_cpu,expected_initial))
                        initial=actual
                    lengths=[65+(i%3) for i in range(p)]
                    starts=[0]
                    for n in lengths:starts.append(starts[-1]+n)
                    total=starts[-1]
                    generator=torch.Generator(device="cpu").manual_seed(260627513+p*1009+int(continuation))
                    q=(torch.randn(1,total,4,128,generator=generator)*.1).bfloat16()
                    k=(torch.randn(1,total,4,128,generator=generator)*.1).bfloat16()
                    v=(torch.randn(1,total,12,128,generator=generator)*.02).bfloat16()
                    g=-torch.rand(1,total,12,generator=generator)*.04
                    beta=(torch.rand(1,total,12,generator=generator)*.4+.2).bfloat16()
                    operands=[nd(x) for x in (q,k,v,g,beta)]
                    cu=nd(torch.tensor(starts,dtype=torch.int64))
                    tensors=operands+[initial,cu,arena.raw]
                    gate.fixture={"stage":"actual_native_chunk","p":p,"continuation":continuation,
                        "input_origin":"synthetic_BF16_operation_fixture_actual_native_chunk",
                        "q":q,"k":k,"v":v,"g":g,"beta":beta,"cu":starts,
                        "initial_cpu":initial.cpu().clone(),"plan":{"c":plan.c,"pk":plan.pk,"pv":plan.pv}}
                    result,cpu,after,record=observe(torch,gate,"native_chunk",
                        lambda:gdn.chunk_gated_delta_rule(*operands,initial_state=initial,
                            output_final_state=True,cu_seqlens=cu,prebuilt_meta=None,head_first=False,
                            use_qk_l2norm_in_kernel=True),tensors)
                    gate.healthy(record,"actual_native_chunk_dispatch")
                    gate.check("native_chunk_all_inputs_and_packed_arena_immutable",
                        record["pointers_before"]==record["pointers_after"] and
                        all(exact(torch,a,b) for a,b in zip(record["before"],after)))
                    require(isinstance(result,(list,tuple)) and len(result)==2,"native chunk arity")
                    output,last=result
                    require(tuple(last.shape)==(p,12,128,128) and last.dtype==torch.float32 and
                        tuple(output.shape)==(1,total,12,128) and output.dtype==torch.bfloat16 and
                        bool(torch.isfinite(cpu[0]).all()) and bool(torch.isfinite(cpu[1]).all()),
                        "actual native prefill output/final ABI/finite")
                    final=nd(last.transpose(-1,-2).contiguous())
                    indices=nd(ids)
                    prepare_inputs=[final,*arena.states,*devplans,indices,arena.raw]
                    _,_,prepared_after,prepared_record=observe(torch,gate,"native_pack_prepare",
                        lambda:pack_ops.prepare(final,*arena.states,*devplans,indices,False),prepare_inputs)
                    gate.healthy(prepared_record,"native_pack_prepare_dispatch")
                    gate.check("native_pack_prepare_entire_inputs_raw_immutable",
                        prepared_record["returns"] is None and
                        prepared_record["pointers_before"]==prepared_record["pointers_after"] and
                        all(exact(torch,a,b) for a,b in zip(prepared_record["before"],prepared_after)))
                    label="native_P"+str(p)+"_"+kind+("_continuation" if continuation else "_fresh")
                    pack_once(torch,npu,gate,pack_ops,arena,final,(plan,devplans),indices,golden,label)
                    gate.report["cases"][-1]["fixture_origin"]="actual_native_chunk_FP32_final"
                    feedback(torch,npu,nd,decode_ops,ref,invoke_reference,turn,gate,arena,golden,
                             plan,devplans,inv_pv,p,label)
                    # No native FP32 dense state retained as the cache feedback.
                    del initial,final,last,result,cpu
    require(loaded(native_library)==native_binding["native_runtime_library_sha256"],
            "actual native library loaded, not just source present")

def feedback(torch,npu,nd,decode_ops,ref,invoke_reference,turn,gate,arena,golden,
             plan,devplans,inv_pv,batch,label):
    independent=importlib.import_module("independent_oracle")
    generator=torch.Generator(device="cpu").manual_seed(260627513+batch)
    plans=[devplans[0],devplans[1],inv_pv];sr=devplans[2]
    lengths=nd(torch.tensor([0]+[1]*batch,dtype=torch.int32))
    q0=nd(torch.zeros(batch,4,128,dtype=torch.bfloat16))
    tensors=[q0,arena.states[0],*plans,sr,*arena.states[1:],arena.raw]
    _,_,after,record=observe(torch,gate,"decode_prepare",
        lambda:decode_ops.prepare(q0,arena.states[0],*plans,sr),tensors)
    gate.healthy(record,"decode_prepare_dispatch")
    gate.check("decode_prepare_all_inputs_raw_immutable",
        record["returns"] is None and record["pointers_before"]==record["pointers_after"] and
        all(exact(torch,a,b) for a,b in zip(record["before"],after)))
    case={"label":label+"_feedback","stage":"prefill_seeded_decode","p":batch,"status":"running","steps":[]}
    gate.report.setdefault("feedback_cases",[]).append(case)
    for index in range(160):
        q,k,v,g,beta,ids=turn(batch,batch+3,index,generator,False)
        inputs=[nd(x) for x in (q,k,v,g,beta)];nids=nd(ids)
        before=arena.raw.cpu().clone();golden_before=golden.clone()
        gate.fixture={"stage":"prefill_seeded_compressed_feedback","label":label,"step":index+1,
            "q":q,"k":k,"v":v,"g":g,"beta":beta,"indices":ids,"raw_before":before,
            "golden_before":{n:getattr(golden_before,n) for n in REGIONS}}
        # The reference starts from ITS own independent quantized trajectory.
        selected=independent.unpack_value_major(golden,plan).index_select(0,ids.long()).contiguous()
        updated,fp32_output,expected=invoke_reference(gate,ref,inputs,selected,plans,sr,nd)
        selected_packed=independent.pack_value_major(updated,plan)
        selected_update(golden,selected_packed,ids)
        gate.fixture.update(reference_updated_FP32=updated,reference_original_output_FP32=fp32_output,
            expected_output=expected,expected_raw=arena.expected_raw(before,golden))
        tensors=inputs+arena.states+plans+[sr,lengths,nids,arena.raw]
        device_out,cpu_out,after,record=observe(torch,gate,"selected_prefill_decode",
            lambda:decode_ops.decode(*inputs,*arena.states,*plans,sr,lengths,nids),tensors)
        gate.healthy(record,"decode_dispatch")
        actual=independent.ValueMajorPacked(*after[5:8])
        actual_dense=independent.restore_state(independent.unpack_value_major(actual,plan),plan)
        expected_dense=independent.restore_state(independent.unpack_value_major(golden,plan),plan)
        metrics={"selected_state":independent.errors(actual_dense.index_select(0,ids.long()),
                  expected_dense.index_select(0,ids.long())),
                 "complete_state":independent.errors(actual_dense,expected_dense),
                 "output":independent.errors(cpu_out,expected)}
        guards={"protected_and_untouched_bitwise":arena.outside_selected(before,after[-1],ids),
                "arena_identity_stable":arena.identities()==arena.identity}
        output_span=(device_out.data_ptr(),device_out.data_ptr()+device_out.numel()*device_out.element_size())
        guards["output_fresh_nonalias"]=all(output_span[1]<=x.data_ptr() or
            x.data_ptr()+x.numel()*x.element_size()<=output_span[0] for x in tensors)
        guards.update(immutable_inputs_bitwise=all(exact(torch,record["before"][i],after[i])
                      for i in list(range(5))+list(range(8,14))),
                      all_pointers_stable=record["pointers_before"]==record["pointers_after"],
                      output_ABI=tuple(device_out.shape)==(batch,12,128) and device_out.dtype==torch.bfloat16,
                      output_ND=npu.get_npu_format(device_out)==2)
        # Complete packed bitwise equality is diagnostic; frozen metric limits
        # are unchanged. Whole raw guards verify protected bytes and state here.
        passed=all(guards.values()) and all(m["finite"] for m in metrics.values()) and (
            metrics["selected_state"]["max_head_relative_l2"]<=LIMITS["state"] and
            metrics["complete_state"]["max_head_relative_l2"]<=LIMITS["state"] and
            metrics["output"]["max_head_relative_l2"]<=LIMITS["output"])
        row={"step":index+1,"indices":ids.tolist(),"metrics":metrics,"guards":guards,"passed":passed,
             "packed_bitwise_diagnostic":{n:exact(torch,getattr(actual,n),getattr(golden,n)) for n in REGIONS}}
        case["steps"].append(row);gate.check(label+"_step_"+str(index+1),passed,row)
        del selected,updated,actual_dense,expected_dense
    case["status"]="passed";gate.save()
