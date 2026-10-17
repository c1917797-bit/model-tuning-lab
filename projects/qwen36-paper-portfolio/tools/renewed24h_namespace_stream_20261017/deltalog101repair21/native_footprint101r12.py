"""Native-only post-prepare metadata observation. No decoder or cache core call."""
import contextvars,functools,hashlib,inspect,json,os
from pathlib import Path
ACTIVE=contextvars.ContextVar('native101r12_scheduler',default=None)
RUNNER_SHA='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'
BLOCK_SHA='8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a'
ACL_SHA='4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529'
LIMIT=65536
FORMAT_GETTER=None
class DiagnosticStop(RuntimeError):pass
def need(x,message):
 if not x:raise ValueError(message)
def exact(ref):
 p=Path(ref['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256'],'source exact Ref3');return p,b
def source_file(value,sha):
 p=Path(inspect.getsourcefile(value));b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==sha,'actual installed native source unchanged');return dict(path=str(p),bytes=len(b),sha256=sha)
def geometry(t):
 need(t.is_contiguous()and t.numel()>0,'only actual contiguous nonempty ND cache views')
 shape=list(t.shape);stride=list(t.stride());ptr=t.data_ptr();es=t.element_size();st=t.untyped_storage();base=st.data_ptr();n=st.nbytes()
 need(ptr==base+t.storage_offset()*es and base<=ptr<ptr+t.numel()*es<=base+n,'actual view within own storage')
 fmt=None
 if t.device.type!='cpu':
  need(FORMAT_GETTER is not None,'actual device-format metadata API required');fmt=int(FORMAT_GETTER(t))
 return dict(tensor_id=id(t),device=str(t.device),dtype=str(t.dtype),shape=shape,stride=stride,storage_offset=t.storage_offset(),data_ptr=ptr,element_size=es,numel=t.numel(),storage_ptr=base,storage_nbytes=n,start=ptr,end=ptr+t.numel()*es,npu_format_code=fmt,interval_requires_confirmed_unpacked_ND=True)
def selected(g,index,role,req):
 need(type(index)is int and len(g['shape'])>=2 and 0<=index<g['shape'][0],'actual selected first-axis index bounds')
 size=g['stride'][0]*g['element_size'];need(size>0,'positive contiguous row size')
 return dict(role=role,request_id=req,index=index,device=g['device'],start=g['data_ptr']+index*size,end=g['data_ptr']+(index+1)*size)
def small(t):
 need(str(t.dtype)in('torch.int32','torch.int64','torch.bool')and 0<=t.numel()<=LIMIT,'bounded integer index D2H only')
 return t.detach().cpu().tolist()
def ints(x):
 if x is None:return None
 if type(x)is int:return x
 need(type(x)in(list,tuple),'source-proven CPU integer container');return [ints(y)for y in x]
