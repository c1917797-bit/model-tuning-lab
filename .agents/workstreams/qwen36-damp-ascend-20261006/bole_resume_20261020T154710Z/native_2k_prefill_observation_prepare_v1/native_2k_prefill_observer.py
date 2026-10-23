"""Native-only after-return metadata observation, not BOLE/cache qualification."""
import inspect,json,os
from pathlib import Path
STATE={}
FLAG='NATIVE_2K_PREFILL_OBSERVE_ENABLE'
FALSES=dict(numerical_qualified=False,formal_performance=False,task_accuracy=False)
def need(v,s):
 if not v:raise ValueError(s)
def write(C,m,name,value):
 root=Path(os.environ['DENSE_OPPORTUNITY090_RECEIPT_ROOT'])
 need(str(root)==m['model_receipt_root']and root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents)),'sole owned actual native receipt root')
 data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 need(len(data)<=2**21,'bounded2MiB native integer metadata receipt')
 p=root/name
 with p.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(root,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return C.ref(p)
def source(C,sr):
 m=C.source(sr)
 need(m['performance_arm']=='native_ar'and m.get('native_2k_observation')==dict(
  schema='native.2k-prefill-observation/v1',input_tokens=2048,output_tokens=1,request_count=1,
  concurrency=1,synthetic=True,screening_only=True,no_general_gain_claim=True,
  numerical_qualified=False,formal_performance=False,task_accuracy=False),'exact bound native2048/1 metadata-only source')
 need(C.ref(__file__)==m['files']['native_2k_prefill_observer.py'],'source-owned native observer')
 need(not any(k.startswith(('BOLE_','BOLE111_'))for k in os.environ),'no BOLE plugin opt-in in native observer')
 need(os.environ.get('HCCL_DETERMINISTIC')=='true'and os.environ.get('VLLM_PLUGINS')=='ascend,dense_opportunity090','same native common configuration')
 return m
def tensor(t,E):
 return dict(identity=E.tensor_id(t),shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device))
