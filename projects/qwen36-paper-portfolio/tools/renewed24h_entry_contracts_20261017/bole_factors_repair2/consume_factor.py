"""Independent same-input path oracle; no candidate layout function imported."""
import gc
import diagnose as D,decision_gate as G
ARMS=('anchor_paged_s1_i2','inner_only_paged_s1_i0','sparse_only_paged_s0_i2','storage_only_contiguous_s1_i2')

def anchor_comparison(t,capture,output):
 # R17 model_entry._fa saved adapter.native's BF16 inverse-layout output.clone().
 # Neither this comparison nor that inverse layout casts the native output.
 original=capture['output']
 if original.dtype!=t.bfloat16 or tuple(original.shape)!=(3,6,256):
  raise ValueError('exact original saved R17 BF16 FA output [3,6,256]')
 if output.dtype!=original.dtype or tuple(output.shape)!=tuple(original.shape):
  raise ValueError('actual anchor output retains original native BF16 ABI')
 return dict(original_field='tree_context.captures[layer].output',original_dtype=str(original.dtype),
    output_dtype=str(output.dtype),comparison_cast=False,bitwise_reproduced=D.bits(t,output,original),
    metrics=D.metric(t,output,original))
def consume(t,C,m,sr,stage_ref):
 stage=C.obj(stage_ref);C.need(stage['schema']=='bole.saved-FA-single-factor-stage/v1'and stage['source']==sr and stage['NPU']is True and stage['qualified']is False,'actual same-source native stage')
 proof=G.consume(C,m['actual_diagnostic_source'],m['actual_diagnostic_owner'])
 expected=[(r,l,a)for r in range(4)for l in range(3,64,4)for a in ARMS]
 C.need([(r['rank'],r['layer'],r['arm'])for r in stage['rows']]==expected,'complete ordered256 no cherry-picking')
 rows=[]
 for pair in proof['ranks']:
  blob=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False);raw=blob['payload']
  for layer in range(3,64,4):
   capture=raw['tree_context']['captures'][layer]
   saved=capture['trial']['native_before'];anchor=None
   for arm in ARMS:
    index=expected.index((pair['rank'],layer,arm));record=stage['rows'][index]
    actual=t.load(C.checked(record['raw']),map_location='cpu',weights_only=False);before=t.load(C.checked(record['before']),map_location='cpu',weights_only=False)
    C.need(actual['source']==before['source']==sr and actual['rank']==pair['rank']and actual['layer']==layer and actual['original_raw']==pair['raw'],'actual immutable call provenance')
    call=actual['call'];b=call['before'];a=call['after'];pre=before['call']
    C.need(call['arm']==arm and pre['operator_executed']is False and pre['NPU']is True and call['primary']==record['primary'],'same attempted arm and preserved native exception')
    expected_kwargs=dict(input_layout='BNSD',actual_seq_lengths=[3],actual_seq_lengths_kv=[134],
      num_key_value_heads=1,num_heads=6,scale=.0625,sparse_mode=0 if arm.startswith('sparse_')else 1,
      pre_tokens=2147483647,next_tokens=2147483647,inner_precise=0 if arm.startswith('inner_')else 2)
    if not arm.startswith('storage_'):expected_kwargs['block_size']=128
    C.need(call['kwargs']==pre['kwargs']==expected_kwargs,'independent preregistered exact kwargs for each one-factor arm')
    wanted=dict(saved)
    if arm.startswith('storage_'):
     # Independent explicit page/block/key-head walk, NOT factor.inputs.
     keys=[];values=[]
     for page in saved['block_table'][0].tolist():
      for offset in range(128):keys.append(saved['key'][page,0,offset]);values.append(saved['value'][page,0,offset])
     wanted={'query':saved['query'],'key':t.stack(keys).reshape(1,1,256,256),
             'value':t.stack(values).reshape(1,1,256,256),'atten_mask':saved['atten_mask']}
    input_bits=set(b)==set(a)==set(wanted)==set(pre['actual_before'])and all(D.bits(t,b[k],a[k])and D.bits(t,b[k],wanted[k])and D.bits(t,b[k],pre['actual_before'][k])for k in wanted)
    C.need(input_bits,'every actual input bit and semantic layout transform unchanged')
    q=saved['query'].squeeze(0).permute(1,0,2);keys=saved['key'].permute(0,2,1,3).reshape(-1,256);vals=saved['value'].permute(0,2,1,3).reshape(-1,256)
    metrics={}
    if call['primary']is None:
     for name,dtype in(('double',t.float64),('float',t.float32)):
      truth=D.matrix(t,q,keys,vals,saved['atten_mask'][0,0],dtype)
      metrics[name]=dict(whole=D.metric(t,call['output'],truth),nodes=[D.metric(t,call['output'][n],truth[n])for n in range(3)])
     if arm==ARMS[0]:anchor=anchor_comparison(t,capture,call['output'])
    rows.append(dict(rank=pair['rank'],layer=layer,arm=arm,raw=record['raw'],before=record['before'],
       native_exception=call['primary'],input_bits_preserved=True,metrics=metrics,qualified=False,
       original_saved_output_anchor=anchor,
       attribution_scope='reproduced-original-call-only'if anchor and anchor['bitwise_reproduced']else 'standalone-only-original-output-not-reproduced'))
  del raw,blob;gc.collect()
 return dict(schema='bole.saved-FA-single-factor-independent/v1',source=sr,actual_capture=stage_ref,rows=rows,
    diagnostic_complete=True,qualified=False,original_numeric_failures_unchanged=True,
    model_ready=False,performance_ready=False,numeric_pass_not_implied=True)
