"""Lazy private initial snapshots; unactivated until explicit runtime wiring.

Prepared results already own final tensors. A serial shadow still needs original
initial state, so only prepared/no-shadow may omit the redundant snapshot.
No cache mutation or numerical/ownership gate is performed here.
"""

def initial_snapshot(state_cache, conv_cache, slot, *, has_initial_state,
                     prepared_result, serial_shadow):
    for value in (has_initial_state, prepared_result, serial_shadow):
        if type(value) is not bool:
            raise ValueError("explicit snapshot policy booleans required")
    if type(slot) is not int or slot < 0:
        raise ValueError("actual nonnegative state slot required")
    if prepared_result and not serial_shadow:
        return None
    state=state_cache[slot].transpose(-1,-2).contiguous().clone()
    tail=conv_cache[slot].clone()
    if not has_initial_state:
        state.zero_()
        tail.zero_()
    return state,tail
