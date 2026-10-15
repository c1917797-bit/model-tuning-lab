"""Existing owned host ABI: real Devices[] Meta before one singleton frame."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def stage_report(sr,ar,kind,**kw):
 return dict(schema='deltalog.single-frame-sidecar-stage/v040',source=sr,authority=ar,stage=kind,steps=0 if kind=='cpu-preflight'else 1,records=0 if kind=='cpu-preflight'else 1,primary=None,observation_complete=True,NPU=kind=='numeric',qualification=False,**kw)
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight','numeric'),required=True)
 for k in('source-ref','authority-ref','output'):p.add_argument('--'+k,required=True)
 p.add_argument('--plan-ref');p.add_argument('--cpu-preflight-ref');a=p.parse_args();sr,ar=json.loads(a.source_ref),json.loads(a.authority_ref);m=C.source(sr);C.admissions(m,ar,m['meta_ref'],m['numeric_ref']);out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new bounded stage output');out.mkdir()
 import torch
 torch.set_num_threads(1)
 if a.stage=='cpu-preflight':
  C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and'torch_npu'not in sys.modules,'actual Devices[] only Meta')
  from frame import unpack
  raw=torch.load(C.checked(m['saved_raw_ref']),map_location='cpu',weights_only=False);cap,i,slots=unpack(torch,raw)
  D=C.load(m['files']['direct_round.py'],'_040_exact013_RNE');controls=D.controls(torch)
  args=[torch.empty_like(i[n],device='meta')for n in('query','key','value','g','beta')]+[torch.empty_like(cap['before'][n],device='meta')for n in('base','k_log','u_log','lambda_log','decay','length')]+[torch.empty_like(i[n],device='meta')for n in('actual_seq_lengths','ssm_state_indices')];registration=[]
  for name,r,namespace in(('baseline',m['baseline_ref'],'qwen36_deltalog_key_projection'),('production',m['production_ref'],'qwen36_deltalog_readout_mac042'),('debug',m['debug_library'],'qwen36_deltalog_readout_mac042_debug')):
   torch.ops.load_library(r['path']);op=getattr(torch.ops,namespace).decode;C.need(all(torch._C._dispatch_has_kernel_for_dispatch_key(namespace+'::decode',key)for key in('Meta','PrivateUse1')),'real CPU Meta/native registration')
   v=op(*args,*([torch.empty((16,12,128),dtype=torch.float32,device='meta')]if name=='debug'else[]));C.need(v.device.type=='meta'and v.dtype==torch.bfloat16 and tuple(v.shape)==(16,12,128),'actual unchanged16 Meta ABI')
   C.need(any(r['path']in line for line in Path('/proc/self/maps').read_text().splitlines()),'actual DSO loaded without NPU compute');registration.append(dict(arm=name,library=r,schema=str(op.default._schema),Meta=True,PrivateUse1=True))
  import unittest,io
  suite=unittest.defaultTestLoader.discover(str(P),pattern='test_*.py');stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite);C.need(result.wasSuccessful()and result.testsRun==m['software_cases'],'actual full040 sameimage software controls '+stream.getvalue())
  dm=stage_report(sr,ar,'cpu-preflight',debug_build=m['debug_build_ref'],library=m['debug_library'],pass_gate=True,actual_registration=registration);C.write(out/'DEBUG_META.json',dm)
  report=stage_report(sr,ar,a.stage,pass_gate=True,debug_meta_ref=C.ref(out/'DEBUG_META.json'),direct_round_controls=controls,actual_new_library_registration=registration,software_cases=result.testsRun,Devices=[])
 else:
  C.need(a.plan_ref and a.cpu_preflight_ref,'existing owned plan and actual CPU result required');cp=C.obj(json.loads(a.cpu_preflight_ref));dm=C.obj(cp['debug_meta_ref']);C.need(cp['source']==sr and cp['authority']==ar and cp['pass_gate']is True and cp['NPU']is False and dm['library']==m['debug_library']and dm['debug_build']==m['debug_build_ref']and dm['source']==sr,'actual same-source CPU/Meta release predecessor')
  import producer
  pr=json.loads(a.plan_ref);rr=producer.run(torch,m,sr,ar,pr,out);report=stage_report(sr,ar,a.stage,actual_result=rr,plan=pr,pass_gate=False,diagnostic_capture_complete=True)
 C.write(out/'STAGE_RESULT.json',report);return 0
if __name__=='__main__':raise SystemExit(main())
