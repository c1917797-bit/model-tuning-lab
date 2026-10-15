"""MAIN-only source-pinned full native-core mixed producer; zero prep imports.

Real native conv + Qwen rearrange + fused gating + chunk64 remain unchanged.
Native PCP1 GroupCoordinator and ForwardContext are used; no dummy ABI/group.
One-rank fixture executes TP4-local 4/12-head geometry, not a TP4 serving model.
"""
import ast, contextlib, functools, tempfile
from pathlib import Path
from types import SimpleNamespace
from .contract import (AUX_NAMES,STEPS,OUTPUT_LIMIT,STATE_LIMIT,
    QWEN_SHA,CHUNK_SHA,BUILDER_SHA,PARALLEL_SHA,CONTEXT_SHA,CONFIG_SHA,require_digest)
from .transform import clone_core
from .runtime_helpers import execute_mixed_core
from .provider import _route
from collection_policy import reject as collection_reject
# BEGIN DL030 import
from . import capture_evidence as E030
# END DL030 import

def native_method(source,class_name,method,namespace):
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
    node=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(node)
    ns=dict(namespace);exec(compile(node,"<source-pinned native method>","exec"),ns)
    return ns[method]

@contextlib.contextmanager
def native_pcp_context(torch):
    from vllm.distributed import parallel_state as ps
    require_digest(ps.__file__,PARALLEL_SHA)
    if torch.distributed.is_initialized() or ps._PCP is not None:
        raise RuntimeError("numeric fixture requires its own isolated process groups")
    if not torch.distributed.is_backend_available("hccl"):
        raise RuntimeError("real HCCL group unavailable; no dummy/fallback readiness")
    # Private temporary rendezvous only; no network service and no source write.
    with tempfile.TemporaryDirectory(prefix="deltalog-numeric-pcp1-") as tmp:
        try:
            ps.init_distributed_environment(world_size=1,rank=0,local_rank=0,
                distributed_init_method="file://"+tmp+"/rendezvous",backend="hccl")
            ps._PCP=ps.init_model_parallel_group([[0]],0,"hccl",
                group_name="deltalog_numeric_pcp1",use_device_communicator=False)
            if not isinstance(ps.get_pcp_group(),ps.GroupCoordinator) or ps.get_pcp_group().world_size!=1:
                raise RuntimeError("native PCP1 coordinator failed")
            yield
        finally:
            if ps._PCP is not None:
                ps._PCP.destroy();ps._PCP=None
            ps.destroy_distributed_environment()

