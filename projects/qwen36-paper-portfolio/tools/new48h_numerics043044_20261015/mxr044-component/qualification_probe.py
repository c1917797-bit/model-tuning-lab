"""Existing-Owned callback + independent CPU CLI, not a new resource owner.

MAIN's existing042 child must supply already initialized/proven singleton solver,
pool/backend and actual ARM receipt. No container/device discovery or launch here.
"""
import argparse,hashlib,importlib.util,json,os,random,time
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 h=hashlib.sha256();size=0
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):
 need(Path(r['path']).is_absolute()and not Path(r['path']).is_symlink()and ref(r['path'])==r,'actual immutable Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def module(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def recipes():
 cases=[('real16-short129',[0,129]),('real40-short129',[0,129]),('long32768-B1',[0,32768]),('long40960-B2',[0,32768,40960]),('long40960-B16',[0]+[2049*i for i in range(1,16)]+[40960])]
 for group in range(4):
  cu=[0]
  for tail in range(group*16,(group+1)*16):cu.append(cu[-1]+64+tail)
  cases.append(('tail-family-%d'%group,cu))
 return cases
def make_input(torch,seeds,cu,ordinal,planner):
 if ordinal<2:return seeds[ordinal].clone()
 A=torch.zeros((1,cu[-1],12,64),dtype=torch.float32);rng=random.Random(2610154401+ordinal)
 for _,start,n in planner.plan(cu,cu[-1])[0]:
  source=seeds[rng.randrange(2)];base=64*rng.randrange(2)
  A[0,start:start+n,:,:n].copy_(source[0,base:base+n,:,:n])
 return A
def produce(solver,pool,event_backend,*,source_ref,actual042_probe_ref,owner_arm_ref,plan_ref,output,deadline_monotonic):
 """Exact callback after existing MAIN DEVICE->SMI proof->ARM; three repeats.

Retains original source/budget authority. Caller must wrap this with its existing
Owned child, actual cleanup and actual producer/independent receipt consumers.
"""
 m=obj(source_ref);B=module(m['files']['block_refine.py'],'_044actualblock');legacy=module(m['files']['legacy_refine.py'],'_044actuallegacy');torch=solver.torch
 need(os.environ.get(B.ENABLE)=='1'and os.environ.get('MXR_ORIGINAL_A32_RESIDUAL027_ENABLE')=='1','both explicit numeric optins')
 need(time.monotonic()<deadline_monotonic<=time.monotonic()+900 and time.time()+900<1792135097,'existing child900/fixed cutoff')
 plan=obj(plan_ref);need(plan==dict(schema='mxr.saved-frame-replay-plan/v044',source=source_ref,physical=4,logical=0,output=str(output)),'literal new source/output/physical plan')
 arm=obj(owner_arm_ref);need(arm['schema']=='mxr.actual-owned-replay-arm/v1'and arm['pid']==os.getpid()and arm['physical']==4 and arm['plan_sha256']==plan_ref['sha256'],'actual prior owner ARM for this exact new plan, no self dispatch')
 old=obj(actual042_probe_ref);need(old['source']==m['actual042_source']and old['primary']is None and old['candidate_hits']==18 and len(old['raws'])==9,'actual042 complete real source inputs')
 seeds=[]
 for index,layer in((0,16),(3,40)):
  raw=torch.load(checked(old['raws'][index]),map_location='cpu',weights_only=True);need(raw['selection_row']['prefix']=='language_model.model.layers.%d.linear_attn'%layer and raw['selection_row']['role']=='nontrivial_heldout_layer%d'%layer,'source-bound original model A, not witness')
  A=raw['matrices']['native'];need(tuple(A.shape)==(1,129,12,64)and A.dtype==torch.float32,'actual originalA32');seeds.append(A)
 output=Path(output);need(output.is_absolute()and not output.exists(),'new owned output');output.mkdir();rows=[];primary=None
 try:
  for ordinal,(name,cu)in enumerate(recipes()):
   need(time.monotonic()<deadline_monotonic,'same child deadline');A=make_input(torch,seeds,cu,ordinal,B);deviceA=A.to(solver.device);devicecu=torch.tensor(cu,dtype=torch.int32,device=solver.device);chunks=len(B.plan(cu,cu[-1])[0]);outputs=[];legacy_output=None
   for repeat in range(3):
    result=B.eager(solver,deviceA,devicecu,chunks,torch.bfloat16,pool,event_backend,cu);pool.finish();outputs.append(result.cpu());del result
   if ordinal<2:
    legacy_output=legacy.eager(solver,deviceA,devicecu,chunks,torch.bfloat16,pool,event_backend,cu);pool.finish();legacy_output=legacy_output.cpu()
   unchanged=torch.equal(deviceA.cpu(),A);payload=dict(source=source_ref,name=name,cu=cu,A=A,outputs=outputs,legacy_short_output=legacy_output,input_unchanged=unchanged,operator=solver.experiment_identity,budget=B.budget(cu,cu[-1]),seed=2610154401+ordinal)
   target=output/(name+'.pt');torch.save(payload,target);rows.append(ref(target));need(sum(r['bytes']for r in rows)<=1280*1024**2,'registered1.25GiB evidence within old4GiB disk budget')
 except BaseException as exc:primary=repr(exc)
 result=dict(schema='mxr.block-refinement-actual-numeric/v044',source=source_ref,actual042_probe=actual042_probe_ref,owner_arm=owner_arm_ref,plan=plan_ref,raws=rows,primary=primary,NPU=True,model_ready=False,performance_ready=False,math_qualification=False)
 with(output/'RESULT.json').open('x')as f:json.dump(result,f,sort_keys=True);f.write('\n')
 need(primary is None,'preserved actual numeric failure '+str(primary));return ref(output/'RESULT.json')
def consume(source_ref,result_ref,output):
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not list(Path('/dev').glob('davinci[0-9]*')),'actual Owned Devices[] CPU')
 m=obj(source_ref);result=obj(result_ref);need(result['source']==source_ref and result['primary']is None and result['NPU']is True and len(result['raws'])==9,'all actual nine cases before CPU gate')
 O=module(m['original_metrics'],'_044independent_original_metrics');import torch
 torch.set_num_threads(1);rows=[]
 for rr,(name,cu)in zip(result['raws'],recipes()):
  raw=torch.load(checked(rr),map_location='cpu',weights_only=True);need(raw['source']==source_ref and raw['name']==name and raw['cu']==cu and raw['input_unchanged']is True and len(raw['outputs'])==3,'all frozen input/case/repeat evidence')
  expected,residual=O.fp64_reference(torch,raw['A'],cu);metrics=[O.metrics(torch,v,expected)for v in raw['outputs']];tiles=[]
  for seq,(a,z)in enumerate(zip(cu,cu[1:])):
   for start in range(a,z,64):
    n=min(64,z-start)
    for head in range(12):
     index=(0,slice(start,start+n),head,slice(0,n));tiles.append(all(O.metrics(torch,v[index],expected[index])['pass']for v in raw['outputs']))
  old=raw['legacy_short_output'];same=old is None or all(torch.equal(v,old)for v in raw['outputs']);passed=all(x['pass']for x in metrics)and all(tiles)and same
  rows.append(dict(name=name,raw=rr,cu=cu,metrics=metrics,all_tile_head_pass=all(tiles),legacy_short_bitwise=same,pass_gate=passed,FP64_residuals=residual))
 value=dict(schema='mxr.block-refinement-independent/v044',source=source_ref,actual_result=result_ref,rows=rows,complete=True,pass_gate=all(x['pass_gate']for x in rows),NPU=False,model_ready=False,performance_ready=False,task_ready=False,scope='operator numeric shape/metadata only; repeated real A is not longest fullGDN/model qualification')
 with Path(output).open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0 if value['pass_gate']else 3
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--result-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 return consume(json.loads(a.source_ref),json.loads(a.result_ref),a.output)
if __name__=='__main__':raise SystemExit(main())
