"""Matched metadata observer. Never wraps GDN core or alters inputs/results."""
from __future__ import annotations
import hashlib
import inspect
import json
import os
from pathlib import Path
import time
from contract import COMMON, LAYERS, PLUGIN_SHA, budget, canonical, digest, require, sha

def register():
    if os.environ.get("KVBP_SERVICE_EVIDENCE") != "1":
        return
    arm=os.environ.get("KVBP_SERVICE_ARM")
    require(arm in ("dense","candidate"),"explicit service arm required")
    root=Path(os.environ["KVBP_SERVICE_OUTPUT"]).resolve()
    require(root.is_dir() and Path("/kvbuffer-results") in root.parents,"external arm root required")
    import kvbuffer_parallel.patch as patch
    require(sha(patch.__file__) == PLUGIN_SHA,"frozen candidate source changed")
    # Idempotent forced order: candidate installs before observer; dense returns.
    patch.register()
    import vllm_ascend.ops
    import vllm_ascend.ops.gdn as gdn
    import vllm_ascend.worker.model_runner_v1 as runner_module
    from kvbuffer_parallel.contract import source_identity, live_bindings
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as target
    from vllm.distributed import get_tensor_model_parallel_rank, get_tensor_model_parallel_world_size
    import torch
    import torch.distributed as dist
    sources=source_identity()
    cls=gdn.AscendGatedDeltaNetAttention; runner_cls=runner_module.NPUModelRunner
    require(not hasattr(runner_cls,"_kvbp_service_original"),"service observer double install")
    service_root=Path(__file__).resolve().parents[1]
    arm_manifest=json.loads((root/"ARM.json").read_text())
    service_sources={str(p.relative_to(service_root)):sha(p) for p in service_root.rglob("*") if p.is_file()}
    require(service_sources==arm_manifest["service_sources"],"service observer/script source differs from launch")
    original=runner_cls._model_forward
    seen_requests=set(); proof_done=False; turns=0
    live_layers=[]; base_pins=None; aux_pins=None
    path=None
    event_io_seconds=0.0
    def emit(event,**fields):
        nonlocal path,event_io_seconds
        io_start=time.perf_counter()
        if path is None:
            rank=get_tensor_model_parallel_rank()
            path=root/("service-rank%d-pid%d.jsonl"%(rank,os.getpid()))
            require(not path.exists(),"rank evidence must not overwrite")
        with path.open("ab") as stream:
            stream.write(canonical(dict(event=event,rank=get_tensor_model_parallel_rank(),
                pid=os.getpid(),time_ns=time.time_ns(),arm=arm,**fields))+b"\n")
        event_io_seconds+=time.perf_counter()-io_start
    def fingerprint(auxiliary=False):
        result=[]
        for layer in live_layers:
            require(layer._forward_core.__func__ is target._forward_core and
                    layer.forward.__func__ is cls.forward,"receiver rebound during live service")
            tensors=[layer.kv_cache[1]]
            if auxiliary:
                aux=getattr(layer,"_kvbp_aux",None)
                require(aux is not None and aux["base_ptr"]==tensors[0].untyped_storage().data_ptr(),
                        "native state storage changed while auxiliary payload live")
                tensors.extend(aux[n] for n in ("k_log","u_log","lambda_log","decay","length"))
            result.append((layer.prefix,[(t.data_ptr(),t.untyped_storage().data_ptr(),
                           tuple(t.shape),str(t.dtype),str(t.device),tuple(t.stride())) for t in tensors]))
        return result
    def wrapped(runner,*args,**kwargs):
        nonlocal proof_done,turns,live_layers,base_pins,aux_pins
        observer_start=time.perf_counter()
        count=int(runner.input_batch.num_reqs)
        ids=tuple(runner.input_batch.req_ids[:count])
        if not ids:
            require(not proof_done,"post-live untracked warmup rejected")
            return original(runner,*args,**kwargs)
        try:
            require(dist.is_initialized() and dist.get_world_size()==4 and
                    get_tensor_model_parallel_world_size()==4,"world/TP4 required")
            rank=get_tensor_model_parallel_rank()
            require(rank in range(4) and torch.npu.current_device()==rank,"logical rank/device mismatch")
            config=runner.vllm_config
            require(runner.model_config.enforce_eager and not runner.speculative_config and
                    runner.pcp_size==runner.dcp_size==1,"eager/non-spec/no-CP service only")
            require(config.cache_config.enable_prefix_caching is False and
                    str(config.cache_config.mamba_cache_mode)=="none" and
                    config.scheduler_config.enable_chunked_prefill is False,"unsupported state lifecycle")
            require(config.cache_config.kv_cache_memory_bytes == budget(arm)["native_bytes"],
                    "actual native budget differs")
            actual_common=dict(tensor_parallel_size=config.parallel_config.tensor_parallel_size,
                data_parallel_size=config.parallel_config.data_parallel_size,
                dtype=str(runner.model_config.dtype).removeprefix("torch."),
                max_model_len=runner.model_config.max_model_len,
                max_num_batched_tokens=config.scheduler_config.max_num_batched_tokens,
                max_num_seqs=config.scheduler_config.max_num_seqs,
                enforce_eager=runner.model_config.enforce_eager,
                enable_prefix_caching=config.cache_config.enable_prefix_caching,
                mamba_cache_mode=str(config.cache_config.mamba_cache_mode),
                enable_chunked_prefill=config.scheduler_config.enable_chunked_prefill,
                seed=runner.model_config.seed,speculative=bool(runner.speculative_config),profiling=False)
            require(actual_common==COMMON,"actual model/scheduler common configuration differs")
            context=gdn.get_forward_context()
            require(isinstance(context.attn_metadata,dict),"real attention context required")
            if not proof_done:
                bindings=live_bindings(context.no_compile_layers,cls,target,target._forward_core)
                owner=Path(inspect.getfile(target._forward_core)).resolve()
                require(sha(owner)==(PLUGIN_SHA if arm=="candidate" else sources[str(owner)]),
                        "actual owning core source differs")
                shapes={tuple(context.no_compile_layers[r["prefix"]].kv_cache[1].shape) for r in bindings}
                require(len(shapes)==1,"uniform state arena required")
                shape=shapes.pop()
                require(len(shape)==4 and shape[1:]==(12,128,128),"real local FP32 state shape differs")
                budget(arm,int(shape[0]))
                require(all(str(context.no_compile_layers[r["prefix"]].kv_cache[1].dtype)=="torch.float32"
                            for r in bindings),"native state is not FP32")
                emit("worker_proof",physical_device=rank+4,sources=sources,layers=bindings,common=actual_common,
                     service_sources=service_sources,
                     base_slots=shape[0],budget=budget(arm),
                     core_source=str(owner),core_source_sha256=sha(owner),
                     candidate_successful_turn_has_frozen_seen48_gate=arm=="candidate",
                     dense_scope="actual48-binding-native-network-not-new-per-core-hook")
                live_layers=[context.no_compile_layers[r["prefix"]] for r in bindings]
                base_pins=fingerprint()
                proof_done=True
            require(all(context.no_compile_layers.get(layer.prefix) is layer for layer in live_layers),
                    "forward context replaced an admitted receiver instance")
            require(fingerprint()==base_pins,"native cache storage/shape/stride changed")
            if aux_pins is not None:
                require(fingerprint(True)==aux_pins,"live auxiliary storage changed")
            # All are CPU scalars/views; no tensor.detach/cpu, no NPU synchronization.
            starts=runner.gdn_query_start_loc.cpu[:count+1].tolist()
            require(len(starts)==count+1 and starts[0]==0 and
                    all(x<y for x,y in zip(starts,starts[1:])),"CPU scheduler timeline")
            layer=next(k for k in context.attn_metadata if k in context.no_compile_layers and
                       isinstance(context.no_compile_layers[k],target))
            meta=context.attn_metadata[layer]
            nd,np=int(meta.num_decodes),int(meta.num_prefills)
            require(nd+np==count and starts[:nd+1]==list(range(nd+1)) and
                    int(meta.num_decode_tokens)==nd and nd<=16,"real mixed partition")
            for rid in ids:
                if rid in seen_requests:continue
                request=runner.requests[rid]
                from kvbuffer_parallel.contract import admit_text_request
                admit_text_request(request.prompt_token_ids,request.prompt_embeds,
                                   request.mm_features,request.prompt_is_token_ids)
                params=request.sampling_params
                require(params is not None and params.temperature==0 and params.seed==0 and
                        params.ignore_eos is True and params.max_tokens in (1,1024),"unexpected workload")
                emit("request_started",request_id=rid,prompt_ids_sha256=digest(request.prompt_token_ids),
                     prompt_tokens=len(request.prompt_token_ids),max_tokens=params.max_tokens)
                seen_requests.add(rid)
            observer_pre_seconds=time.perf_counter()-observer_start
            native_start=time.perf_counter()
            result=original(runner,*args,**kwargs)  # exact original args and result
            native_return=time.perf_counter()
            require(fingerprint()==base_pins,"native cache changed during forward")
            if arm=="candidate":
                actual_aux=fingerprint(True)
                if aux_pins is None:
                    aux_pins=actual_aux
                    emit("aux_storage_proof",pointers=aux_pins,scope="metadata-only-no-value-read")
                require(actual_aux==aux_pins,"auxiliary cache changed during forward")
            turns+=1
            emit("successful_turn",turn=turns,request_ids=ids,num_decodes=nd,num_prefills=np,
                 num_actual_tokens=starts[-1],pure_decode=bool(nd and not np),
                 mixed=bool(nd and np),native_prefill_resets=np if arm=="candidate" else 0,
                 materialized_slots_per_layer=nd if arm=="candidate" and np else 0,
                 candidate_layers_admitted=48 if arm=="candidate" else 0,
                 native_arguments_unmodified=True,observer_pre_seconds=observer_pre_seconds,
                 native_host_envelope_seconds=native_return-native_start,
                 prior_evidence_io_seconds_total=event_io_seconds,
                 observer_post_before_emit_seconds=time.perf_counter()-native_return,
                 storage_pointers_unchanged=True,
                 timing_scope="CPU-only-not-NPU-critical-path")
            return result
        except BaseException as error:
            emit("failed",error=repr(error));raise
    runner_cls._kvbp_service_original=original
    runner_cls._model_forward=wrapped
