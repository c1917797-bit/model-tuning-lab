"""Devices[] independent actual-A residual + exact BF16 RNE and chain audit."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import guest_core as G
def metric(torch,a,b):
 G.need(a.shape==b.shape and bool(torch.isfinite(a).all()and torch.isfinite(b).all()),'finite same-shape actual comparison');d=a.double()-b.double()
 ulp=None
 if a.dtype==b.dtype and a.dtype in(torch.float32,torch.bfloat16):
  bits=32 if a.dtype==torch.float32 else 16;integer=torch.int32 if bits==32 else torch.int16;mask=(1<<bits)-1;sign=1<<(bits-1)
  def ordered(t):
   n=t.contiguous().view(integer).to(torch.int64)&mask;return torch.where((n&sign)!=0,mask-n,n+sign)
  ulp=int((ordered(a)-ordered(b)).abs().max())
 return dict(relative_l2=float(d.norm()/max(float(b.double().norm()),1e-30)),max_abs=float(d.abs().max()),bitwise=G.equal(torch,a,b),changed_cells=int((a!=b).sum()),changed_bytes=int((a.contiguous().view(torch.uint8)!=b.contiguous().view(torch.uint8)).sum())if a.dtype==b.dtype else None,signedzero_differences=int(((a==0)&(b==0)&(torch.signbit(a)!=torch.signbit(b))).sum()),ULP_max_including_signedzero=ulp)
def consume(torch,m,stage,saved):
 G.need(stage['schema']=='mxr.two-residual-stage/v097'and stage['primary']is None and stage['NPU']is True and stage['qualified']is False and stage['raw']==G.RAW and stage['authority']==G.AUTHORITY,'actual complete097 stage, never model PASS')
 rows=stage['result']['rows'];G.need([r['arm']for r in rows]==list(G.ARMS)and sum(r['raw']['bytes']for r in rows)==stage['result']['raw_bytes']<=G.RAW_CAP,'exact two complete new arms')
 values={r['arm']:torch.load(G.checked(r['raw']),map_location='cpu',weights_only=True)for r in rows};old,new=values['saved_candidate'],values['refined_two']
 previous=G.obj(m['prior092_stage']);G.need(previous['schema']=='mxr.prefill-three-arm-stage/v084'and previous['source']==m['prior084_source']and previous['raw']==G.RAW and previous['authority']==G.AUTHORITY and previous['primary']is None and previous['NPU']is True and previous['qualified']is False,'actual092 previous sameoperand stage, not synthetic old PASS')
 G.need(previous['result']['rows']==m['prior092_rows'],'exact frozen092 artifact refs')
 prior={r['arm']:torch.load(G.checked(r['raw']),map_location='cpu',weights_only=True)for r in previous['result']['rows']}
 keys=('A','G','B','W','U','Hentry','Vnew','Hend_final','output','state')
 G.need(all(G.equal(torch,old[k],prior['saved_candidate'][k])for k in keys),'recomputed original044 whole API path bitwise equals actual092 old arm')
 G.need(G.equal(torch,old['B'],saved['solve']['output'])and G.equal(torch,old['output'],saved['output'])and G.equal(torch,old['state'],saved['final_state']),'independent originalB/output/state anchor')
 for row in [old,new,*prior.values()]:
  G.need(G.equal(torch,row['A'],saved['solve']['A'])and G.equal(torch,row['G'],old['G'])and row['inputs_after']==old['inputs_after'],'same actual A/G/native operands across new and retained native/CPUcast')
  G.need(all(bool(torch.isfinite(row[k]).all())for k in keys),'actual complete finite API path')
 passed=G.obj(m['actual037_prerequisite'])
 for row in (old,new):G.need(row['actual_solver']['source']==passed['source']and row['actual_solver']['build']==passed['build']and row['actual_solver']['library']==passed['library']and row['actual_solver']['symbol']=='call_mxr_y16_compensated','same original037 actual production launch identity')
 O=G.load(m['original_metrics'],'_097_independent_inverse');x=G.validate_frame(torch,saved);inverse,residual=O.fp64_reference(torch,saved['solve']['A'],x['cu_seqlens'].tolist())
 R=G.load(m['files']['direct_round.py'],'_097_independent_integerRNE');nearest=R.round_bf16(torch,inverse)
 G.need(G.equal(torch,prior['cpu64_cast']['B'],inverse.to(torch.bfloat16)),'retained092 CPU64 cast independently recomputed from exactactualA')
 entries=[];seen=[]
 for group in new['refinement_trace']:
  G.need(set(group)=={'rows','A32','X0','X1','R1','X2','R2'},'actual complete two-residual FP32 trace')
  for key in('A32','X0','X1','R1','X2','R2'):G.need(group[key].dtype==torch.float32 and bool(torch.isfinite(group[key]).all()),'actual finite FP32 correction trace')
  for i,(sequence,start,length)in enumerate(group['rows']):
   G.need(sequence==0 and length==64,'actual full2K chunk plan')
   for head in range(12):
    j=i*12+head;seen.append((start,head));A=saved['solve']['A'][0,start:start+64,head,:].double();G.need(G.equal(torch,group['A32'][j],A.float()),'trace packed originalA actual index')
    M=torch.eye(64,dtype=torch.float64)+A;ideal=inverse[0,start:start+64,head,:];bf=nearest[0,start:start+64,head,:]
    b1=group['X1'][j].bfloat16();b2=group['X2'][j].bfloat16();G.need(G.equal(torch,b1,old['B'][0,start:start+64,head,:])and G.equal(torch,b2,new['B'][0,start:start+64,head,:]),'X1 and X2 cast/scatter join exact old/new actualB')
    metrics={}
    for key in('X0','X1','X2'):
     value=group[key][j];r=torch.eye(64,dtype=torch.float64)-M@value.double();metrics[key]=dict(FP64_residual_l2=float(r.norm()),FP64_residual_max=float(r.abs().max()),vs_independent_inverse=metric(torch,value,ideal),cast_vs_direct_integerRNE=metric(torch,value.bfloat16(),bf),FP32_vs_inverse_rounded=metric(torch,value,ideal.float()))
    for iteration,key in((1,'X0'),(2,'X1')):
     e=torch.eye(64,dtype=torch.float64)-M@group[key][j].double();metrics['R'+str(iteration)]=metric(torch,group['R'+str(iteration)][j],e)
    entries.append(dict(start=start,head=head,metrics=metrics))
 G.need(len(seen)==384 and set(seen)=={(s,h)for s in range(0,2048,64)for h in range(12)},'all32chunk×12head trace exactly once')
 pairs={};allrows=dict(old=old,refined_two=new,native=prior['native'],cpu64_cast=prior['cpu64_cast'])
 for name in('old','native','cpu64_cast'):
  other=allrows[name];chunks=[]
  for chunk in range(32):
   z=slice(chunk*64,(chunk+1)*64);cells={k:metric(torch,new[k][:,z],other[k][:,z])for k in('A','G','B','W','U','output')};cells['Hentry']=metric(torch,new['Hentry'].reshape(1,12,32,128,128)[:,:,chunk],other['Hentry'].reshape(1,12,32,128,128)[:,:,chunk]);cells['Vnew']=metric(torch,new['Vnew'].reshape(1,12,2048,128)[:,:,z],other['Vnew'].reshape(1,12,2048,128)[:,:,z]);chunks.append(dict(chunk=chunk,metrics=cells))
  pairs['refined_two_vs_'+name]=dict(chunks=chunks,final_state=metric(torch,new['state'],other['state']),old_registered_peer_metrics=dict(output=O.metrics(torch,new['output'],other['output']),state=O.metrics(torch,new['state'],other['state'])))
 boundary=G.load(m['original_working_oracle'],'_097_unchanged_R6_working');expected=boundary.evaluate(torch,x)
 return dict(schema='mxr.two-residual-independent/v097',source=stage['source'],raw_rows=rows,reused092_stage=m['prior092_stage'],oldB_and_API_bitwise=True,actual_A_only=True,FP64_residual_records=entries,independent_inverse_residual=residual,pairs=pairs,unchanged_R6_working_gate=dict(output=O.metrics(torch,new['output'],expected['output']),state=O.metrics(torch,new['state'],expected['state'])),qualification=False,performance=False,old_failures_unchanged=True,no_new_model_or_holdout=True)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 G.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[] independent consumer')
 sr=json.loads(a.source_ref);m=G.obj(sr);stage=G.obj(json.loads(a.stage_ref));G.need(stage['source']==sr,'exact097 actual stage');model,_,_,_=G.readset(m)
 import torch
 torch.set_num_threads(1);report=consume(torch,m,stage,G.frame(torch,model));G.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'exclusive new CPU report');G.write(a.output,report);return 0
if __name__=='__main__':raise SystemExit(main())
