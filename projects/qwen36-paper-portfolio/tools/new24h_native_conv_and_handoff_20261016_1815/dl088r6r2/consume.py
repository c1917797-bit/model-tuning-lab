"""CPU-only independent scalar recurrence and bitwise raw bridge audit."""
import argparse,json,sys,math,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import bridge_io as C
def relative(torch,a,b):return float((a.double()-b.double()).norm()/max(float(b.double().norm()),1e-30))
def error(torch,a,b):return float((a.double()-b.double()).abs().max()/max(float(b.double().abs().max()),1e-30))
def normalized(torch,x):
 # Independent implementation of the pinned Ascend prefill normalization boundary.
 y=x.float();return(y*torch.rsqrt((y*y).sum(-1,keepdim=True)+1e-6)).to(x.dtype)
def prefill(torch,R,cap):
 i=cap['inputs'];q,k,v,g,beta=[i[n] for n in('q','k','v','g','beta')]
 C.need(i['use_qk_l2norm_in_kernel']is True and list(i['cu_seqlens'])==[0,64] and q.shape==(1,64,4,128),'single actual64 prefill ABI')
 q,k=normalized(torch,q),normalized(torch,k);state=i['initial_state'][0].transpose(-1,-2).double();outs=[]
 for t in range(64):
  inp=dict(query=q[0,t:t+1],key=k[0,t:t+1],value=v[0,t:t+1],g=g[0,t:t+1],beta=beta[0,t:t+1])
  state,o=R.advance(torch,state,inp,0);outs.append(o)
 return dict(state_error=relative(torch,cap['final_state'][0].transpose(-1,-2),state),output_error=error(torch,cap['output'][0],torch.stack(outs)))
def mixed(torch,R,raw):
 state=raw['state'];ids=raw['ids'].tolist();restored=torch.stack([R.restore(torch,state,s)for s in ids]);native=raw['native_state'][ids].double()
 metrics=dict(state_error=relative(torch,restored,native),output_error=error(torch,raw['candidate_output'],raw['native_output']),conv_bitwise=torch.equal(state['conv'],raw['native_conv']),decode=[],prefill=[])
 unchosen=[s for s in range(state['base'].shape[0])if s not in set(ids)]
 metrics.update(untouched_bitwise=all(torch.equal(state[k][unchosen],v)for k,v in raw['unchosen'].items()),guard_bitwise=all(torch.equal(state[k][-2:],v)for k,v in raw['guards'].items()),inputs_bitwise=all(torch.equal(raw['inputs'][k],v)for k,v in raw['original_inputs'].items()),pointers_bitwise=raw['pointer_before']==raw['pointer_after'],prefill_aux_reset_bitwise=all(bool((x==0).all())for x in raw['prefill_aux_after'].values()))
 for cap in raw['captures'].get('decode',[]):
  i=cap['inputs'];slots=i['ssm_state_indices'].flatten().tolist();outs=[];expected=[]
  for j,s in enumerate(slots):
   current,o=R.advance(torch,R.restore(torch,cap['before'],s),i,j);expected.append(current);outs.append(o)
  metrics['decode'].append(dict(output_error=error(torch,cap['output'],torch.stack(outs)),state_error=relative(torch,torch.stack([R.restore(torch,state,s)for s in slots]),torch.stack(expected))))
 for cap in raw['captures'].get('prefill',[]):
  if not raw['prefill_has_initial_state']:C.need(bool((cap['inputs']['initial_state']==0).all()),'real reset reaches native chunk as zero initial state')
  metrics['prefill'].append(prefill(torch,R,cap))
 C.need(len(metrics['decode'])==1 and len(metrics['prefill'])==1,'actual both dispatches recorded')
 return metrics
