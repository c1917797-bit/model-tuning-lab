"""Bounded CPU affine accumulation for one canonical producer generation."""
from independent_public_chunk_plan import ProducerCoverage
from independent_c1_reference import SegmentAffine,compose_segments
from independent_compact_material_pool import CompactLinearBody

class PublicChunkState:
    def __init__(self,request_id,identity,*,max_bytes=16777216):
        if type(max_bytes) is not int or max_bytes<=0:raise ValueError("positive state bound required")
        self.coverage=ProducerCoverage(request_id,identity)
        self.affine=None;self.max_bytes=max_bytes
    def accept(self,request_id,identity,chunk,affine=None,conv_tail=None):
        body=chunk.body_end-chunk.body_start
        if bool(body)!=(affine is not None):raise ValueError("exact chunk affine required")
        if chunk.completes_public and (conv_tail is None or conv_tail.ndim!=2 or conv_tail.shape[0]!=3):
            raise ValueError("final canonical conv tail required")
        # Validate coverage before mutating numerical accumulation.
        c=self.coverage
        if c.complete or c.request_id!=request_id or c.identity!=identity or c.next_token!=chunk.computed:
            raise ValueError("producer generation/coverage mismatch")
        updated=self.affine
        if affine is not None:
            t=affine.transition.detach().to("cpu").clone()
            s=affine.zero_state.detach().to("cpu").clone()
            if t.ndim!=3 or s.ndim!=3 or t.shape[:2]!=s.shape[:2] or t.shape[-1]!=s.shape[-2]:
                raise ValueError("chunk state layout mismatch")
            if t.numel()*t.element_size()+s.numel()*s.element_size()>self.max_bytes:
                raise ValueError("chunk state memory bound exceeded")
            incoming=SegmentAffine(t,s)
            updated=incoming if updated is None else compose_segments(updated,incoming)
        if chunk.completes_public and updated is None:raise ValueError("public body missing")
        complete=c.accept(request_id,identity,chunk)
        self.affine=updated
        if not complete:return None
        tail=conv_tail.detach().to("cpu").clone()
        return CompactLinearBody(identity,updated,tail)
