"""Register real C1 cache objects inside the original target forward context.

No virtual_engine indexing: this actual660 Attention.get_attention_context
returns attn_layer.kv_cache directly. Physical IDs come from the runner's CPU
block table, and are checked against actual metadata and every prefix slot.
"""
import inspect
from model_entry import need, code_source, tensor_id
import prefill_tail
import fa_prefill131r10
import layer_slots131r10


def register(torch,C,worker,inner,*,request_id,request,metadata,
             forward_context,get_attention_context,refs,length):
 runner=worker.model_runner
 need(C.ref(inspect.getsourcefile(type(runner)))==refs['runner'], 'actual installed runner class')
 code_source(C,get_attention_context,refs['attention'])
 need(type(length)is int and length==131, 'first real model smoke uses exactly131 prefix tokens')
 ids=[r for r in runner.input_batch.req_ids if r is not None]
 need(ids==[request_id] and runner.requests[request_id]is request and
      runner.input_batch.req_id_to_index[request_id]==0,
      'genuine request object and scheduler C1 row')
 need(forward_context.attn_metadata is metadata and type(metadata)is dict,
      'inside original actual native target forward context')
 need(forward_context.dp_metadata is None and forward_context.ubatch_slices is None and
      str(forward_context.cudagraph_runtime_mode).split('.')[-1]=='NONE',
      'single DP, no microbatch/graph context extrapolation')
 static=runner.vllm_config.compilation_config.static_forward_context
 groups=runner.kv_cache_config.kv_cache_groups
 rows=[];slots=set();counts={'gdn':0,'fa':0};intervals=[]
 for i,layer in enumerate(inner.layers):
  need(layer.layer_idx==i, 'actual complete ordered layer objects')
  if layer.layer_type=='linear_attention':
   obj=layer.linear_attn;prefix=obj.prefix;kind='gdn'
  else:
   need(layer.layer_type=='full_attention', 'known actual hybrid layer kind')
   obj=layer.self_attn.attn;prefix=obj.layer_name;kind='fa'
  need(static[prefix]is obj and forward_context.no_compile_layers[prefix]is obj,
       'actual static registry and live native dispatcher own same layer')
  gids=[g for g,group in enumerate(groups)if prefix in group.layer_names]
  need(len(gids)==1,'unique real KV cache group; no inferred group0')
  gid=gids[0];block=runner.input_batch.block_table[gid]
  code_source(C,block.get_cpu_tensor,refs['block_table'])
  table=block.get_cpu_tensor()
  need(table.device.type=='cpu'and table.ndim==2,'actual committed CPU block table')
  allocated=int(block.num_blocks_per_row[0])
  physical=[int(x)for x in table[0,:allocated].tolist()]
  need(allocated>0 and len(set(physical))==allocated and all(x>=0 for x in physical),
       'only allocated unique physical IDs, never padded table zeroes')
  row=dict(index=i,layer=layer,kind=kind,prefix=prefix,group=gid,allocated_table=tuple(physical))
  m=metadata[prefix]
  if kind=='gdn':
   native=inspect.getmodule(obj._forward_core.__func__)
   slotids=m.prefill_state_indices.cpu().tolist();need(len(slotids)==1,'one actual GDN slot')
   slot=slotids[0];need(slot in physical,'actual GDN index belongs to real allocated group row')
   tail=prefill_tail.bind(torch,obj,m,original_gdn_module=native,request=request,
        request_id=request_id,slot=slot,length=length,native_prefill_returned=True)
   frozen=layer_slots131r10.Binding(prefix,gid,slot,runner,request_id,request,groups[gid],block,tuple(physical),m,obj,tensor_id(obj.kv_cache[0]),tensor_id(obj.kv_cache[1]),length)
   row.update(conv=tail.view,conv_arena=tail.arena,tail=tail,state=obj.kv_cache[1],physical_slot=slot,slot_binding=frozen)
   for name,tensor in(('conv',tail.arena),('state',obj.kv_cache[1])):
    selected=tensor[slot]
    need(selected.is_contiguous(),'selected native cache inner dimensions contiguous')
    intervals.append((selected.data_ptr(),selected.data_ptr()+selected.numel()*selected.element_size(),i,name))
   slots.add(slot)
  else:
   code_source(C,type(obj).forward,refs['attention'])
   meta,actual,kv,slot_mapping=get_attention_context(prefix)
   need(actual is obj and meta is m and kv is obj.kv_cache,
        'exact actual Attention context cache, no virtual-engine assumption')
   code_source(C,obj.impl.forward,refs['ascend_attention'])
   need(obj.kv_sharing_target_layer_name is None and obj.query_quant is None and
        obj.calculate_kv_scales is False, 'unquantized nonsharing native FA cache')
   need(len(kv)==2,'actual separate K/V pages')
   key,value=kv[0],kv[1]
   need(tensor_id(key)==tensor_id(obj.impl.key_cache)and
        tensor_id(value)==tensor_id(obj.impl.value_cache), 'actual backend cache alias matches live layer cache')
   need(key.shape==value.shape and key.ndim==4 and tuple(key.shape[1:])==(128,1,256)and
        key.dtype==value.dtype==torch.bfloat16, 'real ND page128, TP4 KV1/D256 BF16')
   pages=(length+2+127)//128
   need(allocated>=pages and all(x<key.shape[0]for x in physical), 'already allocated accepted-path physical pages')
   need(m.num_prefills==1 and m.num_decodes==0 and m.num_actual_tokens==length and
        m.seq_lens_list==[length] and m.actual_seq_lengths_q==[length], 'actual pure-prefill attention chronology')
   need(m.block_tables[0,:allocated].cpu().tolist()==physical, 'CPU allocation agrees with actual native table')
   code_source(C,obj.impl.reshape_and_cache,refs['ascend_attention'])
   code_source(C,block.get_device_tensor,refs['block_table'])
   fa_prefill131r10.mapping(torch,block,m,forward_context,prefix,slot_mapping,physical,allocated,length,request.block_ids[gid])
   row.update(key=key,value=value,table=tuple(physical))
   for name,tensor in(('key',key),('value',value)):
    for page in physical[:pages]:
     selected=tensor[page];need(selected.is_contiguous(),'selected native ND page contiguous')
     intervals.append((selected.data_ptr(),selected.data_ptr()+selected.numel()*selected.element_size(),i,name))
  rows.append(row);counts[kind]+=1
 need(len(rows)==64 and counts==dict(gdn=48,fa=16)and len(slots)>=1,
      'all64 real objects and exact per-layer GDN group/physical-slot bindings')
 ordered=sorted(intervals)
 need(all(a[1]<=b[0]for a,b in zip(ordered,ordered[1:])),
      'selected physical cache regions disjoint across64 layers and K/V/state types')
 return rows,dict(request=request,request_id=request_id,metadata=metadata,
                  slot=runner.input_batch.req_id_to_index[request_id],length=length)
