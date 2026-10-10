"""Actual raw publisher from original post-RoPE native Q/K/V and compact planes.
Independent CPU can reconstruct every past token without a candidate cache read.
"""
from pathlib import Path
import contract as C
def blob(x,torch):return x.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
class Publisher:
    def __init__(self,root,source,torch):
        self.root=Path(root);self.source=source;self.torch=torch;self.originals={};self.pre_binding={}
        C.need(self.root.is_absolute()and not self.root.exists()and self.root.parent.is_dir(),"absent owned rank raw sink")
        self.root.mkdir()
    def prefill(self,name,binding,descriptors,q,k,v):
        C.need(name not in self.originals and binding["phase"]=="prefill"and q.shape[0]==32768,"once true original prefill")
        directory=self.root/("layer-"+name.split(".")[2]);directory.mkdir()
        raw={axis:C.atomic(directory/(axis+"-prefill.bin"),blob(x,self.torch),binary=True)for axis,x in(("K",k),("V",v))}
        row=C.atomic(directory/"PREFILL.json",dict(schema="skvq.compiled-reader.original-prefill/v1",
          source_ref=self.source,native_binding=binding,descriptors=descriptors,original=raw,post_RoPE_K=True,
          original_precision=str(q.dtype),full32768_input=True))
        self.originals[name]={"prefill_ref":row,"decode_refs":[]};self.pre_binding[name]=binding
        return row
    def __call__(self,name,binding,descriptors,q,k,v,cache,scores,probs,output):
        directory=self.root/("layer-"+name.split(".")[2])/("decode-"+str(cache.length));directory.mkdir()
        current={axis:C.atomic(directory/(axis+".bin"),blob(x,self.torch),binary=True)for axis,x in(("Q",q),("K",k),("V",v))}
        self.originals[name]["decode_refs"].append(dict(length=cache.length,original=current))
        planes={axis:{key:C.atomic(directory/(axis+"-"+key+".bin"),blob(x,self.torch),binary=True)
          for key,x in p.items()}for axis,p in cache.pool.items()}
        actual={key:C.atomic(directory/(key+".bin"),blob(x,self.torch),binary=True)for key,x in
          (("scores",scores[:,:,:cache.length]),("probabilities",probs[:,:,:cache.length]),("output",output))}
        event=dict(schema="skvq.compiled-reader.model-frame/v1",source_ref=self.source,logical_layer=name,
          native_binding=binding,descriptors=descriptors,kind=str(q.dtype).removeprefix("torch."),bits=cache.bits,
          length=cache.length,capacity=cache.capacity,controls=C.atomic(directory/"controls.bin",blob(cache.controls,self.torch),binary=True),
          original_prefill_ref=self.originals[name]["prefill_ref"],
          original_decode_history=list(self.originals[name]["decode_refs"]),pool=planes,layouts=cache.layouts,
          current_input=current,actual=actual,native_dense_prefill_and_cache_write_retained=True,
          no_memory_reduction_claim=True,**C.scopes())
        return C.atomic(directory/"FRAME.json",event)
