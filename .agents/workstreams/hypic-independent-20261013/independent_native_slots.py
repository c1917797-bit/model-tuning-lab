"""Independent native linear-slot adapter; runtime request attachment pending."""
from independent_hybrid_material import validate_material,materialize_linear_body
def install_linear_material(actual,expected,body_affine,live_boundary_state,conv_tail,
                            ssm_slots,conv_slots,slot):
    validate_material(actual,expected)
    if not isinstance(slot,int) or slot<0 or slot>=ssm_slots.shape[0] or slot>=conv_slots.shape[0]:
        raise ValueError("invalid native slot")
    state=materialize_linear_body(actual,expected,body_affine,live_boundary_state)
    native_state=state.transpose(-1,-2).contiguous()
    if native_state.shape!=ssm_slots[slot].shape or conv_tail.shape!=conv_slots[slot].shape:
        raise ValueError("native state layout mismatch")
    if state.device!=ssm_slots.device or conv_tail.device!=conv_slots.device:
        raise ValueError("state device mismatch")
    # Validate both writes before either target is mutated. Caller must own slot
    # and retain its request/generation lease through device completion.
    ssm_slots[slot].copy_(native_state.to(ssm_slots.dtype))
    conv_slots[slot].copy_(conv_tail.to(conv_slots.dtype))
    return {'slot':slot,'state_layout':'value-major','request_identity':actual}
