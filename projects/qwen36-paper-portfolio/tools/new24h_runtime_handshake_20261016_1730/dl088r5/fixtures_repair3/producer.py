"""Real native full GDN mixed core plus actual native descriptor copy."""
import argparse,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','authority-ref','lifecycle-ref','plan-ref','output'):p.add_argument('--'+k,required=True)
 p.add_argument('--steps',type=int,choices=(16,160),default=16);a=p.parse_args();sr,ar,lr,pr=[json.loads(getattr(a,k))for k in('source_ref','authority_ref','lifecycle_ref','plan_ref')];m=C.source(sr);C.window(ar);plan=C.obj(pr)
 C.need(plan['source']==sr and plan['authority']==ar and plan['lifecycle']==lr and plan['physical']==5 and plan['logical']==0 and plan['steps']==a.steps and a.steps in m['allowed_steps'] and plan['graph']is False,'actual owned eager plan/registered raw budget')
 if a.steps==160:
  smoke=C.obj(plan['smoke']);gate=C.load(m['files']['preregister.py'],'actual_registered_smoke_gate')
  gate.admit_smoke(smoke,sr,C.obj(smoke['independent_consumer']))
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'fresh leaf');out.mkdir();start=time.monotonic();records=[];events=[];primary=None;used=0
 import torch,torch_npu
 from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
 import vllm_ascend.ops.gdn as gdn
 from vllm.v1.worker import mamba_utils as mu
 from qwen36_deltalog_fresh import provider as V,primitives as L,runtime_helpers as H,native_fixture as F
 import copy_bootstrap as COPY
 torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0);init_device_properties_triton()
 admission=V.configure(sr,lr,explicit=True);import sidecar_capture;sidecar=sidecar_capture.install(torch,V,m,C.checked);h=C.load(m['probe_ref'],'frozen_inputs_native');R=C.load(m['files']['oracle.py'],'independent_scalar_oracle')
 canary=(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(canary==[4.,5.]and torch.npu.device_count()==1 and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0','actualsingleton')
 C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical=5,visible='0',plan=pr,canary=canary));end=time.monotonic()+30
 while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<end,'owned ARM30');time.sleep(.2)
 C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='deltalog.fresh-bridge-arm/v2',pid=os.getpid(),plan_sha256=pr['sha256'],physical=5),'actual MAIN PID/physical ARM')
 import raw_codec
 store=raw_codec.Store(torch,out,m['resources']['raw_cap_bytes'])
 def save(name,value):
  nonlocal used
  rr=store.write(out/name,value);used=store.used;return rr
 def legacy_save_unused(name,value):
  nonlocal used
  def size(v):
   if isinstance(v,torch.Tensor):return v.numel()*v.element_size()
   if isinstance(v,dict):return sum(size(x)for x in v.values())
   if isinstance(v,(list,tuple)):return sum(size(x)for x in v)
   return 0
  C.need(used+size(value)+2097152<=m['resources']['raw_cap_bytes'],'rawbudget8GiB beforewrite');path=out/name
  with path.open('xb')as f:torch.save(value,f)
  rr=C.ref(path);used+=rr['bytes'];return rr
 sidecar.sink=save
 def emit(name,**fields):events.append(dict(event=name,fields=fields,scope='actual-native-PCP1-TP4-local-geometry-not-serving',time_ns=time.time_ns()))
 native_copy=COPY.install(mu,out,execute=True)
 V.install_fixture(torch,gdn,mu,emit)
 COPY.marker(out,'delta-wrapper-installed',native_copy=native_copy)
 I=C.load(m['files']['flush_increment.py'],'actual021_increment')
 class FlushSink:
  def append(self,value):
   rr=save('dead-flush-%03d.pt'%sum(x['kind']=='dead_flush'for x in records),value);records.append(dict(kind='dead_flush',batch=int(value['ids'].numel()),raw=rr))
 I.install(torch,L,m['flush021_ref'],FlushSink(),execute=True,max_records=4)
 def logical(state,ids):
  host={k:v.cpu()for k,v in state.items()};result=torch.stack([R.restore(torch,host,int(s))for s in ids.cpu().tolist()]);logical.last_norms=dict(logical_norm_FP64=float(result.norm()));return result
 class Diagnostics:
  def __init__(self,batch,captures):self.batch=batch;self.captures=captures;self.last=None;self.started=time.monotonic()
  # BEGIN DL030 initial
  def initial(self,value):
   C.need(not hasattr(self,'initial_anchor_ref') and value['batch']==self.batch,'one actual initial anchor per batch')
   value['source']=sr;value['plan']=pr
   self.initial_anchor_ref=save('initial-anchor-B%d.pt'%self.batch,value)
  # END DL030 initial
  def step(self,identity,step,current,reference,state_error,output_error,snapshot,norms):
   # BEGIN DL030 attach-anchor
   C.need(hasattr(self,'initial_anchor_ref'),'initial anchor before first mixed raw')
   snapshot030=snapshot
   def snapshot():
    value030=snapshot030();value030['initial_anchor_ref']=self.initial_anchor_ref;return value030
   # END DL030 attach-anchor
   C.need(time.monotonic()-start<1800 and time.monotonic()-self.started<(600 if self.batch==1 else 1200),'numeric bounded1800/B1-600/B16-1200');value=snapshot();value['captures']=dict(self.captures);value['norms']=norms;rr=save('mixed-B%d-%03d.pt'%(self.batch,step),value);self.last=rr;records.append(dict(kind='mixed',batch=self.batch,step=step,raw=rr,producer_state_error=state_error,producer_output_error=output_error))
  def capture(self,reason):return self.last
 class Buffer:
  def __init__(self,n,dtype):self.cpu=torch.zeros(n,dtype=dtype);self.np=self.cpu.numpy();self.gpu=torch.zeros(n,dtype=dtype,device='npu:0')
  def copy_to_gpu(self,n):self.gpu[:n].copy_(self.cpu[:n]);return self.gpu[:n]
 def copy_case(batch,length):
  COPY.marker(out,'copy-before-B%d-L%d'%(batch,length),batch=batch,length=length)
  slots=2*batch+4;gen=torch.Generator().manual_seed(20261015000+batch*10+length);initial=(torch.randn((slots,12,128,128),generator=gen)*.005).float();state=h.allocate_state(initial);conv=(torch.randn((slots,3,2560),generator=gen)*.01).bfloat16().npu();layer=SimpleNamespace(prefix='bridge.copy.B'+str(batch),kv_cache=[conv,state['base']],_qwen36_deltalog_aux={**state,'base_ptr':state['base'].untyped_storage().data_ptr(),'slots':slots});ids=torch.arange(batch,dtype=torch.int32,device='npu:0');seq=torch.arange(batch+1,dtype=torch.int32,device='npu:0')
  for step in range(length):
   inp=h.make_inputs(batch,slots,step,gen);inp['indices']=ids;V._route(torch,L,layer,query=inp['query'],key=inp['key'],value=inp['value'],g=inp['g'],beta=inp['beta'],state=state['base'],scale=128**-.5,actual_seq_lengths=seq,ssm_state_indices=ids);torch.npu.synchronize()
  before={k:v.cpu()for k,v in state.items()};before_conv=conv.cpu();b=mu.MambaCopyBuffers(Buffer(batch*8,torch.int64),Buffer(batch*8,torch.int64),Buffer(batch*8,torch.int32),[0],None);cfg=SimpleNamespace(kv_cache_groups=[SimpleNamespace(layer_names=[layer.prefix])]);pairs=[]
  for s in range(batch):
   d=batch+s;pairs.append((s,d));req=SimpleNamespace(block_ids=([s,d],),req_id='bridge-fork-'+str(s));mu.collect_mamba_copy_meta(b,cfg,(mu.get_conv_copy_spec,mu.get_temporal_copy_spec),[0],0,1,0,req,{layer.prefix:layer})
  descriptor=dict(src=b.src_ptrs.cpu[:b.offset].clone(),dst=b.dst_ptrs.cpu[:b.offset].clone(),sizes=b.sizes.cpu[:b.offset].clone(),offset=b.offset);mu.do_mamba_copy_block(b);torch.npu.synchronize();after={k:v.cpu()for k,v in state.items()};after_conv=conv.cpu();proof=all(torch.equal(before[k][s],after[k][d])and torch.equal(before[k][s],after[k][s])for k in state for s,d in pairs)and all(torch.equal(before_conv[s],after_conv[d])and torch.equal(before_conv[s],after_conv[s])for s,d in pairs)
  rr=save('copy-B%d-L%d.pt'%(batch,length),dict(before=before,after=after,before_conv=before_conv,after_conv=after_conv,pairs=pairs,descriptors=descriptor,layer=layer.prefix,initial=initial));records.append(dict(kind='copy',batch=batch,length=length,raw=rr,producer_bitwise=proof,actual_descriptors=b.offset));C.need(proof and b.offset==7*batch,'actual nativecopy fullaux/conv proof')
  COPY.marker(out,'copy-after-B%d-L%d'%(batch,length),raw=rr,bitwise=proof,descriptors=b.offset)
 boundary_controls=[]
 try:
  import npu_controls
  boundary_controls=npu_controls.run(torch,h,sidecar)
  with F.native_pcp_context(torch):
   for batch in(1,16):
    for n in(0,1):
     gen=torch.Generator().manual_seed(2610152400+batch+n);slots=2*batch+4;initial=(torch.randn((slots,12,128,128),generator=gen)*.005).float();st=h.allocate_state(initial);layer=SimpleNamespace(prefix='explicit.flush.B%d.L%d'%(batch,n),kv_cache=[None,st['base']],_qwen36_deltalog_aux={**st,'base_ptr':st['base'].untyped_storage().data_ptr(),'slots':slots});ids=torch.arange(batch,dtype=torch.int32,device='npu:0')
     if n:
      inp=h.make_inputs(batch,slots,0,gen);inp['indices']=ids;V._route(torch,L,layer,query=inp['query'],key=inp['key'],value=inp['value'],g=inp['g'],beta=inp['beta'],state=st['base'],scale=128**-.5,actual_seq_lengths=torch.arange(batch+1,dtype=torch.int32,device='npu:0'),ssm_state_indices=ids)
     L._flush_slots(torch,layer,layer._qwen36_deltalog_aux,ids,'explicit-zero-or-partial')
   for batch in(1,16):
    COPY.marker(out,'mixed-before-B%d'%batch,batch=batch,steps=a.steps)
    captures={};d=Diagnostics(batch,captures);F.mixed_case(torch,gdn,L,h,logical,batch,'eager',m['config_ref']['path'],steps=a.steps,diagnostics=d,captures=captures)
    COPY.marker(out,'mixed-after-B%d'%batch,batch=batch,steps=a.steps)
   for batch in(1,16):
    for length in(1,7):copy_case(batch,length)
 except BaseException as e:primary=repr(e)
 finally:C.write(out/'RESULT.json',dict(schema='deltalog.actual-fresh-bridge/v5',source=sr,authority=ar,lifecycle=lr,plan=pr,steps=a.steps,records=records,actual_sidecar_records=sidecar.records,actual_mixed_sidecar_records=sidecar.mixed_records,boundary_controls=boundary_controls,events=events,primary=primary,admission=admission,raw_bytes=used,NPU=True,fullmodel=False,graph=False,copy_factory_qualified=False,scope='native-full-GDN-core-and-native-descriptor-copy-single-NPU-TP4local',elapsed_seconds=time.monotonic()-start))
 return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