def capture(C,sr,worker,inner,*,request_id,request,input_ids,positions,metadata,forward_context,native_input,**unused):
 m=source(C,sr)
 for name in('model_entry.py','fa_prefill131r10.py'):C.checked(m['files'][name])
 import torch
 import model_entry as E
 import fa_prefill131r10 as F
 from vllm.model_executor.layers.attention.attention import get_attention_context
 refs=m['runtime_sources'];r=worker.model_runner;ctx=forward_context
 need(C.ref(E.__file__)==m['files']['model_entry.py']and C.ref(F.__file__)==m['files']['fa_prefill131r10.py'],'bound original identity/mapping math')
 E.code_source(C,get_attention_context,refs['attention'])
 need(r.requests.get(request_id)is request and r.input_batch.req_id_to_index=={request_id:0},'strong original native request/CPU row')
 need(input_ids.device.type=='npu'and input_ids.dtype==torch.int32 and tuple(input_ids.shape)==(2048,),'actual NPU2048 prefill IDs')
 ids=input_ids.cpu().tolist()
 need(ids==native_input['actual_CPU_token_ids']==native_input['request_prompt_token_ids']==request.prompt_token_ids and native_input['request_id']==request_id,'all2048 real GPU/CPU/request IDs joined')
 need(positions.dtype==torch.int64 and positions.cpu().tolist()==(list(range(2048))if positions.ndim==1 else[list(range(2048))]*3)and positions.ndim in(1,2)and
      (positions.ndim==1 or tuple(positions.shape)==(3,2048)),'actual native2k RoPE positions')
 need(ctx.attn_metadata is metadata and ctx.dp_metadata is None and ctx.ubatch_slices is None and str(ctx.cudagraph_runtime_mode).split('.')[-1]=='NONE','actual eager PP1/DP1 native context')
 groups=r.kv_cache_config.kv_cache_groups;static=r.vllm_config.compilation_config.static_forward_context
 rows=[];gdn=[]
 for index,layer in enumerate(inner.layers):
  need(layer.layer_idx==index,'all actual native layer indices')
  if layer.layer_type=='linear_attention':
   obj=layer.linear_attn;prefix=obj.prefix;meta=metadata[prefix]
   gids=[i for i,g in enumerate(groups)if prefix in g.layer_names];need(len(gids)==1,'unique actual GDN group')
   gid=gids[0];b=r.input_batch.block_table[gid];n=int(b.num_blocks_per_row[0]);cpu=b.get_cpu_tensor()[0,:n]
   need(static[prefix]is obj and ctx.no_compile_layers[prefix]is obj,'same actual GDN static/native dispatcher')
   selected=F.operand(meta.prefill_state_indices);need(len(selected['values'])==1 and selected['values'][0]in cpu.tolist(),'actual GDN selected slot belongs to allocated group')
   gdn.append(dict(layer=index,prefix=prefix,group=gid,layer_object_id=id(obj),metadata_object_id=id(meta),request_object_id=id(request),
    allocated=n,CPU_table=F.operand(cpu),selected=selected,conv=tensor(obj.kv_cache[0],E),state=tensor(obj.kv_cache[1],E)))
   continue
  need(layer.layer_type=='full_attention','actual hybrid layer kind')
  obj=layer.self_attn.attn;prefix=obj.layer_name;gids=[i for i,g in enumerate(groups)if prefix in g.layer_names];need(len(gids)==1,'unique actual FA group')
  gid=gids[0];b=r.input_batch.block_table[gid];n=int(b.num_blocks_per_row[0]);need(0<n<=65536,'bounded real allocated table')
  meta,actual,kv,generic=get_attention_context(prefix)
  need(actual is obj and meta is metadata[prefix]and kv is obj.kv_cache and len(kv)==2,'same actual attention/context K/V objects')
  need(static[prefix]is obj and ctx.no_compile_layers[prefix]is obj,'same actual FA static/native dispatcher')
  for fn,key in ((type(obj).forward,'attention'),(obj.impl.forward,'ascend_attention'),(obj.impl.reshape_and_cache,'ascend_attention'),
                 (b.get_cpu_tensor,'block_table'),(b.get_device_tensor,'block_table')):E.code_source(C,fn,refs[key])
  key,value=kv
  need(obj.kv_sharing_target_layer_name is None and obj.query_quant is None and obj.calculate_kv_scales is False,'unquantized nonsharing native FA')
  need(key.device.type==value.device.type=='npu'and key.shape==value.shape and key.ndim==4 and tuple(key.shape[1:])==(128,1,256)and key.dtype==value.dtype==torch.bfloat16,'actual native ND128 TP4 KV1 D256 BF16')
  need(E.tensor_id(key)==E.tensor_id(obj.impl.key_cache)and E.tensor_id(value)==E.tensor_id(obj.impl.value_cache),'live layer/backend cache aliases')
  cpu=b.get_cpu_tensor()[0,:n];physical=cpu.tolist()
  need(cpu.device.type=='cpu'and len(set(physical))==n and all(type(x)is int and 0<=x<key.shape[0]for x in physical)and n*128>=2048,'actual allocated unique native pages cover prefill')
  F.mapping(torch,b,meta,ctx,prefix,generic,physical,n,2048,request.block_ids[gid])
  need(meta.num_prefills==1 and meta.num_decodes==0 and meta.num_actual_tokens==2048 and list(meta.seq_lens_list)==list(meta.actual_seq_lengths_q)==[2048],'full native2k pure-prefill chronology')
  rows.append(dict(layer=index,prefix=prefix,group=gid,request_object_id=id(request),layer_object_id=id(obj),metadata_object_id=id(meta),context_object_id=id(ctx),
   group_object_id=id(groups[gid]),block_object_id=id(b),allocated=n,request_physical_blocks=list(request.block_ids[gid]),
   physical_block_size=b.physical_block_size,kernel_block_size=b.logical_block_size,blocks_per_phys_block=b.blocks_per_phys_block,
   use_hybrid_blocks=b.use_hybrid_blocks,pcp=b.pcp_world_size,dcp=b.dcp_world_size,
   CPU_table=F.operand(cpu),GPU_table=F.operand(b.get_device_tensor(1)[0,:n]),metadata_table=F.operand(meta.block_tables[0,:n]),
   native_slot_mapping=F.operand(b.slot_mapping.gpu,2048),metadata_slot_mapping=F.operand(meta.slot_mapping,2048),
   generic_slot_mapping=None if generic is None else F.operand(generic,2048),
   key=tensor(key,E),value=tensor(value,E),impl_key=tensor(obj.impl.key_cache,E),impl_value=tensor(obj.impl.value_cache,E),
   num_prefills=meta.num_prefills,num_decodes=meta.num_decodes,num_actual_tokens=meta.num_actual_tokens,
   seq_lens_list=list(meta.seq_lens_list),actual_seq_lengths_q=list(meta.actual_seq_lengths_q)))
 need(len(inner.layers)==64 and len(rows)==16 and len(gdn)==48,'all16 FA/48GDN after real native prefill')
 rank=int(torch.distributed.get_rank());device=int(torch.npu.current_device())
 need(rank==device and rank in range(4),'actual TP4 rank/logical device')
 value=dict(schema='native.actual-2k-prefill-observation/v1',source=sr,rank=rank,npu_logical_device=device,pid=os.getpid(),
  request_epoch=1,request_id=request_id,request_object_id=id(request),worker_object_id=id(worker),runner_object_id=id(r),
  actual_token_ids=ids,input_identity_sources=native_input['sources'],actual_input_mode=native_input['actual_input_mode'],
  no_mm_features=native_input['no_mm_features'],no_soft_prompt=native_input['no_soft_prompt'],
  generic_context_type=type(ctx.slot_mapping).__name__,generic_context_keys=sorted(ctx.slot_mapping)if type(ctx.slot_mapping)is dict else None,
  rows=rows,GDN_selected_operands=gdn,phase='original native target prefill returned; no BOLE/cache registration',
  runtime_sources={k:refs[k]for k in('runner','block_table','attention','ascend_attention','forward_context','ascend_forward_context','qwen35','qwen_next','worker','base_runner')},
  native_output_not_substituted=True,cache_contents_captured=False,integer_metadata_D2H=True,**FALSES)
 receipt=write(C,m,'NATIVE2K-PREFILL-RANK-%d.json'%rank,value)
 STATE.update(worker=worker,source=sr,request_id=request_id,request=request,receipt=receipt,rank=rank,pid=os.getpid())
 return receipt
