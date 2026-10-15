"""Frozen empirical readout predicate, not a CANN error-bound theorem."""
import math
PEAK=.00303;L2=2.0**-13
def bits(torch,a,b):return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
def evaluate(torch,y,z,truth):
 from direct_round import round_bf16
 if y.dtype!=torch.float32 or z.dtype!=torch.bfloat16 or truth.dtype!=torch.float64 or y.shape!=z.shape or y.shape!=truth.shape:raise ValueError('exact actual sidecar/BF16/wholeCPU64 ABI')
 if truth.ndim<1 or truth.numel()==0:raise ValueError('nonempty request dimension')
 finite=all(bool(torch.isfinite(v).all())for v in(y,z,truth));peak=l2=None;cast=False;requests=[];whole=None
 def metric(a,t):
  e=a.double()-t;M=float(t.abs().max());N=float(t.norm());E=float(e.norm());A=float(e.abs().max());p=A/M if M else(0. if A==0 else None);r=E/N if N else(0. if E==0 else None)
  return dict(peak=p,relative_l2=r,passed=p is not None and r is not None and p<=PEAK and r<=L2)
 if finite:
  whole=metric(y,truth)
  for i in range(truth.shape[0]):requests.append(dict(request_row=i,**metric(y[i],truth[i])))
  peak=max(x['peak']for x in requests)if all(x['peak']is not None for x in requests)else None;l2=max(x['relative_l2']for x in requests)if all(x['relative_l2']is not None for x in requests)else None;cast=bits(torch,z,round_bf16(torch,y.double()))
 return dict(peak=peak,relative_l2=l2,requests=requests,whole_batch_diagnostic=whole,per_request_worst=True,cast_bitwise=cast,finite=finite,passed=finite and bool(requests)and all(x['passed']for x in requests)and cast)
def pair(torch,before,debug_before,after,debug_after,z,dz,inputs,inputs_after):
 return set(before)==set(debug_before)==set(after)==set(debug_after)and all(bits(torch,before[k],debug_before[k])and bits(torch,after[k],debug_after[k])for k in before)and bits(torch,z,dz)and set(inputs)==set(inputs_after)and all(bits(torch,v,inputs_after[k])for k,v in inputs.items())
def load(torch,C,r):return torch.load(C.checked(r),map_location='cpu',weights_only=True)
def regression_truth(torch,C,m,R,S):
 i=C.obj(m['files']['REGRESSION_INPUTS.json']);p=C.obj(i['producer']);rows=[x for x in p['rows']if x['phase']=='full'and x['batch']==16]
 C.need(len(rows)==138 and [dict(step=x['step'],raw=x['raw'])for x in rows]==i['rows'],'original137 actual138 trajectory')
 scenario=S.plan(16);gen=torch.Generator().manual_seed(2610161317);initial=(torch.randn((scenario['slots'],12,128,128),generator=gen)*.005).float();ledger={f'initial-{s}':initial[s].double().clone()for s in range(16)}
 for step,item in enumerate(rows):
  raw=load(torch,C,item['raw']);e=scenario['events'][step];C.need(raw['event']==e and torch.equal(load(torch,C,raw['initial']),initial),'original137 event/initial')
  for a in e['actions']:
   if a['op']=='retire':ledger.pop(a['request']);continue
   v=(torch.randn((12,128,128),generator=gen)*.005).float()if a['initial']=='nonzero'else torch.zeros((12,128,128));C.need(torch.equal(v,raw['joins'][a['slot']]),'original137 joins');ledger[a['request']]=v.double().clone()
  b=len(e['ids']);truth=[]
  if b:
   q=torch.nn.functional.normalize(torch.randn((b,4,128),generator=gen),dim=-1);k=torch.nn.functional.normalize(torch.randn((b,4,128),generator=gen),dim=-1)
   inp=dict(query=q.bfloat16(),key=k.bfloat16(),value=(torch.randn((b,12,128),generator=gen)*.2).bfloat16(),g=-(.002+.18*torch.rand((b,12),generator=gen)),beta=torch.sigmoid(torch.randn((b,12),generator=gen)).bfloat16(),indices=torch.tensor(e['ids'],dtype=torch.int32))
   C.need(set(inp)==set(raw['inputs'])and all(bits(torch,v,raw['inputs'][k])and bits(torch,v,raw['inputs_after'][k])for k,v in inp.items()),'original137 complete input recipe')
   for n,request in enumerate(e['requests']):ledger[request],y=R.advance(torch,ledger[request],inp,n);truth.append(y)
 return i['rows'][-1]['raw'],raw,torch.stack(truth),ledger
def regression_run(torch,C,m,prod,debug,save,snapshot,R,S):
 ir,original,truth,ledger=regression_truth(torch,C,m,R,S);before={k:load(torch,C,r)for k,r in original['before'].items()};states={arm:{k:v.clone().npu()for k,v in before.items()}for arm in('prod','debug')};inp={k:v.npu()for k,v in original['inputs'].items()};seq=original['sequence'].npu();side=torch.empty_like(original['candidate_output'],dtype=torch.float32,device='npu:0');outputs={}
 for arm,op in(('prod',prod),('debug',debug)):
  st=states[arm];args=[inp[k]for k in('query','key','value','g','beta')]+[st[k]for k in('base','k_log','u_log','lambda_log','decay','length')]+[seq,inp['indices']];outputs[arm]=op(*args,*([side]if arm=='debug'else[]));torch.npu.synchronize()
 after={arm:{k:v.cpu()for k,v in st.items()}for arm,st in states.items()};z=outputs['prod'].cpu();dz=outputs['debug'].cpu();y=side.cpu();p=evaluate(torch,y,z,truth);p['original_output_bitwise']=bits(torch,z,original['candidate_output']);p['production_debug_bitwise']=pair(torch,before,before,after['prod'],after['debug'],z,dz,original['inputs'],{k:v.cpu()for k,v in inp.items()});p['original_after_bitwise']=all(bits(torch,after['prod'][k],load(torch,C,original['after'][k]))for k in before);p['passed'] &=p['original_output_bitwise']and p['production_debug_bitwise']and p['original_after_bitwise'];p['original_raw']=ir
 p['state_relative_l2']=max(float((R.restore(torch,after['prod'],s)-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30))for s,request in zip(original['event']['ids'],original['event']['requests']));p['passed'] &=p['state_relative_l2']<=R.STATE_LIMIT and all(R.invariant(torch,before,after['prod'],original['event']['ids']).values())
 p['raw']=save(dict(original_raw=ir,before=original['before'],after=snapshot(after['prod']),debug_after=snapshot(after['debug']),candidate_output=z,debug_output=dz,actual_precast_FP32=y,inputs_after={k:v.cpu()for k,v in inp.items()}));return p
