"""Bounded service-prefix FIA experiment; each new prefix needs independent consumption."""
from sourceio import need,ref
import g3_fia_contract as DOMAIN
class ServiceFiaBoundary:
 def __init__(self,t,delegate,trial,source):
  need(ref(__file__)==source,'exact service FIA experiment source')
  length=trial['owner'].length
  geometry=DOMAIN.shape(length)
  need('fp16_boundary'not in trial,'one boundary receipt per service frame')
  self.t=t;self.delegate=delegate;self.length=length;self.geometry=geometry
  self.record=dict(source=source,completed=False,prefix_length=length,
   input_dtype='torch.float16',output_dtype='torch.bfloat16',cast={},
   scope='explicit fixed1024 C1/131..1153/one physical1536 allocation; every frame independently consumed',
   scratch_kernel_pages=geometry['scratch_kernel_pages'],publication_kernel_pages=geometry['publication_kernel_pages'],
   physical_allocation_growth_proven=False)
  trial['fp16_boundary']=self.record
 def npu_fused_infer_attention_score(self,**kwargs):
  t=self.t;need(not self.record['completed'],'one service FIA call')
  q,k,v=(kwargs[x]for x in('query','key','value'))
  need(q.shape==self.geometry['query_shape']and k.shape==v.shape==self.geometry['KV_shape']and
       q.dtype==k.dtype==v.dtype==t.bfloat16,'source-owned service Q6/KV1/page128 BF16')
  need(kwargs['input_layout']=='BNSD'and kwargs['block_size']==128 and
   kwargs['actual_seq_lengths']==[3]and kwargs['actual_seq_lengths_kv']==[self.length+3]and
   kwargs['num_heads']==6 and kwargs['num_key_value_heads']==1 and kwargs['scale']==256**-.5 and
   kwargs['sparse_mode']==1 and kwargs['pre_tokens']==kwargs['next_tokens']==2147483647 and
   kwargs['inner_precise']==2,'unchanged paged tree arguments and declared actual prefix')
  need(kwargs['atten_mask'].shape==self.geometry['mask_shape']and kwargs['atten_mask'].dtype==t.bool and
   kwargs['block_table'].shape==self.geometry['table_shape']and kwargs['block_table'].dtype==t.int32,
   'actual native scratch mask/table covers declared long prefix plus all3 private rows')
  expected=t.arange(self.geometry['scratch_kernel_pages'],dtype=t.int32,device=q.device).reshape(1,-1)
  need(t.equal(kwargs['block_table'],expected),'original adapter-owned contiguous private scratch page table')
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


