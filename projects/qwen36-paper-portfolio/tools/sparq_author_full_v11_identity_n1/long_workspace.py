"""Independent shared ANN long-native-cache arena. Import is stdlib/OFF.
Inherited ANN.run is byte-bound numerical source; constructor only broadens the
registered real metadata capacity. Never modifies the numerical18-page class.
One max-B16 backing/rank is used across sequential FA layers and all batch views.
No actual model/NPU authority is granted by building these Python classes.
"""
import hashlib,importlib.util,sys
from pathlib import Path
import allocation_contract as c
KERNEL=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6")
WORKSPACE_SHA="3393fbd9552a2ec7fb914b472cb5ec00aa95025de9051433e372fe0b2e92e46e"
CONTRACT_SHA="b1fdf5714e8a64c63208bb05d46f31fcae2eabf343df3dad7966626e9bd7572a"
NUMERIC_MANIFEST_SHA="eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528"
def bound(path,want):
 p=Path(path);c.require(p.is_absolute() and p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==want,"exact inherited author numerical source bytes")
 return p
def numeric_source():
 # Does not authorize Torch/NPU/model; actual component whole-reader runs first
 # in future integration. A foreign cached contract is rejected, never replaced.
 bound(KERNEL/"SOURCE_MANIFEST.json",NUMERIC_MANIFEST_SHA);bound(KERNEL/"contract.py",CONTRACT_SHA)
 old=list(sys.path)
 try:
  sys.path.insert(0,str(KERNEL))
  import contract
  c.require(Path(contract.__file__).resolve()==KERNEL/"contract.py" and
   bound(contract.__file__,CONTRACT_SHA),"source-bound canonical contract, not unrelated cached module")
  spec=importlib.util.spec_from_file_location("_ann_long_domain_inherited_numeric",str(bound(KERNEL/"ann_workspace.py",WORKSPACE_SHA)))
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  c.require(module.ANNWorkspace.run.__module__==module.__name__,"unaltered ANN run function from frozen entire source")
  return module
 finally:sys.path[:]=old
def build(torch):
 numeric=numeric_source();base=numeric.substrate()
 class LongArena:
  def __init__(self,device,pages,actual_native_blocks,noncapture_warmup,other_owned,current,baseline,peak,geometry=None):
   c.require(noncapture_warmup is True and type(actual_native_blocks) is int and actual_native_blocks>=16*c.MIN_PAGES,
    "actual original native cache allocator C16 backing and noncapture warmup, not toy17blocks")
   self.geometry=geometry;self.plan=c.shape_plan(pages,geometry);self.admission=c.budget_admission(pages,other_owned,current,baseline,peak,geometry)
   self.pages=pages;self.batch=16;self.capacity=pages*128;self.rank=32;self.budget=128;self.local=1;self.scratch_pages=1
   self.base=base;self._guards=[];self._views={}
   dtype={1:torch.bool,2:torch.bfloat16,4:torch.float32,8:torch.int64}
   int32={"lengths","pa_table","budget_tensor"}
   for name,(shape,size) in self.plan.items():
    dt=torch.int32 if name in int32 else dtype[size]
    g=base.Guarded(torch,shape,dt,device,fill=True if dt==torch.bool else 7)
    self._guards.append(g);g.value.zero_();setattr(self,name,g.value)
   self.logical.copy_(torch.arange(self.capacity,dtype=torch.int64,device=device))
   self.logical_page.copy_((self.logical//128)[None,:].expand(16,-1))
   self.offset.copy_(self.logical.remainder(128));self.batch_index.copy_(torch.arange(16,dtype=torch.int64,device=device))
   self.pa_table.copy_(torch.arange(16,dtype=torch.int32,device=device)[:,None]);self.budget_tensor.fill_(128)
   self.bytes=sum(g.bytes() for g in self._guards)
   c.require(self.bytes==c.guarded_bytes(pages,geometry),"all actual Guarded byte accounting incl128 redzone elements per allocation")
   self.owner_identity={n:(getattr(self,n).data_ptr(),getattr(self,n).untyped_storage().data_ptr(),tuple(getattr(self,n).shape)) for n in self.plan}
  def view(self,batch):
   c.require(type(batch) is int and batch in c.BATCHES,"all original real batches1..16")
   if batch not in self._views:
    ws=object.__new__(numeric.ANNWorkspace)
    for name in ("base","max_pages","capacity","rank","budget","local","scratch_pages"):
     setattr(ws,name,self.pages if name=="max_pages" else getattr(self,name))
    ws.batch=batch;ws._guards=self._guards;ws.bytes=0 # owner accounted once, never zero real backing.
    for name in c.ROW_VIEWS:setattr(ws,name,getattr(self,name)[:batch])
    for name in c.FIXED_VIEWS:setattr(ws,name,getattr(self,name))
    # All views share the one untouched fixed guard page row16, NOT rowbatch.
    # .run only reads/writes key[:batch]/value[:batch], so extra rows stay unused.
    c.require(type(ws).run is numeric.ANNWorkspace.run and all(t.is_contiguous() for t in ws.tensors().values()),
     "same frozen ANN arithmetic plus contiguous first-B views, no copied/reimplemented mathematics")
    self._views[batch]=ws
   return self._views[batch]
  def guard_page(self):return self.key[16:17],self.value[16:17]
  def intact(self):
   return all(g.intact() for g in self._guards) and self.owner_identity=={
    n:(getattr(self,n).data_ptr(),getattr(self,n).untyped_storage().data_ptr(),tuple(getattr(self,n).shape)) for n in self.plan}
  def snapshot_copy(self,sample,batch,out,selected,alpha,channels):
   # Diagnostic graph only; original formal timing has NO observer copies.
   sample.output.copy_(out);sample.key[:batch].copy_(self.key[:batch]);sample.value[:batch].copy_(self.value[:batch])
   sample.key[-1:].copy_(self.key[16:17]);sample.value[-1:].copy_(self.value[16:17])
   sample.selected.copy_(selected);sample.alpha.copy_(alpha);sample.channels.copy_(channels)
 return LongArena
