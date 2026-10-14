"""One producer's canonical KV rows assembled across contiguous native chunks."""
import torch
from independent_public_chunk_plan import ProducerCoverage

class PublicChunkKV:
    def __init__(self,request_id,identity,*,max_bytes=67108864):
        self.coverage=ProducerCoverage(request_id,identity)
        self.max_bytes=max_bytes;self.keys=None;self.values=None;self.written=0
    def accept(self,request_id,identity,chunk,keys,values):
        c=self.coverage
        if c.complete or request_id!=c.request_id or identity!=c.identity or chunk.computed!=c.next_token:
            raise ValueError("KV producer generation/coverage mismatch")
        if keys.ndim!=3 or values.shape!=keys.shape or keys.shape[0]!=chunk.scheduled:
            raise ValueError("native scheduled KV coverage mismatch")
        if keys.dtype!=values.dtype or keys.device!=values.device or not keys.is_floating_point():
            raise ValueError("KV dtype/device mismatch")
        count=chunk.body_end-chunk.body_start
        if count:
            length=identity.length-identity.boundary_tokens
            if self.keys is None:
                size=2*length*keys.shape[1]*keys.shape[2]*keys.element_size()
                if type(self.max_bytes) is not int or not 0<size<=self.max_bytes:
                    raise ValueError("KV assembly memory bound exceeded")
                self.keys=torch.empty((length,*keys.shape[1:]),dtype=keys.dtype,device="cpu")
                self.values=torch.empty_like(self.keys)
            if tuple(self.keys.shape[1:])!=tuple(keys.shape[1:]) or self.keys.dtype!=keys.dtype:
                raise ValueError("KV chunk shape/dtype drift")
            start=chunk.computed+chunk.body_start-identity.boundary_tokens
            if start!=self.written:raise ValueError("KV public body gap")
            self.keys[start:start+count].copy_(keys[chunk.body_start:chunk.body_end].detach().to("cpu"))
            self.values[start:start+count].copy_(values[chunk.body_start:chunk.body_end].detach().to("cpu"))
            self.written+=count
        complete=c.accept(request_id,identity,chunk)
        if not complete:return None
        if self.written!=identity.length-identity.boundary_tokens:
            raise ValueError("KV public body incomplete")
        return {"keys":self.keys,"values":self.values,
            "positions":torch.arange(identity.boundary_tokens,identity.length,dtype=torch.int64)}
