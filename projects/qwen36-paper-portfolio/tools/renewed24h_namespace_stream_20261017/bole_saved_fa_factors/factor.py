"""Four same-input FIA attribution arms; not an algorithm qualification.

The anchor is the ACTUAL saved paged call. Each other arm changes one semantic
factor. No model or native GDN import/initialization is performed here.
"""
import os,time,traceback
ARMS=(('anchor_paged_s1_i2',True,1,2),('inner_only_paged_s1_i0',True,1,0),
      ('sparse_only_paged_s0_i2',True,0,2),('storage_only_contiguous_s1_i2',False,1,2))
def need(v,s):
 if not v:raise ValueError(s)
def bits(t,a,b):return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def inputs(t,saved,paged):
 need(set(saved)=={'query','key','value','atten_mask','block_table'},'complete original actual FIA input set')
 q,k,v,mask,table=(saved[n]for n in('query','key','value','atten_mask','block_table'))
 need(q.shape==(1,6,3,256)and k.shape==v.shape==(2,1,128,256)and
      q.dtype==k.dtype==v.dtype==t.bfloat16 and mask.shape==(1,1,3,256)and mask.dtype==t.bool and
      table.dtype==t.int32 and table.tolist()==[[0,1]],'exact saved R17 PA layout/wholemask/table domain')
 out={n:x.clone()for n,x in saved.items()}
 if not paged:
  # Explicit logical-page gather; never pretend BnNBsD is dense BNSD merely
  # because B=KVhead=1 makes some dimensions coincidentally equal.
  order=table[0].to(t.long)
  out['key']=k.index_select(0,order).permute(1,0,2,3).reshape(1,1,256,256).contiguous()
  out['value']=v.index_select(0,order).permute(1,0,2,3).reshape(1,1,256,256).contiguous()
  del out['block_table']
  need(bits(t,out['key'].reshape(256,256),k.permute(0,2,1,3).reshape(256,256))and
       bits(t,out['value'].reshape(256,256),v.permute(0,2,1,3).reshape(256,256)),
       'dense materialization is elementwise exact original PA logical order')
 return out
def kwargs(paged,sparse,inner):
 need((paged,sparse,inner)in[(a[1],a[2],a[3])for a in ARMS],'only preregistered single-factor arms')
 out=dict(input_layout='BNSD',actual_seq_lengths=[3],actual_seq_lengths_kv=[134],num_key_value_heads=1,
  num_heads=6,scale=256**-.5,sparse_mode=sparse,pre_tokens=2147483647,next_tokens=2147483647,inner_precise=inner)
 if paged:out['block_size']=128
 return out
def validate_abi(t,torch_npu,C,abi):
 need(abi['schema']=='bole.actual-FIA-installed-ABI/v115'and abi['NPU']is False and abi['operator_executed']is False,'actual no-op installed ABI')
 C.checked(abi['header_ref']);C.checked(abi['torch_npu_python_ref'])
 need(C.ref(torch_npu.__file__)==abi['torch_npu_python_ref'],'exact actual torch_npu module identity')
 family={name:str(schema)for name,schema in t.ops.npu.npu_fused_infer_attention_score._schemas.items()}
 need(family==abi['schema_family'],'actual installed dispatcher family exact equality')
 required={'query','key','value','atten_mask','block_table','input_layout','block_size','actual_seq_lengths','actual_seq_lengths_kv','num_key_value_heads','num_heads','scale','sparse_mode','pre_tokens','next_tokens','inner_precise'}
 need(required<=set(abi['argument_names']),'actual ABI contains complete factors and mask fields')
 return family
def call(t,torch_npu,saved,arm,*,before_callback):
 need(os.environ.get('BOLE_SAVED_FA_FACTOR_ENABLE')=='1','new default OFF; existing admitted guest only')
 name,paged,sparse,inner=arm
 live={k:v.to('npu:0')for k,v in inputs(t,saved,paged).items()}
 before={k:v.clone()for k,v in live.items()};result=None;primary=None
 before_callback(dict(arm=name,paged=paged,sparse=sparse,inner=inner,kwargs=kwargs(paged,sparse,inner),
    actual_before={k:v.cpu()for k,v in before.items()},NPU=True,operator_executed=False,qualified=False))
 try:
  output,aux=torch_npu.npu_fused_infer_attention_score(**live,**kwargs(paged,sparse,inner))
  t.npu.synchronize();need(output.shape==(1,6,3,256)and output.dtype==t.bfloat16,'original native output ABI; no output cast')
  result=output.squeeze(0).permute(1,0,2).contiguous().cpu()
 except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
 capture_primary=None
 try:after={k:v.cpu()for k,v in live.items()}
 except BaseException as e:
  after={};capture_primary=dict(error=repr(e),traceback=traceback.format_exc())
  if primary is None:primary=capture_primary
 before={k:v.cpu()for k,v in before.items()}
 return dict(arm=name,paged=paged,sparse=sparse,inner=inner,kwargs=kwargs(paged,sparse,inner),
  before=before,after=after,output=result,primary=primary,capture_primary=capture_primary,
  actual_layout={k:dict(shape=list(v.shape),stride=list(v.stride()),dtype=str(v.dtype))for k,v in live.items()},qualified=False)