def mixed_case(torch,gdn,legacy,h,logical,batch,mode,config_path,steps=STEPS,diagnostics=None,captures=None):
    import json
    import vllm.forward_context as fc
    import vllm_ascend.ops.gdn_attn_builder as mb
    import vllm_ascend.ops.triton.fla.chunk as chunk
    from vllm.model_executor.layers.mamba.gdn import qwen_gdn_linear_attn as qwen
    from vllm.v1.attention.backends.gdn_attn import GDNAttentionMetadata
    require_digest(fc.__file__,CONTEXT_SHA);require_digest(mb.__file__,BUILDER_SHA)
    require_digest(chunk.__file__,CHUNK_SHA);require_digest(qwen.__file__,QWEN_SHA)
    require_digest(Path(chunk.__file__).with_name('l2norm.py'),'07657e33f2240cf39e8dec9991d00022181b43946a8c1497c6c236bf4c230126')
    require_digest(config_path,CONFIG_SHA)
    cfg=json.loads(Path(config_path).read_text())["text_config"]
    geometry=(cfg["linear_num_key_heads"],cfg["linear_num_value_heads"],
        cfg["linear_key_head_dim"],cfg["linear_value_head_dim"],cfg["linear_conv_kernel_dim"])
    if geometry!=(16,48,128,128,4) or cfg["mamba_ssm_dtype"]!="float32" or cfg["dtype"]!="bfloat16":
        raise RuntimeError("real Qwen local geometry drift")
    slots=2*batch+4;tokens=batch+64;gen=torch.Generator().manual_seed(2610154301+batch)
    initial=(torch.randn((slots,12,128,128),generator=gen)*.005).float()
    state=h.allocate_state(initial);native=initial.to("npu:0")
    conv_initial=(torch.randn((slots,3,2560),generator=gen)*.01).bfloat16()
    conv=conv_initial.to("npu:0");native_conv=conv_initial.to("npu:0")
    weights=(torch.randn((2560,1,4),generator=gen)*.05).bfloat16().to("npu:0")
    A_log=(torch.randn(12,generator=gen)*.05).float().to("npu:0")
    dt_bias=torch.full((12,),-2.,dtype=torch.float32,device="npu:0")
    rearrange=native_method(Path(qwen.__file__).read_text(),"QwenGatedDeltaNetAttention",
        "rearrange_mixed_qkv",{"torch":torch})
    def layer(prefix,arena,cstate):
        obj=SimpleNamespace(prefix=prefix,kv_cache=[cstate,arena],tp_size=4,
            key_dim=2048,value_dim=6144,head_k_dim=128,head_v_dim=128,
            num_k_heads=16,num_v_heads=48,conv_kernel_size=4,activation="silu",
            conv1d=SimpleNamespace(weight=weights,bias=None),A_log=A_log,dt_bias=dt_bias)
        obj.rearrange_mixed_qkv=functools.partial(rearrange,obj)
        return obj
    candidate_layer=layer("numeric.layers.0.linear_attn",state["base"],conv)
    native_layer=layer("numeric.reference.layers.0.linear_attn",native,native_conv)
    aux={**state,"base_ptr":state["base"].untyped_storage().data_ptr(),"slots":slots}
    candidate_layer._qwen36_deltalog_aux=aux
    def route(*args,**kwargs):
        before={k:v.cpu() for k,v in state.items()}
        args_cpu={k:v.cpu() if isinstance(v,torch.Tensor) else v for k,v in kwargs.items() if k!='state'}
        value=_route(torch,legacy,*args,**kwargs)
        torch.npu.synchronize()
        if captures is not None:
            from . import provider as _provider043
            actual_sidecar043=_provider043._OP.take("mixed")
            captures.setdefault("decode",[]).append(dict(before=before,inputs=args_cpu,output=value.cpu(),actual_sidecar043=actual_sidecar043))
        return value
    specialized=clone_core(Path(gdn.__file__).read_text(),vars(gdn),route)
    original_chunk=specialized.__globals__["chunk_gated_delta_rule"]
    # BEGIN DL030 counter
    native_chunk_counter=0
    # END DL030 counter
    def captured_chunk(*args,**kwargs):
        # BEGIN DL030 nonlocal
        nonlocal native_chunk_counter
        # END DL030 nonlocal
        raw={k:v.cpu() if isinstance(v,torch.Tensor) else v for k,v in kwargs.items() if k in("q","k","v","g","beta","initial_state","cu_seqlens","use_qk_l2norm_in_kernel")}
        # BEGIN DL030 before
        call_before=E030.begin(torch,original_chunk,gdn,chunk,native_chunk_counter,args,kwargs,raw)
        # END DL030 before
        value=original_chunk(*args,**kwargs)
        torch.npu.synchronize()
        # BEGIN DL030 after
        native_chunk_counter+=1
        call_evidence=E030.finish(torch,original_chunk,gdn,chunk,native_chunk_counter,call_before,value,kwargs)
        # END DL030 after
        if captures is not None:captures.setdefault("prefill",[]).append(dict(inputs=raw,output=value[0].cpu(),final_state=value[1].cpu()))
        # BEGIN DL030 attach
        if captures is not None:captures['prefill'][-1]['native_call']=call_evidence
        # END DL030 attach
        return value
    specialized.__globals__["chunk_gated_delta_rule"]=captured_chunk
    original=gdn.AscendGatedDeltaNetAttention._forward_core
    builder=SimpleNamespace(use_full_cuda_graph=False,vllm_config=SimpleNamespace(
        model_config=SimpleNamespace(hf_text_config=SimpleNamespace(**cfg)),
        parallel_config=SimpleNamespace(tensor_parallel_size=4,prefill_context_parallel_size=1)))
    starts_cpu=torch.tensor(list(range(batch+1))+[batch+64],dtype=torch.int32)
    starts=starts_cpu.to("npu:0");prefill_starts_cpu=torch.tensor([0,64],dtype=torch.int32)
    prefill_starts=prefill_starts_cpu.to("npu:0")
    indices=torch.arange(batch+1,dtype=torch.int32,device="npu:0")
    cache_indices=indices[:,None].contiguous()
    prefill_indices=indices[-1:]
    initial_modes=torch.ones(batch+1,dtype=torch.bool,device="npu:0")
    chunk_meta=mb._build_non_spec_chunked_prefill_metadata(builder,prefill_starts_cpu,torch.device("npu:0"))
    meta=GDNAttentionMetadata(num_prefills=1,num_prefill_tokens=64,num_decodes=batch,
        num_decode_tokens=batch,num_spec_decodes=0,num_spec_decode_tokens=0,
        num_actual_tokens=tokens,has_initial_state=initial_modes,
        chunk_indices=chunk_meta.chunk_indices_chunk64,chunk_offsets=chunk_meta.chunk_offsets_chunk64,
        prefill_query_start_loc=prefill_starts,prefill_state_indices=prefill_indices,
        prefill_has_initial_state=initial_modes[-1:],spec_query_start_loc=None,
        non_spec_query_start_loc=starts,spec_state_indices_tensor=None,
        non_spec_state_indices_tensor=indices,spec_sequence_masks=None,
        spec_token_indx=None,non_spec_token_indx=None,num_accepted_tokens=None,
        nums_dict=None,batch_ptr=None,token_chunk_offset_ptr=None)
    mb.AscendGDNAttentionMetadataBuilder._attach_non_spec_prefill_metadata(
        builder,meta,chunk_meta,cache_indices)
    mb.AscendGDNAttentionMetadataBuilder._attach_spec_decode_metadata(builder,meta)
    mb.AscendGDNAttentionMetadataBuilder._attach_non_spec_decode_metadata(builder,meta,cache_indices)
    context=fc.ForwardContext(no_compile_layers={candidate_layer.prefix:candidate_layer,
        native_layer.prefix:native_layer},attn_metadata={candidate_layer.prefix:meta,
        native_layer.prefix:meta},slot_mapping={})
    inp={name:torch.zeros(shape,dtype=torch.bfloat16,device="npu:0") for name,shape in
         (("mixed_qkv",(tokens,2560)),("b",(tokens,12)),("a",(tokens,12)))}
    out=torch.zeros((tokens,12,128),dtype=torch.bfloat16,device="npu:0")
    expected=torch.zeros_like(out)
    # All guards include native conv arena; no skipped/unchosen row may mutate.
    for n in AUX_NAMES:state[n][-2:].fill_(13)
    state["conv"]=conv
    guards={n:t[-2:].clone() for n,t in state.items()}
    pointers={n:t.data_ptr() for n,t in state.items()}
    # BEGIN DL030 initial
    if diagnostics is not None:
        diagnostics.initial(E030.initial(torch,initial,conv_initial,state,native,pointers,batch,__file__,config_path))
    # END DL030 initial
    def reset():
        h.reset_state({n:t for n,t in state.items() if n!="conv"},initial.to("npu:0"))
        conv.copy_(conv_initial.to("npu:0"))
        for n in AUX_NAMES:state[n][-2:].copy_(guards[n])
    def candidate():
        return execute_mixed_core(torch,legacy,gdn,specialized,original,
            candidate_layer,inp["mixed_qkv"],inp["b"],inp["a"],out)
    graph=None
    with fc.override_forward_context(context):
        if mode=="graph":
            for _ in range(3):candidate()
            torch.npu.synchronize();reset()
            graph=torch.npu.NPUGraph()
            with torch.npu.graph(graph):candidate()
            torch.npu.synchronize();reset()
        row=dict(batch=batch,mode=mode,scenario="mixed-prefill-decode",steps=0,passed=False,
            output_error=0.,state_relative_l2=0.,finite=True,untouched_bitwise=True,
            pointers_stable=True,inputs_unchanged=True,copy_source_unchanged=True,
            owner_isolated=True,redzones_unchanged=True,merge_observations=0,
            materialized_prefill_with_live_log=0,native_full_core_invocations=0,
            fixture_scope="real-single-rank-PCP1/TP4-local-geometry-not-serving")
        for step in range(steps):
            if captures is not None:captures.clear()
            # Swap decode0 and prefill slot every9 steps, so resumed prefill
            # genuinely consumes a delayed log; metadata storages remain fixed.
            decode=[0 if (step//9)%2==0 else batch]+list(range(1,batch))
            prefill=batch if decode[0]==0 else 0
            decode=decode[step%batch:]+decode[:step%batch]
            ids_cpu=torch.tensor(decode+[prefill],dtype=torch.int32)
            indices.copy_(ids_cpu.to("npu:0"));cache_indices[:,0].copy_(indices)
            initial_modes.fill_(True)
            if step in (5,33,73,113):initial_modes[-1:].fill_(False)
            for n,t in inp.items():
                t.copy_((torch.randn(tuple(t.shape),generator=gen)*.1).bfloat16().to("npu:0"))
            originals={n:t.clone() for n,t in inp.items()}
            chosen=torch.zeros(slots,dtype=torch.bool,device="npu:0")
            chosen.index_fill_(0,indices.long(),True)
            unchosen={n:t[~chosen].clone() for n,t in state.items()}
            decode_ids=indices[:batch].long()
            before_len=state["length"].index_select(0,decode_ids)[:,:,0].clone()
            before_base=state["base"].index_select(0,decode_ids).clone()
            row["materialized_prefill_with_live_log"]+=int((state["length"][prefill]>0).any().cpu())
            original(native_layer,inp["mixed_qkv"],inp["b"],inp["a"],expected)
            if graph is None:candidate()
            else:torch.npu.synchronize();graph.replay()
            torch.npu.synchronize();row["native_full_core_invocations"]+=1
            current=logical(state,indices.long())
            output_error=h.normalized_max_error(out,expected)
            reference=native.index_select(0,indices.long()).cpu().double()
            state_error=(float((current.double()-reference).square().sum())/
                         max(float(reference.square().sum()),1.0e-30))**0.5
            if diagnostics is not None:
                def snapshot():
                    return dict(kind="mixed",identity=(batch,mode,"mixed-prefill-decode"),step=step,
                        candidate_output=out.cpu(),native_output=expected.cpu(),native_state=native.cpu(),
                        state={k:v.cpu() for k,v in state.items()},ids=indices.cpu(),
                        inputs={k:v.cpu() for k,v in inp.items()},native_conv=native_conv.cpu(),
                        before_base=before_base.cpu(),before_length=before_len.cpu(),
                        prefill_slot=prefill,prefill_has_initial_state=bool(initial_modes[-1].cpu()),
                        prefill_aux_after={n:state[n][prefill].cpu()for n in AUX_NAMES},
                        unchosen={k:v.cpu()for k,v in unchosen.items()},guards={k:v.cpu()for k,v in guards.items()},original_inputs={k:v.cpu()for k,v in originals.items()},pointer_before=pointers,pointer_after={k:t.data_ptr()for k,t in state.items()},
                        producer_logical_CPU_FP64=current,producer_state_error=state_error,producer_output_error=output_error)
                diagnostics.step((batch,mode,"mixed-prefill-decode"),step,current,reference,state_error,output_error,snapshot,logical.last_norms)
            row["output_error"]=max(row["output_error"],output_error)
            row["state_relative_l2"]=max(row["state_relative_l2"],state_error)
            row["finite"] &= bool(torch.isfinite(out).all().cpu()) and bool(torch.isfinite(current).all())
            row["untouched_bitwise"] &= all(torch.equal(state[n][~chosen],t) for n,t in unchosen.items())
            row["inputs_unchanged"] &= all(torch.equal(inp[n],t) for n,t in originals.items())
            row["pointers_stable"] &= pointers=={n:t.data_ptr() for n,t in state.items()}
            row["redzones_unchanged"] &= all(torch.equal(state[n][-2:],t) for n,t in guards.items())
            row["owner_isolated"] &= torch.equal(conv,native_conv)
            row["copy_source_unchanged"] &= row["untouched_bitwise"]
            if any(bool((state[n][prefill]!=0).any().cpu()) for n in AUX_NAMES):
                raise RuntimeError("real prefill did not reset all auxiliary entries")
            append=before_len[:,0]<7
            if not torch.equal(before_base[append],state["base"].index_select(0,decode_ids)[append]):
                raise RuntimeError("mixed prefill materialized decode append slots")
            row["merge_observations"]+=int((before_len==7).any().cpu());row["steps"]=step+1
            if collection_reject(output_error,state_error,row,diagnostics,OUTPUT_LIMIT,STATE_LIMIT):
                if diagnostics is not None:diagnostics.capture("first-mixed-failure")
                raise RuntimeError("real mixed-core first failure "+str((batch,mode,step,row)))
        if row["materialized_prefill_with_live_log"]==0 or row["merge_observations"]==0:
            raise RuntimeError("mixed lifecycle/merge path never exercised")
        if diagnostics is not None:row["reference_final_raw"]=diagnostics.capture("mixed-final-success")
        row["passed"]=True;return row
