"""Independent native2k metadata/HTTP join; never a live-object or numeric proof."""
from pathlib import Path
FALSES=dict(numerical_qualified=False,formal_performance=False,task_accuracy=False)
def need(v,s):
 if not v:raise ValueError(s)
def integer(x,minval=0):return type(x)is int and x>=minval
def vector(x,n=None):
 need(type(x)is list and(n is None or len(x)==n)and all(integer(v)for v in x),'complete integer vector')
 return x
def operand(x,n,dtype=None):
 need(type(x)is dict and set(x)=={'identity','shape','stride','dtype','device','values'},'whole integer operand schema')
 need(x['shape']==[n]and x['stride']==[1]and x['dtype']in('torch.int32','torch.int64')and(dtype is None or x['dtype']==dtype),'complete contiguous integer metadata shape')
 need(type(x['identity'])in(list,tuple)and len(x['identity'])==7 and list(x['identity'][3])==x['shape']and list(x['identity'][4])==x['stride']and x['identity'][5]==x['dtype']and x['identity'][6]==x['device'],'identity/shape/dtype/stride joins')
 need(all(integer(v,1)for v in x['identity'][:2])and integer(x['identity'][2]),'typed actual storage/pointer/offset metadata')
 vector(x['values'],n);return x['values']
def tensor(x):
 need(type(x)is dict and set(x)=={'identity','shape','stride','dtype','device'}and type(x['identity'])in(list,tuple)and len(x['identity'])==7,'whole native tensor identity')
 need(list(x['identity'][3])==x['shape']and list(x['identity'][4])==x['stride']and x['identity'][5]==x['dtype']and x['identity'][6]==x['device'],'actual tensor identity metadata joins')
 need(all(integer(v,1)for v in x['identity'][:2])and integer(x['identity'][2]),'typed actual tensor storage/pointer/offset')
 need(all(integer(v,1)for v in x['shape'])and len(x['stride'])==len(x['shape'])and all(integer(v)for v in x['stride']),'typed tensor geometry')
 return x
