"""Independent original metrics, exact FP64 inverse and three-arm propagation."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
def need(x,s):
 if not x:raise ValueError(s)
def checked(r):
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exactRef3');return b
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r['path']);M=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec'),M.__dict__);return M
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--probe-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'Devices[] explicitCPU')
 sr,pr=json.loads(a.source_ref),json.loads(a.probe_ref);m=json.loads(checked(sr));probe=json.loads(checked(pr));G=module(m['files']['probe_contract.py'],'_shared027_probe_contract');need(G.ready(probe,sr),'complete actual four-arm replay rows/hits')
 sel=json.loads(checked(probe['selection']));cap=json.loads(checked(sel['capture_source']));R=module(cap['files']['independent_reference.py'],'_original013_CPU64');O=module(m['original_metrics'],'_original_metrics027')
 import torch
 BOUNDARY=module(m['files']['boundary_oracle.py'],'_independent_boundary042')
 torch.set_num_threads(1);rows=[]
 for ordinal,rr in enumerate(probe['raws']):
  repeat=ordinal%G.REPEATS;selection_row=sel['rows'][ordinal//G.REPEATS]
  raw=torch.load(__import__('io').BytesIO(checked(rr)),map_location='cpu',weights_only=True);x=raw['normalized_inputs'];need(raw['selection_row']==selection_row and raw['repeat']==repeat,'frozenframe/repeat')
  names=('native','candidate','a32_refined','cpu64_cast');need(set(raw['results'])==set(raw['matrices'])==set(raw['solve_outputs'])==set(names),'all3 realB saved')
  A=raw['matrices']['native'];need(all(torch.equal(A,raw['matrices'][n])for n in names)and (selection_row['role']=='initial_state_rounding_witness'or torch.equal(A,raw['saved_solve_A'])),'sameA')
  inv,checks=O.fp64_reference(torch,A,x['cu_seqlens'].tolist());expected,final=R.recurrence(torch,x);canonical=BOUNDARY.evaluate(torch,x);arms={};tiles=[];dtype=raw['solve_outputs']['native'].dtype;cast=inv.to(dtype)
  need(all(raw['solve_outputs'][n].dtype==dtype for n in names)and torch.equal(cast,raw['solve_outputs']['cpu64_cast']),'same realdtype/exactCP64castB')
  for n in names:
   y=raw['results'][n];B=raw['solve_outputs'][n];imm=all(torch.equal(y['inputs_after'][k],x[k])for k in('q','k','v','g','beta'))and torch.equal(y['initial_after'],x['initial_state'])and torch.equal(y['cu_after'],x['cu_seqlens'])
   arms[n]=dict(output=O.metrics(torch,y['output'],expected),state=O.metrics(torch,y['state'],final),solve_vs_FP64=O.metrics(torch,B,inv),solve_vs_FP64_cast=O.metrics(torch,B,cast.double()),B_equal_cast=torch.equal(B,cast),inputs_unchanged=imm,working_domain_output=O.metrics(torch,y['output'],canonical['output']),working_domain_state=O.metrics(torch,y['state'],canonical['state']))
  for seq,(bos,eos)in enumerate(zip(x['cu_seqlens'].tolist(),x['cu_seqlens'].tolist()[1:])):
   for start in range(bos,eos,64):
    stop=min(start+64,eos)
    for h in range(12):
     idx=(slice(None),slice(start,stop),slice(h,h+1),slice(None));tiles.append(dict(sequence=seq,start=start,valid_rows=stop-start,head=h,arms={n:O.metrics(torch,raw['solve_outputs'][n][idx],inv[idx])for n in names}))
  pairs={}
  for l,r in (('candidate','native'),('candidate','cpu64_cast'),('native','cpu64_cast'),('a32_refined','native'),('a32_refined','cpu64_cast')):
   pairs[l+'_vs_'+r]={k:O.metrics(torch,raw['results'][l][k],raw['results'][r][k].double())for k in ('output','state')};pairs[l+'_vs_'+r]['solve_B']=O.metrics(torch,raw['solve_outputs'][l],raw['solve_outputs'][r].double());pairs[l+'_vs_'+r]['WY']={k:O.metrics(torch,raw['wy_intermediates'][l][k],raw['wy_intermediates'][r][k].double())for k in('w','u')}
  trace=raw['refinement'];need(raw['FP32_policy']['allow_hf32']is False and raw['FP32_policy']['common_to_all_arms']is True,'same actual common matmul policy')
  need(trace['X0_FP32'].dtype==torch.float32 and trace['X1_FP32'].dtype==torch.float32 and torch.equal(trace['X0_FP32'].to(dtype),raw['solve_outputs']['candidate'])and torch.equal(trace['X1_FP32'].to(dtype),raw['solve_outputs']['a32_refined']),'unchanged037 output before correction and actual final cast')
  packed=[]
  for bos,eos in zip(x['cu_seqlens'].tolist(),x['cu_seqlens'].tolist()[1:]):
   for start in range(bos,eos,64):
    count=min(64,eos-start);tile=torch.zeros((12,64,64),dtype=torch.float32);tile[:,:count]=A[0,start:start+count].permute(1,0,2);packed.append(tile)
  packed=torch.cat(packed);need(torch.equal(trace['A32_tiles'],packed),'independent original-A32 pack/sequence/head association')
  eye=torch.eye(64,dtype=torch.float64);refR=eye-torch.bmm(eye+packed.double(),trace['X0_tiles'].double());refX=trace['X0_tiles'].double()+torch.bmm(trace['X0_tiles'].double(),refR)
  correction_diagnostic=dict(R=O.metrics(torch,trace['R'],refR),X1=O.metrics(torch,trace['X1_tiles'],refX),FP32_vs_inverse=O.metrics(torch,trace['X1_FP32'],inv))
  gate=all(arms['a32_refined'][k]['pass']for k in('output','state','solve_vs_FP64'))and all(pairs['a32_refined_vs_native'][k]['pass']for k in('output','state'))and arms['a32_refined']['inputs_unchanged']
  domain_gate=all(arms['native'][k]['pass']and arms['a32_refined'][k]['pass']for k in('working_domain_output','working_domain_state','solve_vs_FP64'))and all(pairs['a32_refined_vs_native'][k]['pass']for k in('output','state'))and all(v['inputs_unchanged']for v in arms.values())
  witness=selection_row['role']=='initial_state_rounding_witness'
  if witness:
   domain_gate=all(bool(torch.equal(raw['results'][n]['state'],x['initial_state'].bfloat16().float()))and bool((raw['results'][n]['output']==0).all())for n in names)
  rows.append(dict(working_domain_gate_pass=domain_gate,initial_state_calibration=witness,role=selection_row['role'],canonical_vs_ideal={k:O.metrics(torch,canonical[k],truth)for k,truth in(('output',expected),('state',final))},discriminating_gate_pass=gate,original_A32_correction_diagnostic=correction_diagnostic,raw=rr,repeat=repeat,prefix=raw['selection_row']['prefix'],actual_B_dtype=str(dtype),arms=arms,pairs=pairs,tile_head_solve=tiles,CPU64_inverse_residuals=checks,candidate_B_saved_bitwise=torch.equal(raw['solve_outputs']['candidate'],raw['saved_solve_output']),cast_floor=O.metrics(torch,cast,inv)))
 need(len(rows)==G.FRAMES*G.REPEATS and all(all(v['inputs_unchanged']for v in row['arms'].values())for row in rows),'all frozeninput evidence')
 need('torch_npu'not in sys.modules and a.output.is_absolute()and not a.output.exists(),'independentCPU newoutput')
 value=dict(schema='mxr.three-arm-solve-chain-independent/v042',source=sr,probe=pr,selection=probe['selection'],rows=rows,complete=True,working_domain_heldout_pass=all(r['working_domain_gate_pass']for r in rows if not r['initial_state_calibration']),actual_native_initial_state_calibration_pass=all(r['working_domain_gate_pass']for r in rows if r['initial_state_calibration']),new_domain_not_instruction_exact=True,model_ready=False,discriminating_gate_pass=all(r['discriminating_gate_pass']for r in rows),numerical_qualification_granted=False,original_failures_unchanged=True,performance=False,task=False,NPU=False,interpretation='measuredB/downstream differences; no automatic cause/no-go; CPU Torch cast is operational, not universal exact-realRNE')
 with a.output.open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
