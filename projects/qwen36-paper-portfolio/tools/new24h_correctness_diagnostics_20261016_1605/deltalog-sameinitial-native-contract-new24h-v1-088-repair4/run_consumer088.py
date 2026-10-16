"""Explicit eager component-operational report; no whole-history ideal promise."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import consumer088 as C
def checked(r):
 p=Path(r['path']);h=hashlib.sha256();n=0
 C.need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink(),'Ref3')
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 C.need((n,h.hexdigest())==(r['bytes'],r['sha256']),'exact immutable bytes');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true')
 for n in('source-ref','producer-ref','output'):ap.add_argument('--'+n)
 a=ap.parse_args()
 if not a.execute:print('disabled');return 0
 sr,pr=json.loads(a.source_ref),json.loads(a.producer_ref);m,r=obj(sr),obj(pr);C.need(m.get('component_operational088')==dict(seed=2610168801,mode='eager',qualification=False),'explicit actual new source only; old069 forbidden')
 C.need(r['source']==sr and r['primary']is None and r['NPU']is True and r['graph']is False and r['steps']in(16,160),'actual complete new eager160; graph remains missing, never relabel')
 import torch as t
 sys.path.insert(0,str(checked(m['files']['precast.py']).parent))
 t.set_num_threads(1);codec=load(m['files']['raw_codec.py'],'independent088codec');codec.install(t)
 R=load(m['files']['oracle.py'],'independent088CPU64');L=load(m['files']['consume.py'],'original088metrics');A=load(m['files']['sidecar_audit.py'],'independent088sidecar');PRE=load(m['files']['precast.py'],'original088precast');D=load(m['files']['domain_consumer.py'],'original088runtime')
 def raw(ref):return t.load(checked(ref),map_location='cpu',weights_only=False)
 rows=[];sidecar_results=[];primary=None;start=time.monotonic();previous={};ledgers={};anchors={}
 try:
  steps=r['steps'];records=r['records'];C.need(len(records)==2*steps+8,'complete retained records')
  sidecar_results=[];overflow={v['raw']['path']for v in r['boundary_controls']if v['case']=='overflow'}
  C.need(len(r['actual_sidecar_records'])==2*steps+31 and len({v['path']for v in r['actual_sidecar_records']})==2*steps+31,'all original351 sidecar records retained')
  for side_ref in r['actual_sidecar_records']:
   checked_side=A.audit(t,R,PRE,raw(side_ref),overflow=side_ref['path']in overflow);sidecar_results.append(dict(raw=side_ref,audit=checked_side));C.need(checked_side['passed'],'all original independent boundary/production-debug sidecar gates')
  for batch in(1,16):C.need([z['step']for z in records if z['kind']=='mixed'and z['batch']==batch]==list(range(steps)),'complete ordered both B1/B16 mixed lifecycle')
  for rec in records:
   C.need(time.monotonic()-start<600,'CPU600s');x=raw(rec['raw'])
   if rec['kind']!='mixed':
    F=load(m['files']['consume_increment.py'],'original088flushcopy');v=F.check(t,x)if rec['kind']=='dead_flush'else L.copied(t,R,x);C.need(v['state_error']<=R.STATE_LIMIT and all(value is True for key,value in v.items()if key.endswith('bitwise')or key=='descriptors_exact'),'original flush/copy state/byte gate');rows.append(dict(record=rec,unchanged_primitive=v));continue
   batch=rec['batch'];cap=x['captures']['decode'][0];side=raw(cap['actual_sidecar043']);v=A.audit(t,R,PRE,side);C.need(v['passed'],'changed decode original strict CPU64/precast/state/byte predicate')
   pf=C.check(t,R,x);metrics=L.mixed(t,R,x)
   C.need(all(metrics[k]is True for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')),'all original byte/slot/guard gates')
   if batch not in anchors:
    ar=x['initial_anchor_ref'];anchor=raw(ar);C.need(anchor['seed']==2610168801+batch and anchor['before_any_candidate_dispatch']is True and t.equal(anchor['generated_base'],anchor['native_initial']),'independent new initial anchor');anchors[batch]=ar;ledgers[batch]=anchor['generated_base'].double().clone();previous[batch]=D.initial_anchor(t,anchor,sr,r,m,batch)
   C.need(x['initial_anchor_ref']==anchors[batch],'one source initial anchor');ledger=ledgers[batch]
   D.runtime_proof(t,x['captures']['prefill'][0],x['step'],raw(anchors[batch])['pid'],m)
   for ordinal,control in enumerate(x['captures']['prefill'][0]['same_initial088']['controls']):
    control_cap=dict(inputs=control['captured_inputs'],output=control['output'],final_state=control['state'],native_call=control['call']);D.runtime_proof(t,control_cap,ordinal,raw(anchors[batch])['pid'],m)
   transition=D.transition(t,R,x,previous[batch]);C.need(transition['local_transition_pass']and not transition['missing'],'complete original independent state/slot/reset/continuity checks');previous[batch]=x
   for j,s in enumerate(cap['inputs']['ssm_state_indices'].tolist()):ledger[s],_=R.advance(t,ledger[s],cap['inputs'],j)
   pc=x['captures']['prefill'][0];i=pc['inputs'];s=x['prefill_slot'];st=ledger[s].clone()if x['prefill_has_initial_state']else t.zeros_like(ledger[s]);q,k=L.normalized(t,i['q']),L.normalized(t,i['k'])
   for token in range(64):
    inp={n:z for n,z in zip(('query','key','value','g','beta'),(q[0,token:token+1],k[0,token:token+1],i['v'][0,token:token+1],i['g'][0,token:token+1],i['beta'][0,token:token+1]))};st,_=R.advance(t,st,inp,0)
   ledger[s]=st;ids=x['ids'].tolist();ca=t.stack([R.restore(t,x['state'],slot)for slot in ids]);na=x['native_state'][ids].double()
   cross=dict(candidate_vs_independent_cumulative_CPU64=C.relative(t,ca,ledger[ids]),native_vs_independent_cumulative_CPU64=C.relative(t,na,ledger[ids]),candidate_vs_native=C.relative(t,ca,na),numeric_domain='actual captured transformed operands + original FP32 normalizer boundary + independent cumulative FP64 recurrence, not exact native instruction truth')
   rows.append(dict(record=rec,decode=v,prefill=pf,old_cross_history_metrics=metrics,cross_history=cross,component_operational_pass=True))
 except BaseException as e:primary=repr(e)
 out=Path(a.output);C.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'new exclusive receipt')
 result=dict(schema='deltalog.eager-component-operational-report/v088',source=sr,producer=pr,steps=r['steps'],anchors=anchors,validation_contract=dict(schema='deltalog.eager-sameinitial-native-operational/v088',seed=2610168801,graph_qualified=False),domain_checks_pass=primary is None,missing_evidence=[],failures=[]if primary is None else[primary],rows=rows,sidecar_results=sidecar_results,primary=primary,eager_component_operational_pass=primary is None,graph_tested=False,full_requested_scope_pass=False,qualified=False,old069_FAIL_unchanged=True,native_is_not_mathematical_truth=True,cumulative_error_not_ignored=True,NPU_reexecuted=False)
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,sort_keys=True,allow_nan=False)
 return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())
