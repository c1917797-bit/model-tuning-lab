"""Bounded service-prefix FIA experiment; each new prefix needs independent consumption."""
from sourceio import need,ref
class ServiceFiaBoundary:
 def __init__(self,t,delegate,trial,source):
  need(ref(__file__)==source,'exact service FIA experiment source')
  length=trial['owner'].length
  need(type(length)is int and 131<=length<=135,'only first3 service steps from131 prefix')
  need('fp16_boundary'not in trial,'one boundary receipt per service frame')
  self.t=t;self.delegate=delegate;self.length=length
  self.record=dict(source=source,completed=False,prefix_length=length,
   input_dtype='torch.float16',output_dtype='torch.bfloat16',cast={},
   scope='experimental C1/131..135; no qualification inferred for a new prefix')
  trial['fp16_boundary']=self.record
 def npu_fused_infer_attention_score(self,**kwargs):
  t=self.t;need(not self.record['completed'],'one service FIA call')
  q,k,v=(kwargs[x]for x in('query','key','value'))
  need(q.shape==(1,6,3,256)and k.shape==v.shape==(2,1,128,256)and
       q.dtype==k.dtype==v.dtype==t.bfloat16,'source-owned service Q6/KV1/page128 BF16')
  need(kwargs['input_layout']=='BNSD'and kwargs['block_size']==128 and
   kwargs['actual_seq_lengths']==[3]and kwargs['actual_seq_lengths_kv']==[self.length+3]and
   kwargs['num_heads']==6 and kwargs['num_key_value_heads']==1 and kwargs['scale']==256**-.5 and
   kwargs['sparse_mode']==1 and kwargs['pre_tokens']==kwargs['next_tokens']==2147483647 and
   kwargs['inner_precise']==2,'unchanged paged tree arguments and declared actual prefix')
  converted=dict(kwargs);before={}
  for name in('query','key','value'):
   original=kwargs[name];need(bool(t.isfinite(original).all()),'finite original service input')
   value=original.to(t.float16);need(bool(t.isfinite(value).all()),'finite service FP16 conversion')
   delta=(value.double()-original.double()).abs()
   self.record['cast'][name]=dict(changed=int((delta!=0).sum()),elements=delta.numel(),peak_abs=float(delta.max()))
   converted[name]=value;before[name]=value.clone()
  result=self.delegate.npu_fused_infer_attention_score(**converted)
  for name,value in before.items():
   need(t.equal(converted[name].contiguous().view(t.uint8),value.contiguous().view(t.uint8)),'service FIA input unchanged')
  need(isinstance(result,(tuple,list))and len(result)==2 and result[0].dtype==t.float16 and
       result[0].shape==(1,6,3,256)and bool(t.isfinite(result[0]).all()),'finite actual service FIA output')
  output=result[0].to(t.bfloat16);need(bool(t.isfinite(output).all()),'finite service BF16 output boundary')
  self.record['completed']=True
  return output,result[1]


