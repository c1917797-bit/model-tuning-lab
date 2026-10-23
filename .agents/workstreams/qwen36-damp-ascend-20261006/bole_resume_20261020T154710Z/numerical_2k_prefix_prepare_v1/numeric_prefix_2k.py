"""Independent 2048/1024 reference domain. No candidate imports or runtime admission."""
import hashlib,json,math
INPUT=2048
OUTPUT=1024
KERNEL=128
FRAME_CAP=384*2**20
RETAINED_CAP=2**30
def need(v,s):
 if not v:raise ValueError(s)
def shape(length):
 need(type(length)is int and INPUT<=length<=INPUT+OUTPUT-2,'actual 2k/output1024 owner prefix, not131 or labels')
 native=(length+2+127)//128;scratch=(length+3+127)//128
 return dict(length=length,publication_kernel_pages=native,scratch_kernel_pages=scratch,
  query_shape=(1,6,3,256),KV_shape=(scratch,1,128,256),mask_shape=(1,1,3,scratch*128),table_shape=(1,scratch))
def publication_indices(length,table,path):
 shape(length);need(path in([0],[0,1],[0,2]),'inclusive root plus at most one accepted sibling')
 need(type(table)in(list,tuple)and len(table)>=(length+2+127)//128 and
  all(type(x)is int and x>=0 for x in table)and len(set(table))==len(table),'actual complete native pages, no invented scratch page')
 # Child2 is private scratch index L+2, but its ACCEPTED permanent destination is L+1.
 return [table[(length+j)//128]*128+(length+j)%128 for j in range(len(path))]
def frame_domain(frame):
 o=frame['owner'];g=shape(o['length'])
 need(type(o['version'])is int and 0<=o['version']<=1022 and o['version']==frame['ordinal']and
  frame['generation']==o['generation']in(1,2),'actual frame/version/generation')
 if o['version']==0:need(o['length']==2048,'first actual owner follows full2048 native prefill')
 p=frame['publication'];path=frame['staged']['processed_nodes']
 need(path in([0],[0,1],[0,2])and p['processed_nodes']==path and p['next_length']==o['length']+len(path)
  and p['next_version']==o['version']+1 and len(path)<=3071-o['length']
  and o['version']<=o['length']-2048<=2*o['version'],'actual root/accepted child/output budget only; never third permanent slot')
 return g
def fixed_pages(previous,current):
 need(previous['owner']['request']==current['owner']['request']and
  previous['owner']['generation']==current['owner']['generation']and
  previous['publication']['next_length']==current['owner']['length']and
  previous['publication']['next_version']==current['owner']['version'],'actual dynamic-prefix continuity')
 a={r['layer']:r for r in previous['after_FA']};b={r['layer']:r for r in current['before_FA']}
 need(set(a)==set(b)==set(range(3,64,4)),'all16 FA layer page witnesses')
 for i,r in b.items():
  need(r['physical_pages']==a[i]['physical_pages']and r['ownership']==a[i]['ownership'],
   'same captured native allocation; growth/migration/reuse not qualified by private scratch')
def bits(t,a,b,why):
 need(a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)),why)
def prefill(t,observed,ids,expected_sources):
 need(ids.dtype==t.int32 and ids.shape==(2048,)and observed['sources']==expected_sources,
  'actual source-pinned int32 native2048 prefill')
 bits(t,observed['actual_token_ids'],ids,'actual native tensor equals retained prefill IDs')
 need(ids.tolist()==observed['actual_CPU_token_ids']==observed['request_prompt_token_ids']and
  observed['no_mm_features']is True and observed['no_soft_prompt']is True,'all three actual prefix ID witnesses, no truncation')
 mode=observed['actual_input_mode'];need(mode in('native-token-ids','native-text-embeddings'),'actual native text route')
 if mode=='native-text-embeddings':
  a=observed['actual_native_embeddings'];b=observed['independent_token_embeddings']
  need(a.shape==b.shape==(2048,5120)and a.dtype==b.dtype==t.bfloat16,'actual2048 native embedding ABI')
  bits(t,a,b,'native BEFORE-forward embeds equal independent source-pinned lookup')
 return dict(input_tokens=2048,actual_input_mode=mode,numerical_qualified=False)
def added_capture_budget(length,*,base_logical_bytes=None,actual_wire_bytes=None,retained_first_bytes=None,
                         checkpoint_bytes=None,combined_metadata_bytes=None,failed_frame_bytes=None):
 g=shape(length);s=g['scratch_kernel_pages']
 # Full observed BF16 K/V, actual bool mask, actual int32 table for EACH16FA.
 per_layer=2*s*128*256*2+3*s*128+s*4
 added=16*per_layer
 operands=dict(base_logical_bytes=base_logical_bytes,actual_wire_bytes=actual_wire_bytes,
  retained_first_bytes=retained_first_bytes,checkpoint_bytes=checkpoint_bytes,
  combined_metadata_bytes=combined_metadata_bytes,failed_frame_bytes=failed_frame_bytes)
 missing=[k for k,v in operands.items()if v is None]
 for k,v in operands.items():
  if v is not None:need(type(v)is int and v>=0,'actual nonnegative byte count '+k)
 logical=None if base_logical_bytes is None else base_logical_bytes+added
 peak=None if missing else actual_wire_bytes+retained_first_bytes+checkpoint_bytes+combined_metadata_bytes+failed_frame_bytes
 if logical is not None:need(logical<=FRAME_CAP,'original384MiB frame cap, never expanded')
 if peak is not None:need(peak<=RETAINED_CAP,'one joint actual retained/current/checkpoint/metadata/failed-frame1GiB cap')
 return dict(extra_logical_bytes=added,extra_per_FA_layer_bytes=per_layer,
  converted_full_tensor_copies_persisted=0,
  max_single_CPU_digest_payload_bytes=s*128*256*2,
  minimum_CPU_digest_tensor_plus_bytes_copy_bytes=2*s*128*256*2,
  CPU_digest_peak_RSS_measurement_pending=True,
  logical_frame_bytes=logical,joint_retained_current_checkpoint_metadata_bytes=peak,
  missing_actual_byte_measurements=missing,fit_proven=False,actual_NPU_geometry_pending=True,
  actual_wire_serializer_measurement_pending=True,runtime_admitted=False)
