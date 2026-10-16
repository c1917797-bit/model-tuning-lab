"""Source-bound request-map runtime adapter. No cache skipping is implemented here."""
import hashlib,inspect,threading,weakref
from pathlib import Path
from independent_request_map import freeze_request_slices
from independent_runner_context import install_runner_context,CURRENT_PROMPT_TOKENS
from independent_cache_map import freeze_cache_slices
from independent_linear_map import freeze_prefill_linear_slices
BLOCK_TABLE_SHA256="8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a"
RUNNER_SHA256="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
steps=weakref.WeakKeyDictionary();lock=threading.Lock()

def associate_native_linear(layer,requests,metadata):
    """Source-bound pure-prefill GDN association for the treatment entry.
    Reject mixed/spec batches; fallback selection must happen before invoking.
    No tensor mutation or independently claimed scheduler ownership lease.
    """
    cls=type(layer)
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    if cls is not QwenGatedDeltaNetAttention:
        raise ValueError("unexpected linear runtime class")
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(cls._forward_core))).read_bytes()).hexdigest()!="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816":
        raise ValueError("official GDN source drift")
    if metadata.num_prefills!=len(requests):
        raise ValueError("pure-prefill sequence coverage mismatch")
    conv,state=layer.kv_cache[0],layer.kv_cache[1]
    if conv.shape[0]!=state.shape[0]:
        raise ValueError("conv/SSM slot capacity mismatch")
    return freeze_prefill_linear_slices(
        requests,metadata.prefill_query_start_loc.detach().cpu().tolist(),
        metadata.prefill_state_indices.detach().cpu().tolist(),
        metadata.prefill_has_initial_state.detach().cpu().tolist(),
        state_capacity=state.shape[0],
        speculative=metadata.spec_sequence_masks is not None,
        num_decodes=metadata.num_decodes)
def associate_native_mixed_linear(layer,requests,metadata):
    """Verified decode-first mixed association; no cache writes or activation.

    Decode-only frames have no initial-state mask in the official builder and
    stay on the unchanged native path. This entry requires a prefill tail.
    """
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    from vllm.v1.attention.backends.gdn_attn import GDNAttentionMetadata
    from vllm_ascend.ops.gdn_attn_builder import AscendGDNAttentionMetadataBuilder
    from independent_mixed_linear_map import freeze_mixed_linear_slices
    if type(layer) is not QwenGatedDeltaNetAttention or type(metadata) is not GDNAttentionMetadata:
        raise ValueError('unexpected mixed GDN runtime identity')
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(type(layer)._forward_core))).read_bytes()).hexdigest()!='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816':
        raise ValueError('official mixed GDN source drift')
    if hashlib.sha256(Path(inspect.getfile(GDNAttentionMetadata)).read_bytes()).hexdigest()!='27f5561c4b191f2be5a4a91820a6c64a38b755477b3f037178fb02bbc3bc1caf':
        raise ValueError('official mixed metadata builder drift')
    if hashlib.sha256(Path(inspect.getfile(AscendGDNAttentionMetadataBuilder)).read_bytes()).hexdigest()!='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16':
        raise ValueError('actual Ascend mixed metadata builder drift')
    if metadata.num_prefills<1 or metadata.has_initial_state is None:
        raise ValueError('mixed association requires native prefill tail')
    conv,state=layer.kv_cache[:2]
    if conv.shape[0]!=state.shape[0]:raise ValueError('mixed conv/state capacity drift')
    def cpu(value):
        if value is None:raise ValueError('mixed metadata tensor missing')
        return value.detach().cpu().tolist()
    return freeze_mixed_linear_slices(requests,
        cpu(metadata.non_spec_query_start_loc),cpu(metadata.non_spec_state_indices_tensor),
        cpu(metadata.has_initial_state),state_capacity=state.shape[0],
        num_decodes=metadata.num_decodes,num_prefills=metadata.num_prefills,
        num_decode_tokens=metadata.num_decode_tokens,
        prefill_query_start=cpu(metadata.prefill_query_start_loc),
        prefill_state_indices=cpu(metadata.prefill_state_indices),
        prefill_has_initial=cpu(metadata.prefill_has_initial_state),
        speculative=metadata.spec_sequence_masks is not None)

def verify_runner(cls):
    if cls.__name__!="NPUModelRunner" or cls.__module__!="vllm_ascend.worker.model_runner_v1":
        raise ValueError("unexpected runner identity")
    path=Path(inspect.getfile(cls))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=RUNNER_SHA256:
        raise ValueError("official runner source drift")
    if list(inspect.signature(cls._prepare_inputs).parameters)!=['self','scheduler_output','num_scheduled_tokens']:
        raise ValueError("prepare ABI drift")
