"""Owned CPU predicate/oracle preflight and real numeric child; default OFF."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight','numeric'),required=True)
 for k in('source-ref','authority-ref','output'):p.add_argument('--'+k,required=True)
 p.add_argument('--plan-ref');p.add_argument('--cpu-preflight-ref');a=p.parse_args();sr,ar=json.loads(a.source_ref),json.loads(a.authority_ref);m=C.source(sr);ad=C.admissions(m,ar,m['meta_ref'],m['numeric_ref']);out=Path(a.output)
 C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new stage leaf')
 if a.stage=='cpu-preflight':
  C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','Devices[] CPU preflight')
  import torch
  C.need('torch_npu'not in sys.modules,'no imported NPU backend in CPU oracle preflight');torch.set_num_threads(1)
  R=C.load(m['files']['oracle.py'],'independent_cpu_oracle');g=torch.Generator().manual_seed(20261014002);base=(torch.randn((2,12,128,128),generator=g)*.005).float();key=torch.nn.functional.normalize(torch.randn((1,4,128),generator=g),dim=-1).to(torch.bfloat16);value=torch.randn((1,12,128),generator=g).to(torch.bfloat16);query=key.clone();inputs=dict(key=key,value=value,query=query,g=torch.full((1,12),-.1),beta=torch.full((1,12),.5,dtype=torch.bfloat16));actual,output=R.advance(torch,base[0].double(),inputs,0)
  keys=key[0].double().repeat_interleave(3,dim=0);decay=base[0].double()*torch.exp(inputs['g'][0].double())[:,None,None];u=inputs['beta'][0].double()[:,None]*(value[0].double()-torch.einsum('hvk,hk->hv',decay,keys));expected=decay+u[:,:,None]*keys[:,None,:];expected_output=torch.einsum('hvk,hk->hv',expected,query[0].double().repeat_interleave(3,dim=0))*128**-.5
  C.need(torch.allclose(actual,expected,rtol=1e-12,atol=1e-12)and torch.allclose(output,expected_output,rtol=1e-12,atol=1e-12),'scalar versus independent vectorized nonzero CPU64 recurrence/scale')
  st=dict(base=base,k_log=torch.zeros((2,4,7,128),dtype=torch.bfloat16),u_log=torch.zeros((2,12,7,128)),lambda_log=torch.full((2,12,16),float('nan')),decay=torch.zeros((2,12,16)),length=torch.zeros((2,12,16),dtype=torch.int32));C.need(torch.equal(R.restore(torch,st,0),base[0].double()),'dead-lambda poison not read')
  # Fresh actual new-library schema/Meta admission; old numeric receipts are ABI history ONLY.
  registration=[]
  for arm,lib in m['libraries'].items():
   torch.ops.load_library(lib['path']);name='qwen36_deltalog_'+arm+'::decode'
   C.need(torch._C._dispatch_has_kernel_for_dispatch_key(name,'Meta') and torch._C._dispatch_has_kernel_for_dispatch_key(name,'PrivateUse1'),'actual new schema/Meta/native registrations')
   op=getattr(torch.ops,'qwen36_deltalog_'+arm).decode
   b,s=16,19;meta=lambda shape,dtype:torch.empty(shape,dtype=dtype,device='meta')
   result=op(meta((b,4,128),torch.bfloat16),meta((b,4,128),torch.bfloat16),meta((b,12,128),torch.bfloat16),meta((b,12),torch.float32),meta((b,12),torch.bfloat16),meta((s,12,128,128),torch.float32),meta((s,4,7,128),torch.bfloat16),meta((s,12,7,128),torch.float32),meta((s,12,16),torch.float32),meta((s,12,16),torch.float32),meta((s,12,16),torch.int32),meta((b+1,),torch.int32),meta((b,),torch.int32))
   C.need(tuple(result.shape)==(b,12,128)and result.dtype==torch.bfloat16 and result.device.type=='meta','actual new Meta output')
   C.need(any(lib['path']in line for line in Path('/proc/self/maps').read_text().splitlines()),'actual new DSO mapping')
   registration.append(dict(library=lib,schema=str(op.default._schema),Meta=True,PrivateUse1=True))
  debug=m['debug_library'];torch.ops.load_library(debug['path']);dop=torch.ops.qwen36_deltalog_readout_sidecar_v015.decode
  C.need(torch._C._dispatch_has_kernel_for_dispatch_key('qwen36_deltalog_readout_sidecar_v015::decode','Meta')and torch._C._dispatch_has_kernel_for_dispatch_key('qwen36_deltalog_readout_sidecar_v015::decode','PrivateUse1'),'actual debug Meta/native registration')
  dv=dop(meta((b,4,128),torch.bfloat16),meta((b,4,128),torch.bfloat16),meta((b,12,128),torch.bfloat16),meta((b,12),torch.float32),meta((b,12),torch.bfloat16),meta((s,12,128,128),torch.float32),meta((s,4,7,128),torch.bfloat16),meta((s,12,7,128),torch.float32),meta((s,12,16),torch.float32),meta((s,12,16),torch.float32),meta((s,12,16),torch.int32),meta((b+1,),torch.int32),meta((b,),torch.int32),meta((b,12,128),torch.float32));C.need(tuple(dv.shape)==(b,12,128)and dv.dtype==torch.bfloat16,'actual debug output Meta')
  from direct_round import controls
  direct_round_controls=controls(torch)
  boundaries=R.boundary_tests(torch);sequence_boundaries=R.sequence_tests(torch)
  out.mkdir();C.write(out/'DEBUG_META.json',dict(schema='deltalog.actual-debug-Meta/v016',source=sr,debug_build=m['debug_build_ref'],library=debug,pass_gate=True,NPU=False,actual_schema=str(dop.default._schema),shape=list(dv.shape),dtype=str(dv.dtype)));C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.lifecycle-CPU-preflight/v007',source=sr,authority=ar,admissions=ad,CPU_FP64_oracle_tests_passed=True,direct_round_controls=direct_round_controls,actual_new_library_registration=registration,debug_meta_ref=C.ref(out/'DEBUG_META.json'),boundary_tests=boundaries,sequence_tests=sequence_boundaries,pass_gate=True,NPU=False,model_ready=False));return 0
 cpu=C.obj(json.loads(a.cpu_preflight_ref));C.need(cpu['schema']=='deltalog.lifecycle-CPU-preflight/v007'and cpu['source']==sr and cpu['admissions']==ad and cpu['pass_gate']is True,'fresh same-source CPU oracle qualification')
 dm=C.obj(cpu['debug_meta_ref']);C.need(dm['source']==sr and dm['debug_build']==m['debug_build_ref']and dm['library']==m['debug_library']and dm['pass_gate']is True and dm['NPU']is False,'actual same-source CPU debug Meta receipt')
 rawproducer=C.load(m['files']['producer.py'],'source_actual_producer');old=sys.argv
 sys.argv=[m['files']['producer.py']['path'],'--execute','--source-ref',json.dumps(sr),'--authority-ref',json.dumps(ar),'--meta-ref',json.dumps(m['meta_ref']),'--numeric-ref',json.dumps(m['numeric_ref']),'--plan-ref',a.plan_ref,'--output',str(out)]
 try:code=rawproducer.main()
 finally:sys.argv=old
 rr=C.ref(out/'RESULT.json');v=C.obj(rr);C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.lifecycle-actual-stage/v007',source=sr,authority=ar,actual_result=rr,observation_complete=v.get('regression')is not None,producer_exit=code,NPU=True,model_ready=False));return code
if __name__=='__main__':raise SystemExit(main())
