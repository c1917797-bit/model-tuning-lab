"""Independent request-local prefix/boundary/cached-body/tail C1 execution."""
import torch
from independent_linear_reuse import reuse_linear_segment
from independent_segment_selection import require_full_scheduled_segment

def execute_private_linear(material,expected,selection,request,initial_state,
                           incoming_conv,*,run_live):
    """run_live(lo,hi,state,conv) returns core output/key-major state/conv tail.
    Offsets refer to this request's scheduled token slice. All writes remain
    private until the serving caller verifies and commits native state slots.
    """
    start,end=require_full_scheduled_segment(selection,request)
    if end-start!=expected.length or selection.tokens_sha256!=expected.tokens_sha256:
        raise ValueError("private selection/material token identity mismatch")
    boundary_end=start+expected.boundary_tokens
    if boundary_end>=end:raise ValueError("cached body is empty")
    state=initial_state.clone();conv=incoming_conv.clone();parts=[]
    if start:
        output,state,conv=run_live(0,start,state,conv)
        if output.shape[0]!=start:raise ValueError("live prefix coverage mismatch")
        parts.append(output)
    def boundary(incoming):
        output,after,_=run_live(start,boundary_end,incoming,conv)
        return output,after
    core,state,conv=reuse_linear_segment(material,expected,state,boundary)
    parts.append(core)
    if end<request.scheduled_tokens:
        output,state,conv=run_live(end,request.scheduled_tokens,state,conv)
        if output.shape[0]!=request.scheduled_tokens-end:
            raise ValueError("live tail coverage mismatch")
        parts.append(output)
    output=torch.cat(parts,dim=0)
    if output.shape[0]!=request.scheduled_tokens:
        raise ValueError("private request output coverage mismatch")
    return output,state,conv
