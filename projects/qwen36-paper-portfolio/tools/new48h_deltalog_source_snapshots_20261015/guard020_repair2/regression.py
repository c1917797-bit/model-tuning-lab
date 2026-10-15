"""One actual original137 call pair, independent truth reused; no full trajectory NPU."""
import math
def identity(t):
 return dict(data_ptr=t.data_ptr(),storage_ptr=t.untyped_storage().data_ptr(),storage_nbytes=t.untyped_storage().nbytes(),storage_offset=t.storage_offset(),shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device))
def identities(states,inputs,seq,side,back):
 return dict(states={a:{k:identity(v)for k,v in s.items()}for a,s in states.items()},inputs={k:identity(v)for k,v in inputs.items()},sequence=identity(seq),sidecar=identity(side),side_back=identity(back))
def strict_state(torch,before,after,ids):
 from precast import bits
 return dict(exact_keys=set(before)==set(after),inactive_bytes=all(bits(torch,before[k][s],after[k][s])for k in before for s in range(before['base'].shape[0])if s not in ids),metadata_padding_bytes=bits(torch,before['lambda_log'][:,:,7:],after['lambda_log'][:,:,7:])and all(bits(torch,before[k][:,:,1:],after[k][:,:,1:])for k in('decay','length')),guards=all(bool((after[k][-2:]==13).all())for k in after))
def byte_invariants(torch,R,before,after,ids):
 from precast import bits
 result=R.invariant(torch,before,after,ids)
 result['untouched_bitwise']=all(bits(torch,before[k][s],after[k][s])for k in before for s in range(before['base'].shape[0])if s not in ids)
 result['append_base_unchanged']=all(bits(torch,before['base'][s],after['base'][s])for s in ids if int(before['length'][s,0,0])<7)
 return result
def run(torch,C,m,prod,debug,save,snapshot,R,S):
 from precast import regression_truth,evaluate,bits,pair,load
 ir,original,truth,ledger=regression_truth(torch,C,m,R,S)
 C.need(original['event']['step']==137 and original['event']['ids'] and original['sequence']is not None,'one exact original137')
 before={k:load(torch,C,r)for k,r in original['before'].items()}
 states={a:{k:v.clone().npu()for k,v in before.items()}for a in('prod','debug')}
 inp={k:v.clone().npu()for k,v in original['inputs'].items()};seq=original['sequence'].clone().npu()
 back=torch.full((original['candidate_output'].numel()+256,),13.,dtype=torch.float32,device='npu:0')
 side=back[128:-128].view_as(original['candidate_output']);side.fill_(float('nan'))
 pre=identities(states,inp,seq,side,back);outs={};before_refs=snapshot(before);debug_before_refs=snapshot({k:v.cpu()for k,v in states['debug'].items()})
 for a,op in(('prod',prod),('debug',debug)):
  st=states[a];args=[inp[k]for k in('query','key','value','g','beta')]+[st[k]for k in('base','k_log','u_log','lambda_log','decay','length')]+[seq,inp['indices']]
  outs[a]=op(*args,*([side]if a=='debug'else[]));torch.npu.synchronize()
 post=identities(states,inp,seq,side,back);after={a:{k:v.cpu()for k,v in st.items()}for a,st in states.items()}
 z,dz,y=outs['prod'].cpu(),outs['debug'].cpu(),side.cpu();red=back.cpu();inputs_after={k:v.cpu()for k,v in inp.items()};seq_after=seq.cpu();q=evaluate(torch,y,z,truth)
 q.update(original_output_bitwise=bits(torch,z,original['candidate_output']),original_after_bitwise=all(bits(torch,after['prod'][k],load(torch,C,original['after'][k]))for k in before),production_debug_bitwise=pair(torch,before,{k:load(torch,C,r)for k,r in debug_before_refs.items()},after['prod'],after['debug'],z,dz,original['inputs'],inputs_after),pointers_stable=pre==post,sidecar_redzones=bool((red[:128]==13).all()and(red[-128:]==13).all()),sequence_unchanged=bits(torch,seq_after,original['sequence']),strict_state=strict_state(torch,before,after['prod'],original['event']['ids']))
 ratios=[]
 for s,request in zip(original['event']['ids'],original['event']['requests']):
  state=R.restore(torch,after['prod'],s);C.need(bool(torch.isfinite(state).all())and bool(torch.isfinite(ledger[request]).all()),'live CPU64 state/truth finite')
  ratio=float((state-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30));C.need(math.isfinite(ratio),'finite ratio');ratios.append(ratio)
 q['state_relative_l2']=max(ratios);q['passed'] &=q['state_relative_l2']<=R.STATE_LIMIT and all(byte_invariants(torch,R,before,after['prod'],original['event']['ids']).values())and all(q['strict_state'].values())and all(q[k]for k in('original_output_bitwise','original_after_bitwise','production_debug_bitwise','pointers_stable','sidecar_redzones','sequence_unchanged'))
 q['raw']=save(dict(original_raw=ir,before=before_refs,debug_before=debug_before_refs,after=snapshot(after['prod']),debug_after=snapshot(after['debug']),candidate_output=z,debug_output=dz,actual_precast_FP32=y,sidecar_backing=red,inputs_after=inputs_after,sequence_after=seq_after,pointers_before=pre,pointers_after=post));return q
