"""Opt-in actual NPU GLOBAL graph active K128, V-shift, same-slot epoch reuse.
Component-only synthetic dyadic inputs. No controller/device permission/model claim.
"""
import argparse,dataclasses,hashlib,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--zero-only',action='store_true');p.add_argument('--source-ref-json');p.add_argument('--expected-cid');p.add_argument('--remaining-seconds',type=float);p.add_argument('--output');a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 import importlib.util
 spec=importlib.util.spec_from_file_location('_active128_reference',P/'active_reference.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
 need=R.need;own=json.loads(Path(a.source_ref_json).read_bytes());mf=json.loads(R.checked(own));need(mf['schema']=='kivi.active128-slot-reuse-source/v1' and mf['root']==str(P),'exact source root')
 for r in mf['files'].values():R.checked(r)
 need(os.environ.get('KIVI_ACTIVE128_CASES_ENABLE')=='1' and os.environ.get('QWEN36_KIVI_DIRECT_FP32_FULL_GRAPH')=='1','explicit opt-in; default OFF')
 need(type(a.remaining_seconds)is float and 0<a.remaining_seconds<=900 and time.time()+a.remaining_seconds<=1792002456,'fixed R156 new experiment budget')
 end=time.monotonic()+a.remaining_seconds
 def clock():need(time.monotonic()<end and time.time()<1792002456,'no phase budget renewal')
 cid=a.expected_cid;need(type(cid)is str and len(cid)==64 and all(x in '0123456789abcdef'for x in cid) and os.environ.get('MAIN_OWNED_CID')==cid and cid in Path('/proc/self/cgroup').read_text(),'MAIN actual own namespace')
 need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0','only one guest logical device; physical lease consumed by MAIN')
 out=Path(a.output);need(out.is_absolute() and out.resolve()==out and not out.exists() and out.parent.is_dir(),'fresh output no overwrite');out.mkdir()
 cache=out/'jit-cache';cache.mkdir();os.environ['TRITON_CACHE_DIR']=str(cache)
 G=R.load(mf['standalone'],'_active128_actual_standalone');gm=json.loads(R.checked(mf['graph_source']));roles=gm['standalone_import_roles']
 torch,torch_npu,triton,tl,rt,origins=G.backend_imports(roles['numeric'],roles['numeric_manifest'])
 need(torch.npu.device_count()==1 and not torch.npu.is_initialized(),'actual one device before initialization');torch.npu.set_device(0);device=torch.device('npu:0')
 props=triton.runtime.driver.active.utils.get_device_properties(0);rt.init_device_properties_triton()
 need(props['num_aicore']==rt.get_aicore_num()>0 and props['num_vectorcore']==rt.get_vectorcore_num()>0,'actual driver cores')
 for r in gm['software_dependencies']:R.checked(r)
 def dep(sha):return next(r for r in gm['software_dependencies']if r['sha256']==sha)
 lc_ref=dep('20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533');wr_ref=dep('051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b');base_ref=dep('a5622c480d90e12491740858979fff2984637480e8ae0e16bed5df1a23484df3')
 lc=G.lifecycle_classes(lc_ref,R.load(wr_ref,'_active128_original_device_writer'),R.load(roles['reader'],'_active128_original_reader'))
 base=R.load(base_ref,'_active128_original_compute');g=R.load(gm['files']['graph_kernel.py'],'_active128_graph_kernel');l=R.load(gm['files']['graph_lane.py'],'_active128_graph_lane');s=R.load(gm['files']['slot_plan.py'],'_active128_slot_plan');w=R.load(mf['writer'],'_active128_channel32_writer')
 fmt=torch_npu.get_npu_format
 def get_format(t):
  x=fmt(t);n=x if type(x)is int else getattr(x,'value',None);need(n==2,'real ND format');return n
 arena=lc.CompactArena(torch,8,16,2,torch.bfloat16,device,8*1024**2)
 shared=g.SharedCompute(torch,capacity=33792,device=device,dtype=torch.bfloat16,qualify=clock);remaps=g.LayerRemaps(torch,capacity=33792,device=device,qualify=clock)
 ws=g.Workspace(torch,batch=1,capacity=33792,bits=2,pool=arena.pool,device=device,dtype=torch.bfloat16,get_format=get_format,qualify=clock,shared=shared,remaps=remaps)
 model=g.build(torch,triton,tl,base=base,base_ref=base_ref,device_properties=props,get_format=get_format,qualify=clock)(ws);writer=w.build(triton,tl,qualify=clock)()
 ident=lambda:G.owned_identity(cid)
 lane=l.Lane(ws,model,writer,arena,actual_types=(lc.Request,lc.ReadView,lc.CompactArena),qualify=clock,identity=ident,row_plan=s.row_plan,producer_check=lambda rs,ps:clock())
 # No stepwise zero-prefix repeat: retain the exact original Lane.warm_compile below.
 q,k,v=R.inputs(torch);qdev=q.to(device);kd=k[255:256].to(device);vd=v[255:256].to(device)
 desc=__import__('collections').namedtuple('StandaloneDescriptor','num_tokens num_reqs uniform has_lora')(1,1,True,False)
 try:lane.warm_compile()
 except BaseException as e:
  (out/'RESULT.json').write_text(json.dumps(dict(schema='kivi.real-zero-control-stage/v1',source=own,primary=repr(e),zero_observations=str(out/'ZERO_CONTROL_KERNEL_OBSERVATIONS.json'),numerical_qualified=False,active128_executed=False,model_ready=False,performance_ready=False),sort_keys=True,indent=2)+'\n',encoding='utf-8');raise
 if a.zero_only:
  (out/'RESULT.json').write_text(json.dumps(dict(schema='kivi.real-zero-control-stage/v1',source=own,primary=None,zero_observations=str(out/'ZERO_CONTROL_KERNEL_OBSERVATIONS.json'),original_strict_warm_compile_returned=True,numerical_qualified=False,active128_executed=False,model_ready=False,performance_ready=False),sort_keys=True,indent=2)+'\n',encoding='utf-8');return 0
 before={n:R.tensor_bytes(arena.pool[n].cpu())for n in R.FIELDS}
 graph=torch.npu.NPUGraph();torch.npu.synchronize()
 with torch.npu.graph(graph):result=lane.capture_forward(qdev,kd,vd,capturing=True,descriptor=desc)
 torch.npu.synchronize();need(all(R.tensor_bytes(arena.pool[n].cpu())==before[n]for n in R.FIELDS),'zero-control capture leaves every byte unchanged')
 def save(name,wire):
  path=out/name
  with path.open('xb')as f:need(f.write(wire)==len(wire),'complete raw write')
  return dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
 state=R.State(torch,mf['author']);report=dict(schema='kivi.active128-slot-reuse-raw/v1',source=own,actual_cid=cid,identity=ident(),actual_imports=origins,cases=[],primary=None,actual_graph_captured=True,native_scheduler_qualified=False,model_ready=False,performance_ready=False,task_ready=False,run_authority=False)
 try:
  for ci in range(2):
   state.start(k,v,'active128-epoch%d'%(ci+1));r=arena.acquire(0,state.rid)
   need(r.epoch==state.epoch,'real same-slot new epoch')
   for n in R.FIELDS:arena.pool[n].copy_(state.pool[n].to(device))
   r.length=state.n;r.generation=state.gen;r.kp=tuple(state.kp);r.vp=tuple(state.vp);r.kt=state.kt;r.vt=state.vt
   arena.krefs={p:1 for p in state.kp};arena.vrefs={p:1 for p in state.vp};arena.free_k=list(state.free_k);arena.free_v=list(state.free_v)
   case=dict(request_id=r.owner,epoch=r.epoch,steps=[]);report['cases'].append(case)
   for j in range(3):
    clock();position=r.length;pending=state.pending(k[255+j],v[255+j]);kd.copy_(k[255+j:256+j].to(device));vd.copy_(v[255+j:256+j].to(device))
    stream=torch.npu.current_stream();lane.pre_step((r,),(position,),batch_descriptor=desc,stream=stream);lane.submitted(descriptor=desc,stream=stream);graph.replay();event=torch.npu.Event();event.record(stream);lane.complete(event);clock()
    output=save('c%d-s%d-OUTPUT.bin'%(ci,j),R.tensor_bytes(result.cpu()))
    pools={n:save('c%d-s%d-%s.bin'%(ci,j,n),R.tensor_bytes(arena.pool[n].cpu()))for n in R.FIELDS}
    case['steps'].append(dict(pending_row=pending,output_ref=output,pool_refs=pools,actual_graph_replayed=True,actual_error_zero=True))
    state.finish();need((r.length,r.kt,r.vt,list(r.kp),list(r.vp),r.generation)==(state.n,state.kt,state.vt,state.kp,state.vp,state.gen),'independent ordered publication and actual K128/V-shift')
    for n,b in state.bytes().items():need(R.checked(pools[n])==b,'all full pool bytes independent author '+n)
   # This is an explicit STANDALONE finished callback, never a native scheduler receipt.
   lane.retire(r,actual_native_finished_ids={r.owner});need(0 not in arena.active and not arena.krefs and not arena.vrefs,'real release of both packed maps')
   rejected=False
   try:arena.owned(r)
   except ValueError:rejected=True
   need(rejected,'stale actual owner rejected before slot reuse');state.release();case.update(retired_by_probe_finished_callback=True,stale_request_rejected=True)
  need(sum(p.stat().st_size for p in out.rglob('*')if p.is_file()and cache not in p.parents)<=256*1024**2 and sum(p.stat().st_size for p in cache.rglob('*')if p.is_file())<=512*1024**2,'raw/JIT budgets')
 except BaseException as e:report['primary']=repr(e)
 rr=save('RESULT.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode());print(json.dumps(rr,sort_keys=True));need(report['primary']is None,'active128 component failed, retained original raw')
 return 0
if __name__=='__main__':raise SystemExit(main())
