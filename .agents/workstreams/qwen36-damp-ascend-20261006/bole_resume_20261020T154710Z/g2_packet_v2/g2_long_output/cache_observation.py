"""Post-native-prefill metadata only; never copies device tensor contents."""
import json,os,time
from pathlib import Path
from model_entry import need

def integers(v):
 if v is None:return None
 if type(v)is int:return v
 need(type(v)in(list,tuple),'already-host integer metadata only')
 return [integers(x)for x in v]

def geometry(t):
 s=t.untyped_storage()
 return dict(object_id=id(t),device=str(t.device),dtype=str(t.dtype),shape=list(t.shape),stride=list(t.stride()),storage_offset=t.storage_offset(),data_ptr=t.data_ptr(),storage_ptr=s.data_ptr(),storage_nbytes=s.nbytes(),numel=t.numel(),element_size=t.element_size(),contiguous=t.is_contiguous())

def collect(worker,inner,request_id,request,metadata,context,rank):
 r=worker.model_runner;batch=r.input_batch
 need(batch.req_id_to_index[request_id]==0 and r.requests[request_id]is request,'actual strong C1 request row')
 need(context.attn_metadata is metadata,'actual post-native context metadata identity')
 groups=r.kv_cache_config.kv_cache_groups;static=r.vllm_config.compilation_config.static_forward_context
 need(len(groups)<=128,'bounded actual cache groups')
 group_rows=[]
 for gid,g in enumerate(groups):
  b=batch.block_table[gid];table=b.get_cpu_tensor()
  need(table.device.type=='cpu'and table.ndim==2,'actual host CPU block table; no device copy')
  n=int(b.num_blocks_per_row[0]);need(0<=n<=table.shape[1]and n<=65536,'bounded allocated CPU row')
  spec=g.kv_cache_spec
  group_rows.append(dict(gid=gid,layer_names=list(g.layer_names),spec_type=type(spec).__module__+'.'+type(spec).__qualname__,shapes=integers(getattr(spec,'shapes',None)),dtypes=None if getattr(spec,'dtypes',None)is None else[str(x)for x in spec.dtypes],page_size_bytes=getattr(spec,'page_size_bytes',None),allocated=n,CPU_row=table[0,:n].tolist(),table_object_id=id(b)))
 declarations=[]
 for k,v in enumerate(r.kv_cache_config.kv_cache_tensors):
  need(k<1024 and len(v.shared_by)<=256,'bounded pooled declarations')
  declarations.append(dict(index=k,size=int(v.size),shared_by=list(v.shared_by)))
 rows=[]
 for i,layer in enumerate(inner.layers):
  if layer.layer_type!='linear_attention':continue
  obj=layer.linear_attn;prefix=obj.prefix;need(len(rows)<48,'bounded actual48 GDN')
  gids=[g for g,v in enumerate(groups)if prefix in v.layer_names]
  kv=obj.kv_cache;need(len(kv)==2,'actual conv/state pair')
  m=metadata[prefix]
  rows.append(dict(index=i,prefix=prefix,layer_id=id(layer),object_id=id(obj),cache_object_id=id(kv),class_name=type(obj).__module__+'.'+type(obj).__qualname__,groups=gids,static_same=static.get(prefix)is obj,dispatcher_same=context.no_compile_layers.get(prefix)is obj,conv=geometry(kv[0]),state=geometry(kv[1]),prefill_state_indices=geometry(m.prefill_state_indices),num_prefills=getattr(m,'num_prefills',None),num_decodes=getattr(m,'num_decodes',None)))
 need(len(rows)==48,'all48 actual GDN metadata before unchanged registration')
 return dict(schema='bole.post-native-prefill-cache-observation/v131r4',rank=rank,pid=os.getpid(),observed_time_ns=time.time_ns(),phase='native target prefill returned; BEFORE original cache_registry.register',context_object_id=id(context),metadata_object_id=id(metadata),native_prefill_returned=True,epoch_proof='source-bound callback ordinal1 only; no scheduler epoch inferred',observation_ordinal=1,request=dict(request_id=request_id,object_id=id(request),CPU_row=0,block_ids=integers(request.block_ids)),all48=rows,groups=group_rows,cache_tensor_declarations=declarations,actual_slot_ids_not_copied=True,guard_bypassed=False,numerical_qualified=False)

def capture(C,sr,worker,inner,*,request_id,request,metadata,context,rank,request_epoch=1):
 import g1_contract as G1
 G1.epoch(request_epoch)
 m=C.obj(sr);need(C.ref(__file__)==m['files']['cache_observation.py'],'exact observation source')
 value=collect(worker,inner,request_id,request,metadata,context,rank)
 value.update(request_epoch=request_epoch,observation_ordinal=request_epoch,epoch_proof='source-bound process registration ordinal; native request object independently retained',source=sr,observer=m['files']['cache_observation.py'],runtime_sources={k:m['runtime_sources'][k]for k in('runner','base_runner','gdn','block_table')})
 root=Path(os.environ['BOLE_MODEL_RAW_ROOT'])
 need(str(root)==m['model_receipt_root']and root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents)),'actual sole-owned receipt root')
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(data)<=2**21,'metadata bounded2MiB per worker')
 path=root/('BOLE-PREFILL-CACHE-REQUEST-%02d-RANK-%d.json'%(request_epoch,rank))
 with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(str(root),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return C.ref(path)
