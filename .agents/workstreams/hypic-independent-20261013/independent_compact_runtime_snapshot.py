"""Immutable current-step sampling and writable KV mapping for compact admission."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CompactRuntimeSnapshot:
    request_ids: tuple
    rank: int
    step: int
    sampled_rows: tuple
    cache_slices: tuple
    attention_groups: tuple
    writable_kv_slots: tuple
    prompt_logprobs: bool


def freeze_compact_runtime(requests,cache_slices,groups,sampled_rows,*,prompt_logprobs):
    """Input maps must come from this step's verified native runner capture.

    Scheduled mappings are the native write destinations. Reject all cross-
    request writes and computed-prefix aliases before granting compact writes.
    This does not change allocator ownership or retain slots past this step.
    """
    requests=tuple(requests);caches=tuple(cache_slices);groups=tuple(groups)
    if not requests:raise ValueError('request batch absent')
    rank=requests[0].rank;step=requests[0].step
    ids=tuple(r.request_id for r in requests)
    if len(set(ids))!=len(ids) or any((r.rank,r.step)!=(rank,step) for r in requests):
        raise ValueError('runtime request identity drift')
    samples=tuple(int(x) for x in sampled_rows)
    expected=tuple(r.token_end-1 for r in requests)
    if samples!=expected:raise ValueError('speculative or nonterminal sampling layout')
    gids=tuple(g for g,_ in groups)
    if not gids or len(set(gids))!=len(gids):raise ValueError('attention groups missing/duplicated')
    if len(caches)!=len(requests)*len(gids):raise ValueError('cache request/group coverage mismatch')
    leases=[]
    for gid in gids:
        seen=set();prefix=set();pairs=[]
        for req in requests:
            found=[c for c in caches if c.group==gid and c.request_id==req.request_id]
            if len(found)!=1:raise ValueError('cache association missing/duplicated')
            c=found[0]
            if (c.rank,c.step,c.row)!=(req.rank,req.step,req.row) or len(c.slots)!=req.scheduled_tokens:
                raise ValueError('cache step/row coverage drift')
            if c.block_size<=0:raise ValueError('invalid block size')
            for position in range(req.computed_tokens):
                block,offset=divmod(position,c.block_size)
                if block>=len(c.block_ids):raise ValueError('computed prefix map incomplete')
                prefix.add(c.block_ids[block]*c.block_size+offset)
            slots=set(c.slots)
            if len(slots)!=len(c.slots) or seen.intersection(slots):
                raise ValueError('scheduled writes alias within/between requests')
            seen.update(slots);pairs.append((req.request_id,gid,c.slots))
        if seen.intersection(prefix):raise ValueError('scheduled write aliases a computed shared prefix')
        leases.extend(pairs)
    return CompactRuntimeSnapshot(ids,rank,step,samples,caches,groups,tuple(leases),bool(prompt_logprobs))


def capture_compact_runtime(runner,requests):
    from independent_runtime_adapter import capture_native_cache_slices,verify_runner
    from vllm.v1.kv_cache_interface import FullAttentionSpec
    verify_runner(type(runner))
    if runner.use_cp:raise ValueError('compact runtime CP unsupported')
    groups=tuple((i,tuple(g.layer_names)) for i,g in enumerate(runner.kv_cache_config.kv_cache_groups)
                 if isinstance(g.kv_cache_spec,FullAttentionSpec))
    caches=capture_native_cache_slices(runner,requests,attention_group_ids=tuple(i for i,_ in groups))
    samples=runner.logits_indices.detach().cpu().tolist()
    return freeze_compact_runtime(requests,caches,groups,samples,
                                  prompt_logprobs=bool(runner.num_prompt_logprobs))


def activate_compact_runner(*,enabled=False,allow_mixed=False,emit=None,request_limit=128):
    if not enabled:return lambda:None
    import vllm_ascend.ops
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    from independent_runtime_adapter import freeze_native_runner,verify_runner
    from independent_runner_context import install_runner_context,CURRENT_RUNTIME_SNAPSHOT
    from independent_request_progress import RequestProgressLedger
    progress=RequestProgressLedger(request_limit)
    def capture(runner,requests):
        CURRENT_RUNTIME_SNAPSHOT.set(None)
        if emit is not None:
            for event in progress.observe(requests):emit(event)
        # Native mixed/decode and profiling paths continue without compact
        # admission. Complete eligible prefill is checked later by selector.
        if not requests or runner.use_cp:return
        if not allow_mixed and any(r.scheduled_tokens<=1 for r in requests):return
        if allow_mixed and all(r.scheduled_tokens<=1 for r in requests):return
        CURRENT_RUNTIME_SNAPSHOT.set(capture_compact_runtime(runner,requests))
    return install_runner_context(NPUModelRunner,freeze_native_runner,enabled=True,
                                  verify_source=verify_runner,after_prepare=capture)
