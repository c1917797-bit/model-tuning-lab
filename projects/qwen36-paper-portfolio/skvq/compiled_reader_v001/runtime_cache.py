"""SKVQ-specific compact single-request eager cache, exact original writer only.
Diagnostic adapter retains native dense cache for unmodified prefill/native write;
therefore this module makes NO memory-saving or production-allocator claim.
"""
from layout import validate,addresses,interval,need
class Cache:
    def __init__(self,torch,layout_module,device_writer,layouts,*,bits,capacity,dtype,device):
        need(type(capacity)is int and capacity==33792 and type(bits)is int and bits in(2,4),"fixed current model capacity")
        self.torch=torch;self.layout_module=layout_module;self.writer=device_writer
        self.layouts={k:validate(layouts[k])for k in("K","V")};self.bits=bits;self.capacity=capacity
        self.length=0;self.request=None;self.epoch=0;self.closed=False;self.pool={}
        for axis,l in self.layouts.items():
            mapping,width=addresses(l,bits)
            self.pool[axis]=dict(payload=torch.full((1,capacity,width),165,dtype=torch.uint8,device=device),
              scales=torch.full((1,capacity,4),.5,dtype=dtype,device=device),
              zero_points=torch.full((1,capacity,4),-1.,dtype=dtype,device=device),
              edges=torch.zeros((1,133,256),dtype=dtype,device=device),
              map=torch.tensor(mapping,dtype=torch.int32,device=device))
        self.controls=torch.zeros((1,4),dtype=torch.int32,device=device)
    def layout(self,axis):
        l=self.layouts[axis]
        return self.layout_module.Layout(tuple(l["permutation"]),tuple(l["starts"]),tuple(l["smooth"]),l["clip"])
    def prefill(self,request,key,value):
        need(not self.closed and self.request is None and self.length==0 and type(request)is str and request,"new exact native request")
        need(key.shape==value.shape and tuple(key.shape[1:])==(1,256)and 1<=key.shape[0]<=32768,"actual full native prefill QKV")
        self.request=request;self.epoch+=1;self.length=key.shape[0];start,stop=interval(self.length)
        for axis,x in(("K",key),("V",value)):
            p=self.pool[axis];rows=x.reshape(self.length,256)
            if stop>start:self.writer.seal_into(rows[start:stop],self.layout(axis),
              p["payload"][0],p["scales"][0],p["zero_points"][0],start,bits=self.bits)
            p["edges"][0,:start].copy_(rows[:start])
            p["edges"][0,start:start+self.length-stop].copy_(rows[stop:self.length])
        self.controls.copy_(self.torch.tensor([[self.length,start,stop,0]],dtype=self.torch.int32,device=self.controls.device))
    def append(self,request,key,value):
        need(not self.closed and self.request==request and self.length>0 and self.length<self.capacity,"same actual request/epoch append")
        need(tuple(key.shape)==tuple(value.shape)==(1,1,256),"one actual fresh decode KV")
        start,oldstop=interval(self.length);newstart,newstop=interval(self.length+1)
        for axis,x in(("K",key),("V",value)):
            p=self.pool[axis];edge=p["edges"][0]
            if newstop>oldstop:
                # Quantize exactly the oldest live recent token before it leaves window.
                need(newstop-oldstop==1 and start==newstart,"one-token semantic transition")
                self.writer.seal_into(edge[start:start+1],self.layout(axis),
                  p["payload"][0],p["scales"][0],p["zero_points"][0],oldstop,bits=self.bits)
                count=self.length-oldstop-1
                if count:edge[start:start+count].copy_(edge[start+1:start+1+count].clone())
                edge[start+count].copy_(x.reshape(256))
            elif self.length<5:edge[self.length].copy_(x.reshape(256))
            else:edge[start+self.length-oldstop].copy_(x.reshape(256))
        self.length+=1;self.controls.copy_(self.torch.tensor([[self.length,newstart,newstop,0]],
          dtype=self.torch.int32,device=self.controls.device))
    def assert_live(self,request,epoch):
        need(not self.closed and request==self.request and epoch==self.epoch and 0<self.length<=self.capacity,"live actual request/epoch")
    def finish(self,request,epoch):
        self.assert_live(request,epoch);self.request=None;self.length=0;self.closed=True
        # Real model consumer must establish native finished dispatch; HTTP DONE cannot invoke this.
