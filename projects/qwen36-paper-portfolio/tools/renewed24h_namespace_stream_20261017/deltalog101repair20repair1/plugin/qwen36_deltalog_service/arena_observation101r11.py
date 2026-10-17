"""Read metadata before the UNCHANGED registration guard; no D2H/admission."""
import hashlib,json,os
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def integers(value):
 if value is None:return None
 if type(value)is int:return value
 need(type(value)in(list,tuple),'already-CPU list/tuple integers only')
 return [integers(v)for v in value]
def geometry(t):
 storage=t.untyped_storage();start=t.data_ptr();size=t.numel()*t.element_size()
 return dict(base_id=id(t),device=str(t.device),dtype=str(t.dtype),shape=list(t.shape),stride=list(t.stride()),storage_offset=t.storage_offset(),data_ptr=start,storage_ptr=storage.data_ptr(),storage_nbytes=storage.nbytes(),numel=t.numel(),element_size=t.element_size(),contiguous=t.is_contiguous(),start=start,end=start+size)
def collect(r,rows,scheduler):
 need(len(rows)==48,'bounded actual48 registration observation')
 ctx=r.compilation_config.static_forward_context;groups=r.kv_cache_config.kv_cache_groups;tables=r.input_batch.block_table.block_tables
 result=[]
 for layer,gid in rows:
  g=geometry(layer.kv_cache[1]);g.update(prefix=layer.prefix,layer_idx=layer.layer_idx,gid=gid,layer_id=id(layer),kv_cache_id=id(layer.kv_cache),static_context_same=ctx.get(layer.prefix)is layer,class_name=type(layer).__module__+'.'+type(layer).__qualname__);result.append(g)
 collisions=[]
 for i,a in enumerate(result):
  for b in result[:i]:
   if a['device']==b['device']and not(a['end']<=b['start']or a['start']>=b['end']):collisions.append(dict(left=b['prefix'],right=a['prefix'],same_gid=a['gid']==b['gid'],left_gid=b['gid'],right_gid=a['gid']))
 cfg=[]
 for k,t in enumerate(r.kv_cache_config.kv_cache_tensors):
  need(k<1024 and len(t.shared_by)<=256,'bounded cache declaration metadata');cfg.append(dict(index=k,size=int(t.size),shared_by=list(t.shared_by)))
 req_ids=list(r.input_batch.req_ids);need(len(req_ids)<=16 and all(type(x)is str for x in req_ids),'bounded current request identities')
 requests=[dict(req_id=rid,object_id=id(r.requests[rid]),block_ids=integers(r.requests[rid].block_ids))for rid in req_ids]
 table_rows=[];specs=[]
 for gid,table in enumerate(tables):
  group=groups[gid];spec=group.kv_cache_spec
  specs.append(dict(gid=gid,layer_names=list(group.layer_names),is_mamba_group=bool(table.is_mamba_group),spec_type=type(spec).__module__+'.'+type(spec).__qualname__,shapes=integers(getattr(spec,'shapes',None)),dtypes=None if getattr(spec,'dtypes',None)is None else[str(x)for x in spec.dtypes],page_size_bytes=getattr(spec,'page_size_bytes',None)))
  array=table.get_numpy_array();entries=[]
  for i,rid in enumerate(req_ids):
   n=int(table.num_blocks_per_row[i]);need(0<=n<=array.shape[1]and n<=65536,'bounded CPU block row');entries.append(dict(req_id=rid,num_blocks=n,values=array[i,:n].tolist()))
  table_rows.append(dict(gid=gid,rows=entries,phase='pre-original-prepare; commit NOT observed'))
 scheduled=None
 if scheduler is not None:
  cached=scheduler.scheduled_cached_reqs
  scheduled=dict(num_scheduled_tokens=dict(scheduler.num_scheduled_tokens),total_num_scheduled_tokens=int(scheduler.total_num_scheduled_tokens),new_requests=[dict(req_id=x.req_id,block_ids=integers(x.block_ids))for x in scheduler.scheduled_new_reqs],cached_requests=dict(req_ids=list(cached.req_ids),new_block_ids=[integers(x)for x in cached.new_block_ids],resumed_req_ids=sorted(cached.resumed_req_ids)))
 return dict(schema='deltalog.pre-registration-arena-observation/v101R11',pid=os.getpid(),phase='before original _prepare_inputs and commit_block_table',actual_committed_slot_proof=False,all48=result,collisions=collisions,cache_tensor_declarations=cfg,groups=specs,current_requests=requests,CPU_tables=table_rows,scheduler=scheduled,guard_unchanged=True,guard_bypassed=False,numerical_qualified=False)
def checked(r):
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'exact source observation Ref');return p,b
def capture(r,rows,scheduler):
 sr=json.loads(os.environ['QWEN36_DELTALOG_SERVICE023_SOURCE_REF']);_,b=checked(sr);source=json.loads(b);key='qwen36_deltalog_service/arena_observation101r11.py';p,raw=checked(source['files'][key]);need(p.resolve()==Path(__file__).resolve(),'actual source-owned observation helper')
 value=collect(r,rows,scheduler);value.update(runtime_source=sr,observer_ref=source['files'][key],model_source=json.loads(os.environ['QWEN36_DELTALOG_TRACE025_SOURCE_REF']))
 root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT']);need(root.is_dir(),'existing actual owned audit leaf');out=root/('ARENA-REGISTRATION-%d.json'%os.getpid());data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(data)<=2*1024**2,'bounded metadata observation2MiB')
 with out.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 print('DL101R11_ARENA '+json.dumps(dict(path=str(out),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())),flush=True)
