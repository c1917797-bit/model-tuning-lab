"""Independent raw re-opening CPU64 ledger; no candidate materializer/native recurrence."""
import argparse,json,math,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','result-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,rr=json.loads(a.source_ref),json.loads(a.result_ref);m=C.source(sr);stage=C.obj(rr);C.need(stage['schema']=='deltalog.lifecycle-actual-stage/v004'and stage['source']==sr and stage['observation_complete']is True,'actual source-bound stage');producer_ref=stage['actual_result'];v=C.obj(producer_ref);C.need(v['schema']=='deltalog.actual-lifecycle-kernel/v004'and v['source']==sr and v['NPU']is True,'actual producer/source');C.need(not list(Path('/dev').glob('davinci*')),'Devices[] CPU consumer')
 import torch
 torch.set_num_threads(1);R=C.load(m['files']['oracle.py'],'independent_scalar_oracle');S=C.load(m['files']['scenarios.py'],'actual_scenario_source');records=[];statuses={};loaded={}
 def tensor(r):
  C.checked(r)
  if r['sha256']not in loaded:
   if len(loaded)>18:loaded.clear()
   loaded[r['sha256']]=torch.load(r['path'],map_location='cpu',weights_only=True)
  return loaded[r['sha256']]
 def state(refs):return {k:tensor(r)for k,r in refs.items()}
 for batch in(1,16):
  scenario=S.plan(batch)
  for arm in('baseline','kdma'):
   rows=[x for x in v['rows']if x['batch']==batch and x['arm']==arm];expected_step=0;failed=False;gen=torch.Generator().manual_seed(260815533+batch);initial=(torch.randn((scenario['slots'],12,128,128),generator=gen)*.005).float();ledger={f'initial-{s}':initial[s].double().clone()for s in range(batch)};previous=None
   for item in rows:
    C.need(not failed and item['step']==expected_step,'contiguous firstfailure trajectory');raw=torch.load(C.checked(item['raw']),map_location='cpu',weights_only=True);e=scenario['events'][expected_step];C.need(raw['event']==e and torch.equal(tensor(raw['initial']),initial),'frozen event/RNGinitial');before,after=state(raw['before']),state(raw['after']);join_slots=set()
    for action in e['actions']:
     if action['op']=='retire':ledger.pop(action['request']);continue
     s=action['slot'];join_slots.add(s);initial_join=(torch.randn((12,128,128),generator=gen)*.005).float()if action['initial']=='nonzero'else torch.zeros((12,128,128));C.need(torch.equal(raw['joins'][s],initial_join),'join RNGstate');ledger[action['request']]=initial_join.double().clone();C.need(torch.equal(before['base'][s],initial_join)and all(bool((before[k][s]==0).all())for k in before if k!='base'),'complete joined state reset')
    if previous is not None:C.need(all(torch.equal(previous[k][s],before[k][s])for k in before for s in range(scenario['slots'])if s not in join_slots),'previous persistentstate continuity')
    ids=e['ids'];inputs=raw['inputs'];outputs=[];rel=0.;native_rel=None
    if ids:
     b=len(ids);q=torch.nn.functional.normalize(torch.randn((b,4,128),generator=gen),dim=-1);k=torch.nn.functional.normalize(torch.randn((b,4,128),generator=gen),dim=-1)
     generated=dict(query=q.to(torch.bfloat16),key=k.to(torch.bfloat16),value=(torch.randn((b,12,128),generator=gen)*.2).to(torch.bfloat16),g=-(.002+.18*torch.rand((b,12),generator=gen)),beta=torch.sigmoid(torch.randn((b,12),generator=gen)).to(torch.bfloat16),indices=torch.tensor(ids,dtype=torch.int32))
     C.need(set(inputs)==set(generated)and all(torch.equal(inputs[k],generated[k])and torch.equal(inputs[k],raw['inputs_after'][k])for k in inputs),'all-step exact inputrecipe/unchanged');C.need(torch.equal(raw['sequence'],torch.arange(b+1,dtype=torch.int32)),'frozen candidate sequence argument')
     C.need(torch.equal(raw['native_sequence'],torch.cat((torch.zeros(1,dtype=torch.int32),torch.ones(b,dtype=torch.int32)))),'native per-sequence lengths ABI, NOT cumulative starts')
     for row,(s,request)in enumerate(zip(ids,e['requests'])):
      ledger[request],o=R.advance(torch,ledger[request],inputs,row);outputs.append(o);actual=R.restore(torch,after,s);rel=max(rel,float((actual-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30)))
      if raw['native_state']is not None:
       r=float((raw['native_state'][s].double()-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30));native_rel=max(native_rel or 0.,r)
     ca=raw['candidate_output'].float();na=raw['native_output'].float();expected=torch.stack(outputs).float();out_error=float((ca-na).abs().max())/max(float(na.abs().max()),1e-30);cpu_output_error=float((ca-expected).abs().max())/max(float(expected.abs().max()),1e-30);finite=bool(torch.isfinite(ca).all())and bool(torch.isfinite(na).all())and all(bool(torch.isfinite(R.restore(torch,after,s)).all())for s in ids)
    else:C.need(inputs is None and raw['candidate_output']is None and raw['sequence']is None and raw['native_sequence']is None,'emptybatch actualno-op');out_error=cpu_output_error=0.;finite=True
    inv=R.invariant(torch,before,after,ids);guards=all(torch.equal(after[k][-2:],torch.full_like(after[k][-2:],13))for k in after);ptr=raw['pointers_before']==raw['pointers_after'];passed=(not e['checkpoint'] or native_rel is None or native_rel<=R.STATE_LIMIT) and finite and rel<=R.STATE_LIMIT and out_error<=R.OUTPUT_LIMIT and all(inv.values())and guards and ptr
    same=lambda x,y:(y is None and not math.isfinite(x))or(y is not None and math.isfinite(x)and abs(x-y)<1e-12)
    C.need(passed==item['passed']and same(rel,item['state_relative_l2'])and same(out_error,item['output_error'])and inv==item['invariants'],'independent raw verdict/metrics agree');clean=lambda x:x if x is None or math.isfinite(x)else None
    records.append(dict(batch=batch,arm=arm,step=expected_step,passed=passed,state_relative_l2=clean(rel),output_error=clean(out_error),CPU64_output_error=clean(cpu_output_error),native_CPU64_checkpoint_relative_l2=clean(native_rel)));previous=after;expected_step+=1;failed=not passed
   statuses[f'{arm}-B{batch}']=dict(steps=expected_step,first_failure=expected_step-1 if failed else None,complete=expected_step==160 and not failed)
 complete=v['primary']is None and all(statuses['kdma-B'+str(b)]['complete']for b in(1,16));C.write(a.output,dict(schema='deltalog.independent-lifecycle-consumption/v004',source=sr,actual_result=rr,raw_producer=producer_ref,records=records,statuses=statuses,observation_complete=bool(records),pass_gate=complete,missing_cases_allowed_only_after_first_kdma_failure=v['primary']is not None,NPU=False,graph_qualified=False,actual_runtime_copy_qualified=False,model_ready=False));return 0
if __name__=='__main__':raise SystemExit(main())
