"""Actual Ascend metadata-owned KV writes; generic vLLM map is not authority.

Only bounded integer metadata is copied for this untimed diagnostic. It does
not demonstrate any cache contents, mathematical correctness or qualification.
"""
import json,os
from pathlib import Path
from model_entry import need,tensor_id

def mapping(torch,block,meta,context,prefix,generic,physical,allocated,length,request_blocks):
 need(type(context.slot_mapping)is dict and not context.slot_mapping and generic is None,
      'exact actual Ascend context has no generic unified-KV mapping; unknown map refused')
 need(block.pcp_world_size==block.dcp_world_size==1,'actual C1 CP1 untransformed mapping')
 ratio=block.blocks_per_phys_block;kernel=block.logical_block_size;size=block.physical_block_size
 need(type(ratio)is int and ratio>0 and kernel==block.block_size==128 and size==ratio*kernel,
      'actual native physical/kernel page geometry')
 need(type(request_blocks)in(list,tuple)and request_blocks and all(type(x)is int and x>=0 for x in request_blocks),
      'actual strong request physical block allocation')
 expanded=[p*ratio+j for p in request_blocks for j in range(ratio)]if block.use_hybrid_blocks else list(request_blocks)
 need(expanded==list(physical)and len(physical)==allocated,'actual native physical-to-kernel CPU expansion')
 device_table=block.get_device_tensor(1)[0,:allocated]
 need(meta.block_tables.dtype==device_table.dtype==torch.int32 and
      tensor_id(meta.block_tables[0,:allocated])==tensor_id(device_table)and
      device_table.cpu().tolist()==list(physical),'same committed actual GPU/metadata table and full CPU values')
 actual=block.slot_mapping.gpu[:length]
 need(meta.slot_mapping.dtype==actual.dtype==torch.int32 and
      tensor_id(meta.slot_mapping[:length])==tensor_id(actual),'actual Ascend metadata aliases native slot-mapping buffer')
 expected=[physical[p//128]*128+p%128 for p in range(length)]
 need(meta.slot_mapping[:length].cpu().tolist()==actual.cpu().tolist()==expected,
      'every actual native prefill write destination matches independent complete hybrid table')
 return expected

def operand(t,length=None):
 view=t if length is None else t[:length]
 need(view.numel()<=65536 and str(view.dtype)in('torch.int32','torch.int64','torch.bool'),'bounded actual integer metadata evidence')
 return dict(identity=tensor_id(view),shape=list(view.shape),stride=list(view.stride()),dtype=str(view.dtype),device=str(view.device),values=view.cpu().tolist())

def capture(C,sr,worker,inner,*,request_id,request,metadata,context,rank,length,request_epoch=1):
 import g1_contract as G1
 G1.epoch(request_epoch)
 m=C.obj(sr);need(C.ref(__file__)==m['files']['fa_prefill131r10.py'],'actual source-bound FA metadata observer')
 r=worker.model_runner;need(r.requests.get(request_id)is request and r.input_batch.req_id_to_index=={request_id:0},'strong native C1 request and CPU row')
 need(type(length)is int and length==131 and context.attn_metadata is metadata,'same actual first-prefill context')
 rows=[];gdn=[];groups=r.kv_cache_config.kv_cache_groups
 for layer in inner.layers:
  if layer.layer_type=='linear_attention':
   obj=layer.linear_attn;meta=metadata[obj.prefix]
   gdn.append(dict(layer=layer.layer_idx,prefix=obj.prefix,selected=operand(meta.prefill_state_indices),
    conv_identity=tensor_id(obj.kv_cache[0]),state_identity=tensor_id(obj.kv_cache[1])))
   continue
  need(layer.layer_type=='full_attention','known real hybrid layer kind')
  obj=layer.self_attn.attn;prefix=obj.layer_name;gids=[i for i,g in enumerate(groups)if prefix in g.layer_names];need(len(gids)==1,'one actual FA group')
  gid=gids[0];b=r.input_batch.block_table[gid];a=int(b.num_blocks_per_row[0]);need(0<a<=65536,'bounded actual allocated row')
  meta=metadata[prefix];cpu=b.get_cpu_tensor()[0,:a];need(cpu.device.type=='cpu','already-host allocation table')
  generic=context.slot_mapping.get(prefix)if type(context.slot_mapping)is dict else None
  rows.append(dict(layer=layer.layer_idx,prefix=prefix,group=gid,layer_object_id=id(obj),metadata_object_id=id(meta),context_object_id=id(context),
   allocated=a,CPU_table=operand(cpu),GPU_table=operand(b.get_device_tensor(1)[0,:a]),metadata_table=operand(meta.block_tables[0,:a]),
   native_slot_mapping=operand(b.slot_mapping.gpu,length),metadata_slot_mapping=operand(meta.slot_mapping,length),
   generic_slot_mapping=None if generic is None else operand(generic,length),
   physical_block_size=b.physical_block_size,kernel_block_size=b.logical_block_size,blocks_per_phys_block=b.blocks_per_phys_block,use_hybrid_blocks=b.use_hybrid_blocks,
   request_physical_blocks=list(request.block_ids[gid]),num_actual_tokens=meta.num_actual_tokens,seq_lens_list=list(meta.seq_lens_list),actual_seq_lengths_q=list(meta.actual_seq_lengths_q)))
 need(len(rows)==16 and len(gdn)==48,'all16 FA and48 selected GDN operands before registration assertion')
 value=dict(schema='bole.actual-FA-prefill-mapping-operands/v131r10',source=sr,rank=rank,request_epoch=request_epoch,request_id=request_id,request_object_id=id(request),
  generic_context_type=type(context.slot_mapping).__name__,generic_context_keys=sorted(context.slot_mapping)if type(context.slot_mapping)is dict else None,
  phase='native target prefill returned; BEFORE cache registration checks',rows=rows,GDN_selected_operands=gdn,numerical_qualified=False,cache_contents_captured=False,integer_metadata_D2H=True,
  runtime_sources={k:m['runtime_sources'][k]for k in('runner','block_table','attention','ascend_attention','forward_context','ascend_forward_context')})
 root=Path(os.environ['BOLE_MODEL_RAW_ROOT']);need(str(root)==m['model_receipt_root']and root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents)),'exact sole-owned diagnostic receipt root')
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(data)<=2**21,'bounded2MiB per-rank FA integer receipt')
 path=root/('BOLE-FA-PREFILL-MAPPING-REQUEST-%02d-RANK-%d.json'%(request_epoch,rank))
 with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(root,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return C.ref(path)
