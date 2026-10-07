"""Native recurrent padding is undefined; candidate/state finiteness remains strict."""
from __future__ import annotations
import math

FINITE_SCOPE = "kvbp.finite-scope/native-active-output-v2"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def finite_receipt(state, actual, expected, complete, native_state, active,
                   metrics, all_finite):
    """No masking/writing tensor data; only select the native-defined output domain.

    all_finite must evaluate every element of its argument. The NPU caller uses
    bool(torch.isfinite(t).all().cpu()). Inactive candidate output is still checked
    and the original independent zero_length_output_zero assertion is unchanged.
    """
    require(type(active) is int and 0 <= active <= actual.shape[0],
            "invalid active domain")
    require(tuple(actual.shape) == tuple(expected.shape) and len(actual.shape) == 3
            and tuple(actual.shape[1:]) == (12,128),
            "complete candidate/native output shape differs")
    require(set(state) == {"base","k_log","u_log","lambda_log","decay","length"},
            "complete state/log finite coverage differs")
    metric_finite = all(math.isfinite(v) for v in metrics)
    sources = {**{"state."+n:t for n,t in state.items()},
               "actual_all":actual, "expected_active":expected[:active],
               "logical_complete":complete, "native_state_all":native_state}
    parts = {name:all_finite(t) for name,t in sources.items()}
    require(all(type(v) is bool for v in parts.values()),
            "finite predicate must return an observed bool")
    return {
        "finite": metric_finite and all(parts.values()),
        "metric_finite": metric_finite, "finite_scope": FINITE_SCOPE,
        "finite_buffer_checks": parts, "native_expected_defined_rows": active,
        "native_expected_undefined_padding_rows": actual.shape[0]-active,
        "native_padding_values_rewritten": False,
    }
