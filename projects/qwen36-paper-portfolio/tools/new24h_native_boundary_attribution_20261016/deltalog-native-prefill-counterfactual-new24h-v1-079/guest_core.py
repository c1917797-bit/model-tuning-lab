"""MAIN-owned diagnostic only: original native chunk, two real initial states."""
import argparse,ast,contextlib,hashlib,importlib.machinery,importlib.util,inspect,json,os,sys,tempfile,time
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
SOURCE={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-split-scale-numeric-new24h-v1-069-repair1/SOURCE_MANIFEST.json','bytes':52969,'sha256':'b9cb456d960072d8e6730bb5307dcabfc83b3ad7bffd9d3476d9b92220048f21'}
PRODUCER={'path':'/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/run-numeric160-MAIN-20261016-NEW24H-069-repair1-001/numeric/result/RESULT.json','bytes':100542,'sha256':'4a5b125780618a6020e2d2bf619be1e4258dbafd9b7699bfe52aabc16fa12caa'}
AUTHORITY={'path':'/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json','bytes':3481,'sha256':'e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28'}
CANN={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-direct-d8-fp32-model-boundary-r87-v1-011/cann_python.py','bytes':4503,'sha256':'cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104'}
CHUNK_SHA='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'
BUILDER_SHA='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16'
GDN_SHA='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'
CONTEXT_SHA='1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5'
PARALLEL_SHA='df02e5386bc83e6ac644ff46f0297fdd19003bd55584c629840348a5fda8473f'
RAW_CAP=256*2**20
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):n+=len(b);h.update(b)
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'ordinary exact whole bytes');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def write(p,v):
 with Path(p).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def require_digest(path,sha):need(ref(path)['sha256']==sha,'actual installed source drift '+str(path))
def select_records(v):
 need(v['source']==SOURCE,'actual failed069 producer, not a success relabel')
 rows=[x for x in v['records']if x['kind']=='mixed'and x['batch']==1 and x['step']in(89,90)]
 need([x['step']for x in rows]==[89,90],'exact retained B1 steps89/90');return rows
def fingerprints(torch,t):
 t=t.detach().cpu().contiguous();return dict(shape=list(t.shape),dtype=str(t.dtype),sha256=hashlib.sha256(t.view(torch.uint8).numpy().tobytes()).hexdigest())
def equal(torch,a,b):return fingerprints(torch,a)==fingerprints(torch,b)
def flush_join(torch,previous,before,slot):
 # The real helper flushes selected prefill BEFORE the decode capture. It also
 # poisons logically dead K/U. Comparing all six full arrays would be false.
 other=[i for i in range(previous['base'].shape[0])if i!=slot]
 for n in ('base','k_log','u_log','lambda_log','decay','length'):need(equal(torch,previous[n][other],before[n][other]),'non-prefill six-array continuity '+n)
 lengths=previous['length'][slot,:,0];need(bool((lengths==lengths[0]).all())and 0<=int(lengths[0])<=7,'actual synchronous log length')
 n=int(lengths[0])
 for name in ('u_log','k_log'):need(equal(torch,previous[name][slot,:,:n],before[name][slot,:,:n]),'selected flush live payload unchanged '+name)
 need(equal(torch,previous['lambda_log'][slot],before['lambda_log'][slot])and bool((before['decay'][slot]==0).all()and(before['length'][slot]==0).all()),'selected flush lambda preserved and decay/length reset')
 return dict(selected_log_length=n,nonprefill_sixarrays_unchanged=True,live_payload_unchanged=True,dead_payload_not_compared_as_live=True)
def extract(torch,previous,current):
 need(previous['step']==89 and current['step']==90 and previous['ids'].tolist()==[1,0]and current['ids'].tolist()==[0,1]and current['prefill_slot']==1 and current['prefill_has_initial_state']is True,'actual slot-swap/no-reset provenance')
 need(current['captures']['decode'][0]['inputs']['ssm_state_indices'].tolist()==[0],'decode does not touch prefill1')
 before=current['captures']['decode'][0]['before'];flush_join(torch,previous['state'],before,1)
 pc=current['captures']['prefill'][0];x=pc['inputs'];need(set(x)=={'q','k','v','g','beta','initial_state','cu_seqlens','use_qk_l2norm_in_kernel'}and x['use_qk_l2norm_in_kernel']is True and x['cu_seqlens'].tolist()==[0,64],'actual postconv native64 operand inventory')
 for n,h in (('q',4),('k',4),('v',12)):need(tuple(x[n].shape)==(1,64,h,128)and x[n].dtype==torch.bfloat16,'actual BF16 chunk geometry '+n)
 sc=x['initial_state'].clone();sn=previous['native_state'][1].transpose(-1,-2).unsqueeze(0).contiguous()
 need(sc.dtype==sn.dtype==torch.float32 and tuple(sc.shape)==tuple(sn.shape)==(1,12,128,128),'real two FP32 K,V initial states')
 need(equal(torch,sc[0].transpose(-1,-2).contiguous(),before['base'][1]),'SC is actual flushed prefill base, not an invented restoration')
 return x,sc,sn,pc
