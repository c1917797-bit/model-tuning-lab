"""C1 transition handoff for a decoder stream with public body rows omitted."""
import torch
from independent_c1_reference import apply_segment
from independent_hybrid_material import validate_material


def execute_compact_linear(material,expected,plan,initial_state,incoming_conv,
                           *,run_live):
    """run_live consumes offsets in the COMPACT hidden/projected row stream.

    Prefix and seam run first. Cached T/S then advances the recurrent state
    across the omitted body, and canonical body conv-tail feeds the suffix.
    Public body hidden/core outputs are never accessed or materialized here.
    Native slot writes are deferred to the caller after complete validation.
    """
    validate_material(material.identity,expected)
    if plan.rank!=expected.rank or plan.tokens_sha256!=expected.tokens_sha256:
        raise ValueError("compact request/material rank or token identity mismatch")
    if (plan.body_end-plan.body_start != expected.length-expected.boundary_tokens
            or not plan.windows or len(plan.windows)>2):
        raise ValueError("compact plan/body material coverage mismatch")
    if initial_state.shape!=material.affine.zero_state.shape:
        raise ValueError("incoming state layout mismatch")
    if (incoming_conv.shape!=material.conv_tail.shape
            or incoming_conv.ndim!=2 or incoming_conv.shape[0]!=3):
        raise ValueError("selected width4 conv-tail layout mismatch")
    if any(t.device!=initial_state.device for t in
           (incoming_conv,material.conv_tail,material.affine.transition,
            material.affine.zero_state)):
        raise ValueError("compact material device mismatch")
    state=initial_state.clone();tail=incoming_conv.clone();pieces=[]
    for i,w in enumerate(plan.windows):
        if i:
            state=apply_segment(material.affine,state)
            tail=material.conv_tail.clone()
        output,state,tail=run_live(w.compact_start,w.compact_end,state,tail)
        wanted=(w.compact_end-w.compact_start,initial_state.shape[0],initial_state.shape[-1])
        if (output.shape!=wanted or state.shape!=initial_state.shape
                or tail.shape!=incoming_conv.shape):
            raise ValueError("live compact linear output/state coverage mismatch")
        pieces.append(output)
    if len(plan.windows)==1:
        state=apply_segment(material.affine,state)
        tail=material.conv_tail.clone()
    output=torch.cat(pieces,dim=0)
    if output.shape[0]!=len(plan.retained_offsets):
        raise ValueError("retained row count mismatch")
    if not all(torch.isfinite(t).all().item() for t in (output,state,tail)):
        raise ValueError("nonfinite compact C1 result")
    return output,state,tail
