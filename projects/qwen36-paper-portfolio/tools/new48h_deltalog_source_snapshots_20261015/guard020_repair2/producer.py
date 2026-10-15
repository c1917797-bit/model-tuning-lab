"""Actual eager kernels with request lifecycle; explicit owned ARM required."""
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','authority-ref','meta-ref','numeric-ref','plan-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,ar,mr,nr,pr=[json.loads(getattr(a,k))for k in('source_ref','authority_ref','meta_ref','numeric_ref','plan_ref')];m=C.source(sr);ad=C.admissions(m,ar,mr,nr);plan=C.obj(pr)
 C.need(plan['source']==sr and plan['physical']==4 and plan['logical']==0 and plan['admissions']==ad and plan['graph']is False,'exact new ownedplan eager/physical4')
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new output');out.mkdir();(out/'blobs').mkdir();start=time.monotonic();rows=[];primary=None
 import torch,torch_npu
 from vllm_ascend.utils import enable_custom_op
 from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
 import vllm_ascend.ops.gdn as gdn
 C.need(C.ref(gdn.__file__)['sha256']=='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'and enable_custom_op(),'actual native source/ops')
 torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0);init_device_properties_triton()
 h=C.load(m['probe_ref'],'actual_frozen_probe');R=C.load(m['files']['oracle.py'],'independent_request_oracle');S=C.load(m['files']['scenarios.py'],'frozen_scenarios')
 canary=(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(torch.npu.device_count()==1 and canary==[4.,5.]and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0','singleton actual canary')
 C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,visible='0',physical=4,plan=pr,canary=canary))
 end=time.monotonic()+30
 while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<end,'bounded real ownership ARM');time.sleep(.2)
 C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='deltalog.lifecycle-owned-arm/v007',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'source/physical ARM')
 ops={};maps=[]
 for arm,r in m['libraries'].items():
  torch.ops.load_library(r['path']);name='qwen36_deltalog_'+arm;ops[arm]=getattr(torch.ops,name).decode
  C.need(torch._C._dispatch_has_kernel_for_dispatch_key(name+'::decode','PrivateUse1'),'loaded native registration')
  C.need(any(r['path']in line for line in Path('/proc/self/maps').read_text().splitlines()),'actual mapped library');maps.append(dict(arm=arm,library=r,schema=str(ops[arm].default._schema)))
 debuglib=m['debug_library'];torch.ops.load_library(debuglib['path']);debugop=torch.ops.qwen36_deltalog_readout_sidecar_v015.decode
 C.need(torch._C._dispatch_has_kernel_for_dispatch_key('qwen36_deltalog_readout_sidecar_v015::decode','PrivateUse1')and any(debuglib['path']in x for x in Path('/proc/self/maps').read_text().splitlines()),'actual debug mapping/registration');maps.append(dict(arm='debug',library=debuglib,schema=str(debugop.default._schema)))
 from regression import run as regression_run
 stored_bytes=0
 def account(path):
  nonlocal stored_bytes
  stored_bytes+=path.stat().st_size;C.need(stored_bytes<=m['resources']['raw_disk_cap_bytes'],'actual accumulated raw disk cap')
 def tensor_blob(t):
  t=t.detach().cpu().contiguous();digest=hashlib.sha256(str(t.dtype).encode()+str(list(t.shape)).encode()+t.view(torch.uint8).numpy().tobytes()).hexdigest();path=out/'blobs'/(digest+'.pt')
  if not path.exists():
   C.need(stored_bytes+t.numel()*t.element_size()+2097152<=m['resources']['raw_disk_cap_bytes'],'pre-write raw disk reserve')
   with path.open('xb')as f:torch.save(t,f)
   account(path)
  return C.ref(path)
 def snapshot(st):return {k:tensor_blob(v)for k,v in st.items()}
 def save_raw(path,value):
  def size(v):
   if isinstance(v,torch.Tensor):return v.numel()*v.element_size()
   if isinstance(v,dict):return sum(size(x)for x in v.values())
   if isinstance(v,(list,tuple)):return sum(size(x)for x in v)
   return 0
  C.need(stored_bytes+size(value)+2097152<=m['resources']['raw_disk_cap_bytes'],'pre-write raw disk reserve')
  with path.open('xb')as f:torch.save(value,f)
  account(path)
  return C.ref(path)
 try:
  regression=regression_run(torch,C,m,ops['key_projection'],debugop,lambda value:save_raw(out/'original137-guard.pt',value),snapshot,R,S)
  C.need(regression['passed'],'single actual137 guard/pointer/full numerical replay')
 except BaseException as exc:primary=repr(exc)
 finally:C.write(out/'RESULT.json',dict(schema='deltalog.actual-lifecycle-kernel/v007',scope='single-original137-guard-v020',source=sr,admissions=ad,plan=pr,rows=[],regression=locals().get('regression'),primary=primary,mapped=maps,raw_stored_bytes=stored_bytes,NPU=True,graph_qualified=False,actual_runtime_copy_qualified=False,model_ready=False,elapsed_seconds=time.monotonic()-start))
 return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