def overlap(a,b):return a['device']==b['device']and max(a['start'],b['start'])<min(a['end'],b['end'])
def collect(r,scheduler,ctx,out=None):
 ids=list(r.input_batch.req_ids);need(len(ids)==1 and type(ids[0])is str,'registered C1 first real request only')
 rid=ids[0];counts=dict(scheduler.num_scheduled_tokens);need(set(counts)==set(ids)and counts[rid]==2048,'one actual fixed2048 request, no padding inferred as live')
 need(r.pcp_size==1,'PCP1 only');groups=r.kv_cache_config.kv_cache_groups;tables=r.input_batch.block_table.block_tables;need(len(groups)==len(tables),'real group/table join')
 meta=ctx.attn_metadata;need(type(meta)is dict,'actual post-set-context metadata dictionary, not speculative list')
 static=r.compilation_config.static_forward_context
 if out is None:out={}
 out.update(schema='deltalog.native-postprepare-footprint/v101R12',pid=os.getpid(),phase='actual _model_forward entry after native prepare/build_metadata/set_forward_context; BEFORE decoder forward',epoch=1,request_ids=ids,num_scheduled_tokens=counts,total_num_scheduled_tokens=int(scheduler.total_num_scheduled_tokens),groups=[],layers=[],collisions=[],errors=[],native_prepare_unchanged=True,DL_prepare_installed=False,original_registration_guard_unchanged=True,registration_guard_not_invoked=True,decoder_forward_invoked=False,candidate_math_invoked=False,qualified=False)
 need(out['total_num_scheduled_tokens']==2048,'actual scheduler token sum')
 declarations=[]
 for x in r.kv_cache_config.kv_cache_tensors:declarations.append(dict(size=int(x.size),shared_by=list(x.shared_by)))
 out['shared_raw_declarations']=declarations
 out['pool_num_blocks']=int(r.kv_cache_config.num_blocks)
 out['cache_config_observed']={k:dict(present=hasattr(r.cache_config,k),value=getattr(r.cache_config,k,None))for k in('mamba_cache_mode','enable_prefix_caching','num_gpu_blocks_override')}
 footprint=[];seen=set();index_reads=0
 for gid,(group,table)in enumerate(zip(groups,tables)):
  need(table.pcp_world_size==table.dcp_world_size==1,'PCP/DCP1 table semantics')
  n=int(table.num_blocks_per_row[0]);need(0<n<=LIMIT,'nonempty bounded committed row')
  cpu=table.get_numpy_array()[0,:n].tolist();gpu=small(table.get_device_tensor(1)[0,:n]);index_reads+=n
  physical=ints(r.requests[rid].block_ids[gid]);need(physical and all(type(v)is int and v>=0 for v in physical),'real request-owned physical blocks')
  ratio=int(table.blocks_per_phys_block);need(ratio>0 and int(table.physical_block_size)==int(table.logical_block_size)*ratio,'physical/kernel block ratio')
  expanded=[p*ratio+j for p in physical for j in range(ratio)]if table.use_hybrid_blocks else physical
  need(cpu==expanded and gpu==cpu,'actual CPU-to-GPU table commit and logical-to-kernel expansion exact')
  group_value=dict(gid=gid,is_mamba=bool(table.is_mamba_group),layer_names=list(group.layer_names),physical_blocks=physical,CPU_table=cpu,GPU_table=gpu,physical_block_size=int(table.physical_block_size),logical_block_size=int(table.logical_block_size),blocks_per_phys_block=ratio,kernel_sizes=ints(table.kernel_sizes),spec_block_size=int(group.kv_cache_spec.block_size),num_speculative_blocks_observed=getattr(group.kv_cache_spec,'num_speculative_blocks',None),CPU_GPU_table_equal=True)
  out['groups'].append(group_value)
  for prefix in group.layer_names:
   need(prefix not in seen and prefix in static and prefix in meta,'unique all-layer static-context/metadata join');seen.add(prefix);layer=static[prefix];m=meta[prefix]
   value=dict(prefix=prefix,gid=gid,layer_id=id(layer),metadata_id=id(m),class_name=type(layer).__module__+'.'+type(layer).__qualname__,cache_object_id=id(layer.kv_cache),metadata_class=type(m).__module__+'.'+type(m).__qualname__,views=[],selected=[],actual_shared_by=[x for x in declarations if prefix in x['shared_by']])
   cache=layer.kv_cache
   if not table.is_mamba_group:
    if len(cache)==1 and isinstance(cache[0],(tuple,list)):cache=cache[0]
   need(len(cache)==2,'actual exactly conv/SSM or K/V; sparse/quant/unknown packing not covered')
   geoms=[geometry(x)for x in cache];value['views']=geoms
   if table.is_mamba_group:
    slots=small(m.non_spec_state_indices_tensor[:1]);index_reads+=1
    need(slots==physical[:1]and m.num_prefills==1 and m.num_decodes==0,'GDN actual committed selected same-request prefill slot')
    pref=m.non_spec_prefill_metadata;need(pref is not None,'actual native GDN prefill metadata')
    cache_indices=small(pref.causal_conv1d.cache_indices[:1]);q=small(pref.causal_conv1d.query_start_loc)
    value['GDN_indices']=dict(non_spec_state_indices=slots,conv_cache_indices=cache_indices,query_start_loc=q,prefill_state_indices=small(m.prefill_state_indices[:1]))
    index_reads+=len(q)+len(value['GDN_indices']['prefill_state_indices'])+(len(cache_indices[0])if cache_indices and type(cache_indices[0])is list else len(cache_indices))
    need(cache_indices in(slots,[[slots[0]]])and q==[0,2048]and value['GDN_indices']['prefill_state_indices']==slots,'native conv/SSM actual index/query agreement')
    for g,role in zip(geoms,('conv','SSM')):value['selected'].append(selected(g,slots[0],role,rid))
   else:
    mb=small(m.block_tables[:1,:n]);sm=small(m.slot_mapping[:2048]);actualsm=small(table.slot_mapping.gpu[:2048]);index_reads+=n+4096
    need(mb==[gpu]and sm==actualsm and len(sm)==2048,'FA metadata actual GPU table/slot mapping same committed request')
    need(list(m.actual_seq_lengths_q)==[2048],'actual FA query token count')
    bs=int(table.logical_block_size);expected=[gpu[p//bs]*bs+p%bs for p in range(2048)]
    need(sm==expected,'first-prefill token-to-kernel-slot bijection, no guessed physical ID')
    value['FA_indices']=dict(block_tables=mb,slot_mapping=sm,actual_seq_lengths_q=list(m.actual_seq_lengths_q),seq_lens=small(m.seq_lens))
    index_reads+=len(value['FA_indices']['seq_lens'])
    for g,role in zip(geoms,('K','V')):
     need(len(g['shape'])==4 and g['shape'][1]==bs,'actual ND kernel-block/token/head/dim layout')
     for block in gpu:value['selected'].append(selected(g,int(block),role+'-whole-block-conservative-read',rid))
     tokenbytes=g['stride'][1]*g['element_size']
     intervals=[]
     for s in sorted(sm):
      start=g['data_ptr']+s*tokenbytes;end=start+tokenbytes
      if intervals and intervals[-1]['end']==start:intervals[-1]['end']=end
      else:intervals.append(dict(role=role+'-current-write',request_id=rid,start=start,end=end,device=g['device']))
     value.setdefault('current_write_intervals',[]).extend(intervals)
   for x in value['selected']:x.update(prefix=prefix,gid=gid)
   footprint.extend(value['selected']);out['layers'].append(value)
  need(index_reads<=1024**2,'global bounded integer D2H1M entries')
 need(len(seen)==64 and sum(len(x['layer_names'])for x in out['groups']if x['is_mamba'])==48,'all64 including48GDN and16FA actual prefixes')
 # This is an observation, never permission to bypass the old full-arena guard.
 for i,a in enumerate(footprint):
  for b in footprint[:i]:
   if a['prefix']!=b['prefix']and overlap(a,b):out['collisions'].append(dict(left=a,right=b,same_gid=a['gid']==b['gid']))
 out['index_entries_D2H']=index_reads;out['all64_complete']=True;out['physical_layout_valid']=all(g['npu_format_code']==2 for layer in out['layers']for g in layer['views']);out['physical_layout_reason']='actual format code2 matches source-bound actual ACL_FORMAT_ND=2; any other/unknown code retains logical-only evidence';out['footprint_semantics']='only if physical_layout_valid: GDN selected full state; FA referenced kernel-block conservative read intervals; current writes separately exact. No alias admission.'
 return out
def publish(value,source):
 root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT']);need(root.is_absolute()and root.is_dir()and not root.is_symlink(),'existing exact owned audit leaf')
 value.update(source=source,run_id=os.environ['MST_MXR_NATIVE_WORKER_RUN_ID'],qualified=False)
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode('utf8');need(len(data)<=8*1024**2,'bounded observation8MiB per worker')
 path=root/('NATIVE-POSTPREPARE-%d.json'%os.getpid())
 with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 print('DL101R12_NATIVE '+json.dumps(dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())),flush=True)
 return path
def install(cls,get_context,source,get_rank,proof,format_getter):
 global FORMAT_GETTER
 FORMAT_GETTER=format_getter
 need(not getattr(cls,'_native_observation101r12',False),'sole native observer installation')
 native_execute=cls.execute_model;native_forward=cls._model_forward
 @functools.wraps(native_execute)
 def execute(r,scheduler_output,*a,**kw):
  token=ACTIVE.set((r,scheduler_output))
  try:return native_execute(r,scheduler_output,*a,**kw)
  finally:ACTIVE.reset(token)
 @functools.wraps(native_forward)
 def forward(r,*a,**kw):
  active=ACTIVE.get()
  if active is None:
   need(not any(x is not None for x in r.input_batch.req_ids),'unscoped real request cannot reach model')
   return native_forward(r,*a,**kw) # Original native dummy profiling only.
  need(active[0]is r,'same execute/forward runner')
  value=dict(schema='deltalog.native-postprepare-footprint/v101R12',errors=[],all64_complete=False,qualified=False,decoder_forward_invoked=False,candidate_math_invoked=False)
  try:collect(r,active[1],get_context(),value)
  except BaseException as e:value['errors'].append(dict(type=type(e).__name__,error=str(e)))
  value['tp_rank']=int(get_rank());need(value['tp_rank']in range(4),'real TP4 rank');value['native_source_proof']=proof
  publish(value,source)
  raise DiagnosticStop('DL101R12 diagnostic stop BEFORE decoder forward; no correctness/performance qualification')
 cls.execute_model=execute;cls._model_forward=forward;cls._native_observation101r12=True