def bootstrap_cann():
 helper=load(CANN,'_source_bound_original011_CANN');cached=helper.cached()
 root='/usr/local/Ascend/cann-9.1.0/python/site-packages';need(helper.ROOT==root,'original CANN root')
 helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
 direct=helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]))
 if root not in sys.path:sys.path.insert(0,root)
 active=helper.spec_identity(importlib.util.find_spec('acl'));need(active==direct,'actual active acl is exact direct CANN extension, not stub')
 return dict(helper=CANN,cached_preexisting=cached is not None,direct=direct,active=active,root=root)
def native_context(m):
 # Reuse the precise already-executed069 real PCP1 context function, without
 # importing the candidate provider/algorithm or replacing distributed objects.
 r=m['files']['qwen36_deltalog_fresh/native_fixture.py'];tree=ast.parse(checked(r).read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='native_pcp_context')
 scope=dict(contextlib=contextlib,tempfile=tempfile,require_digest=require_digest,PARALLEL_SHA=PARALLEL_SHA)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),r['path']+'#unchanged-real-PCP1-only','exec'),scope);return scope['native_pcp_context']
def metric(torch,a,b):
 a,b=a.double(),b.double();need(a.shape==b.shape and bool(torch.isfinite(a).all()and torch.isfinite(b).all()),'finite same-shape diagnostic')
 return dict(relative_l2=float((a-b).norm()/max(float(b.norm()),1e-30)),absolute_l2=float((a-b).norm()),absolute_max=float((a-b).abs().max()),bitwise=equal(torch,a,b))
