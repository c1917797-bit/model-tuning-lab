"""Explicit timed mode, distinct from the mandatory-shadow numerical canary."""
def validate_c1_mode(*, packed, native, completion, shadow, probe, performance):
    if any(type(v)is not bool for v in (packed,native,completion,shadow,probe,performance)):
        raise ValueError("explicit C1 mode booleans required")
    if performance:
        if not (packed and native and completion) or shadow or probe:
            raise ValueError("timed mode requires packed/native/finite completion without diagnostics")
    elif packed and not (native and completion and shadow):
        raise ValueError("packed C1 canary requires native batch, completion and shadow")
    if shadow and not completion:
        raise ValueError("C1 shadow requires completion")
