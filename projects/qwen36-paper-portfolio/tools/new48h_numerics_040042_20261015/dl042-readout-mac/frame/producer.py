"""Same originalB010 versus actual015 sidecar, one complete saved B16 frame."""
import json,os,time
from pathlib import Path
import io_contract as C
from frame import FIELDS,identity,bits,unpack,transparency
def run(T,m,sr,ar,pr,out):
 import torch_npu
 T.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);T.npu.set_device(0)
 plan=C.obj(pr);need=C.need
 need(plan['source']==sr and plan['authority']==ar and plan['physical']==4 and plan['logical']==0 and plan['graph']is False,'existing source-bound singleton4 plan')
 canary=(T.tensor([1.,2.],device='npu:0')+3).cpu().tolist();need(T.npu.device_count()==1 and canary==[4.,5.],'actual singletoncanary')
 C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical=4,visible='0',plan=pr,canary=canary))
 end=time.monotonic()+30
 while not(out/'MAIN_ARM.json').exists():need(time.monotonic()<end,'existing owned ARM30');time.sleep(.2)
 need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='deltalog.lifecycle-owned-arm/v007',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'actual MAIN process identity/card ARM')
 raw=T.load(C.checked(m['saved_raw_ref']),map_location='cpu',weights_only=False);cap,inputs,slots=unpack(T,raw);before=cap['before'];started=time.monotonic()
 T.ops.load_library(m['baseline_ref']['path']);T.ops.load_library(m['production_ref']['path']);T.ops.load_library(m['debug_library']['path']);ops=dict(baseline=T.ops.qwen36_deltalog_key_projection.decode,production=T.ops.qwen36_deltalog_readout_mac042.decode,debug=T.ops.qwen36_deltalog_readout_mac042_debug.decode)
 maps=[]
 for name,r in(('baseline',m['baseline_ref']),('production',m['production_ref']),('debug',m['debug_library'])):
  lines=[x for x in Path('/proc/self/maps').read_text().splitlines()if r['path']in x];need(lines and T._C._dispatch_has_kernel_for_dispatch_key(str(ops[name].default._schema).split('(')[0],'PrivateUse1'),'actual exact DSO maps/NPU');maps.append(dict(arm=name,library=r,lines=lines,schema=str(ops[name].default._schema)))
 backing={};states={};guard_before={}
 def upload(name,x):
  b=T.full((x.numel()+256,),13,dtype=x.dtype,device='npu:0');v=b[128:-128].view(x.shape);v.copy_(x.to('npu:0'));backing[name]=b;guard_before[name]=(b[:128].cpu().clone(),b[-128:].cpu().clone());return v
 for arm in('baseline','production','debug'):states[arm]={n:upload(arm+'/'+n,before[n])for n in FIELDS}
 src={n:inputs[n]for n in('query','key','value','g','beta','actual_seq_lengths','ssm_state_indices')};inp={n:upload('input/'+n,v)for n,v in src.items()};side=upload('sidecar',T.zeros((16,12,128),dtype=T.float32));allptr={**{arm+'/'+n:v for arm,st in states.items()for n,v in st.items()},**{'input/'+n:v for n,v in inp.items()},'sidecar':side};ptr_before={n:identity(v)for n,v in allptr.items()};outputs={}
 for arm in('baseline','production','debug'):
  st=states[arm];args=[inp[n]for n in('query','key','value','g','beta')]+[st[n]for n in FIELDS]+[inp['actual_seq_lengths'],inp['ssm_state_indices']]
  outputs[arm]=ops[arm](*args,*([side]if arm=='debug'else[]));T.npu.synchronize()
 outcpu={n:v.cpu()for n,v in outputs.items()};after={arm:{n:v.cpu()for n,v in st.items()}for arm,st in states.items()};inputs_after={n:v.cpu()for n,v in inp.items()};ptr_after={n:identity(v)for n,v in allptr.items()};guard_values={n:(b[:128].cpu(),b[-128:].cpu())for n,b in backing.items()};guard_checks=[bits(T,a,guard_values[n][j])for n,v in guard_before.items()for j,a in enumerate(v)]
 checks=transparency(T,raw,before,outcpu,after,src,inputs_after,guard_checks,ptr_before,ptr_after)
 wire=dict(source=sr,saved_raw=m['saved_raw_ref'],before=before,outputs=outcpu,after=after,inputs=src,inputs_after=inputs_after,actual_precast_FP32=side.cpu(),guard_before=guard_before,guard_after=guard_values,pointers_before=ptr_before,pointers_after=ptr_after,transparency=checks,library_maps=maps,scope='single complete B16step80',NPU=True)
 with(out/'RAW.pt').open('xb')as f:T.save(wire,f)
 need((out/'RAW.pt').stat().st_size<=1024**3,'unchanged bounded singleframe raw1GiB')
 C.write(out/'PRODUCER.json',dict(schema='deltalog.single-frame-sidecar-producer/v040',source=sr,authority=ar,plan=pr,raw=C.ref(out/'RAW.pt'),saved_raw=m['saved_raw_ref'],steps=1,batch=16,records=1,transparency=checks,observation_complete=True,primary=None,NPU=True,qualification=False,elapsed=time.monotonic()-started))
 return C.ref(out/'PRODUCER.json')
