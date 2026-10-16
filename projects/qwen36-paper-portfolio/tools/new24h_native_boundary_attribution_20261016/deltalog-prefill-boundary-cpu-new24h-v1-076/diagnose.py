"""Two old mixed frames only. No hardware execution, threshold or qualification."""
import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
CHUNK_SHA='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and not p.is_symlink(),'Ref3');h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 need((n,h.hexdigest())==(r['bytes'],r['sha256']),'exact retained source/raw');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def fingerprint(t):return dict(dtype=str(t.dtype),shape=list(t.shape),sha256=hashlib.sha256(t.detach().cpu().contiguous().view(__import__('torch').uint8).numpy().tobytes()).hexdigest())
def bitwise(a,b):return a.dtype==b.dtype and tuple(a.shape)==tuple(b.shape)and fingerprint(a)==fingerprint(b)
def flush_join(t,previous,before,slot):
 other=[i for i in range(previous['base'].shape[0])if i!=slot]
 same={n:bitwise(previous[n][other],before[n][other])for n in FIELDS};need(all(same.values()),'six-array continuity outside the selected prefill flush slot')
 lengths=previous['length'][slot,:,0];need(bool((lengths==lengths[0]).all())and 0<=int(lengths[0])<=7,'head-synchronous capacity')
 n=int(lengths[0]);live_u=bitwise(previous['u_log'][slot,:,:n],before['u_log'][slot,:,:n]);live_k=bitwise(previous['k_log'][slot,:,:n],before['k_log'][slot,:,:n]);lam=bitwise(previous['lambda_log'][slot],before['lambda_log'][slot]);reset=bool((before['length'][slot]==0).all()and(before['decay'][slot]==0).all())
 need(live_u and live_k and lam and reset,'selected flush preserves live K/U and lambda, resets length/decay')
 return dict(nonprefill_sixarrays_unchanged=same,selected_before_log_length=n,selected_live_u_bitwise=live_u,selected_live_k_bitwise=live_k,selected_lambda_bitwise=lam,selected_decay_length_zero=reset,selected_dead_u_NaN_count=int(t.isnan(before['u_log'][slot,:,n:]).sum()),selected_dead_k_NaN_count=int(t.isnan(before['k_log'][slot,:,n:]).sum()),dead_payload_not_compared_as_live=True)
def metric(t,a,b):
 a,b=a.double(),b.double();need(bool(t.isfinite(a).all()and t.isfinite(b).all()),'active finite evidence')
 diff=a-b;flat=int(diff.abs().reshape(-1).argmax());shape=list(a.shape);coord=[]
 for d in reversed(shape):coord.append(flat%d);flat//=d
 return dict(relative_l2=float(diff.norm()/max(float(b.norm()),1e-30)),absolute_l2=float(diff.norm()),reference_l2=float(b.norm()),peak=float(diff.abs().max()/max(float(b.abs().max()),1e-30)),absolute_max=float(diff.abs().max()),max_coordinate=list(reversed(coord)))
def actual_chunk_capture(pc):
 call=pc['native_call'];need(call['schema']=='deltalog.native-chunk-dispatch/v030'and call['actual_original_call_returned']is True,'actual native candidate chunk call returned')
 before,after=call['before'],call['after'];need(before['module_file']['sha256']==after['module_file']['sha256']==CHUNK_SHA and after['counter']==before['counter']+1,'unchanged actual native chunk source/counter')
 need(before['original_id']==before['gdn_alias_id']==before['chunk_alias_id']==after['original_id']==after['gdn_alias_id']==after['chunk_alias_id']and before['controls']==after['controls'],'actual same callable aliases and metadata before/after')
 for name,value in pc['inputs'].items():
  operand=before['operands'][name]
  if type(value)is bool:need(operand==dict(value=value),'native bool operand')
  else:need(fingerprint(value)==operand['actual']==operand['captured']==after['input_fingerprints'][name],'actual captured unchanged native input '+name)
 need(fingerprint(pc['final_state'])==call['returned_state']and fingerprint(pc['output'])==call['returned_output'],'actual native returned tensors join retained capture')
 return dict(source=before['module_file'],pid=before['pid'],before_counter=before['counter'],after_counter=after['counter'],actual_alias_identity=before['original_id']==before['gdn_alias_id']==before['chunk_alias_id'],inputs_after_bitwise=True,returns_joined=True,controls=before['controls'])
