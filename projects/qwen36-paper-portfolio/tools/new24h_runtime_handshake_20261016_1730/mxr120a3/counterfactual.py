"""Independent CPU A/G-input counterfactuals; no qualification or kernel change."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
VARIANTS=('baseline','actual_G_only','actual_A_only','actual_A_and_G')


def need(v,s):
 if not v:raise ValueError(s)


def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())


def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3');p=Path(r['path'])
 need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'ordinary immutable exact Ref');return p


def obj(r):return json.loads(checked(r).read_bytes())


def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fp(torch,t):
 t=t.detach().cpu().contiguous();return dict(dtype=str(t.dtype),shape=list(t.shape),sha256=hashlib.sha256(t.view(torch.uint8).numpy().tobytes()).hexdigest())


def metric(torch,a,b):
 need(a.shape==b.shape and bool(torch.isfinite(a).all()and torch.isfinite(b).all()),'finite equal-shape diagnostic')
 d=a.double()-b.double();return dict(relative_l2=float(d.norm())/max(float(b.double().norm()),1e-30),max_abs=float(d.abs().max()),changed_values=int((a.double()!=b.double()).sum()),bitwise=fp(torch,a)==fp(torch,b))


def exact_baseline(torch,left,right):
 need(left.keys()==right.keys(),'same original reference result keys')
 names=('output','state');proof={n:fp(torch,left[n])==fp(torch,right[n])for n in names}
 need(len(left['trace'])==len(right['trace']),'same baseline trace coverage')
 trace=[]
 for a,b in zip(left['trace'],right['trace']):
  need(a.keys()==b.keys(),'same exact trace keys');row={}
  for k,v in a.items():row[k]=fp(torch,v)==fp(torch,b[k])if torch.is_tensor(v)else v==b[k]
  need(all(row.values()),'unmodified baseline trace bitwise identity');trace.append(row)
 need(all(proof.values()),'unmodified baseline output/state bitwise identity')
 return dict(output_state=proof,trace_rows=len(trace),all_trace_fields_bitwise=True,current_original_vs_hook_None=True,historical_tensor_hash_available=False,output_refingerprint=fp(torch,left['output']),state_refingerprint=fp(torch,left['state']))


def validate_operands(torch,x,A,G):
 need(x['already_normalized']is True and x['cu_seqlens'].tolist()==[0,2048]and x['scale']==128**-.5,'source-bound actual2K same normalized input')
 for t,shape in((A,(1,2048,12,64)),(G,(1,2048,12))):
  need(t.device.type=='cpu'and t.dtype==torch.float32 and tuple(t.shape)==shape and bool(torch.isfinite(t).all()),'actual FP32 A/G shape and dtype')
 for start in range(0,2048,64):need(not bool(torch.count_nonzero(torch.triu(A[0,start:start+64].permute(1,0,2),diagonal=0))),'actualA strictly lower factor')


def positive_stats(torch,x,A,G,baseline):
 actual_positive=working_positive=actual_A_nonzero_on_positive=0
 for i,w in enumerate(baseline['trace']):
  z=slice(i*64,(i+1)*64);actual=G[0,z].transpose(0,1).double();c=w['g_cumsum'];mask=torch.tril(torch.ones((64,64),dtype=torch.bool),diagonal=-1)
  active=(actual[:,:,None]-actual[:,None,:]>0)&mask
  actual_positive+=int(active.sum());working_positive+=int(((c[:,:,None]-c[:,None,:]>0)&mask).sum())
  actual_A_nonzero_on_positive+=int((active&(A[0,z].permute(1,0,2)!=0)).sum())
 return dict(input_g_positive=int((x['g']>0).sum()),actual_G_lower_positive_diff=actual_positive,working_G_lower_positive_diff=working_positive,actual_A_nonzero_where_actual_lower_diff_positive=actual_A_nonzero_on_positive,safe_exp_A_vs_clamp_can_differ=bool(actual_positive or working_positive),no_safe_exp_formula_change_applied=True,output_QK_clamp_is_separate_semantics=True)


def paired_effect(torch,a,b):
 return dict(output=metric(torch,a['output'],b['output']),state=metric(torch,a['state'],b['state']))


def evaluate_case(torch,original,hook,metrics,x,A,G,arms):
 validate_operands(torch,x,A,G)
 base=original.evaluate(torch,x)
 results=dict(baseline=hook.evaluate(torch,x))
 baseline_proof=exact_baseline(torch,base,results['baseline'])
 for name,a,g in(('actual_G_only',None,G),('actual_A_only',A,None),('actual_A_and_G',A,G)):
  results[name]=hook.evaluate(torch,x,actual_A=a,actual_G=g)
 variants={}
 keys=('B','W','U','Hstart','vnew','decayed_vnew','Hend','output')
 for name,result in results.items():
  chunks=[]
  for i,(t,b)in enumerate(zip(result['trace'],base['trace'])):
   z=slice(i*64,(i+1)*64)
   transitions={k:metric(torch,t[k],b[k])for k in keys}
   if i<31:transitions['Hnext_BF16']=metric(torch,result['trace'][i+1]['Hstart'],base['trace'][i+1]['Hstart'])
   actual={}
   for arm,row in arms.items():
    actual[arm]=dict(B=metric(torch,row['B'][0,z].permute(1,0,2),t['B']),W=metric(torch,row['W'][0,z].transpose(0,1),t['W']),U=metric(torch,row['U'][0,z].transpose(0,1),t['U']),Hentry=metric(torch,row['Hentry'].reshape(1,12,32,128,128)[0,:,i],t['Hstart']),Vnew=metric(torch,row['Vnew'].reshape(1,12,2048,128)[0,:,z],t['vnew']))
   chunks.append(dict(chunk=i,A_vs_actual=metric(torch,A[0,z].permute(1,0,2),t['A32']),G_vs_actual=metric(torch,G[0,z].transpose(0,1),t['g_cumsum']),versus_baseline=transitions,actual_arms=actual))
  variants[name]=dict(actual_arms={arm:dict(output=metrics.metrics(torch,row['output'],result['output']),state=metrics.metrics(torch,row['state'],result['state']))for arm,row in arms.items()},effect_vs_original_baseline=paired_effect(torch,result,base),chunks=chunks)
 interaction=results['actual_A_and_G']['state']-results['actual_A_only']['state']-results['actual_G_only']['state']+base['state']
 return dict(baseline_identity=baseline_proof,positive_g_and_safe_exp=positive_stats(torch,x,A,G,base),variants=variants,state_A_G_interaction_norm=float(interaction.norm()),state_A_G_interaction_max_abs=float(interaction.abs().max()),interaction_is_diagnostic_not_additive_error_budget=True,hidden_actual_intermediate_FP32_Hend_available=False,original_gates_unchanged=True,reference_validity_resolved=False,qualification=False)


def readset(m):
 need(m['default_enabled']is False,'defaultOFF independent CPU source')
 gm=obj(m['guest_source_ref']);G=load(gm['files']['guest_core.py'],'_CF120_exact_guest');model,_,_,refs=G.readset(gm)
 stage=obj(m['actual_stage_ref']);report=obj(m['actual_analysis_ref'])
 need(stage['source']==m['guest_source_ref']and stage['primary']is None and stage['NPU']is True and stage['qualified']is False,'actual complete3frame child stage; failed parent not relabelled')
 need(report['schema']=='mxr.prefill-source-and-round-cell-analysis/v120-analysis1'and report['source']==m['analysis_source_ref']and report['stage_ref']==m['actual_stage_ref']and report['qualification']is False and report['reference_validity_resolved']is False,'exact actual previous source-bound CPU report, not qualification')
 need(report['original_consumer']['source']==m['guest_source_ref']and report['original_consumer']['candidate_anchor_bitwise']is True,'actual original independent anchors')
 need([c['case']for c in report['cases']]==gm['cases']and[case['case_id']for case in stage['result']['cases']]==[c['case_id']for c in gm['cases']],'same3actual input cases')
 refs +=[m['guest_source_ref'],*gm['files'].values(),m['actual_stage_ref'],m['actual_analysis_ref'],m['analysis_source_ref'],m['original_reference_ref'],*m['files'].values()]
 for case in stage['result']['cases']:
  need([r['arm']for r in case['result']['rows']]==['saved_candidate','native','cpu64_cast'],'all9actual arms')
  refs +=[r['raw']for r in case['result']['rows']]
 [checked(r)for r in refs];return gm,G,model,stage,report,refs


def run(torch,m):
 gm,G,model,stage,prior,_=readset(m);original=load(m['original_reference_ref'],'_CF120_independent_original');hook=load(m['files']['reference_inputs.py'],'_CF120_independent_input_hook');metrics=G.load(gm['original_metrics'],'_CF120_original_metrics');out=[]
 for case,item,old in zip(gm['cases'],stage['result']['cases'],prior['cases']):
  saved=G.frame(torch,model,case);x=G.validate_frame(torch,saved);arms={r['arm']:torch.load(checked(r['raw']),map_location='cpu',weights_only=True)for r in item['result']['rows']}
  c=arms['saved_candidate'];need(G.equal(torch,c['B'],saved['solve']['output'])and G.equal(torch,c['output'],saved['output'])and G.equal(torch,c['state'],saved['final_state']),'fresh sameactual X2 B/output/state bitwise anchor')
  need(all(G.equal(torch,z['A'],c['A'])and G.equal(torch,z['G'],c['G'])for z in arms.values()),'same actualA/G for every arm')
  result=evaluate_case(torch,original,hook,metrics,x,c['A'],c['G'],arms)
  # Exact old metrics are carried without overwriting or reinterpreting them.
  out.append(dict(case=case,original_registered_metrics=old['registered_working'],counterfactual=result))
 return dict(schema='mxr.actual-A-G-independent-CPU-counterfactual/v120-analysis3',guest_source=m['guest_source_ref'],actual_stage_ref=m['actual_stage_ref'],prior_analysis_ref=m['actual_analysis_ref'],cases=out,variants=list(VARIANTS),baseline_unchanged=True,qualification=False,model=False,performance=False,task=False,reference_validity_resolved=False,NPU=False,old_failures_preserved=True,no_X3_selected=True)


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"qualification":false}');return 0
 sr=json.loads(a.source_ref);m=obj(sr);need(m['schema']=='mxr.counterfactual-source/v120-analysis3'and m['root']==str(P)and m['files']['counterfactual.py']==ref(__file__),'exact CPU source identity');_,_,_,_,_,refs=readset(m)
 if a.source_audit:print(json.dumps(dict(source=sr,readset=refs,NPU=False,qualification=False)));return 0
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[] CPU only')
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'exclusive new report')
 import torch
 torch.set_num_threads(1);result=run(torch,m);result['source']=sr
 payload=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode();need(len(payload)<=m['budgets']['output_bytes'],'full small report budget; abort never drop evidence')
 with a.output.open('xb')as f:f.write(payload);f.flush();os.fsync(f.fileno())
 return 0


if __name__=='__main__':raise SystemExit(main())
