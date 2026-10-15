"""One leased material acquisition per unique body/layer in a packed C1 wave."""
import torch
from independent_mixed_query_plan import NativeQueryPlan
from independent_c1_packed_wave import build_wave_layout
from independent_plan_material_identity import identity_for_plan
from independent_hybrid_material import validate_material
from independent_c1_packed_backend import run_packed_c1,source_verified_backend

def prepare_packed_layer(layer,stage,plans,associations,projected,b,a,leases,
                         backend_state,*,finite_check=None,probe_factory=None,
                         short_prefix_policy="chunk64",prefix_route_observer=None):
    layout=build_wave_layout(plans,associations)
    conv_cache,state_cache=layer.kv_cache[:2]
    states=[];tails=[];leased={};materials={};identities={}
    for plan,assoc in zip(plans,associations):
        state=state_cache[assoc.state_slot].transpose(-1,-2).contiguous().clone()
        tail=conv_cache[assoc.state_slot].clone()
        if not assoc.has_initial_state:state.zero_();tail.zero_()
        states.append(state);tails.append(tail)
        if isinstance(plan,NativeQueryPlan):continue
        expected=identity_for_plan(stage,layer.prefix,plan);key=plan.tokens_sha256
        if key not in materials:
            generation,body=leases.enter_context(stage.compact_store.acquire_private(
                expected,device=projected.device))
            materials[key]=body;identities[key]=(expected,generation)
        body=materials[key];identity,generation=identities[key]
        validate_material(body.identity,expected);validate_material(identity,expected)
        if (plan.rank!=expected.rank or key!=expected.tokens_sha256
                or plan.body_end-plan.body_start!=expected.length-expected.boundary_tokens):
            raise ValueError("packed C1 plan/material coverage mismatch")
        if state.shape!=body.affine.zero_state.shape or tail.shape!=body.conv_tail.shape:
            raise ValueError("packed native state/material layout mismatch")
        leased[plan.request_id]=(expected,generation,body)
    if not layout.windows:return {},leased,layout
    if 'official' not in backend_state:
        backend_state['official']=source_verified_backend(layer)
    backend_state.pop('geometry',None)
    backend_state.pop('probe',None)
    probe=probe_factory(layer,layout,plans,leased) if probe_factory is not None else None
    if probe is not None:
        backend_state['probe']=probe
        leases.callback(probe.discard)
    probe_kwargs={'stage_probe':probe} if probe is not None else {}
    if short_prefix_policy!="chunk64":
        probe_kwargs.update(short_prefix_policy=short_prefix_policy,
                            prefix_route_observer=prefix_route_observer)
    result=run_packed_c1(layer,layout,projected,b,a,torch.stack(states),torch.stack(tails),
                         materials,backends=backend_state['official'],finite_check=finite_check,
                         geometry_observer=lambda geometry:backend_state.update(geometry=geometry),
                         **probe_kwargs)
    return result,leased,layout
