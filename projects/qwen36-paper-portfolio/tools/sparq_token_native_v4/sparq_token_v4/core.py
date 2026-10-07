"""SparQ paper Algorithm1/GQA token gather on unchanged native KV.
Default-off import; no model monkeypatch or performance admission.
Only selected channels then selected full tokens are gathered from original KV.
"""
from __future__ import annotations
import math
HEADS,DIM,BLOCK,SLOTS=6,256,128,16
def require(ok,text):
    if not ok:raise ValueError(text)
def support(query,cache,rows,lengths,rank=32,budget=128,local=1,variant="paper-gqa-probability"):
    import torch
    require(query.shape==(len(lengths),HEADS,DIM) and 1<=len(lengths)<=SLOTS and
            1<=rank<=DIM and type(budget) is int and budget>=max(1,local) and
            variant in ("paper-gqa-probability","author-ann-logits"),"frozen SparQ token geometry")
    supports=[];alphas=[];dims=[]
    for q,row,n in zip(query,rows,lengths):
        require(type(n) is int and n>0 and len(row)>=(n+BLOCK-1)//BLOCK,"native live length")
        channels=torch.argsort(q.float().abs().sum(0),descending=True,stable=True)[:rank]
        logical=torch.arange(n,device=q.device,dtype=torch.long)
        pages=torch.tensor(row,device=q.device,dtype=torch.long)
        physical=pages[torch.div(logical,BLOCK,rounding_mode="floor")]
        # Advanced indexing selects r channels BEFORE materializing cache tokens.
        short=cache[physical[:,None],logical.remainder(BLOCK)[:,None],0,channels[None,:]].float()
        qshort=q.float().index_select(-1,channels)
        total=q.float().abs().sum(-1);covered=qshort.abs().sum(-1)
        temperature=torch.sqrt(torch.where(total>0,DIM*covered/total,torch.ones_like(total)))
        scores=(qshort@short.T)/temperature[:,None]
        approximate=torch.softmax(scores,dim=-1)
        ranking=approximate.sum(0) if variant=="paper-gqa-probability" else scores.sum(0)
        k=min(n,budget);forced=min(local,n)
        # Stable tie policy is an explicit deterministic port adaptation.
        if k==n:chosen=logical
        elif forced:
            prior=torch.argsort(ranking[:-forced],descending=True,stable=True)[:k-forced]
            chosen=torch.cat((prior,logical[-forced:])).sort().values
        else:chosen=torch.argsort(ranking,descending=True,stable=True)[:k].sort().values
        supports.append(chosen);alphas.append(approximate.index_select(1,chosen).sum(1));dims.append(channels)
    return supports,torch.stack(alphas),dims

def gather_selected(cache,rows,supports,output,counts):
    import torch
    require(len(rows)==len(supports)==output.shape[0] and output.shape[-2:]==(1,DIM),
            "selected token workspace")
    for i,(row,index) in enumerate(zip(rows,supports)):
        pages=torch.tensor(row,device=cache.device,dtype=torch.long)
        physical=pages[torch.div(index,BLOCK,rounding_mode="floor")]
        values=cache[physical,index.remainder(BLOCK),0,:]
        output[i,:values.shape[0],0,:].copy_(values)
        counts.append(values.shape[0])

class MeanBook:
    """Exact request lease/slot and next-native-token guard, not batch-row state."""
    def __init__(self,slots=SLOTS):self.slots=slots;self.live={};self.occupied={}
    def begin(self,rid,generation,slot,length):
        require(type(rid) is str and rid and type(generation) is int and generation>0 and
                type(slot) is int and slot in range(self.slots) and rid not in self.live and
                slot not in self.occupied and type(length) is int and length>0,"new exact mean lease")
        self.live[rid]=(generation,slot,length);self.occupied[slot]=rid
    def append(self,rid,generation,slot,native_position):
        require(self.live.get(rid)==(generation,slot,native_position),
                "duplicate/replay/ABA or foreign native mean append")
        self.live[rid]=(generation,slot,native_position+1)
    def finish(self,rid,generation):
        require(rid in self.live and self.live[rid][0]==generation,"exact finished mean identity")
        _,slot,_=self.live.pop(rid);del self.occupied[slot];return slot
    def native_live(self,identities):
        require(set(identities)==set(self.live),"paused requests retained, finish only exact")
        return dict(self.live)

class Guarded:
    """Fixed backing +64-element prefix/suffix; checked outside capture."""
    def __init__(self,torch,shape,dtype,device,fill=7):
        self.t=torch;self.shape=tuple(shape);count=math.prod(shape)
        self.backing=torch.full((count+128,),fill,dtype=dtype,device=device)
        self.value=self.backing[64:-64].view(shape);self.fill=fill
        self.identity=self.pointer()
    def pointer(self):
        t=self.value
        return (self.backing.data_ptr(),t.data_ptr(),t.storage_offset(),t.untyped_storage().nbytes(),tuple(t.shape),tuple(t.stride()),str(t.dtype))
    def intact(self):
        return bool((self.backing[:64]==self.fill).all().item() and (self.backing[-64:]==self.fill).all().item() and self.pointer()==self.identity)
    def bytes(self):return self.backing.untyped_storage().nbytes()

class MeanPool:
    def __init__(self,device,slots=SLOTS):
        import torch
        require(type(slots) is int and slots>=SLOTS,"actual persistent mean capacity")
        self._guards=[Guarded(torch,(slots,DIM),torch.float32,device),Guarded(torch,(slots,),torch.int64,device)]
        self.sums=self._guards[0].value;self.counts=self._guards[1].value;self.sums.zero_();self.counts.zero_()
        self.payload_bytes=slots*(DIM*4+8);self.bytes=sum(g.bytes() for g in self._guards)
        require(self.bytes==self.payload_bytes+128*(4+8),"actual guarded mean backing bytes; not cache saving")
    def guards(self):return all(g.intact() for g in self._guards)
    def prefill(self,slot,values):
        require(values.ndim==3 and values.shape[1:]==(1,DIM) and values.shape[0]>0,"full actual V prefill")
        self.sums[slot].copy_(values[:,0,:].float().sum(0));self.counts[slot]=values.shape[0]
    def append(self,slots,values):
        import torch
        require(values.shape==(slots.shape[0],1,DIM) and slots.dtype==torch.int64,"writer's true rows")
        self.sums.index_add_(0,slots,values[:,0,:].float())
        self.counts.index_add_(0,slots,torch.ones_like(slots))
    def means(self,slots):return self.sums.index_select(0,slots)/self.counts.index_select(0,slots)[:,None]
    def reset(self,slot):self.sums[slot].zero_();self.counts[slot]=0

class TokenWorkspace:
    """Static selected-token scratch, no eviction/repeated full KV.
    scratch bytes, approximate logits and means must be budgeted together.
    """
    def __init__(self,device,budget=128):
        import torch
        require(type(budget) is int and budget>0,"token budget")
        self.budget=budget;self.pages=(budget+BLOCK-1)//BLOCK;self.capacity=self.pages*BLOCK
        self.key=torch.zeros((SLOTS*self.pages+1,BLOCK,1,DIM),dtype=torch.bfloat16,device=device)
        self.value=torch.zeros_like(self.key)
        self.bytes=self.key.untyped_storage().nbytes()+self.value.untyped_storage().nbytes()
    def run(self,query,kc,vc,rows,lengths,mean=None,reallocation=False,rank=32,local=1,
            variant="paper-gqa-probability"):
        import torch,torch_npu
        b=query.shape[0]
        require(kc.shape==vc.shape and tuple(kc.shape[1:])==(BLOCK,1,DIM) and
                query.dtype==kc.dtype==vc.dtype==torch.bfloat16,"original native BF16 pool")
        selected,alpha,channels=support(query,kc,rows,lengths,rank,self.budget,local,variant)
        packed_k=self.key[:b*self.pages].view(b,self.capacity,1,DIM)
        packed_v=self.value[:b*self.pages].view(b,self.capacity,1,DIM)
        counts=[];gather_selected(kc,rows,selected,packed_k,counts)
        other=[];gather_selected(vc,rows,selected,packed_v,other)
        require(counts==other,"K/V same selected real token support")
        table=torch.arange(b*self.pages,device=query.device,dtype=torch.int32).view(b,self.pages)
        lens=torch.tensor(counts,device=query.device,dtype=torch.int32)
        out=torch.empty_like(query)
        # Native PA reads exactly the gathered token sequence; no whole-page surrogate.
        torch_npu._npu_paged_attention(query=query,key_cache=self.key,value_cache=self.value,
            num_heads=HEADS,num_kv_heads=1,scale_value=1/math.sqrt(DIM),
            block_table=table,context_lens=lens,out=out)
        if reallocation:
            require(mean is not None and mean.shape==(b,DIM),"request-safe actual V mean")
            out=(alpha[:,:,None]*out.float()+(1-alpha[:,:,None])*mean[:,None,:]).to(out.dtype)
        return out,{"support":selected,"alpha":alpha,"channels":channels,
                    "scratch_bytes":self.bytes,"full_native_KV_preserved":True,
                    "selector_graph_supported":False,"model_graph_supported":False}

class GraphTokenWorkspace:
    """Fixed trueB device topology; no host-to-device construction in decode.
    Graph's full candidate writer/mean/selector/gather/PA path remains NPU-pending.
    """
    def __init__(self,device,batch,max_pages,budget=128,rank=32,local=1):
        import torch
        require(type(batch) is int and batch in range(1,SLOTS+1) and
                type(max_pages) is int and max_pages>0 and
                type(budget) is int and 0<budget<=max_pages*BLOCK and
                type(rank) is int and 0<rank<=DIM and type(local) is int and 0<=local<=budget,
                "fixed real device topology")
        self.batch=batch;self.max_pages=max_pages;self.rank=rank;self.local=local;self.budget=budget
        self.capacity=max_pages*BLOCK;self.scratch_pages=(budget+BLOCK-1)//BLOCK
        self._guards=[]
        def alloc(shape,dtype,value=0):
            g=Guarded(torch,shape,dtype,device);self._guards.append(g);g.value.fill_(value);return g.value
        self.rows=alloc((batch,max_pages),torch.int64)
        self.lengths=alloc((batch,),torch.int32)
        self.logical=alloc((self.capacity,),torch.int64);self.logical.copy_(torch.arange(self.capacity,dtype=torch.int64,device=device))
        self.logical_page=alloc((batch,self.capacity),torch.int64);self.logical_page.copy_(torch.div(self.logical,BLOCK,rounding_mode="floor")[None,:].expand(batch,-1))
        self.offset=alloc((self.capacity,),torch.int64);self.offset.copy_(self.logical.remainder(BLOCK))
        self.batch_index=alloc((batch,),torch.int64);self.batch_index.copy_(torch.arange(batch,dtype=torch.int64,device=device))
        self.pa_table=alloc((batch,self.scratch_pages),torch.int32);self.pa_table.copy_(torch.arange(batch*self.scratch_pages,dtype=torch.int32,device=device).view(batch,self.scratch_pages))
        self.budget_tensor=alloc((batch,),torch.int32,budget)
        self.key=alloc((batch*self.scratch_pages+1,BLOCK,1,DIM),torch.bfloat16)
        self.value=alloc((batch*self.scratch_pages+1,BLOCK,1,DIM),torch.bfloat16)
        self.output=alloc((batch,HEADS,DIM),torch.bfloat16)
        self.corrected=alloc((batch,HEADS,DIM),torch.bfloat16)
        self.bytes=sum(g.bytes() for g in self._guards)
    def guards(self):return all(g.intact() for g in self._guards)
    def tensors(self):
        import torch
        return {n:t for n,t in vars(self).items() if isinstance(t,torch.Tensor)}
    def run(self,query,kc,vc,mean,reallocation=False,variant="paper-gqa-probability"):
        import torch,torch_npu
        require(query.shape==(self.batch,HEADS,DIM) and query.dtype==kc.dtype==vc.dtype==torch.bfloat16
                and kc.shape==vc.shape and kc.shape[1:]==(BLOCK,1,DIM),"graph native typed buffers")
        require(variant in ("paper-gqa-probability","author-ann-logits"),"explicit author recipe")
        channels=torch.argsort(query.float().abs().sum(1),dim=-1,descending=True,stable=True)[:,:self.rank]
        physical=self.rows.gather(1,self.logical_page)
        short=kc[physical[:,:,None],self.offset[None,:,None],0,channels[:,None,:]].float()
        qshort=query.float().gather(2,channels[:,None,:].expand(-1,HEADS,-1))
        total=query.float().abs().sum(-1);covered=qshort.abs().sum(-1)
        temperature=torch.sqrt(torch.where(total>0,DIM*covered/total,torch.ones_like(total)))
        logits=torch.bmm(qshort,short.transpose(1,2))/temperature[:,:,None]
        valid=self.logical[None,:]<self.lengths[:,None]
        logits=logits.masked_fill(~valid[:,None,:],float("-inf"))
        approximate=torch.softmax(logits,dim=-1)
        ranking=approximate.sum(1) if variant=="paper-gqa-probability" else logits.sum(1)
        ranking=ranking.masked_fill(~valid,float("-inf"))
        recent=valid & (self.logical[None,:]>=self.lengths[:,None]-self.local)
        ranking=ranking.masked_fill(recent,float("inf"))
        selected=torch.argsort(ranking,dim=-1,descending=True,stable=True)[:,:self.budget].sort(dim=-1).values
        selected_physical=physical.gather(1,selected);selected_offset=selected.remainder(BLOCK)
        nk=kc[selected_physical,selected_offset,0,:]
        nv=vc[selected_physical,selected_offset,0,:]
        sk=self.key[:self.batch*self.scratch_pages].view(self.batch,-1,DIM)
        sv=self.value[:self.batch*self.scratch_pages].view(self.batch,-1,DIM)
        sk[:,:self.budget].copy_(nk);sv[:,:self.budget].copy_(nv)
        context=torch.minimum(self.lengths,self.budget_tensor)
        torch_npu._npu_paged_attention(query=query,key_cache=self.key,value_cache=self.value,
            num_heads=HEADS,num_kv_heads=1,scale_value=1/math.sqrt(DIM),
            block_table=self.pa_table,context_lens=context,out=self.output)
        alpha=approximate.gather(2,selected[:,None,:].expand(-1,HEADS,-1)).sum(-1)
        if reallocation:
            require(mean.shape==(self.batch,DIM),"per-native-lease means")
            self.corrected.copy_((alpha[:,:,None]*self.output.float()+(1-alpha[:,:,None])*mean[:,None,:]).to(self.output.dtype))
            result=self.corrected
        else:result=self.output
        return result,selected,alpha,channels
