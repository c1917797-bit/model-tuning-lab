"""Whole B16 capture geometry and bitwise predicates; no kernel recurrence."""
import math
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
CAPTURE_FIELDS=FIELDS+('conv',)
def need(v,m):
 if not v:raise ValueError(m)
def bits(T,a,b):return a.dtype==b.dtype and a.shape==b.shape and T.equal(a.contiguous().view(T.uint8),b.contiguous().view(T.uint8))
def identity(t):return dict(data_ptr=t.data_ptr(),offset=t.storage_offset(),shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype))
def unpack(T,raw):
 need(raw['kind']=='mixed'and raw['step']==80 and raw['identity'][0]==16,'actual whole B16step80, no request slicing')
 need(len(raw['captures']['decode'])==1,'one exact recurrent capture');cap=raw['captures']['decode'][0];i=cap['inputs'];ids=i['ssm_state_indices'];seq=i['actual_seq_lengths']
 need(ids.dtype==T.int32 and list(ids.shape)==[16]and ids.tolist()==raw['ids'][:16].tolist()and len(set(ids.tolist()))==16,'all ordered16 actual slots')
 need(seq.dtype==T.int32 and seq.tolist()==[0]+[1]*16,'real individual native sequence ABI')
 need(type(i['scale'])in(int,float)and math.isclose(i['scale'],128**-.5,rel_tol=0,abs_tol=1e-12),'exact current source scale')
 for n,dt,shape in(('query',T.bfloat16,(16,4,128)),('key',T.bfloat16,(16,4,128)),('value',T.bfloat16,(16,12,128)),('g',T.float32,(16,12)),('beta',T.bfloat16,(16,12))):need(i[n].dtype==dt and tuple(i[n].shape)==shape,'actual input geometry '+n)
 need(cap['output'].dtype==T.bfloat16 and tuple(cap['output'].shape)==(16,12,128),'saved16 actual output')
 need(bits(T,cap['output'],raw['candidate_output'][:16]),'capture joins saved fullcore output')
 need(set(cap['before'])==set(CAPTURE_FIELDS)and set(raw['state'])==set(CAPTURE_FIELDS),'complete actual seven-field capture; six operator ABI arrays plus conv')
 slots=cap['before']['base'].shape[0]
 for record in (cap['before'],raw['state']):
  need(record['conv'].dtype==T.bfloat16 and tuple(record['conv'].shape)==(slots,3,2560),'source-generated BF16 conv arena geometry')
 need(raw['native_conv'].dtype==T.bfloat16 and tuple(raw['native_conv'].shape)==(slots,3,2560),'source native conv arena geometry')
 return cap,i,ids.tolist()
def transparency(T,original,before,outputs,after,inputs,inputs_after,guards,pointers_before,pointers_after):
 cap,i,slots=unpack(T,original)
 checks=dict(saved_output=bits(T,outputs['baseline'],cap['output']),production_debug_output=bits(T,outputs['production'],outputs['debug']),production_debug_state=all(bits(T,after['production'][n],after['debug'][n])for n in FIELDS),input_bytes=all(bits(T,inputs[n],inputs_after[n])for n in inputs),guards=all(guards),pointer_stable=pointers_before==pointers_after)
 checks['old_new_state']=all(bits(T,after['baseline'][n],after['production'][n])for n in FIELDS)
 checks['saved_active_state']=all(bits(T,after['production'][n][s],original['state'][n][s])for n in FIELDS for s in slots)
 # The original mixed frame also executed native prefill on its separate slot.
 # A decode-only replay must NOT write that inactive slot to its later value.
 checks['inactive_state']=all(bits(T,after['production'][n][s],before[n][s])for n in FIELDS for s in range(before['base'].shape[0])if s not in slots)
 return checks