def analyze(t,previous,current,R,L):
 need(previous['step']==89 and current['step']==90,'only exact old89-to90')
 need(previous['prefill_slot']==0 and current['prefill_slot']==1 and current['prefill_has_initial_state']is True,'actual B1 nine-step slot swap, not a reset')
 need(previous['ids'].tolist()==[1,0]and current['ids'].tolist()==[0,1],'actual request/slot mapping')
 cap=current['captures']['decode'][0];need(cap['inputs']['ssm_state_indices'].tolist()==[0],'current decode touches slot0, not prefill1')
 joins=flush_join(t,previous['state'],cap['before'],1)
 pc=current['captures']['prefill'][0];pi=pc['inputs'];need(tuple(pi['initial_state'].shape)==(1,12,128,128)and pi['initial_state'].dtype==t.float32,'real FP32 prefill initial-state geometry')
 proof=actual_chunk_capture(pc);previous_proof=actual_chunk_capture(previous['captures']['prefill'][0]);need(proof['pid']==previous_proof['pid']and proof['before_counter']==previous_proof['after_counter'],'same saved native callable process and consecutive invocations')
 candidate=pi['initial_state'][0].transpose(-1,-2).contiguous();native=previous['native_state'][1].contiguous();before=R.restore(t,cap['before'],1);old=R.restore(t,previous['state'],1)
 need(bitwise(candidate,cap['before']['base'][1]),'captured prefill initial is actual flushed base; current decode slot0 cannot mutate slot1')
 final=pc['final_state'][0].transpose(-1,-2).contiguous();need(bitwise(final,current['state']['base'][1]),'native returned prefill state written unchanged to actual base')
 q,k=L.normalized(t,pi['q']),L.normalized(t,pi['k']);cs,ns=candidate.double(),native.double();rho=[1.]*12
 for token in range(64):
  inp={n:v for n,v in zip(('query','key','value','g','beta'),(q[0,token:token+1],k[0,token:token+1],pi['v'][0,token:token+1],pi['g'][0,token:token+1],pi['beta'][0,token:token+1]))}
  cs,_=R.advance(t,cs,inp,0);ns,_=R.advance(t,ns,inp,0)
  for h in range(12):
   kk=k[0,token,h//3].double();factor=math.exp(float(pi['g'][0,token,h]))*max(1.,abs(1.-float(pi['beta'][0,token,h])*float((kk*kk).sum())));rho[h]*=factor
 head_rows=[]
 for h in range(12):
  cb,nb=candidate[h].to(t.bfloat16),native[h].to(t.bfloat16);changes=int((cb.view(t.int16)!=nb.view(t.int16)).sum());initial_metric=metric(t,candidate[h],native[h]);actual=metric(t,final[h],current['native_state'][1,h]);pred=metric(t,cs[h],ns[h])
  head_rows.append(dict(head=h,initial=initial_metric,actual_final=actual,independent_same_operands_final_difference=pred,FP64_linear_recurrence_norm_bound_estimate=initial_metric['absolute_l2']*rho[h],spectral_factor_product_estimate=rho[h],CPU_torch_initial_BF16_rounding_changed_elements=changes))
 initial_delta=candidate.double()-native.double();old_delta=old-native.double();flush_delta=candidate.double()-old;actual_delta=final.double()-current['native_state'][1].double();predicted_delta=cs-ns
 def alignment(a,b):
  den=float(a.norm()*b.norm());return None if den==0 else float((a*b).sum()/den)
 return dict(step=90,slot=1,slot_swap=True,reset=False,state_continuity=joins,captured_native_call=proof,previous_native_call=previous_proof,candidate_initial_equals_flushed_base_bitwise=True,candidate_initial_vs_previous_logical=metric(t,candidate,old),candidate_initial_vs_previous_native=metric(t,candidate,native),previous_logical_vs_previous_native=metric(t,old,native),flush_rounding_vs_independent_restoration=metric(t,before,old),initial_delta_vector_decomposition_residual=float((initial_delta-old_delta-flush_delta).abs().max()),initial_delta_alignment_with_flush=alignment(initial_delta,flush_delta),actual_final_delta_vs_same_operands_CPU64_delta=metric(t,actual_delta,predicted_delta),actual_final_delta_CPU64_delta_cosine=alignment(actual_delta,predicted_delta),candidate_prefill_final_vs_native=metric(t,final,current['native_state'][1]),independent_same_operands_two_initials_final_difference=metric(t,cs,ns),candidate_native_chunk_final_vs_CPU64=metric(t,final,cs),native_baseline_final_vs_CPU64_same_candidate_operands=metric(t,current['native_state'][1],ns),head_rows=head_rows,actual_candidate_base_writeback_bitwise=True,raw_inputs_unchanged=all(bitwise(v,current['original_inputs'][n])for n,v in current['inputs'].items()),current_conv_peer_bitwise=bitwise(current['state']['conv'],current['native_conv']),previous_conv_peer_bitwise=bitwise(previous['state']['conv'],previous['native_conv']),native_baseline_postconv_prefill_operands_captured=False,same_official_NPU_chunk_two_initials_replay_performed=False)
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('source-ref','producer-ref','output'):p.add_argument('--'+n,required=True)
 a=p.parse_args();sr,pr=json.loads(a.source_ref),json.loads(a.producer_ref);m,r=obj(sr),obj(pr);need(r['source']==sr,'actual failed producer source');out=Path(a.output);need(not out.exists()and out.parent.is_dir(),'exclusive new output')
 import torch as t
 t.set_num_threads(1);R=load(m['files']['oracle.py'],'independent076_oracle');RC=load(m['files']['raw_codec.py'],'retained076_codec');RC.install(t);L=load(m['files']['consume.py'],'independent076_boundary');rows=[];primary=None;start=time.monotonic()
 try:
  selected=[v for v in r['records']if v['kind']=='mixed'and v['batch']==1 and v['step']in(89,90)];need([v['step']for v in selected]==[89,90],'exact two old producer frameRefs')
  previous,current=[t.load(checked(v['raw']),map_location='cpu',weights_only=False)for v in selected]
  result=analyze(t,previous,current,R,L);rows=[dict(step=89,raw=selected[0]['raw'],prefill_slot=0,decode_slot=1),dict(result,raw=selected[1]['raw'])]
 except Exception as e:primary=repr(e)
 value=dict(schema='deltalog.step89-90-prefill-boundary-diagnosis/v076',source=sr,producer=pr,rows=rows,primary=primary,qualification=False,NPU_reexecuted=False,old_failure_unchanged=True,elapsed=time.monotonic()-start,scope='retained two-frame CPU attribution only; CPU32 normalization and FP64 recurrence use captured candidate chunk operands; baseline native transformed operands not captured; spectral products are floating diagnostic estimates not certified inequalities',required_next_counterfactual='if evidence supports: MAIN-owned same official native chunk, captured q/k/v/g/beta and metadata identical, only two exact FP32 initial states varied, repeats and FP32/BF16 intermediates retained; no candidate-kernel patch or gate change')
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0 if primary is None else 2
if __name__=='__main__':raise SystemExit(main())