def require_runtime_admission(C,m,frame):
 # Deliberately NOT a caller-PASS or fabricated receipt schema. A future source
 # revision must bind actual geometry and the measured joint raw-budget consumer.
 raise ValueError('2k numeric source-only: actual live NPU geometry + native prefill + joint raw/wire budget admission remain unbound')
def delegate_digests(proof,expected):
 names={'query','key','value','atten_mask','block_table'}
 need(set(expected)==set(proof['converted_before'])==set(proof['converted_after'])==names,
  'all five actual delegate input full digests, no omitted mask/table')
 for n in names:
  need(proof['converted_before'][n]==proof['converted_after'][n]==expected[n],
   'actual delegate full operand independently reconstructed and unchanged '+n)
def scratch(t,C,m,row,anchor,owner,digest):
 g=shape(owner['length']);proof=row['actual_2k_FIA_operands']
 need(proof['schema']=='bole.actual-2k-FIA-operands/v1'and proof['owner']==owner and
  proof['layer']==anchor['layer']and proof['source']==m['files']['service_fia.py']and
  proof['stage']=='returned'and proof['boundary_completed']is True,
  'actual same-frame boundary/trial/owner/layer and completed operator, not generated scratch')
 native=proof['native_before']
 for n,sh in(('key',g['KV_shape']),('value',g['KV_shape']),('atten_mask',g['mask_shape']),('block_table',g['table_shape'])):
  need(native[n].shape==sh,'actual independent scratch domain '+n)
 need(native['key'].dtype==native['value'].dtype==t.bfloat16 and
  native['atten_mask'].dtype==t.bool and native['block_table'].dtype==t.int32,'actual scratch operand dtypes')
 query=row['query'].reshape(3,6,256).permute(1,0,2).unsqueeze(0).contiguous()
 need(digest(t,query)==proof['query_BF16_digest'],'same full actual query at BEFORE-call and frame capture')
 for n in('key','value'):
  expected=t.zeros(g['KV_shape'],dtype=t.bfloat16)
  flat=expected.permute(0,2,1,3).reshape(-1,1,256)
  flat[:owner['length']].copy_(anchor[n].reshape(-1,1,256)[:owner['length']])
  flat[owner['length']:owner['length']+3].copy_(row[n].reshape(3,1,256))
  bits(t,native[n],expected,'whole actual private scratch prefix/all3 nodes/zero padding '+n)
 mask=t.ones(g['mask_shape'],dtype=t.bool);L=owner['length']
 mask[0,0,:,:L+1]=False;mask[0,0,1,L+1]=False;mask[0,0,2,L+2]=False
 bits(t,native['atten_mask'],mask,'actual sibling isolation, third private branch and all padding')
 table=t.arange(g['scratch_kernel_pages'],dtype=t.int32).reshape(1,-1)
 bits(t,native['block_table'],table,'actual contiguous PRIVATE table; not native physical mapping')
 expected={n:digest(t,value.to(t.float16))for n,value in
  (('query',query),('key',native['key']),('value',native['value']))}
 # Mask/table are passed unchanged, not FP16-cast. Match the same retained
 # BEFORE values as well as the actual delegate's full BEFORE/AFTER bytes.
 expected.update({n:digest(t,native[n])for n in('atten_mask','block_table')})
 delegate_digests(proof,expected)
 return dict(scratch_pages=g['scratch_kernel_pages'],publication_pages=g['publication_kernel_pages'],
  original_pointwise_bounds_unchanged=True,new_native_page_claimed=False,numerical_qualified=False)
def scalar_branch_reference(prefix_keys,prefix_values,node_keys,node_values,queries):
 """Small independent software discriminator; not a replacement for FP64/32 tensor oracle."""
 need(len(prefix_keys)==len(prefix_values)and len(node_keys)==len(node_values)==len(queries)==3,'scalar oracle geometry')
 result=[]
 for node,path in enumerate(((0,),(0,1),(0,2))):
  keys=list(prefix_keys)+[node_keys[j]for j in path];vals=list(prefix_values)+[node_values[j]for j in path]
  logits=[k*queries[node]for k in keys];peak=max(logits);weights=[math.exp(x-peak)for x in logits]
  result.append(sum(w*v for w,v in zip(weights,vals))/sum(weights))
 return result
