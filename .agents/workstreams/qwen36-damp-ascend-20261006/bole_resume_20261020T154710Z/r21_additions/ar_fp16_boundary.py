"""Explicit precision-qualified private native-AR control; original control retained."""
from sourceio import need,ref,obj,checked
class NativeARBoundary:
 def __init__(self,t,delegate,capture,source,qualification):
  need(ref(__file__)==source,'exact separately qualified AR precision source')
  need(set(qualification)=={'numeric','owner','cleanup'},'complete actual AR replay evidence')
  evidence=obj(qualification['numeric']);owner=obj(qualification['owner']);cleanup=obj(qualification['cleanup'])
  checked(evidence['source'])
  need(evidence['schema']=='bole.native-ar-fia-actual-savedinput-matrix/v1'and
   evidence['frame_count']==evidence['original_bitwise_matches']==256 and
   evidence['summary']['fp16-ip0']==dict(frames=256,failed=0)and not evidence['errors']and
   owner['source']==evidence['source']and owner['frames']==evidence['frames']and owner['cid']==cleanup['cid']and
   owner['physical']==[4]and evidence['physical_npu']==4 and evidence['guest_npu']==0 and
   owner['primary']is None and owner['secondary']==[]and cleanup['stopped']is True and cleanup['retained']is True,
   'actual complete replay256 FP16 ip0 gate and cleanup')
  need('ar_fp16_boundary'not in capture,'one native AR boundary receipt')
  self.t=t;self.delegate=delegate
  self.record=dict(source=source,qualification=qualification,completed=False,input_dtype='torch.float16',
   output_dtype='torch.bfloat16',kernel_kind='dense/BNSD/unmasked/ip0',cast={})
  capture['ar_fp16_boundary']=self.record
 def npu_fused_infer_attention_score(self,**kwargs):
  t=self.t;need(not self.record['completed'],'single native AR boundary call')
  required={'query','key','value','input_layout','num_heads','num_key_value_heads','scale',
   'actual_seq_lengths','actual_seq_lengths_kv','sparse_mode','pre_tokens','next_tokens','inner_precise'}
  need(set(kwargs)==required,'original dense unmasked argument set')
  q,k,v=(kwargs[x]for x in('query','key','value'));length=k.shape[2]if k.ndim==4 else-1
  need(q.shape==(1,6,1,256)and k.shape==v.shape==(1,1,length,256)and length in(132,133),'actual C1/131 native AR geometry')
  need(q.dtype==k.dtype==v.dtype==t.bfloat16,'original native AR inputs BF16')
  need(kwargs['input_layout']=='BNSD'and kwargs['num_heads']==6 and kwargs['num_key_value_heads']==1 and
   kwargs['scale']==256**-.5 and kwargs['actual_seq_lengths']==[1]and kwargs['actual_seq_lengths_kv']==[length]and
   kwargs['sparse_mode']==0 and kwargs['pre_tokens']==kwargs['next_tokens']==2147483647 and kwargs['inner_precise']==0,
   'all original native AR operation arguments unchanged')
  converted=dict(kwargs);before={}
  for name in('query','key','value'):
   original=kwargs[name];need(bool(t.isfinite(original).all()),'finite original AR input')
   value=original.to(t.float16);need(bool(t.isfinite(value).all()),'finite AR FP16 conversion')
   delta=(value.double()-original.double()).abs()
   self.record['cast'][name]=dict(changed=int((delta!=0).sum()),elements=delta.numel(),peak_abs=float(delta.max()))
   converted[name]=value;before[name]=value.clone()
  result=self.delegate.npu_fused_infer_attention_score(**converted)
  for name,value in before.items():
   need(t.equal(converted[name].contiguous().view(t.uint8),value.contiguous().view(t.uint8)),'native AR FIA input unchanged')
  need(isinstance(result,(tuple,list))and len(result)==2 and result[0].shape==(1,6,1,256)and
   result[0].dtype==t.float16 and bool(t.isfinite(result[0]).all()),'actual finite FP16 native AR FIA output')
  output=result[0].to(t.bfloat16);need(bool(t.isfinite(output).all()),'finite AR output BF16 boundary')
  self.record['completed']=True
  return output,result[1]
