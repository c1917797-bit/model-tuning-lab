"""Canary-only ordering comparison; unchanged serialized C1 is the reference."""
from independent_native_decode_prepare import shadow_metrics,SHADOW_ATOL,SHADOW_RTOL


def verify_completion_shadow(actual,reference,plan,layer,emit):
    if len(actual)!=3 or len(reference)!=3:
        raise ValueError("C1 completion full output/state/conv required")
    metrics=[dict(shadow_metrics(x,y),tensor=name)
             for name,x,y in zip(("output","state","conv"),actual,reference)]
    passed=all(m["passed"] for m in metrics)
    emit({"event":"c1_layer_completion_shadow_checked","request_id":plan.request_id,
          "rank":plan.rank,"step":plan.step,"layer":layer,"metrics":metrics,
          "atol":SHADOW_ATOL,"rtol":SHADOW_RTOL,"passed":passed,
          "scope":"same-private-input serialized-vs-layer-completion C1 ordering only"})
    if not passed:raise ValueError("C1 layer completion serialized shadow failed")