def observation(value,sr,ids,worker,registry,runtime):
 need(value['schema']=='native.actual-2k-prefill-observation/v1'and value['source']==sr and value['rank']==worker['distributed_rank']and
      type(value['rank'])is int and type(value['npu_logical_device'])is int and type(value['pid'])is int and
      value['npu_logical_device']==worker['npu_logical_device']and value['pid']==worker['pid'],'actual source/worker/rank/device identity')
 need(type(value['request_epoch'])is int and value['request_epoch']==1 and value['request_id']and integer(value['request_object_id'],1)and integer(value['worker_object_id'],1)and integer(value['runner_object_id'],1),'strong request/worker object identities')
 need(value['actual_token_ids']==vector(ids,2048)and value['input_identity_sources']=={k:runtime[k]for k in('runner','base_runner','qwen35','qwen_next')}and value['actual_input_mode']in('native-token-ids','native-text-embeddings')and
      value['no_mm_features']is True and value['no_soft_prompt']is True,'actual full input IDs/native provenance')
 need(value['runtime_sources']=={k:runtime[k]for k in('runner','block_table','attention','ascend_attention','forward_context','ascend_forward_context','qwen35','qwen_next','worker','base_runner')},'whole actual native framework sources')
 need(value['generic_context_type']=='dict'and value['generic_context_keys']==[]and value['native_output_not_substituted']is True and value['cache_contents_captured']is False and value['integer_metadata_D2H']is True and
      all(value[k]is False for k in FALSES),'metadata-only native scope')
 need(registry['source']==sr and registry['pid']==worker['pid']and registry['rank']==value['rank']and registry['counts']==dict(gdn=48,fa=16)and len(registry['rows'])==64,'actual same-worker full loaded model registry')
 registered=registry['rows'];need([r['index']for r in registered]==list(range(64))and len({r['prefix']for r in registered})==64,'all64 loaded unique prefixes')
 rows=value['rows'];gdn=value['GDN_selected_operands']
 need(len(rows)==16 and len(gdn)==48 and {r['layer']for r in rows+gdn}==set(range(64))and len({r['prefix']for r in rows+gdn})==64,'complete16FA/48GDN without duplicate/missing layers')
 shared={}
 for row in rows:
  i=row['layer'];need(integer(i)and registered[i]['kind']=='fa'and registered[i]['prefix']==row['prefix'],'FA registry prefix/index join')
  need(row['request_object_id']==value['request_object_id']and all(integer(row[k],1)for k in('layer_object_id','metadata_object_id','context_object_id','group_object_id','block_object_id'))and integer(row['group']),'actual FA context/group/objects')
  n=row['allocated'];need(integer(n,1)and n<=65536,'bounded actual allocation')
  cpu=operand(row['CPU_table'],n);gpu=operand(row['GPU_table'],n,'torch.int32');meta=operand(row['metadata_table'],n,'torch.int32')
  need(cpu==gpu==meta and len(set(cpu))==n and row['GPU_table']['identity']==row['metadata_table']['identity']and row['CPU_table']['device']=='cpu'and row['GPU_table']['device']=='npu:%d'%value['npu_logical_device'],'full committed CPU/device/metadata table and alias')
  ratio=row['blocks_per_phys_block'];blocks=vector(row['request_physical_blocks'])
  need(integer(ratio,1)and type(row['use_hybrid_blocks'])is bool and type(row['pcp'])is type(row['dcp'])is int and row['kernel_block_size']==128 and row['physical_block_size']==ratio*128 and row['pcp']==row['dcp']==1,'native CP1 physical/kernel geometry')
  expanded=[b*ratio+j for b in blocks for j in range(ratio)]if row['use_hybrid_blocks']else blocks
  need(expanded==cpu and n*128>=2048,'actual request-to-native allocated row covers2048, not guessed24/25')
  slots=operand(row['native_slot_mapping'],2048,'torch.int32');mapped=operand(row['metadata_slot_mapping'],2048,'torch.int32')
  need(slots==mapped==[cpu[p//128]*128+p%128 for p in range(2048)]and row['native_slot_mapping']['identity']==row['metadata_slot_mapping']['identity']and row['generic_slot_mapping']is None,'all2048 native destinations and metadata alias')
  key=tensor(row['key']);value_cache=tensor(row['value']);tensor(row['impl_key']);tensor(row['impl_value'])
  need(key==row['impl_key']and value_cache==row['impl_value']and key['shape']==value_cache['shape']and key['shape'][1:]==[128,1,256]and len(key['shape'])==4 and key['dtype']==value_cache['dtype']=='torch.bfloat16'and key['device']==value_cache['device']=='npu:%d'%value['npu_logical_device']and max(cpu)<key['shape'][0],'actual layer/backend BF16 ND cache aliases/arena bounds')
  need(all(type(row[k])is int for k in('num_prefills','num_decodes','num_actual_tokens'))and row['num_prefills']==1 and row['num_decodes']==0 and row['num_actual_tokens']==2048 and row['seq_lens_list']==row['actual_seq_lengths_q']==[2048],'complete pure-prefill chronology')
  identity=(cpu,blocks,ratio,row['physical_block_size'],row['block_object_id'],row['group_object_id'])
  if row['group']in shared:need(shared[row['group']]==identity,'same native group has one actual table/allocation')
  else:shared[row['group']]=identity
 for row in gdn:
  i=row['layer'];need(integer(i)and registered[i]['kind']=='gdn'and registered[i]['prefix']==row['prefix']and row['request_object_id']==value['request_object_id'],'GDN actual request/registry join')
  cpu=operand(row['CPU_table'],row['allocated']);selected=operand(row['selected'],1)
  need(selected[0]in cpu,'actual selected GDN slot in allocated group')
  tensor(row['conv']);tensor(row['state'])
 return dict(rank=value['rank'],request_id=value['request_id'],FA=16,GDN=48,allocated_kernel_pages={str(r['layer']):r['allocated']for r in rows},**FALSES)
def consume(*,C,source,manifest,client_output,receipt_root):
 need(C.ref(__file__)==manifest['files']['consume_native_2k.py']and manifest['performance_arm']=='native_ar','bound independent native consumer')
 import native_ar_control_consumer as NA
 need(C.ref(NA.__file__)==manifest['files']['native_ar_control_consumer.py'],'original native worker/lifecycle reader')
 readset=[]
 def obj(p):
  ref=C.ref(p);readset.append(ref);return C.obj(ref)
 inputs=obj(Path(client_output)/'INPUTS.json');http=obj(Path(client_output)/'HTTP_RESULT.json')
 ids=vector(inputs['token_ids'],2048);need(inputs['source']==source and inputs['input_tokens']==2048,'actual source/input identity')
 need(http['schema']=='native.2k-prefill-http/v1'and http['source']==source and http['status']==200 and all(http[k]is False for k in FALSES),'actual HTTP diagnostic scope')
 header='native-2k-prefill-'+manifest['native_2k_request_identity']
 expected=dict(model='qwen36-mxr-eager',prompt=ids,max_tokens=1,temperature=0,top_p=1,n=1,stream=False,ignore_eos=True,return_token_ids=True,seed=0)
 need(http['header']==header and http['request']==expected,'exact frozen one-request native payload')
 value=C.obj(http['response']);readset.append(http['response'])
 need(value['id']=='cmpl-'+header and value['usage']['prompt_tokens']==2048 and value['usage']['completion_tokens']==1 and len(value['choices'])==1 and value['choices'][0]['index']==0,'whole actual response identity/count')
 vector(value['choices'][0]['token_ids'],1)
 assignment=obj(Path(receipt_root)/'NATIVE2K-ASSIGNMENT.json')
 need(assignment['schema']=='native.actual-2k-assignment/v1'and assignment['source']==source and
      assignment['input_processor_ref']==manifest['native_2k_input_processor_ref']and
      assignment['completion_serving_ref']==manifest['native_2k_completion_serving_ref'],'actual native frontend assignment and whole loaded sources')
 event=assignment['event']
 need(event['schema']=='vllm023.actual-assignment/v1'and event['source_sha256']==manifest['native_2k_input_processor_ref']['sha256']and
      event['before_request_id']==value['id']+'-0'and type(event['after_request_id'])is str and event['after_request_id']and
      integer(event['identity']['pid'],1)and integer(event['identity']['start_ticks'],1)and event['identity']['cgroup'],
      'source-proved single engine_input0 completion-to-assignment join; no guessed randomized worker ID')
 engine_id=event['after_request_id']
 command=obj(Path(receipt_root)/'SERVER_COMMAND.json')
 need(command['source']==source and command['performance_arm']=='native_ar'and command['native_MTP']is False and command['num_speculative_tokens']==0 and '--speculative-config'not in command['argv'],'actual native AR command, not observerOFF')
 bindings=obj(Path(receipt_root).parent/'WORKER_BINDINGS.json');need(len(bindings)==4 and len({b['host']['pid']for b in bindings})==4,'actual host-to-guest four worker bindings')
 workers=[b['guest']for b in bindings];NA.worker_flags(workers,source)
 proofs=[]
 for worker in sorted(workers,key=lambda x:x['distributed_rank']):
  rank=worker['distributed_rank'];obs_ref=C.ref(Path(receipt_root)/('NATIVE2K-PREFILL-RANK-%d.json'%rank));readset.append(obs_ref)
  obs=C.obj(obs_ref);registry=obj(Path(receipt_root)/('NATIVE2K-LOADED-RANK-%d.json'%rank))
  status=worker['native_2k_observation']
  need(status['source']==source and status['pid']==worker['pid']and status['rank']==rank and status['receipt']==obs_ref and status['request_id']==engine_id and status['request_absent']is True,'same native observed request actually exited worker')
  need(obs['request_id']==engine_id,'actual HTTP assignment joined to native prefill')
  proofs.append(observation(obs,source,ids,worker,registry,manifest['runtime_sources']))
 return dict(schema='native.2k-prefill-independent-consumption/v1',source=source,readset=readset,rows=proofs,
  actual_native_geometry_observed=True,live_candidate_binding_proven=False,publication24_or_scratch25_not_assumed=True,
  stop_retain_release_proof_pending_outer_owner=True,**FALSES)
