"""Removable, opt-in model row pruning. Layer dispatch is supplied separately."""
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
import torch
from contextlib import ExitStack

CURRENT_COMPACT_MODEL=ContextVar('independent_compact_model',default=None)


@dataclass(frozen=True)
class CompactModelSelection:
    plans: tuple
    sampled_rows: tuple
    prompt_logprobs: bool = False
    cache_slices: tuple = ()
    attention_groups: tuple = ()
    writable_kv_slots: tuple = ()
    material_guard: object = None


def install_compact_model(model_class,*,enabled=False,verify_source=None,
                          select=None,emit=None,metadata_snapshot=False,
                          c2_block_table_snapshot=False):
    if not enabled:return lambda:None
    if type(c2_block_table_snapshot) is not bool:
        raise ValueError('explicit C2 block-table snapshot boolean required')
    if type(metadata_snapshot) is not bool:
        raise ValueError('explicit metadata snapshot boolean required')
    if not all(callable(x) for x in (verify_source,select,emit)):
        raise ValueError('source verifier, complete selection and evidence sink required')
    verify_source(model_class)
    inherited='forward' not in model_class.__dict__
    original=model_class.forward
    if getattr(original,'_independent_compact_model_owned',False):
        raise RuntimeError('compact model hook already installed')
    native_c2_forward=None
    if c2_block_table_snapshot:
        from independent_c2_native_forward import (
            verify_c2_native_forward,assert_c2_owned_forward)
        native_c2_forward=verify_c2_native_forward(model_class,original)

    @wraps(original)
    def wrapped(self,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):
        if c2_block_table_snapshot:
            assert_c2_owned_forward(self,model_class,wrapped,native_c2_forward)
        selection=select(self,input_ids,positions,intermediate_tensors,inputs_embeds)
        if selection is None:
            return original(self,input_ids,positions,intermediate_tensors,inputs_embeds)
        if intermediate_tensors is not None or selection.prompt_logprobs:
            raise ValueError('compact model requires single PP and no prompt logprobs')
        if CURRENT_COMPACT_MODEL.get() is not None:
            raise RuntimeError('nested compact model context')
        plans=tuple(selection.plans)
        if not plans:raise ValueError('empty compact selection')
        total=positions.shape[-1];cursor=0;rows=[];ids=set()
        for plan in plans:
            if (plan.token_start!=cursor or plan.request_id in ids
                    or (plan.rank,plan.step)!=(plans[0].rank,plans[0].step)):
                raise ValueError('compact batch identity/row coverage mismatch')
            ids.add(plan.request_id);rows.extend(plan.packed_rows())
            cursor+=plan.scheduled_tokens
        if cursor>total or len(set(rows))!=len(rows):
            raise ValueError('compact batch token coverage mismatch')
        samples=tuple(selection.sampled_rows)
        if not samples or any(type(x) is not int or x not in rows for x in samples):
            raise ValueError('sampling or logit row was pruned')
        if positions.ndim not in (1,2):raise ValueError('unsupported position shape')
        for p in plans:
            logical=positions[...,p.token_start:p.token_start+p.scheduled_tokens]
            expected=torch.arange(p.computed_tokens,p.computed_tokens+p.scheduled_tokens,
                                  dtype=positions.dtype,device=positions.device)
            if not torch.equal(logical,expected.expand_as(logical)):
                raise ValueError('text position identity drift')
        index=torch.tensor(rows,dtype=torch.int64,device=positions.device)
        compact_ids=None
        if input_ids is not None:
            if input_ids.ndim!=1 or input_ids.shape[0]!=total:
                raise ValueError('input ID row mismatch')
            compact_ids=input_ids.index_select(0,index.to(input_ids.device))
        compact_embeds=None
        if inputs_embeds is not None:
            if inputs_embeds.ndim!=2 or inputs_embeds.shape[0]!=total:
                raise ValueError('embedding row mismatch')
            compact_embeds=inputs_embeds.index_select(0,index.to(inputs_embeds.device))
        if compact_ids is None and compact_embeds is None:
            raise ValueError('model input absent')
        token=CURRENT_COMPACT_MODEL.set(selection)
        metadata_evidence=None;c2_metadata_evidence=None
        try:
            with ExitStack() as resources:
                if metadata_snapshot:
                    from independent_step_metadata_cache import forward_snapshot_scope
                    metadata_evidence=resources.enter_context(forward_snapshot_scope(
                        tuple((p.request_id,p.rank,p.step) for p in plans),enabled=True))
                if c2_block_table_snapshot:
                    from independent_c2_block_table_snapshot import (
                        c2_block_table_snapshot_scope,validate_c2_snapshot_forward)
                    from independent_runner_context import CURRENT_RUNTIME_SNAPSHOT
                    from vllm.forward_context import get_forward_context
                    identities,request_rows,native=validate_c2_snapshot_forward(
                        selection,get_forward_context(),CURRENT_RUNTIME_SNAPSHOT.get())
                    c2_metadata_evidence=resources.enter_context(c2_block_table_snapshot_scope(
                        identities,request_rows=request_rows,enabled=True,
                        source_verified_immutable=True))
                    c2_metadata_evidence.bind_native(native)
                if selection.material_guard is not None:
                    resources.enter_context(selection.material_guard)
                output=original(self,compact_ids,positions.index_select(-1,index),None,compact_embeds)
            if not isinstance(output,torch.Tensor) or output.ndim!=2 or output.shape[0]!=len(rows):
                raise ValueError('auxiliary/PP output or compact output row mismatch')
            # Pruned rows are never sampled. Zero placeholders restore the
            # official runner indexing contract without inventing body outputs.
            restored=output.new_zeros((total,output.shape[1]))
            restored.index_copy_(0,index.to(output.device),output)
            emit({'event':'compact_model_rows_completed','rank':plans[0].rank,
                  'step':plans[0].step,'original_rows':total,'retained_rows':len(rows),
                  'sampled_rows':list(samples),'request_ids':[p.request_id for p in plans],
                  'forward_metadata_snapshot':metadata_snapshot,
                  'c2_block_table_snapshot':c2_block_table_snapshot,
                  'c2_block_table_snapshot_reads':c2_metadata_evidence.reads if c2_metadata_evidence is not None else 0,
                  'c2_block_table_snapshot_hits':c2_metadata_evidence.hits if c2_metadata_evidence is not None else 0,
                  'metadata_snapshot_reads':metadata_evidence.reads if metadata_evidence is not None else 0,
                  'metadata_snapshot_hits':metadata_evidence.hits if metadata_evidence is not None else 0,
                  'scope':'model row pruning; layer mechanism proof required separately'})
            return restored
        finally:CURRENT_COMPACT_MODEL.reset(token)
    wrapped._independent_compact_model_owned=True
    model_class.forward=wrapped
    def stop():
        if model_class.forward is not wrapped:raise RuntimeError('model hook ownership changed')
        if inherited:delattr(model_class,'forward')
        else:model_class.forward=original
    return stop
