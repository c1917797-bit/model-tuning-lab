"""All-or-native C1 batch planning and staged execution, without device imports."""
from independent_segment_selection import select_segment,require_full_scheduled_segment

def plan_prefill_batch(requests,prompts,public_tokens,identity_for,material_present):
    """Return complete immutable plans, or None BEFORE any request is modified.
    Mixed misses intentionally use native execution for the whole layer. This
    does not yet claim mixed decode/spec or overlapping-segment chunk support.
    """
    if not requests or prompts is None:return None
    plans=[]
    for req in requests:
        tokens=prompts.get(req.request_id)
        if tokens is None or tokens==tuple(public_tokens):return None
        try:
            selection=select_segment(tokens,public_tokens)
            require_full_scheduled_segment(selection,req)
        except ValueError:return None
        identity=identity_for(req)
        if not material_present(identity):return None
        plans.append((req,selection,identity))
    return tuple(plans)

def stage_prefill_batch(plans,associations,prepare):
    """Validate every owner before preparing; never commit native slots here."""
    if len(plans)!=len(associations):raise ValueError('batch association coverage')
    slots=set()
    for (req,_,_),a in zip(plans,associations):
        if (a.request_id,a.rank,a.step,a.row,a.token_start,a.token_end)!=(
                req.request_id,req.rank,req.step,req.row,req.token_start,req.token_end):
            raise ValueError('batch association identity')
        if a.state_slot in slots:raise ValueError('batch state alias')
        slots.add(a.state_slot)
    return tuple(prepare(plan,a) for plan,a in zip(plans,associations))
