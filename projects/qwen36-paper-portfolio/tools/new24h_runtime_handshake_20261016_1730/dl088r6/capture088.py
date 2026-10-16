"""Validation-only actual native double controls; no model/timing use."""
import hashlib,inspect
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
CHUNK_SHA='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'
def need(v,s):
 if not v:raise ValueError(s)
def bits(t,a,b):return a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def snapshot(t,kwargs):return {n:v.detach().cpu().clone()for n,v in kwargs.items()if t.is_tensor(v)}
def native_controls(t,native,args,kwargs,actual_result,E,gdn,chunk):
 need(not args and kwargs.get('use_qk_l2norm_in_kernel')is True and kwargs.get('output_final_state')is True and kwargs.get('head_first',False)is False,'original same native prefill API')
 need(kwargs.get('scale')in(None,128**-.5),'fixed native scale, not task tolerance')
 before=snapshot(t,kwargs);need(set(('q','k','v','g','beta','initial_state','cu_seqlens'))<=set(before),'missing native operands')
 need(before['q'].shape==(1,64,4,128)and before['v'].shape==(1,64,12,128)and before['initial_state'].shape==(1,12,128,128)and before['cu_seqlens'].tolist()==[0,64],'actual component geometry')
 proof=E.callable_proof(native,gdn,chunk,0);need(proof['module_file']['sha256']==CHUNK_SHA,'source-proven native chunk, no candidate selfrepeat')
 rows=[]
 for count in(1,2):
  cloned={n:v.clone()if t.is_tensor(v)else v for n,v in kwargs.items()};raw=snapshot(t,cloned)
  need(all(bits(t,before[n],v)for n,v in raw.items()),'actual same given materialized inputs')
  captured_inputs=dict(raw,use_qk_l2norm_in_kernel=cloned['use_qk_l2norm_in_kernel'])
  call_before=E.begin(t,native,gdn,chunk,count-1,(),cloned,captured_inputs)
  value=native(**cloned);t.npu.synchronize();call=E.finish(t,native,gdn,chunk,count,call_before,value,cloned)
  after=snapshot(t,cloned);need(all(bits(t,v,after[n])for n,v in raw.items()),'native control operands changed')
  rows.append(dict(before=raw,after=after,captured_inputs=captured_inputs,call=call,output=value[0].detach().cpu().clone(),state=value[1].detach().cpu().clone()))
 actual=dict(output=actual_result[0].detach().cpu().clone(),state=actual_result[1].detach().cpu().clone())
 need(all(bits(t,r['output'],actual['output'])and bits(t,r['state'],actual['state'])for r in rows),'native same-input controls do not match actual shared prefill')
 return dict(schema='deltalog.actual-same-materialized-native-controls/v088',given_inputs=before,requested_scale=kwargs.get('scale'),effective_scale=128**-.5,actual=actual,controls=rows,original_chunk_source=proof,not_candidate_selfrepeat=True,qualification=False)
def install_flush(t,L,captures):
 original=L._flush_slots
 def flush(T,layer,aux,ids,reason,*a,**kw):
  if reason!='prefill_initial_state_only':return original(T,layer,aux,ids,reason,*a,**kw)
  selected=ids.flatten().long();before={n:aux[n].index_select(0,selected).detach().cpu().clone()for n in FIELDS if n!='base'};before['base']=layer.kv_cache[1].index_select(0,selected).detach().cpu().clone()
  value=original(T,layer,aux,ids,reason,*a,**kw)
  after={n:aux[n].index_select(0,selected).detach().cpu().clone()for n in FIELDS if n!='base'};after['base']=layer.kv_cache[1].index_select(0,selected).detach().cpu().clone()
  captures.setdefault('prefill_flush088',[]).append(dict(before=before,after=after,actual_ids=ids.detach().cpu().clone(),reason=reason));return value
 L._flush_slots=flush
 return lambda:setattr(L,'_flush_slots',original)