def freeze_native_runner(runner,args,kwargs,*,prefill_prompt_snapshot=False):
    if type(prefill_prompt_snapshot)is not bool:
        raise ValueError("explicit prefill prompt snapshot boolean required")
    from vllm.distributed import get_tp_group
    group=get_tp_group()
    if group.world_size!=4:raise ValueError("this27B campaign requires TP4")
    ids=tuple(runner.input_batch.req_ids);n=len(ids)
    scheduled=args[1] if len(args)>1 else kwargs['num_scheduled_tokens']
    scheduled=tuple(int(x) for x in scheduled[:n])
    computed=tuple(int(x) for x in runner.input_batch.num_computed_tokens_cpu[:n])
    from independent_prompt_snapshot import freeze_prompt_tokens
    if prefill_prompt_snapshot:
        from independent_prefill_prompt_snapshot import freeze_prefill_prompt_tokens
        prompts=freeze_prefill_prompt_tokens(ids,runner.requests,computed_tokens=computed,
            scheduled_tokens=scheduled,enabled=True)
    else:
        prompts=freeze_prompt_tokens(ids,runner.requests)
    CURRENT_PROMPT_TOKENS.set(prompts)
    boundaries=tuple(int(x) for x in runner.query_start_loc.cpu[:n+1].tolist())
    with lock:
        step=steps.get(runner,0)+1;steps[runner]=step
    return freeze_request_slices(ids,computed,scheduled,boundaries,rank=group.rank_in_group,step=step)
def activate_context(*,enabled=False):
    if not enabled:return lambda:None
    # Official ops package must finish registration before DeviceOperator/runner.
    import vllm_ascend.ops
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    return install_runner_context(NPUModelRunner,freeze_native_runner,enabled=True,verify_source=verify_runner)

def capture_native_cache_slices(runner,requests,*,attention_group_ids):
    """Explicit diagnostic after native prepare; device-to-CPU sync, no writes.
    Caller supplies full-attention cache groups from actual cache specification.
    Never infer GDN state ownership from a KV slot mapping.
    """
    groups=tuple(attention_group_ids)
    if not groups or len(set(groups))!=len(groups) or any(type(x) is not int or x<0 for x in groups):
        raise ValueError("explicit unique attention cache groups required")
    verify_runner(type(runner))
    from vllm_ascend.worker.block_table import MultiGroupBlockTable
    cls=type(runner.input_batch.block_table)
    if cls is not MultiGroupBlockTable:
        raise ValueError("unexpected block-table implementation")
    if hashlib.sha256(Path(inspect.getfile(cls)).read_bytes()).hexdigest()!=BLOCK_TABLE_SHA256:
        raise ValueError("official block-table source drift")
    reqs=tuple(requests)
    if tuple(x.request_id for x in reqs)!=tuple(runner.input_batch.req_ids):
        raise ValueError("request batch changed before cache capture")
    total=sum(x.scheduled_tokens for x in reqs)
    tables=[];slots=[];sizes=[];counts=[];cp=[]
    for gid in groups:
        if gid>=len(runner.input_batch.block_table.block_tables):
            raise ValueError("attention cache group absent")
        table=runner.input_batch.block_table[gid]
        tables.append(table.get_numpy_array()[:len(reqs)].copy().tolist())
        counts.append(table.num_blocks_per_row[:len(reqs)].copy().tolist())
        slots.append(table.slot_mapping.gpu[:total].detach().cpu().tolist())
        sizes.append(table.block_size)
        cp.append(table.pcp_world_size*table.dcp_world_size)
    captured=freeze_cache_slices(reqs,tables,slots,block_sizes=sizes,
                               row_counts=counts,cp_world_sizes=cp)
    # Preserve native cache group IDs, not ordinal positions in this subset.
    from dataclasses import replace
    return tuple(replace(x,group=groups[x.group]) for x in captured)

def activate_cache_diagnostic(*,enabled=False,emit=None,max_batches=2):
    """Bounded real prepare-path observer. No technique activation/cache writes."""
    if not enabled:return lambda:None
    if not callable(emit) or type(max_batches) is not int or max_batches<1 or max_batches>4:
        raise ValueError("bounded diagnostic sink required")
    import vllm_ascend.ops
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    from vllm.v1.kv_cache_interface import FullAttentionSpec
    seen=weakref.WeakKeyDictionary()
    def observe(runner,requests):
        if seen.get(runner,0)>=max_batches:return
        groups=runner.kv_cache_config.kv_cache_groups
        ids=tuple(i for i,g in enumerate(groups) if isinstance(g.kv_cache_spec,FullAttentionSpec))
        if not ids:raise ValueError("no explicit full-attention cache group")
        captured=capture_native_cache_slices(runner,requests,attention_group_ids=ids)
        from dataclasses import asdict
        import os
        emit({"event":"native_cache_association","pid":os.getpid(),
              "requests":[asdict(x) for x in requests],
              "cache_slices":[asdict(x) for x in captured],
              "group_layers":{str(i):list(groups[i].layer_names) for i in ids},
              "scope":"read-only association; no ownership lease or HYPIC activation"})
        seen[runner]=seen.get(runner,0)+1
    return install_runner_context(NPUModelRunner,freeze_native_runner,enabled=True,
                                  verify_source=verify_runner,after_prepare=observe)
