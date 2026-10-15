"""Independent raw re-opening CPU64 ledger; no candidate materializer/native recurrence."""
import argparse,json,math,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','result-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,rr=json.loads(a.source_ref),json.loads(a.result_ref);m=C.source(sr);stage=C.obj(rr);C.need(stage['schema']=='deltalog.lifecycle-actual-stage/v007'and stage['source']==sr and stage['observation_complete']is True,'actual source-bound stage');producer_ref=stage['actual_result'];v=C.obj(producer_ref);C.need(v['schema']=='deltalog.actual-lifecycle-kernel/v007'and v['source']==sr and v['NPU']is True,'actual producer/source');C.need(not list(Path('/dev').glob('davinci*')),'Devices[] CPU consumer')
 import torch
 torch.set_num_threads(1);from precast import evaluate,pair,bits,regression_truth
 R=C.load(m['files']['oracle.py'],'independent_scalar_oracle');S=C.load(m['files']['scenarios.py'],'actual_scenario_source');records=[];statuses={};loaded={}
 def tensor(r):
  C.checked(r)
  if r['sha256']not in loaded:
   if len(loaded)>18:loaded.clear()
   loaded[r['sha256']]=torch.load(r['path'],map_location='cpu',weights_only=True)
  return loaded[r['sha256']]
 def state(refs):return {k:tensor(r)for k,r in refs.items()}
 for phase,batch,steps in(('smoke',16,4),('full',1,160),('full',16,160)):
  scenario=S.plan(batch)
  for arm in('key_projection',):
   rows=[x for x in v['rows']if x['phase']==phase and x['batch']==batch and x['arm']==arm];expected_step=0;failed=False;gen=torch.Generator().manual_seed(2610151601+batch+(10000 if phase=='full'else 0));initial=(torch.randn((scenario['slots'],12,128,128),generator=gen)*.005).float();ledger={f'initial-{s}':initial[s].double().clone()for s in range(batch)};previous=None
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
     from direct_round import peer_error
     ca=raw['candidate_output'];na=raw['native_output'];expected=torch.stack(outputs);old_point_error,old_point_diagnostic=peer_error(torch,ca,expected);readout_diagnostic=evaluate(torch,raw['actual_precast_FP32'],ca,expected);readout_diagnostic['old_BF16_point_error']=old_point_error;readout_diagnostic['old_BF16_point_diagnostic']=old_point_diagnostic;out_error=readout_diagnostic['peak'] if readout_diagnostic['peak']is not None else float('inf');peer_native=float((ca.float()-na.float()).abs().max())/max(float(na.float().abs().max()),1e-30);cpu_output_error=float((ca.double()-expected).abs().max())/max(float(expected.abs().max()),1e-30);finite=bool(torch.isfinite(ca).all())and bool(torch.isfinite(na).all())and all(bool(torch.isfinite(R.restore(torch,after,s)).all())for s in ids)
    else:C.need(inputs is None and raw['candidate_output']is None and raw['sequence']is None and raw['native_sequence']is None,'emptybatch actualno-op');out_error=cpu_output_error=0.;peer_native=None;readout_diagnostic=None;finite=True
    debug_before=state(raw['debug_before']);debug_after=state(raw['debug_after']);pair_ok=all(bits(torch,before[k],debug_before[k])and bits(torch,after[k],debug_after[k])for k in before)if not ids else pair(torch,before,debug_before,after,debug_after,raw['candidate_output'],raw['debug_output'],inputs,raw['inputs_after']);inv=R.invariant(torch,before,after,ids);guards=all(torch.equal(after[k][-2:],torch.full_like(after[k][-2:],13))for k in after);ptr=raw['pointers_before']==raw['pointers_after'];passed=raw['debug_pointers_before']==raw['debug_pointers_after']and(not ids or bool((raw['sidecar_redzones'][:128]==13).all())and bool((raw['sidecar_redzones'][-128:]==13).all())and bits(torch,raw['sidecar_redzones'][128:-128].view_as(raw['actual_precast_FP32']),raw['actual_precast_FP32'])) and pair_ok and(not ids or readout_diagnostic['passed'])and(not e['checkpoint'] or native_rel is None or native_rel<=R.STATE_LIMIT) and finite and rel<=R.STATE_LIMIT and out_error<=R.OUTPUT_LIMIT and all(inv.values())and guards and ptr
    same=lambda x,y:(y is None and not math.isfinite(x))or(y is not None and math.isfinite(x)and abs(x-y)<1e-12)
    C.need(passed==item['passed']and same(rel,item['state_relative_l2'])and same(out_error,item['output_error'])and inv==item['invariants'],'independent raw verdict/metrics agree');clean=lambda x:x if x is None or math.isfinite(x)else None
    records.append(dict(production_debug_bitwise=pair_ok,actual_precast_readout_pass=not ids or readout_diagnostic['passed'],sidecar_redzones_pass=not ids or bool((raw['sidecar_redzones'][:128]==13).all())and bool((raw['sidecar_redzones'][-128:]==13).all())and bits(torch,raw['sidecar_redzones'][128:-128].view_as(raw['actual_precast_FP32']),raw['actual_precast_FP32']),debug_pointer_stable=raw['debug_pointers_before']==raw['debug_pointers_after'],phase=phase,batch=batch,arm=arm,step=expected_step,passed=passed,state_relative_l2=clean(rel),output_error=clean(out_error),CPU64_output_error=clean(cpu_output_error),peer_native_output_error=peer_native,readout_diagnostic=readout_diagnostic,native_CPU64_checkpoint_relative_l2=clean(native_rel)));previous=after;expected_step+=1;failed=not passed
   statuses[f'{phase}-{arm}-B{batch}']=dict(steps=expected_step,first_failure=expected_step-1 if failed else None,complete=expected_step==steps and not failed)
 regression=None
 if v.get('regression')is not None:
  rg=v['regression'];x=torch.load(C.checked(rg['raw']),map_location='cpu',weights_only=True);ir,original,truth,ledger=regression_truth(torch,C,m,R,S);C.need(x['original_raw']==ir,'actual original137 regression source');after=state(x['after']);da=state(x['debug_after']);before=state(x['before']);regression=evaluate(torch,x['actual_precast_FP32'],x['candidate_output'],truth);regression['original_output_bitwise']=bits(torch,x['candidate_output'],original['candidate_output']);regression['original_after_bitwise']=all(bits(torch,after[k],tensor(original['after'][k]))for k in after);regression['production_debug_bitwise']=pair(torch,before,before,after,da,x['candidate_output'],x['debug_output'],original['inputs'],x['inputs_after']);regression['state_relative_l2']=max(float((R.restore(torch,after,s)-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30))for s,request in zip(original['event']['ids'],original['event']['requests']));regression['passed'] &=regression['state_relative_l2']<=R.STATE_LIMIT and all(R.invariant(torch,before,after,original['event']['ids']).values())and regression['original_output_bitwise']and regression['original_after_bitwise']and regression['production_debug_bitwise'];C.need(regression['passed']==rg['passed'],'independent original137 verdict')
 cpu_ref=C.obj(v['plan'])['cpu_preflight'];cp=C.obj(cpu_ref);dmr=cp['debug_meta_ref'];dm=C.obj(dmr);C.need(cp['source']==sr and cp['pass_gate']is True and dm['source']==sr and dm['debug_build']==m['debug_build_ref']and dm['library']==m['debug_library']and dm['pass_gate']is True and dm['NPU']is False,'independent actual CPU/Meta predecessor')
 complete=regression is not None and regression['passed']and len(records)==324 and v['primary']is None and all(statuses[f'{phase}-key_projection-B{batch}']['complete']for phase,batch in(('smoke',16),('full',1),('full',16)));C.write(a.output,dict(schema='deltalog.independent-lifecycle-consumption/v007',source=sr,actual_result=rr,raw_producer=producer_ref,actual_cpu_preflight_ref=cpu_ref,actual_debug_meta_ref=dmr,validation_contract=m['validation_contract'],records=records,regression=regression,expected_records=325,statuses=statuses,observation_complete=bool(records),pass_gate=complete,missing_cases_allowed_only_after_first_kdma_failure=v['primary']is not None,NPU=False,graph_qualified=False,actual_runtime_copy_qualified=False,model_ready=False));return 0
if __name__=='__main__':raise SystemExit(main())
