"""Opt-in mixed-batch native-only preparation with full-path shadow controls."""
import torch
from independent_native_decode_pack import DecodeRow,pack_native_decode
from independent_native_decode_backend import run_private_native_decode
from independent_mixed_query_plan import NativeQueryPlan

# Pinned official recurrent operator e2e test uses these before this candidate.
# This is a bounded backend-consistency gate, NOT task quality/whole-model equality.
SHADOW_ATOL=1e-2
SHADOW_RTOL=3e-3

def shadow_metrics(actual,expected):
    if actual.shape!=expected.shape or not bool(torch.isfinite(actual).all()) or not bool(torch.isfinite(expected).all()):
        raise ValueError("native batch shadow shape/nonfinite")
    x=actual.float();y=expected.float();delta=(x-y).abs()
    allowed=SHADOW_ATOL+SHADOW_RTOL*y.abs()
    return {"max_abs":float(delta.max()),"rms":float(delta.square().mean().sqrt()),
            "max_scaled":float((delta/allowed).max()),"passed":bool((delta<=allowed).all())}

def prepare_native_decode(layer,plans,associations,mixed_qkv,b,a,metadata,*,shadowed,emit):
    offset=0;rows=[];chosen=[]
    for plan,assoc in zip(plans,associations):
        if isinstance(plan,NativeQueryPlan) and plan.scheduled_tokens==1:
            if len(plan.retained_offsets)!=1:raise ValueError("native one-token plan drift")
            rows.append(DecodeRow(plan.request_id,offset,assoc.state_slot,assoc.has_initial_state))
            chosen.append(plan)
        offset+=len(plan.retained_offsets)
    if not rows:return {}
    ranks={p.rank for p in chosen};steps={p.step for p in chosen}
    if len(ranks)!=1 or len(steps)!=1:raise ValueError("native decode context mismatch")
    indices=getattr(metadata,"non_spec_state_indices_tensor",None)
    if indices is None or indices.dtype not in (torch.int32,torch.int64):
        raise ValueError("live native SSM-index metadata absent")
    conv_cache,state_cache=layer.kv_cache[:2]
    packed=pack_native_decode(rows,mixed_qkv,b,a,conv_cache,state_cache)
    result=run_private_native_decode(layer,packed,ssm_index_dtype=indices.dtype)
    # Outer compact hook commits a row span [1, heads, value_dim], not a bare row.
    result={key:(output.unsqueeze(0),state,conv)
            for key,(output,state,conv) in result.items()}
    # Validate each layer's first singleton AND first multi-request group.
    shadow_key=(layer.prefix,len(rows)>1)
    if shadow_key not in shadowed:
        from independent_native_boundary import make_boundary_runner
        metrics=[]
        for i,row in enumerate(rows):
            expected=make_boundary_runner(layer,packed.projected[i:i+1],
                packed.b[i:i+1],packed.a[i:i+1],packed.conv[i],return_conv=True)(
                    packed.state[i].transpose(-1,-2).contiguous().clone())
            for label,actual,reference in zip(("output","state","conv"),result[row.request_id],expected):
                entry=shadow_metrics(actual,reference)
                metrics.append(dict(entry,request_id=row.request_id,tensor=label))
        passed=all(m["passed"] for m in metrics)
        emit({"event":"native_decode_batch_shadow_checked","layer":layer.prefix,
              "rank":chosen[0].rank,"step":chosen[0].step,"requests":[r.request_id for r in rows],
              "rows":len(rows),"atol":SHADOW_ATOL,"rtol":SHADOW_RTOL,
              "metrics":metrics,"passed":passed,"scope":"sampled-layer full private native boundary only"})
        if not passed:raise ValueError("native decode batch independent full-path shadow failed")
        shadowed.add(shadow_key)
    emit({"event":"native_decode_batch_completed","layer":layer.prefix,
          "rank":chosen[0].rank,"step":chosen[0].step,"requests":[r.request_id for r in rows],
          "slots":[r.state_slot for r in rows],"rows":len(rows),
          "private_buffers":True,"actual_slot_commit":"deferred"})
    return result
