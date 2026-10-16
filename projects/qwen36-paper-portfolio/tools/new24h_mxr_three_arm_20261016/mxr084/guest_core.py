"""Default-OFF saved actual2K frame three-arm diagnostic; no model/qualification."""
import argparse,hashlib,importlib.util,inspect,json,os,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
AUTHORITY={'path':'/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json','bytes':3481,'sha256':'e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'}
MODEL={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-2k-memory32-model-new24h-v1-073-repair6/SOURCE_MANIFEST.json','bytes':111072,'sha256':'8d0608cd3fe3814359fc8141a39afe4b14baa77290d20fd8e57e73bcab4799ab'}
RAW={'path':'/opt/host/vnf/austinov/run-mxr-2k-memory32-model073repair6-main-NEW24H_MXR073R6_001/candidate/model/capture/worker-425/raw/frame-000/RAW.pt','bytes':32140793,'sha256':'394b22b1a1f511f0402446e9d45ba27268d2c0f7c263f12986d87d7fdc83e89b'}
ARMS=('saved_candidate','native','cpu64_cast')
RAW_CAP=256*2**20
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3');p=Path(r['path'])
 need(p.is_absolute()and p.is_file()and all(not q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'ordinary exact source/input');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def fp(torch,t):
 c=t.detach().cpu().contiguous();return dict(dtype=str(t.dtype),shape=list(t.shape),sha256=hashlib.sha256(c.view(torch.uint8).numpy().tobytes()).hexdigest())
def equal(torch,a,b):return fp(torch,a)==fp(torch,b)
def validate_frame(torch,p):
 need(set(p)=={'inputs','inputs_after','normalized_inputs','normalized_inputs_after','output','final_state','solve','FP32_policy','block044'},'actual073 full capture ABI')
 x=p['normalized_inputs'];need(x['already_normalized']is True and x['cu_seqlens'].tolist()==[0,2048]and x['scale']==128**-.5,'fixed actual2K normalized domain')
 for n,h in(('q',4),('k',4),('v',12)):
  need(tuple(x[n].shape)==(1,2048,h,128)and x[n].dtype==torch.bfloat16 and bool(torch.isfinite(x[n]).all()),'actual normalized finite BF16 '+n)
 need(tuple(x['initial_state'].shape)==(1,12,128,128)and x['initial_state'].dtype==torch.float32 and bool(torch.isfinite(x['initial_state']).all()),'actual initial FP32 K,V')
 need(tuple(x['g'].shape)==tuple(x['beta'].shape)==(1,2048,12)and x['g'].dtype==torch.float32 and x['beta'].dtype==torch.bfloat16,'actual gate/beta shape and dtype')
 need(bool(torch.isfinite(x['g']).all()and torch.isfinite(x['beta']).all()),'finite actual gates')
 for n,v in x.items():
  if torch.is_tensor(v):
   z=p['normalized_inputs_after'][n];need(z['dtype']==fp(torch,v)['dtype']and z['shape']==fp(torch,v)['shape']and z['sha256']==fp(torch,v)['sha256'],'actual normalized input unchanged '+n)
 need(tuple(p['solve']['A'].shape)==(1,2048,12,64)and p['solve']['A'].dtype==torch.float32,'saved actual A32 not CPU reconstruction')
 need(tuple(p['solve']['output'].shape)==(1,2048,12,64)and p['solve']['output'].dtype==torch.bfloat16,'saved actual candidate B')
 need(equal(torch,p['solve']['cu'],x['cu_seqlens']),'actual solve cu matches frame')
 need(p['FP32_policy']['allow_hf32']is False and p['FP32_policy']['common_to_all_arms']is True,'original commonHF32OFF')
 need(tuple(p['output'].shape)==(1,2048,12,128)and p['output'].dtype==torch.bfloat16 and tuple(p['final_state'].shape)==(1,12,128,128)and p['final_state'].dtype==torch.float32,'saved final output/state ABI')
 return x
def readset(m):
 model=obj(MODEL);old=obj(m['bootstrap_source']);g=load(old['files']['guest_core.py'],'_084_original079_helpers')
 report=obj(m['frame_report_ref']);selected=[r for r in report['rows']if r['raw']==RAW]
 need(report['capture_source']==MODEL and report['pid']==425 and len(selected)==1 and selected[0]['prefix']=='language_model.model.layers.0.linear_attn'and selected[0]['tokens']==2048 and selected[0]['pass_gate']is False,'exact actual failed layer0 joins real073R6 source/raw, not a PASS')
 refs=[MODEL,RAW,m['raw_sidecar'],m['frame_report_ref'],AUTHORITY,m['bootstrap_source'],m['original_metrics'],m['native_H_layout_source'],model['files']['lossless_raw.py'],model['files']['worker.py'],*old['files'].values(),g.SOURCE,g.CANN]
 context=obj(g.SOURCE);refs+=[context['files']['qwen36_deltalog_fresh/native_fixture.py']]
 for r in refs:checked(r)
 need(Path(m['raw_sidecar']['path'])==Path(RAW['path']).with_suffix('.STORAGE.json'),'exact shared-codec sibling, not stale sidecar')
 return model,g,context,refs
def frame(torch,model):
 codec=load(model['files']['lossless_raw.py'],'_084_actual073_lossless');p=codec.read(torch,checked(RAW));validate_frame(torch,p);return p
def anchored_arms(torch,saved,callback):
 """Real replay uses this same front door. Anchor before running other arms."""
 results={}
 for arm in ARMS:
  value=callback(arm)
  if arm=='saved_candidate':
   need(equal(torch,value['output'],saved['output'])and equal(torch,value['state'],saved['final_state']),'saved candidate full output/state bitwise anchor; stop attribution if false')
  results[arm]=value
 return results
def execute(torch,own,model,g,context,saved,out):
 import vllm.forward_context as fc
 from vllm_ascend.ops.triton.fla import chunk
 from vllm_ascend.ops import gdn_attn_builder as builder
 for module,digest in((chunk,g.CHUNK_SHA),(builder,g.BUILDER_SHA),(fc,g.CONTEXT_SHA)):g.require_digest(module.__file__,digest)
 g.require_digest(inspect.getsourcefile(chunk.recompute_w_u_fwd),'51e23f0876d91ae09b32ae70aa03318b2440b7bd3ba029c0d9838869359597ef')
 g.require_digest(inspect.getsourcefile(chunk.chunk_local_cumsum),'af45679800aa2c49f8587194f6744e3d9c7cabe7658eef9ec37f0a665a70c47d')
 need(inspect.unwrap(chunk.solve_tril).__module__=='vllm_ascend.ops.triton.fla.solve_tril','real official solve before interception')
 precision=load(own['common_precision'],'_084_same_common044_precision').apply(torch)
 need(precision['allow_hf32']is False,'actual commonHF32OFF')
 O=load(own['original_metrics'],'_084_independent_actualA_inverse')
 x=validate_frame(torch,saved);savedA=saved['solve']['A'];savedB=saved['solve']['output']
 original_solve=chunk.solve_tril;original_wy=chunk.recompute_w_u_fwd;original_sum=chunk.chunk_local_cumsum
 h_op=torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h
 need(isinstance(h_op,torch._ops.OpOverloadPacket)and h_op._qualified_op_name=='_C_ascend::chunk_gated_delta_rule_fwd_h','real native H op packet')
 solve_sig=inspect.signature(original_solve);wy_sig=inspect.signature(original_wy);active=None;rows=[];used=0
 def snap(t):return t.detach().cpu().clone()
 def cumsum(*a,**kw):
  value=original_sum(*a,**kw);torch.npu.synchronize();need('G'not in active,'one real cumsum');active['G']=snap(value);return value
 def solve(*a,**kw):
  b=solve_sig.bind(*a,**kw);b.apply_defaults();v=b.arguments;A=snap(v['A']);cu=snap(v['cu_seqlens'])
  need('A'not in active and equal(torch,A,savedA)and equal(torch,cu,x['cu_seqlens'])and v['output_dtype']==torch.bfloat16,'same real native A32/cu for all arms; never author CPU A')
  active['A']=A
  if active['arm']=='native':value=original_solve(*a,**kw)
  elif active['arm']=='saved_candidate':value=savedB.to(v['A'].device).clone()
  else:
   inverse,residual=O.fp64_reference(torch,A,cu.tolist());active['inverse_residual']=residual
   value=inverse.to(torch.bfloat16).to(v['A'].device)
  torch.npu.synchronize();active['B']=snap(value);need(equal(torch,A,v['A']),'A immutable after solve');return value
 def wy(*a,**kw):
  b=wy_sig.bind(*a,**kw);b.apply_defaults();v=b.arguments
  need(equal(torch,v['A'],active['B'])and equal(torch,v['g_cumsum'],active['G']),'WY consumes observed actual B/G')
  before={n:fp(torch,t)for n,t in v.items()if torch.is_tensor(t)};w,u=original_wy(*a,**kw);torch.npu.synchronize()
  need(before=={n:fp(torch,t)for n,t in v.items()if torch.is_tensor(t)},'actual WY inputs unchanged');active.update(W=snap(w),U=snap(u));return w,u
 def h(*a,**kw):
  need(len(a)==3 and 'Hentry'not in active,'one real official H API')
  k,w,u=a;need(equal(torch,k,x['k'].transpose(1,2).contiguous())and equal(torch,w,active['W'].transpose(1,2).contiguous())and equal(torch,u,active['U'].transpose(1,2).contiguous())and equal(torch,kw['g'],active['G'].transpose(1,2).contiguous())and equal(torch,kw['initial_state'],x['initial_state']),'actual H receives same K/initial/observed WY/G')
  before=[fp(torch,t)for t in(*a,kw['g'],kw['initial_state'])];value=h_op(*a,**kw);torch.npu.synchronize()
  need(before==[fp(torch,t)for t in(*a,kw['g'],kw['initial_state'])],'actual H inputs immutable')
  H,V,F=value;need(H.numel()==12*32*128*128 and H.dtype==torch.bfloat16 and H.is_contiguous(),'full32chunk actual BF16 Hentry API storage')
  active.update(Hentry=snap(H),Vnew=snap(V),Hend_final=snap(F));return value
 cfg=SimpleNamespace(vllm_config=SimpleNamespace(model_config=SimpleNamespace(hf_text_config=SimpleNamespace(linear_num_value_heads=48)),parallel_config=SimpleNamespace(tensor_parallel_size=4,prefill_context_parallel_size=1)))
 def one(arm):
  nonlocal active,used
  active=dict(arm=arm);d={n:x[n].clone().to('npu:0')for n in('q','k','v','g','beta','initial_state','cu_seqlens')}
  before={n:fp(torch,t)for n,t in d.items()};meta=builder._build_non_spec_chunked_prefill_metadata(cfg,x['cu_seqlens'].cpu(),torch.device('npu:0'))
  value=chunk.chunk_gated_delta_rule(**d,scale=x['scale'],output_final_state=True,prebuilt_meta=meta,use_qk_l2norm_in_kernel=False)
  torch.npu.synchronize();need(before=={n:fp(torch,t)for n,t in d.items()},'all native operands immutable')
  need(set(('G','A','B','W','U','Hentry','Vnew','Hend_final'))<=set(active),'complete actual API capture ledger')
  active.update(output=snap(value[0]),state=snap(value[1]),inputs_after=before)
  need(equal(torch,active['state'],active['Hend_final']),'returned final state joins actual H final API')
  if arm=='saved_candidate':need(equal(torch,active['output'],saved['output'])and equal(torch,active['state'],saved['final_state']),'actual saved candidate bitwise anchor before other arms')
  if rows:
   first=torch.load(rows[0]['raw']['path'],map_location='cpu',weights_only=True)
   need(equal(torch,active['A'],first['A'])and equal(torch,active['G'],first['G']),'same actual A/G across three arms')
  target=out/(arm+'.pt')
  with target.open('xb')as f:torch.save(active,f);f.flush();os.fsync(f.fileno())
  rr=ref(target);used+=rr['bytes'];need(used<=RAW_CAP,'all full raw within256MiB; no dropping tensors');rows.append(dict(arm=arm,raw=rr));write(out/(arm+'.json'),rows[-1]);return dict(output=active['output'],state=active['state'])
 try:
  chunk.solve_tril=solve;chunk.recompute_w_u_fwd=wy;chunk.chunk_local_cumsum=cumsum;torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h=h
  with g.native_context(context)(torch):
   with fc.override_forward_context(fc.ForwardContext(no_compile_layers={},attn_metadata={},slot_mapping={})):anchored_arms(torch,saved,one)
 finally:
  chunk.solve_tril=original_solve;chunk.recompute_w_u_fwd=original_wy;chunk.chunk_local_cumsum=original_sum;torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h=h_op
 need(chunk.solve_tril is original_solve and torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h is h_op,'restored official API objects')
 return dict(rows=rows,raw_bytes=used,candidate_anchor_bitwise=True,same_actual_A_G=True,API_observed=['A32','G32','B_BF16','W_BF16','U_BF16','Hentry_BF16_all32','Vnew_BF16','Hend_final_FP32'],intermediate_Hend_FP32_API_available=False,intermediate_Hnext_BF16_observed=True,whole_correctness_qualified=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--cpu-preflight',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit or a.cpu_preflight):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=obj(sr);need(m['schema']=='mxr.prefill-three-arm-source/v084'and m['root']==str(HERE)and m['default_enabled']is False,'exact084 source defaultOFF');[checked(r)for r in m['files'].values()];need(m['files']['guest_core.py']==ref(__file__),'actual084 entry source')
 model,g,context,refs=readset(m);refs+=[sr,*m['files'].values(),m['common_precision']];[checked(r)for r in refs]
 if a.source_audit:print(json.dumps(dict(source=sr,readset=refs,NPU=False)));return 0
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'fresh owned output');a.output.mkdir();primary=None;result=None;attempted=False;start=time.monotonic()
 try:
  if a.cpu_preflight:
   need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','Devices[] CPU preflight')
   import torch
   need('torch_npu'not in sys.modules and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'no NPU module or mapped device in CPU stage')
   torch.set_num_threads(1);saved=frame(torch,model);result=dict(actual_saved_frame_extracted=True,output=fp(torch,saved['output']),state=fp(torch,saved['final_state']),NPU=False)
  else:
   auth=obj(AUTHORITY);need(auth['start_epoch']==1792134133 and auth['cutoff_epoch']==1792220533 and 1792134133<=time.time()<1792220533-900,'fixed new24h remaining whole900')
   pr=json.loads(a.plan_ref);plan=obj(pr);need(plan['schema']=='mxr.prefill-three-arm-plan/v084'and plan['source']==sr and plan['raw']==RAW and plan['physical']in(4,5,6,7)and plan['logical']==0 and plan['qualification']is False,'actual MAIN plan')
   need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('VLLM_PLUGINS')=='ascend','single logical0 official-only environment')
   need(not any(v not in('','0')for k,v in os.environ.items()if k.endswith('_ENABLE')and k.startswith(('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_'))),'no ambient candidate/capture plugin')
   write(a.output/'CANN.json',g.bootstrap_cann());sys.path.insert(0,str(Path(m['bootstrap_source']['path']).parent))
   from early_vendor import before_device,after_enable
   write(a.output/'EARLY_VENDOR.json',before_device())
   import torch,torch_npu
   torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);attempted=True;torch.npu.set_device(0);need(torch.npu.device_count()==1,'actual single mapped device')
   canary=(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist();need(canary==[4.,5.],'actual canary')
   write(a.output/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical_declared_by_plan=plan['physical'],plan=pr,canary=canary,physical_proof_must_be_host_owned=True))
   until=time.monotonic()+30
   while not(a.output/'MAIN_ARM.json').exists():need(time.monotonic()<until,'MAIN fresh physical ownership ARM30');time.sleep(.1)
   need(obj(ref(a.output/'MAIN_ARM.json'))==dict(schema='mxr.prefill-three-arm-arm/v084',pid=os.getpid(),plan_sha256=pr['sha256'],physical=plan['physical']),'actual MAIN PIDjoin ARM')
   from native_bootstrap import actual
   proof=actual();write(a.output/'NATIVE_IMPORT.json',proof);need(proof['import_pass']is True,'official native import/properties')
   import vllm_ascend.utils as u
   g.require_digest(u.__file__,'575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02');need(u.enable_custom_op()is True,'actual official native ops');write(a.output/'VENDOR.json',after_enable(u))
   import vllm_ascend.device.device_op as device
   from device_dispatch import prove
   write(a.output/'DISPATCH.json',prove(device,torch));saved=frame(torch,model);result=execute(torch,m,model,g,context,saved,a.output)
 except BaseException as e:primary=repr(e);write(a.output/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
 value=dict(schema='mxr.prefill-three-arm-stage/v084',source=sr,authority=AUTHORITY,plan=json.loads(a.plan_ref)if a.plan_ref else None,raw=RAW,primary=primary,result=result,NPU=attempted,qualified=False,old_failures_unchanged=True,elapsed=time.monotonic()-start)
 write(a.output/'STAGE_RESULT.json',value);return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
