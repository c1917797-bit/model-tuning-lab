"""Public-body chunk coordinates; global seam excluded exactly once."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PublicChunk:
    computed:int
    scheduled:int
    body_start:int
    body_end:int
    completes_public:bool
    conv_tail_start:int|None
    conv_tail_end:int|None

def public_chunk(computed,scheduled,public_length,*,boundary=8):
    if any(type(x) is not int for x in (computed,scheduled,public_length,boundary)):
        raise ValueError("integer chunk geometry required")
    if computed<0 or scheduled<=0 or boundary<3 or public_length<=boundary:
        raise ValueError("valid public chunk geometry required")
    end=computed+scheduled
    start=max(computed,boundary);stop=min(end,public_length)
    if start>=stop:local_start=local_end=0
    else:local_start=start-computed;local_end=stop-computed
    completes=computed<public_length<=end
    tail_start=public_length-3-computed if completes else None
    tail_end=public_length-computed if completes else None
    if completes and tail_start<0:
        raise ValueError("last chunk requires cross-chunk conv tail assembly")
    return PublicChunk(computed,scheduled,local_start,local_end,completes,tail_start,tail_end)

class ProducerCoverage:
    def __init__(self,request_id,identity):
        if not request_id:raise ValueError("explicit producer request identity required")
        self.request_id=request_id;self.identity=identity;self.next_token=0;self.complete=False
    def accept(self,request_id,identity,chunk):
        if self.complete or request_id!=self.request_id or identity!=self.identity:
            raise ValueError("producer generation/identity mismatch")
        if chunk.computed!=self.next_token:
            raise ValueError("producer chunk gap/replay")
        self.next_token=chunk.computed+chunk.scheduled
        self.complete=chunk.completes_public
        return self.complete
