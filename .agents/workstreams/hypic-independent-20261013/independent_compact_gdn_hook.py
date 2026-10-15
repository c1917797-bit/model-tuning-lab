"""Source-bound compact C1 core hook. Defaults disabled; model selection required."""
from contextlib import ExitStack
from functools import wraps
from pathlib import Path
import hashlib,inspect


def install_compact_gdn(stage,*,enabled=False,emit=None,native_decode_batch=False,
                        layer_completion=False,layer_shadow=False,packed_wave=False):
    if not enabled:return lambda:None
    if type(packed_wave) is not bool:raise ValueError('explicit packed C1 boolean required')
    if packed_wave and not (native_decode_batch and layer_completion and layer_shadow):
        raise ValueError('packed C1 canary requires native1 batch, finite gate and shadow')
    if type(native_decode_batch) is not bool:raise ValueError('native decode batch boolean required')
    if type(layer_completion) is not bool or type(layer_shadow) is not bool:
        raise ValueError('C1 completion/shadow booleans required')
    if layer_shadow and not layer_completion:raise ValueError('C1 shadow requires treatment')
    if not callable(emit):raise ValueError('compact evidence sink required')
    import torch
    from vllm.forward_context import get_forward_context
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as cls
    from independent_runner_context import CURRENT_REQUEST_SLICES
    from independent_compact_model_hook import CURRENT_COMPACT_MODEL
    from independent_runtime_adapter import associate_native_linear,associate_native_mixed_linear
    from independent_native_boundary import make_boundary_runner
    from independent_compact_linear import execute_compact_linear,execute_native_linear_plan
    from independent_mixed_query_plan import NativeQueryPlan
    from independent_linear_map import validate_linear_plan_associations
    from independent_plan_material_identity import identity_for_plan
    from independent_compact_material_pool import CompactLinearMaterialPool
    if not isinstance(stage.compact_store,CompactLinearMaterialPool):
        raise ValueError('compact CPU material store required')
    original=cls._forward_core
    shadowed=set();c1_shadowed=set();packed_shadowed=set();packed_backend={}
    if hashlib.sha256(Path(inspect.getfile(inspect.unwrap(original))).read_bytes()).hexdigest()!='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816':
        raise ValueError('official GDN source drift')
    if getattr(original,'_independent_private_owned',False) or getattr(original,'_independent_compact_gdn_owned',False):
        raise RuntimeError('conflicting C1 core hook')
    @wraps(original)
    def wrapped(self,mixed_qkv,b,a,core_attn_out):
        selected=CURRENT_COMPACT_MODEL.get()
        if selected is None:return original(self,mixed_qkv,b,a,core_attn_out)
        requests=CURRENT_REQUEST_SLICES.get();plans=selected.plans
        if not requests or len(requests)!=len(plans):
            raise ValueError('compact/native request coverage missing')
        for req,plan in zip(requests,plans):
            if (req.request_id,req.rank,req.step,req.token_start,req.scheduled_tokens)!=(plan.request_id,plan.rank,plan.step,plan.token_start,plan.scheduled_tokens):
                raise ValueError('compact/native request identity drift')
        raw=get_forward_context().attn_metadata
        if not isinstance(raw,dict) or self.prefix not in raw:
            raise ValueError('native linear metadata absent')
        mixed=any(isinstance(p,NativeQueryPlan) for p in plans)
        associations=(associate_native_mixed_linear(self,requests,raw[self.prefix])
                      if mixed else associate_native_linear(self,requests,raw[self.prefix]))
        associations=validate_linear_plan_associations(plans,associations)
        total=sum(len(p.retained_offsets) for p in plans)
        if any(x.shape[0]!=total for x in (mixed_qkv,b,a,core_attn_out)):
            raise ValueError('compact GDN projected row coverage mismatch')
        conv_cache,state_cache=self.kv_cache[:2];prepared=[];offset=0
        batched={};finite_guard=None;finite_kwargs={}
        if layer_completion:
            from independent_layer_finite_guard import LayerFiniteGuard
            finite_guard=LayerFiniteGuard()
            finite_kwargs={'finite_check':finite_guard.collect}
        if native_decode_batch:
            from independent_native_decode_prepare import prepare_native_decode
            batched=prepare_native_decode(self,plans,associations,mixed_qkv,b,a,
                raw[self.prefix],shadowed=shadowed,emit=emit,**finite_kwargs)
        with ExitStack() as leases:
            packed={};packed_materials={};packed_layout=None
            if packed_wave:
                from independent_c1_packed_prepare import prepare_packed_layer
                packed,packed_materials,packed_layout=prepare_packed_layer(
                    self,stage,plans,associations,mixed_qkv,b,a,leases,packed_backend,**finite_kwargs)
            hot_count=sum(not isinstance(p,NativeQueryPlan) for p in plans if p.request_id in packed)
            packed_shadow_key=(self.prefix,min(2,hot_count),len(packed)>1)
            check_packed_shadow=bool(packed) and packed_shadow_key not in packed_shadowed
            for plan,assoc in zip(plans,associations):
                is_native=isinstance(plan,NativeQueryPlan)
                generation=None;material=None
                if not is_native:
                    if packed_wave:
                        expected,generation,material=packed_materials[plan.request_id]
                    else:
                        expected=identity_for_plan(stage,self.prefix,plan)
                        generation,material=leases.enter_context(
                            stage.compact_store.acquire_private(expected,device=mixed_qkv.device))
                slot=assoc.state_slot
                state=state_cache[slot].transpose(-1,-2).contiguous().clone()
                tail=conv_cache[slot].clone()
                if not assoc.has_initial_state:state.zero_();tail.zero_()
                base=offset;initial_tail=tail
                def live(lo,hi,incoming,conv):
                    span=slice(base+lo,base+hi)
                    return make_boundary_runner(self,mixed_qkv[span],b[span],a[span],conv,
                                                return_conv=True,synchronize=not layer_completion)(incoming)
                if plan.request_id in batched:
                    output,final,tail=batched[plan.request_id]
                elif plan.request_id in packed:
                    output,final,tail=packed[plan.request_id]
                elif is_native:
                    output,final,tail=execute_native_linear_plan(plan,state,tail,run_live=live,**finite_kwargs)
                else:
                    output,final,tail=execute_compact_linear(material,expected,plan,state,tail,run_live=live,**finite_kwargs)
                if check_packed_shadow and plan.request_id in packed:
                    from independent_native_decode_prepare import shadow_metrics
                    def packed_serial_live(lo,hi,incoming,conv):
                        span=slice(base+lo,base+hi)
                        return make_boundary_runner(self,mixed_qkv[span],b[span],a[span],conv,
                            return_conv=True,synchronize=True)(incoming)
                    reference=(execute_native_linear_plan(plan,state,initial_tail,run_live=packed_serial_live)
                        if is_native else execute_compact_linear(material,expected,plan,state,initial_tail,
                                                                run_live=packed_serial_live))
                    metrics=[dict(shadow_metrics(x,y),tensor=label) for label,x,y in
                        zip(('output','state','conv'),(output,final,tail),reference)]
                    passed=all(m['passed'] for m in metrics)
                    emit({'event':'c1_packed_wave_shadow_checked','request_id':plan.request_id,
                        'rank':plan.rank,'step':plan.step,'layer':self.prefix,'metrics':metrics,
                        'passed':passed,'group_requests':list(packed),'private_buffers':True,
                        'atol':.01,'rtol':.003,
                        'actual_slot_commit':'not_started'})
                    if not passed:raise ValueError('packed C1 full private shadow failed')
                if (layer_shadow and not packed_wave and not is_native and self.prefix not in c1_shadowed
                        and plan.body_start>stage.boundary):
                    from independent_c1_completion_shadow import verify_completion_shadow
                    def serial_live(lo,hi,incoming,conv):
                        span=slice(base+lo,base+hi)
                        return make_boundary_runner(self,mixed_qkv[span],b[span],a[span],conv,
                            return_conv=True,synchronize=True)(incoming)
                    reference=execute_compact_linear(material,expected,plan,state,initial_tail,
                                                      run_live=serial_live)
                    verify_completion_shadow((output,final,tail),reference,plan,self.prefix,emit)
                    c1_shadowed.add(self.prefix)
                native=final.transpose(-1,-2).contiguous()
                end=offset+len(plan.retained_offsets)
                if native.shape!=state_cache[slot].shape or tail.shape!=conv_cache[slot].shape or output.shape!=core_attn_out[offset:end].shape:
                    raise ValueError('compact GDN native commit layout mismatch')
                prepared.append((plan,slot,generation,offset,end,output,native,tail));offset=end
            if check_packed_shadow:packed_shadowed.add(packed_shadow_key)
            if packed:
                emit({'event':'c1_packed_wave_prepared','rank':plans[0].rank,'step':plans[0].step,
                    'layer':self.prefix,'requests':list(packed),'windows':len(packed_layout.windows),
                    'packed_tokens':packed_layout.packed_tokens,'shared_wy_preparations':1,
                    'state_passes':3,'actual_slot_commit':'not_started'})
            if CURRENT_COMPACT_MODEL.get() is not selected or CURRENT_REQUEST_SLICES.get() is not requests:
                raise RuntimeError('request context changed before compact commit')
            if finite_guard is not None:
                covered=finite_guard.validate()
                emit({'event':'c1_layer_precommit_validated','rank':plans[0].rank,
                      'step':plans[0].step,'layer':self.prefix,'tensors':covered,
                      'requests':[p.request_id for p in plans],
                      'finite':True,'actual_slot_commit':'not_started'})
            # Every request is prepared before the first native state write.
            for plan,slot,generation,start,end,output,native,tail in prepared:
                state_cache[slot].copy_(native.to(state_cache.dtype))
                conv_cache[slot].copy_(tail.to(conv_cache.dtype))
                core_attn_out[start:end].copy_(output.to(core_attn_out.dtype))
            torch.npu.synchronize()
            for plan,slot,generation,start,end,output,native,tail in prepared:
                emit({'event':('mixed_native_gdn_completed' if isinstance(plan,NativeQueryPlan)
                               else 'compact_gdn_body_composed'),'request_id':plan.request_id,
                    'rank':plan.rank,'step':plan.step,'layer':self.prefix,'slot':slot,
                    'generation':generation,'retained_rows':end-start,
                    'skipped_body_tokens':plan.skipped_tokens,'finite':True})
        return None
    wrapped._independent_compact_gdn_owned=True;cls._forward_core=wrapped
    def stop():
        if cls._forward_core is not wrapped:raise RuntimeError('compact GDN hook ownership changed')
        cls._forward_core=original
        if 'official' in packed_backend:packed_backend['official'][-1].clear()
        packed_backend.clear();packed_shadowed.clear()
    return stop
