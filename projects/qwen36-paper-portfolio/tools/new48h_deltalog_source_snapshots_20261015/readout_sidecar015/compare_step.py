"""One saved failure step: unchanged production vs debug initial-state clones.

Not a resource owner. MAIN must bind an existing owned single5 plan/ARM after
actual build+Meta. No default execution, no model and no gate reclassification.
"""
import argparse,hashlib,json,os,time
from pathlib import Path
def need(x,s):
 if not x:raise ValueError(s)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'actual exactRef3');return Path(r['path'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
 for k in ('source-ref','input-ref','production-ref','debug-build-ref','plan-ref','output'):p.add_argument('--'+k)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 need(os.environ.get('DL_READOUT_SIDECAR_V015_ENABLE')=='1'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','explicit owned singleton debugonly')
 sr,ir,prod,br,pr=map(json.loads,(a.source_ref,a.input_ref,a.production_ref,a.debug_build_ref,a.plan_ref));m=json.loads(checked(sr).read_bytes());build=json.loads(checked(br).read_bytes());plan=json.loads(checked(pr).read_bytes())
 need(m['schema']=='deltalog.readout-sidecar-packet/v015'and m['default_enabled']is False and m['root']==str(Path(__file__).resolve().parent),'frozen own source')
 for r in m['files'].values():checked(r)
 need(prod['bytes']==2332672 and prod['sha256']=='298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7','exact unchanged productionB010')
 need(build['schema']=='deltalog-readout-sidecar-actual-build/v015'and build['source_manifest']==m['kernel_source_ref']and build['primary']is None and len(build['artifacts'])==1 and build['artifacts'][0]['arm']=='readout_sidecar_v015','actual fresh source-bound debug build, no inventedDSO')
 debug=build['artifacts'][0]['library'];checked(prod);checked(debug)
 need(plan['source']==sr and plan['physical']==5 and plan['logical']==0 and plan['input']==ir and plan['production']==prod and plan['debug_build']==br and plan['diagnostic_only']is True,'owned exact one-step plan')
 out=Path(a.output);need(not out.exists()and out.parent.is_dir(),'fresh exclusive output');out.mkdir()
 import torch,torch_npu
 torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);torch.npu.set_device(0)
 need(torch.npu.device_count()==1 and(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist()==[4.,5.],'actual singletoncanary')
 device=dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,visible='0',physical=5,plan=pr,canary=[4.,5.])
 with(out/'DEVICE.json').open('x')as f:json.dump(device,f)
 end=time.monotonic()+30
 while not(out/'MAIN_ARM.json').exists():need(time.monotonic()<end,'ownedARM30');time.sleep(.2)
 need(json.loads((out/'MAIN_ARM.json').read_bytes())==dict(schema='deltalog.sidecar-owned-arm/v015',pid=os.getpid(),plan_sha256=pr['sha256'],physical=5),'actual ownedPID/cardARM')
 raw=torch.load(checked(ir),map_location='cpu',weights_only=True);before={k:torch.load(checked(r),map_location='cpu',weights_only=True)for k,r in raw['before'].items()};inputs=raw['inputs'];need(inputs is not None,'active savedstep')
 states={n:{k:v.clone().npu()for k,v in before.items()}for n in('production','debug')}
 inp={k:v.clone().npu()for k,v in inputs.items()};seq=raw['sequence'].clone().npu();T=inputs['query'].shape[0]
 torch.ops.load_library(prod['path']);torch.ops.load_library(debug['path']);ops=dict(production=torch.ops.qwen36_deltalog_key_projection.decode,debug=torch.ops.qwen36_deltalog_readout_sidecar_v015.decode)
 need(all(torch._C._dispatch_has_kernel_for_dispatch_key(n+'::decode','PrivateUse1')for n in('qwen36_deltalog_key_projection','qwen36_deltalog_readout_sidecar_v015')),'actual native registrations')
 backing=torch.full((T*12*128+256,),13.,dtype=torch.float32,device='npu:0');side=backing[128:-128].view(T,12,128);outputs={}
 for name in ('production','debug'):
  st=states[name];args=[inp[k]for k in('query','key','value','g','beta')]+[st[k]for k in('base','k_log','u_log','lambda_log','decay','length')]+[seq,inp['indices']]
  outputs[name]=ops[name](*args,*([side]if name=='debug'else[]));torch.npu.synchronize()
 wire=dict(input=ir,production=prod,debug_build=br,debug_library=debug,before=before,inputs=inputs,sequence=raw['sequence'],event=raw['event'],after={n:{k:v.cpu()for k,v in st.items()}for n,st in states.items()},outputs={n:v.cpu()for n,v in outputs.items()},actual_precast_FP32=side.cpu(),sidecar_redzones=backing.cpu(),inputs_after={k:v.cpu()for k,v in inp.items()},mapped=[x for x in Path('/proc/self/maps').read_text().splitlines()if prod['path']in x or debug['path']in x],diagnostic_only=True)
 path=out/'RAW.pt'
 with path.open('xb')as f:torch.save(wire,f)
 with(out/'RESULT.json').open('x')as f:json.dump(dict(schema='deltalog.actual-readout-sidecar/v015',raw=ref(path),input=ir,diagnostic_only=True,qualification=False),f)
 return 0
if __name__=='__main__':raise SystemExit(main())