def copied(torch,R,raw):
 before,after=raw['before'],raw['after'];pairs=raw['pairs'];dest={d for s,d in pairs};slots=before['base'].shape[0]
 bitwise=all(torch.equal(before[k][s],after[k][d])for k in before for s,d in pairs)
 untouched=all(torch.equal(before[k][s],after[k][s])for k in before for s in range(slots)if s not in dest)
 conv=all(torch.equal(raw['before_conv'][s],raw['after_conv'][d])for s,d in pairs)and all(torch.equal(raw['before_conv'][s],raw['after_conv'][s])for s in range(slots)if s not in dest)
 logical=max(relative(torch,R.restore(torch,after,d),R.restore(torch,before,s))for s,d in pairs)
 return dict(bitwise=bitwise,untouched_bitwise=untouched,conv_bitwise=conv,state_error=logical,descriptors_exact=raw['descriptors']['offset']==7*len(pairs))
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','producer-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,pr=[json.loads(getattr(a,k))for k in('source_ref','producer_ref')];m=C.source(sr);r=C.obj(pr);C.need(r['source']==sr and r['schema']=='deltalog.actual-fresh-bridge/v5','same actual producer source');out=Path(a.output);C.need(out.parent.is_dir()and not out.exists(),'exclusive consumer file')
 import torch
 torch.set_num_threads(1);R=C.load(m['files']['oracle.py'],'independent_scalar_oracle');rows=[];primary=None;seen=set();start=time.monotonic()
 try:
  for row in r['records']:
   C.need(time.monotonic()-start<600,'consumer600');raw=torch.load(C.checked(row['raw']),map_location='cpu',weights_only=False)
   C.need(row['kind']!='mixed' or raw['prefill_has_initial_state']is (row['step']not in (5,33,73,113)),'actual registered prefill slotreset metadata')
   v=(C.load(m['files']['consume_increment.py'],'independent_dead_flush').check(torch,raw)if row['kind']=='dead_flush'else mixed(torch,R,raw)if row['kind']=='mixed'else copied(torch,R,raw));seen.add((row['kind'],row['batch']));rows.append(dict(identity={k:v for k,v in row.items()if k!='raw'},raw=row['raw'],independent=v))
   flat=[v]+v.get('decode',[])+v.get('prefill',[])
   C.need(all(x.get('state_error',0)<=R.STATE_LIMIT and x.get('output_error',0)<=R.OUTPUT_LIMIT and all(val for key,val in x.items()if key.endswith('bitwise')or key=='descriptors_exact')for x in flat),'independent raw numerical/bitwise gate')
  C.need(all(any(x['kind']=='mixed' and x['batch']==b and x['step']==5 for x in r['records']) for b in (1,16)),'registered step5 reset coverage')
  C.need(r['primary']is None and seen=={('mixed',1),('mixed',16),('copy',1),('copy',16),('dead_flush',1),('dead_flush',16)},'complete actual source coverage')
  for b in(1,16):
   fl=[x['independent']for x in rows if x['identity']['kind']=='dead_flush'and x['identity']['batch']==b];C.need(len(fl)==2 and any(x['length0']for x in fl)and any(x['partial_live']for x in fl),'explicit real zero/partial deadNaN both batches')
   C.need([x['step']for x in r['records']if x['kind']=='mixed'and x['batch']==b]==list(range(r['steps'])),'all ordered mixed steps without duplicate/gaps')
   C.need([x['length']for x in r['records']if x['kind']=='copy'and x['batch']==b]==[1,7],'all registered copy boundaries')
 except BaseException as e:primary=repr(e)
 # Primitive copy is NOT model factory/scheduler/PDC copy qualification.
 result=dict(schema='deltalog.fresh-bridge-consumption/v5',source=sr,producer=pr,rows=rows,primary=primary,pass_gate=primary is None,actual_prefill_CPU64_qualified=primary is None,actual_native_copy_primitive_qualified=primary is None,actual_native_copy_qualified=False,copy_factory_qualified=False,model_ready=False,graph=False,NPU_reexecuted=False)
 result.update(observation_complete=bool(rows),actual_result=pr);C.write(out,result);return 0
if __name__=='__main__':raise SystemExit(main())