def status(C,sr):
 if os.environ.get(FLAG)!='1':return None
 need(STATE.get('source')==sr and STATE.get('pid')==os.getpid(),'one actual completed native2k observation in this worker')
 r=STATE['worker'].model_runner;rid=STATE['request_id']
 return dict(source=sr,pid=os.getpid(),rank=STATE['rank'],request_id=rid,receipt=STATE['receipt'],
  request_absent=rid not in r.requests and rid not in r.input_batch.req_id_to_index and rid not in r.input_batch.req_ids,**FALSES)
def register(C,sr):
 if os.environ.get(FLAG)!='1':return None
 m=source(C,sr)
 # No backend imports and no wrapper until source + current owning gate succeeded.
 import worker_entry as W
 need(C.ref(W.__file__)==m['files']['worker_entry.py'],'exact native-only hook source')
 from vllm_ascend.worker.worker import NPUWorker
 from vllm.forward_context import get_forward_context
 own=m['files']['native_2k_prefill_observer.py'];refs=m['runtime_sources']
 def loaded(worker,registry):
  def after(**kw):return capture(C,sr,**kw)
  W.install_after_native_prefill(worker,C,qwen_next_ref=refs['qwen_next'],get_forward_context=get_forward_context,
    context_source_ref=refs['forward_context'],callback=after,callback_source_ref=own,native_input_source_ref=sr,request_limit=1)
  import torch
  rank=int(torch.distributed.get_rank())
  write(C,m,'NATIVE2K-LOADED-RANK-%d.json'%rank,dict(registry,source=sr,rank=rank,pid=os.getpid(),**FALSES))
 return W.install_after_load(NPUWorker,C,worker_ref=refs['worker'],qwen35_ref=refs['qwen35'],qwen_next_ref=refs['qwen_next'],patch_ref=refs['qwen_patch'],emit=loaded)

def install_frontend(C,sr):
 """Observe the real native assign_request_id call; never infer randomized IDs."""
 if os.environ.get(FLAG)!='1':return None
 m=source(C,sr)
 import identity_capture as I
 need(C.ref(I.__file__)==m['files']['identity_capture.py'],'bound existing read-only assignment observer')
 from vllm.v1.engine.input_processor import InputProcessor
 from vllm.entrypoints.openai.completion.serving import OpenAIServingCompletion
 processor=C.ref(inspect.getsourcefile(InputProcessor.assign_request_id))
 serving=C.ref(inspect.getsourcefile(OpenAIServingCompletion.create_completion))
 need(processor==m['native_2k_input_processor_ref']and processor['sha256']==I.ASSIGN_SHA and
      serving==m['native_2k_completion_serving_ref'],'whole real native processor/serving source before request')
 def emit(kind,event):
  need(kind=='assignment','only actual original native assignment')
  return write(C,m,'NATIVE2K-ASSIGNMENT.json',dict(schema='native.actual-2k-assignment/v1',source=sr,
   input_processor_ref=processor,completion_serving_ref=serving,event=event,**FALSES))
 return I.install_assignment(InputProcessor,emit)
