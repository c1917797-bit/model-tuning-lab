"""Default-OFF same real saved normalized frame native/candidate replay. No model."""
import argparse,hashlib,importlib,importlib.util,inspect,json,os,sys,time,types
from pathlib import Path
from datetime import timedelta
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute()and not p.is_symlink()and ref(p)==r,'exact source/input Ref3');return p.read_bytes()
def module(name,r):
 need(name not in sys.modules,'no injected source module');s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);sys.modules[name]=m;exec(compile(checked(r),r['path'],'exec'),m.__dict__);return m
def write(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--selection-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(os.environ.get('MXR_ORIGINAL_A32_RESIDUAL027_ENABLE')=='1'and os.environ.get('MXR_SAVED_FRAME_REPLAY_ENABLE')=='1'and os.environ.get('MXR_Y16_EXPERIMENT_ENABLE')=='1'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','explicit owned single logical0 optin')
 sr,selr,pr=map(json.loads,(a.source_ref,a.selection_ref,a.plan_ref));m=json.loads(checked(sr));sel=json.loads(checked(selr));plan=json.loads(checked(pr));need(m['default_enabled']is False and m['schema']=='mxr.saved-frame-attribution-source/v042','new diagnostic source')
 for r in [*m['files'].values(),*m['reused'].values()]:checked(r)
 need(time.time()+900<1792135097 and plan==dict(schema='mxr.saved-frame-replay-plan/v042',source=sr,selection=selr,physical=4,logical=0,output=str(a.output)),'fixed window and literal onecard plan')
 G_FRAMES=3;selection=module('_saved018_selection',m['files']['select_frames.py']);need(sel==selection.select(sel['original_report'])and len(sel['rows'])==G_FRAMES,'exact new frozen real-frame selection')
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'new bounded output');a.output.mkdir()
 early=module('_saved018_early',m['reused']['early_vendor.py']);write(a.output/'EARLY_VENDOR.json',early.before_device())
 import torch,torch_npu
 torch.set_num_threads(1);need(torch.npu.device_count()==1,'actual singleton');torch.npu.set_device(0);need((torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist()==[4.,5.],'real NPU canary');torch.npu.synchronize()
 write(a.output.parent/'DEVICE.json',dict(schema='mxr.actual-single-replay-process/v1',pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical_device=0,visible_devices='0',plan_sha256=pr['sha256'],canary=[4.,5.]))
 limit=time.monotonic()+30
 while not(a.output.parent/'BEGIN.json').exists():need(time.monotonic()<limit,'MAIN fresh physical4 ownership ARM30s');time.sleep(.2)
 need(json.loads((a.output.parent/'BEGIN.json').read_bytes())==dict(schema='mxr.actual-owned-replay-arm/v1',pid=os.getpid(),plan_sha256=pr['sha256'],physical=4),'actual host-proven singleton')
 boot=module('_saved018_bootstrap',m['reused']['native_bootstrap.py']);value=boot.actual();write(a.output/'NATIVE_IMPORT.json',value);need(value['import_pass'],'actual device properties/native bootstrap')
 u=importlib.import_module('vllm_ascend.utils');need(u.enable_custom_op()is True,'real native custom ops');write(a.output/'VENDOR_ENABLE.json',early.after_enable(u))
 chunk=importlib.import_module('vllm_ascend.ops.triton.fla.chunk');need(hashlib.sha256(Path(inspect.getsourcefile(chunk)).read_bytes()).hexdigest()=='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5','actual660 fullchunk source')
 ps=importlib.import_module('vllm.distributed.parallel_state');fc=importlib.import_module('vllm.forward_context');builder=importlib.import_module('vllm_ascend.ops.gdn_attn_builder')
 capture=json.loads(checked(sel['capture_source']));R=module('_saved018_prereq',capture['files']['prerequisite.py']);passed=R.gate(m['prerequisite_ref']);component=json.loads(checked(passed['source']));adapter=module('_saved018_solver',component['files']['adapter.py']);_,_,algorithm=adapter.instances(torch,passed['source'],passed['build'],torch.device('npu:0'))
 eager=module('_saved018_eager',m['reused']['safe_eager.py']).eager;Pool=module('_saved018_pool',m['reused']['lifetime.py']).KeepalivePool;Backend=module('_saved018_event',m['reused']['event_backend.py']).EventBackend
 G=module('_shared027_probe_contract',m['files']['probe_contract.py']);refiner=module('_original_A32_refiner027',m['files']['refine.py']);precision=refiner.precision_policy(torch);write(a.output/'FP32_POLICY.json',precision)
 pool=Pool(32*1024**2,2);backend=Backend(torch,torch_npu);original=chunk.solve_tril;original_wy=chunk.recompute_w_u_fwd;signature=inspect.signature(original);active='native';As=[];Bs=[];WYs=[];hits=0;raws=[];primary=None;teardown=[];refinement=[];frozen_cu=None
 def capture_wy(*args,**kwargs):
  result=original_wy(*args,**kwargs);torch.npu.synchronize();WYs.append(tuple(t.detach().cpu().clone()for t in result));return result
 def solve(*args,**kw):
  nonlocal hits
  b=signature.bind(*args,**kw);b.apply_defaults();v=b.arguments;As.append(v['A'].detach().cpu().clone())
  need(v['output_dtype']is torch.bfloat16,'actual source solve output_dtype=k.dtype BF16')
  if active=='native':result=original(*args,**kw)
  elif active=='cpu64_cast':
   oracle=module('_saved027_inverse',m['original_metrics']) if '_saved027_inverse'not in sys.modules else sys.modules['_saved027_inverse']
   inverse,checks=oracle.fp64_reference(torch,v['A'].detach().cpu().clone(),v['cu_seqlens'].detach().cpu().tolist())
   result=inverse.to(v['output_dtype']).to(v['A'].device)
  else:
   hits+=1;cu=v['cu_seqlens'];cu=cu if cu.dtype==torch.int32 else cu.to(torch.int32)
   if active=='a32_refined':
    trace={};result=refiner.eager(algorithm,v['A'],cu,v['chunk_indices_bt'].shape[0],v['output_dtype'],pool,backend,frozen_cu,trace=trace);torch.npu.synchronize();refinement.append({k:t.detach().cpu().clone()for k,t in trace.items()})
   else:result=eager(algorithm,v['A'],cu,v['chunk_indices_bt'].shape[0],v['output_dtype'],pool,backend)
  torch.npu.synchronize();Bs.append(result.detach().cpu().clone());return result
 try:
  need(not torch.distributed.is_initialized()and all(getattr(ps,n)is None for n in('_PCP','_TP','_DP','_PP','_DCP','_WORLD')),'cold private process groups')
  ps.init_distributed_environment(world_size=1,rank=0,local_rank=0,backend='hccl',distributed_init_method='file://'+str(a.output/'world1-store'),timeout=timedelta(seconds=30));ps._PCP=ps.init_model_parallel_group([[0]],local_rank=0,backend='hccl',group_name='pcp',use_device_communicator=False)
  chunk.solve_tril=solve;chunk.recompute_w_u_fwd=capture_wy;ctx=fc.ForwardContext(no_compile_layers={},attn_metadata=None,slot_mapping={});cfg=types.SimpleNamespace(vllm_config=types.SimpleNamespace(model_config=types.SimpleNamespace(hf_text_config=types.SimpleNamespace(linear_num_value_heads=48)),parallel_config=types.SimpleNamespace(tensor_parallel_size=4)))
  for i,row in enumerate(sel['rows']):
   checked(row['raw']);old=torch.load(row['raw']['path'],map_location='cpu',weights_only=True);x=old['normalized_inputs'];need(x['already_normalized']is True and set(('q','k','v','g','beta','initial_state','cu_seqlens','scale'))<=set(x),'exact complete post-normalizer original boundary');frozen_cu=x['cu_seqlens'].tolist();need(frozen_cu==[0,129],'only exact actual129 model-frame domain')
   if row['role']=='initial_state_rounding_witness':
    need(x['initial_state'].dtype==torch.float32,'real native FP32 initial-state supported witness');x={k:(v.clone()if torch.is_tensor(v)else v)for k,v in x.items()}
    for key in ('q','k','v','g','beta'):x[key].zero_()
    x['initial_state'].fill_(1.003)
   for repeat in range(G.REPEATS):
    need(time.time()+300<1792135097,'remaining independentCPU+cleanup reserve');results={};matrices={};solve_outputs={};wy_intermediates={};refinement.clear()
    for arm in G.ARMS:
     d={k:x[k].clone().to('npu:0')for k in('q','k','v','g','beta')};initial=x['initial_state'].clone().to('npu:0');cu=x['cu_seqlens'].clone().to('npu:0');meta=builder._build_non_spec_chunked_prefill_metadata(cfg,x['cu_seqlens'].cpu(),torch.device('npu:0'));active=arm;As.clear();Bs.clear();WYs.clear()
     with fc.override_forward_context(ctx):out,state=chunk.chunk_gated_delta_rule(**d,scale=x['scale'],initial_state=initial,output_final_state=True,cu_seqlens=cu,prebuilt_meta=meta,use_qk_l2norm_in_kernel=False)
     torch.npu.synchronize();pool.finish();need(len(As)==len(Bs)==len(WYs)==1,'one true solve and WY per wholeGDN replay');results[arm]=dict(output=out.cpu(),state=state.cpu(),inputs_after={k:v.cpu()for k,v in d.items()},initial_after=initial.cpu(),cu_after=cu.cpu());matrices[arm]=As[0];solve_outputs[arm]=Bs[0];wy_intermediates[arm]=dict(w=WYs[0][0],u=WYs[0][1])
    need(len(refinement)==1,'one actual original-A32 correction trace per repeat')
    payload=dict(refinement=refinement[0],FP32_policy=precision,selection_row=row,repeat=repeat,original_raw=row['raw'],normalized_inputs=x,saved_output=old['output'],saved_state=old['final_state'],saved_solve_A=old['solve']['A'],saved_solve_output=old['solve']['output'],results=results,matrices=matrices,solve_outputs=solve_outputs,wy_intermediates=wy_intermediates)
    path=a.output/('layer%d-repeat%d.pt'%(i,repeat));torch.save(payload,path);raws.append(ref(path));need(sum(Path(r['path']).stat().st_size for r in raws)<=256*1024**2,'complete raw256MiB cap')
 except BaseException as exc:primary=repr(exc)
 finally:
  chunk.solve_tril=original;chunk.recompute_w_u_fwd=original_wy
  for name,fn in(('pool',pool.finish),('modelgroups',ps.destroy_model_parallel),('world',ps.destroy_distributed_environment)):
   try:fn();teardown.append(dict(stage=name,pass_release=True))
   except BaseException as exc:teardown.append(dict(stage=name,error=repr(exc)))
 write(a.output/'PROBE.json',dict(schema='mxr.saved-frame-actual-replay/v042',source=sr,selection=selr,plan=pr,raws=raws,candidate_hits=hits,actual_algorithm_identity=algorithm.experiment_identity,mapped_library=[s for s in Path('/proc/self/maps').read_text().splitlines()if algorithm.experiment_identity['library']['path']in s],primary=primary,teardown=teardown,NPU=True,model_loaded=False,performance=False))
 need(G.ready(dict(source=sr,primary=primary,raws=raws,candidate_hits=hits,teardown=teardown),sr),'complete replay raw/cleanup; numerical verdict remains independentCPU');return 0
if __name__=='__main__':raise SystemExit(main())