def execute(torch,m,previous,current,out,sr,pr):
 from vllm_ascend.ops import gdn
 from vllm_ascend.ops.triton.fla import chunk
 from vllm_ascend.ops import gdn_attn_builder as builder_module
 import vllm.forward_context as fc
 for module,digest in ((gdn,GDN_SHA),(chunk,CHUNK_SHA),(builder_module,BUILDER_SHA),(fc,CONTEXT_SHA)):require_digest(module.__file__,digest)
 original=chunk.chunk_gated_delta_rule;need(gdn.chunk_gated_delta_rule is original,'actual native gdn/chunk alias, no candidate or shadow')
 need(inspect.unwrap(chunk.solve_tril).__module__=='vllm_ascend.ops.triton.fla.solve_tril','native solve path, not MXR replacement')
 x,sc,sn,saved=extract(torch,previous,current)
 E=load(m['files']['qwen36_deltalog_fresh/capture_evidence.py'],'_actual069_native_dispatch_evidence')
 oldcall=saved['native_call'];need(oldcall['actual_original_call_returned']is True and oldcall['before']['module_file']['sha256']==CHUNK_SHA,'original captured native chunk provenance')
 for n,v in x.items():
  if torch.is_tensor(v):need(fingerprints(torch,v)==oldcall['before']['operands'][n]['actual']==oldcall['after']['input_fingerprints'][n],'actual retained native input fingerprint '+n)
 cfg=obj(m['config_ref'])['text_config'];need((cfg['linear_num_key_heads'],cfg['linear_num_value_heads'],cfg['linear_key_head_dim'],cfg['linear_value_head_dim'])==(16,48,128,128),'actual model config TP4-local geometry')
 builder=SimpleNamespace(vllm_config=SimpleNamespace(model_config=SimpleNamespace(hf_text_config=SimpleNamespace(**cfg)),parallel_config=SimpleNamespace(tensor_parallel_size=4,prefill_context_parallel_size=1)))
 h_op=torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h
 need(isinstance(h_op,torch._ops.OpOverloadPacket)and h_op._qualified_op_name=='_C_ascend::chunk_gated_delta_rule_fwd_h','genuine native H operator, never a fake replacement')
 op_proof=dict(qualified_name=h_op._qualified_op_name,schemas={k:str(v)for k,v in h_op._schemas.items()},object_id=id(h_op))
 rows=[];used=0;active=None
 def save(name,v):
  nonlocal used
  p=out/name
  with p.open('xb')as f:torch.save(v,f);f.flush();os.fsync(f.fileno())
  r=ref(p);used+=r['bytes'];need(used<=RAW_CAP,'full diagnostic256MiB raw cap; retain on failure');return r
 def observe_h(*a,**kw):
  need(active is not None and active.get('H')is None,'exactly one actual H operator per64chunk')
  h0=kw['initial_state'];need(h0.data_ptr()==active['initial_ptr'],'H receives exact requested initial clone')
  before=fingerprints(torch,h0);result=h_op(*a,**kw);torch.npu.synchronize()
  need(isinstance(result,(tuple,list))and len(result)==3,'actual H triple')
  h,vnew,final=result;need(h.dtype==torch.bfloat16 and h.numel()==12*128*128,'actual onechunk BF16 gmH entry, not a cast proxy')
  need(fingerprints(torch,h0)==before,'actual H initial input unchanged')
  active['H']=dict(actual_gmH=h.detach().cpu().clone(),actual_gmH_KV=h.detach().cpu().reshape(1,12,128,128).clone(),actual_vnew=vnew.detach().cpu().clone(),actual_H_final=final.detach().cpu().clone(),actual_initial=h0.detach().cpu().clone(),initial_fingerprint=before,initial_data_ptr=h0.data_ptr(),operator=op_proof)
  return result
 plan=[('SC-repeat0',sc),('SN-repeat0',sn),('SC-repeat1',sc),('SN-repeat1',sn),('SC-common-control0',sc),('SC-common-control1',sc)]
 write(out/'CALLABLES.json',dict(chunk=ref(chunk.__file__),gdn=ref(gdn.__file__),builder=ref(builder_module.__file__),forward_context=ref(fc.__file__),H_operator=op_proof,source_to_binary_identity_proved=False))
 try:
  torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h=observe_h
  with native_context(m)(torch):
   context=fc.ForwardContext(no_compile_layers={},attn_metadata={},slot_mapping={})
   with fc.override_forward_context(context):
    for index,(label,initial)in enumerate(plan):
     kw={n:v.to('npu:0').clone()if torch.is_tensor(v)else v for n,v in x.items()};kw['initial_state']=initial.to('npu:0').clone();cu=x['cu_seqlens'].clone()
     meta=builder_module._build_non_spec_chunked_prefill_metadata(builder,cu,torch.device('npu:0'))
     kw.update(prebuilt_meta=meta,output_final_state=True,head_first=False)
     raw={n:kw[n].detach().cpu().clone()if torch.is_tensor(kw[n])else kw[n]for n in x}
     active=dict(initial_ptr=kw['initial_state'].data_ptr());before=E.begin(torch,original,gdn,chunk,index,(),kw,raw)
     value=original(**kw);torch.npu.synchronize();call=E.finish(torch,original,gdn,chunk,index+1,before,value,kw)
     need(tuple(value[0].shape)==(1,64,12,128)and value[0].dtype==torch.bfloat16 and tuple(value[1].shape)==(1,12,128,128)and value[1].dtype==torch.float32,'actual native64 full output/state ABI')
     need(active.get('H')is not None,'actual gmH observation happened; no guessed CPU cast')
     rr=save('native-%02d.pt'%index,dict(label=label,inputs=raw,H=active['H'],output=value[0].detach().cpu().clone(),state=value[1].detach().cpu().clone(),native_call=call))
     rows.append(dict(index=index,label=label,raw=rr,call=call));write(out/('CALL-%02d.json'%index),rows[-1]);active=None
 finally:
  torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h=h_op
 need(torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h is h_op,'original native H operator restored')
 values=[torch.load(r['raw']['path'],map_location='cpu',weights_only=False)for r in rows]
 comparisons={}
 for label,a,b in (('SC-repeat',0,2),('SN-repeat',1,3),('SC-same-initial-clones',4,5),('SC-v-SN',0,1)):
  comparisons[label]={n:metric(torch,values[a][n],values[b][n])for n in('output','state')};comparisons[label]['actual_gmH_changed_cells']=int((values[a]['H']['actual_gmH'].view(torch.int16)!=values[b]['H']['actual_gmH'].view(torch.int16)).sum())
 comparisons['SC-replay-v-saved-candidate']={n:metric(torch,values[0][n],saved['output'if n=='output'else'final_state'])for n in('output','state')}
 comparisons['SN-replay-v-saved-native-final-state']=metric(torch,values[1]['state'][0].transpose(-1,-2),current['native_state'][1])
 return dict(rows=rows,comparisons=comparisons,raw_bytes=used,whole_correctness_qualified=False,native_baseline_postconv_inputs_were_captured=False,source_to_binary_identity_proved=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);own=obj(sr);need(own['root']==str(HERE)and own['schema']=='deltalog.native-prefill-counterfactual-source/v079'and own['default_enabled']is False,'exact own source')
 for r in own['files'].values():checked(r)
 need(own['files']['guest_core.py']==ref(__file__),'actual guest source');m=obj(SOURCE);r=obj(PRODUCER);records=select_records(r)
 readset=[sr,SOURCE,PRODUCER,AUTHORITY,CANN,m['config_ref'],*[m['files'][n]for n in('raw_codec.py','qwen36_deltalog_fresh/native_fixture.py','qwen36_deltalog_fresh/capture_evidence.py')],*[x['raw']for x in records]]
 for item in readset:checked(item)
 if a.source_audit:print(json.dumps(dict(source=sr,readset=readset,raw_RO_root=str(Path(PRODUCER['path']).parent),source_audit_only=True,NPU=False)));return 0
 authority=obj(AUTHORITY);need(authority['start_epoch']==1792134133 and authority['cutoff_epoch']==1792220533 and 1792134133<=time.time()<1792220533-900,'current independent authority/900s fits')
 pr=json.loads(a.plan_ref);plan=obj(pr);need(plan['schema']=='deltalog.native-prefill-counterfactual-plan/v079'and plan['source']==sr and plan['retained_source']==SOURCE and plan['producer']==PRODUCER and plan['physical']in(4,5,6,7)and plan['logical']==0 and plan['qualification']is False,'MAIN actual singlecard plan, not qualification')
 need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('VLLM_PLUGINS')=='ascend','actual singleton/native-only environment')
 need(not any(v not in('','0')for k,v in os.environ.items()if k.endswith('_ENABLE')and k.startswith(('MXR_','MST_MXR_','QWEN36_DELTALOG','DLOG_'))),'no candidate/capture plugin')
 out=a.output;need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new bounded owned output');out.mkdir();start=time.monotonic();primary=None;result=None;npu_attempted=False
 try:
  cann=bootstrap_cann();write(out/'CANN.json',cann)
  sys.path.insert(0,str(HERE))
  from early_vendor import before_device,after_enable
  write(out/'EARLY_VENDOR.json',before_device())
  import torch,torch_npu
  torch.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);npu_attempted=True;torch.npu.set_device(0)
  need(torch.npu.device_count()==1,'actual singleton device count')
  canary=(torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist();need(canary==[4.,5.],'actual singleton canary')
  write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical_declared_by_plan=plan['physical'],plan=pr,canary=canary,physical_proof_must_be_host_owned=True))
  until=time.monotonic()+30
  while not(out/'MAIN_ARM.json').exists():need(time.monotonic()<until,'MAIN owned ARM30');time.sleep(.1)
  arm=obj(ref(out/'MAIN_ARM.json'));need(arm==dict(schema='deltalog.native-prefill-counterfactual-arm/v079',pid=os.getpid(),plan_sha256=pr['sha256'],physical=plan['physical']),'exact real PID/plan/physical ARM')
  from native_bootstrap import actual
  native=actual();write(out/'NATIVE_IMPORT.json',native);need(native['import_pass']is True,'actual official package-first import/properties, no replacement op')
  import vllm_ascend.utils as utils
  require_digest(utils.__file__,'575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02')
  need(utils.enable_custom_op()is True,'actual original official custom-op registration')
  write(out/'ACTUAL_VENDOR_ENABLE.json',after_enable(utils))
  import vllm_ascend.device.device_op as device
  from device_dispatch import prove
  write(out/'DISPATCH.json',prove(device,torch))
  RC=load(m['files']['raw_codec.py'],'_exact069_lossless_codec');RC.install(torch)
  previous,current=[torch.load(checked(x['raw']),map_location='cpu',weights_only=False)for x in records]
  result=execute(torch,m,previous,current,out,sr,pr)
 except BaseException as exc:primary=repr(exc);import traceback;write(out/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
 write(out/'STAGE_RESULT.json',dict(schema='deltalog.native-prefill-counterfactual-stage/v079',source=sr,authority=AUTHORITY,plan=pr,retained_source=SOURCE,producer=PRODUCER,selected=records,primary=primary,result=result,NPU=npu_attempted,qualified=False,old160_failure_unchanged=True,elapsed=time.monotonic()-start));return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())
