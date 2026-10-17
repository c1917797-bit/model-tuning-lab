"""Diagnostic clone of actual B010 call; never substitutes production result."""
from pathlib import Path
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
def bits(torch,a,b):return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
class Capture:
 def __init__(self,torch,production,debug):self.t=torch;self.production=production;self.debug=debug;self.pending=None;self.records=[];self.mixed_records=[];self.sink=None
 def __call__(self,*args):
  t=self.t
  if len(args)!=13:raise ValueError('actual production 13 arguments')
  before=[x.detach().cpu().clone()for x in args];clones=[x.clone()for x in args];debug_before=[x.detach().cpu().clone()for x in clones];b=args[0].shape[0]
  side_back=t.full((b*12*128+256,),13.,dtype=t.float32,device=args[0].device);side=side_back[128:-128].reshape(b,12,128);side.fill_(float('nan'))
  guard_before=t.cat((side_back[:128],side_back[-128:])).cpu()
  pointers=[dict(ptr=x.data_ptr(),shape=list(x.shape),stride=list(x.stride()),offset=x.storage_offset())for x in args]
  debug_pointers=[dict(ptr=x.data_ptr(),shape=list(x.shape),stride=list(x.stride()),offset=x.storage_offset())for x in clones]
  z=self.production(*args);dz=self.debug(*clones,side);t.npu.synchronize()
  after=[x.detach().cpu().clone()for x in args];da=[x.detach().cpu().clone()for x in clones];y=side.cpu();z0=z.cpu();dz0=dz.cpu()
  pair=all(bits(t,x,v)for x,v in zip(before,debug_before))and all(bits(t,x,v)for x,v in zip(after,da))and bits(t,z0,dz0)
  immutable=all(bits(t,before[i],after[i])for i in(0,1,2,3,4,11,12))
  guard=bool((side_back[:128]==13).all()and(side_back[-128:]==13).all())
  now=[dict(ptr=x.data_ptr(),shape=list(x.shape),stride=list(x.stride()),offset=x.storage_offset())for x in args]
  debug_now=[dict(ptr=x.data_ptr(),shape=list(x.shape),stride=list(x.stride()),offset=x.storage_offset())for x in clones]
  record=dict(before=before,debug_before=debug_before,after=after,debug_after=da,production_output=z0,debug_output=dz0,actual_precast_FP32=y,production_debug_bitwise=pair,inputs_unchanged=immutable,sidecar_redzones_pass=guard,sidecar_guards_before=guard_before,sidecar_guards_after=t.cat((side_back[:128],side_back[-128:])).cpu(),pointers_before=pointers,pointers_after=now,debug_pointers_before=debug_pointers,debug_pointers_after=debug_now)
  if self.sink is None:raise ValueError('actual raw sink not installed')
  self.pending=self.sink('sidecar-call-%04d.pt'%len(self.records),record);self.records.append(self.pending)
  if not(pair and immutable and guard and pointers==now and debug_pointers==debug_now):raise ValueError('actual production/debug transparency')
  return z
 def take(self,kind=None):
  if self.pending is None:raise ValueError('missing actual sidecar call')
  r=self.pending;self.pending=None
  if kind=='mixed':self.mixed_records.append(r)
  return r
def install(torch,provider,m,checked):
 for k in('debug_library','debug_build_ref','debug_kernel_source_ref'):checked(m[k])
 torch.ops.load_library(m['debug_library']['path']);namespace='qwen36_deltalog_split_scale_sidecar_v051'
 if not torch._C._dispatch_has_kernel_for_dispatch_key(namespace+'::decode','PrivateUse1'):raise ValueError('actual debug PrivateUse1')
 if not any(m['debug_library']['path']in s for s in Path('/proc/self/maps').read_text().splitlines()):raise ValueError('actual debug DSO mapped')
 c=Capture(torch,provider._OP,getattr(torch.ops,namespace).decode);provider._OP=c;return c
