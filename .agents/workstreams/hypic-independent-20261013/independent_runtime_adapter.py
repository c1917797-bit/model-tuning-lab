"""Source-bound request-map runtime adapter. No cache skipping is implemented here."""
import hashlib,inspect,threading,weakref
from pathlib import Path
from independent_request_map import freeze_request_slices
from independent_runner_context import install_runner_context
from independent_cache_map import freeze_cache_slices
BLOCK_TABLE_SHA256="b79a46abf8feb0e2ad9e9de64b55e6fc6d3597eadbd903993cbf4e3e74f1f324"
RUNNER_SHA256="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
steps=weakref.WeakKeyDictionary();lock=threading.Lock()
def verify_runner(cls):
    if cls.__name__!="NPUModelRunner" or cls.__module__!="vllm_ascend.worker.model_runner_v1":
        raise ValueError("unexpected runner identity")
    path=Path(inspect.getfile(cls))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=RUNNER_SHA256:
        raise ValueError("official runner source drift")
    if list(inspect.signature(cls._prepare_inputs).parameters)!=['self','scheduler_output','num_scheduled_tokens']:
        raise ValueError("prepare ABI drift")
def freeze_native_runner(runner,args,kwargs):
    from vllm.distributed import get_tp_group
    group=get_tp_group()
    if group.world_size!=4:raise ValueError("this27B campaign requires TP4")
    ids=tuple(runner.input_batch.req_ids);n=len(ids)
    scheduled=args[1] if len(args)>1 else kwargs['num_scheduled_tokens']
    scheduled=tuple(int(x) for x in scheduled[:n])
    computed=tuple(int(x) for x in runner.input_batch.num_computed_tokens_cpu[:n])
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
    from vllm.v1.worker.block_table import MultiGroupBlockTable
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
