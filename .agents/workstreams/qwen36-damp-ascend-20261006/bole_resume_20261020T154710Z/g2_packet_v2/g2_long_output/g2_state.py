"""Independent streaming CPU numeric state, original per-layer bounds unchanged."""
import hashlib,json
import sourceio as C
import g2_contract as G2
import g1_contract as G1
import g2_numeric as N
import g2_registration as REG
import model_calibration131r12 as MC


def tensor_bytes(t,x):
 if isinstance(x,t.Tensor):
  C.need(x.device.type=='cpu','CPU-only independent frame/checkpoint')
  return x.numel()*x.element_size()
 if type(x)in(list,tuple):return sum(tensor_bytes(t,v)for v in x)
 if type(x)is dict:return sum(tensor_bytes(t,v)for v in x.values())
 C.need(x is None or type(x)in(str,int,float,bool),'primitive independent frame')
 return 0


def open_rank(t,m,raw):
    equal=N.equal;mtp_join=N.mtp_join
    C.need(raw['schema']==G1.REQUEST_SCHEMA and raw['request']['generation']in(1,2) and
           type(raw['request']['generation'])is int and raw['request']['slot']==0 and
           raw['request']['length']==131 and raw['request']['version']==0,
           'actual current G2 request registration')
    rid = raw["request"]["request"]
    C.need(raw["source_after"] == m["files"]
           and raw["runtime_sources_after"] == m["runtime_sources"]
           and raw["primary"] is None,
           "actual source/runtime readsets rechecked unchanged at producer freeze")
    slots = raw["layer_slot_bindings"]
    C.need(len(slots) == 48 and len({item["prefix"] for item in slots}) == 48
           and all(item["request_id"] == rid and item["logical_owner_slot"] == 0
                   and item["length"] == 131 for item in slots),
           "complete original registered GDN physical slot identities")
    ids = raw["actual_native_prefill_ids"]
    pos = raw["actual_native_prefill_positions"]
    hidden = raw["actual_native_prefill_hidden"]
    observation = raw["actual_native_prefill_input"]
    C.need(ids.dtype == t.int32 and ids.shape == (131,)
           and hidden.shape == (131, 5120) and hidden.dtype == t.bfloat16
           and bool(t.isfinite(hidden).all()), "actual native text prefill operands")
    equal(t, observation["actual_token_ids"], ids, "observed actual native prefill IDs")
    C.need(ids.tolist() == observation["actual_CPU_token_ids"]
           == observation["request_prompt_token_ids"]
           and observation["no_mm_features"] is True
           and observation["no_soft_prompt"] is True,
           "strong request and CPU buffer input join")
    C.need(observation["sources"] == {key: m["runtime_sources"][key]
           for key in ("runner", "base_runner", "qwen35", "qwen_next")},
           "actual native-input runtime sources")
    C.need(observation["actual_input_mode"] in
           ("native-token-ids", "native-text-embeddings"), "actual native text route")
    if observation["actual_input_mode"] == "native-text-embeddings":
        equal(t, observation["actual_native_embeddings"],
              observation["independent_token_embeddings"],
              "native text embedding/token lookup join")
        C.need(observation["actual_native_embeddings"].shape == (131, 5120)
               and observation["actual_native_embeddings"].dtype == t.bfloat16,
               "exact native embedding ABI")
    axes = pos.ndim
    C.need(pos.dtype == t.int64 and (axes == 1 or pos.shape == (3, 131))
           and pos.tolist() == (list(range(131)) if axes == 1 else [list(range(131))] * 3),
           "original native prefill RoPE coordinates")
    equal(t, raw["initial_target_head_hidden"], hidden[-1:],
          "actual prefill target LMhead operand")
    equal(t, raw["initial_target_head_local_logits"], raw["initial_root_local_logits"],
          "actual prefill sampler input equals unsanitized real LMhead return")
    root = int(raw["initial_root_logits"][0].argmax())
    stream = [root]
    initial = raw["initial_native_output"]
    C.need(initial["req_ids"] == [rid] and initial["sampled_token_ids"] == [[root]]
           and initial["request_output_tokens_after"] == stream
           and initial["num_tokens_no_spec_after"] == 132,
           "actual original native prefill sample/bookkeeping")
    children = mtp_join(t, m, raw["initial_draft"], ids=ids, positions=pos,
                        hidden=hidden, root=root, sample_index=130,
                        live_prefix=ids[1:].tolist() + [root])
    C.need(all(x['generation']==raw['request']['generation']for x in slots),'generation-bound original GDN registration')
    return dict(raw=raw,stream=stream,children=children,axes=axes,ids_dtype=ids.dtype,
                previous=None,ordinal=0,processed=0,observation=None,acks=[],request=rid,generation=raw['request']['generation'])


class Consumer:
 def __init__(self,t,C_,sr,m,channel):
  self.t=t;self.C=C_;self.source=sr;self.m=m;self.channel=channel
  self.active=[None]*4;self.completed=[[]for _ in range(4)];self.calibration=[None]*4
  self.acquisitions=[[]for _ in range(4)];self.closed=False
  for module in(N,N.I,N.oracle112,MC,G1,G2,REG):
   C.need(C.ref(module.__file__)==m['files'][module.__file__.rsplit('/',1)[-1]],'exact independent stream helper')

 def open(self,rank,raw):
  C.need(self.active[rank]is None and len(self.completed[rank])<2,'one next independent request')
  state=open_rank(self.t,self.m,raw);generation=len(self.completed[rank])+1
  C.need(state['generation']==generation and raw['rank']==rank and raw['source']==self.source,'rank/source/monotonic actual generation')
  old=C.obj(self.m['actual118c']['capture'])['actual_device_abi_ref']
  value=MC.validate(C,raw['same_model_conv_calibration'],old,self.source,rank)
  proof=raw['calibration_acquire'];ident=self.channel['actual_worker_identities'][rank]
  C.need(proof['pid']==ident['pid']and proof['generation']==generation and
         proof['source']==self.source and proof['rank']==rank and
         proof['calibration_ref']==raw['same_model_conv_calibration'] and
         proof['created']is(generation==1)and proof['reused']is(generation==2)and
         proof['original_twelve_receipts_reopened']is True and proof['exact_library_identity']is True,
         'actual worker-local original calibration acquire provenance')
  C.need(MC.identity(proof['actual_registration_before'])==MC.identity(proof['actual_registration_after'])==
         MC.identity(value['registration'])==MC.expected(C.obj(old)['registration']),
         'entire exact loaded DSO set, not a subset allowance')
  if generation==1:self.calibration[rank]=MC.consume(self.t,C,raw['same_model_conv_calibration'],old,self.source,rank)
  else:
   prior=self.acquisitions[rank][0]
   C.need(all(prior[k]==proof[k]for k in('pid','worker_object_id','runner_object_id','model_object_id','callable_object_id','calibration_ref')),
          'same strong actual native process/model/operator calibration handle')
   C.need(self.completed[rank][0]['request']!=state['request'],'distinct actual request IDs')
  self.acquisitions[rank].append(proof);self.active[rank]=state
  return dict(generation=generation,request=state['request'],original12_calibration=True)

 def step(self,rank,step):
  t=self.t;s=self.active[rank]
  C.need(s is not None and s['ordinal']<G2.MAX_OUTPUT-1,'bounded current open request')
  n=step['scheduled_nodes'];length=step['owner']['length'];ordinal=s['ordinal']
  C.need(tuple(step['tokens'])==(s['stream'][-1],*s['children']),'preceding genuine first-MTP root plus two children')
  axes=s['axes'];linear=list(range(length,length+n));depth=[length,length+1,length+1]
  C.need(step['original_positions'].tolist()==(linear if axes==1 else[linear]*3)and
         step['tree_positions'].tolist()==(depth if axes==1 else[depth]*3),'actual native linear and tree coordinates')
  C.need(step['tree_hidden'].shape==(3,5120)and step['tree_hidden'].dtype==t.bfloat16 and
         bool(t.isfinite(step['tree_hidden']).all()),'finite actual all64 normalized target hidden')
  N.equal(t,step['target_head_hidden'],step['tree_hidden'][:n],'actual admitted target head operand')
  N.equal(t,step['target_head_local_logits'],step['target_local_logits'],'unsanitized actual native target sample logits')
  ack=step['previous_native_ack']
  if ordinal==0:C.need(ack is None,'first target step has no invented native counter ACK')
  else:
   pub=s['previous']['publication']
   C.need(ack==dict(schema='bole.service-native-scheduler-ack/v1',request=s['request'],
      previous_version=ordinal-1,version=ordinal,computed_tokens=pub['next_length'],
      next_root=pub['emitted_tokens'][-1],scheduler_committed=True,
      whole_model_qualification=False,final_success=False),
      'actual next native CPU input counter/root independently joins preceding selected publication')
   s['acks'].append(ack)
  policy=step['policy_receipt']
  expected=dict(n=1,temperature=0,top_p=1,min_p=0,repetition_penalty=1,frequency_penalty=0,presence_penalty=0,max_tokens=G2.MAX_OUTPUT,min_tokens=0,ignore_eos=True)
  C.need(all(policy[k]==v for k,v in expected.items())and policy['generated_before']==len(s['stream'])and policy['all_greedy']is True and policy['no_penalties']is True and policy['no_thinking_budget']is True and policy['top_k']in(0,-1),'actual current source-guarded neutral native policy')
  if ordinal==0:
   item=dict(s['raw'],steps=[step],policy_receipts=s['raw']['policy_receipts']+[policy])
   old=C.obj(self.m['actual118c']['capture'])['actual_device_abi_ref']
   calibrated=MC.validate(C,s['raw']['same_model_conv_calibration'],old,self.source,rank)
   observed=REG.capture_join(self.source,self.m,item,self.channel['actual_worker_identities'][rank],calibrated,MC,old)
   if s['generation']==2:
    prior=self.completed[rank][0]['observation']
    C.need(prior['request_object_id']!=observed['request_object_id']and prior['native_arena_identity_sha256']==observed['native_arena_identity_sha256'],'fresh strong request on same actual model arenas')
   s['observation']=observed
  report,stream,path,emitted=N.consume_step(t,self.m,s['raw'],step,ordinal,s['stream'],s['previous'])
  C.need(report['component_checks_pass']is True,'all original per-layer component bounds passed')
  order=[0,2,1]if path[-1]==2 else list(range(n));index=t.tensor(order[:n],dtype=t.long)
  ids=t.tensor(step['tokens'],dtype=s['ids_dtype']).index_select(0,index)
  children=N.mtp_join(t,self.m,step['next_mtp'],ids=ids,
      positions=step['tree_positions'].index_select(-1,index),hidden=step['tree_hidden'].index_select(0,index),
      root=emitted[-1],sample_index=len(path)-1,live_prefix=emitted)
  rejected=step['next_mtp']['num_rejected_tokens']
  C.need((rejected is None and n==1)or(rejected is not None and rejected.tolist()==[n-len(path)]),
         'actual native rejected-tail count with all admitted rows retained')
  # Retain only independently verified actual postimages, not the full frame.
  publication=step['publication']
  previous=dict(after_GDN=step['after_GDN'],after_FA=step['after_FA'],publication=dict(
      owner=publication['owner'],next_length=publication['next_length'],next_version=publication['next_version'],
      emitted_tokens=publication['emitted_tokens']))
  C.need(tensor_bytes(t,previous)+tensor_bytes(t,s['raw'])<=G2.CHECKPOINT_CAP,
         'bounded actual checkpoint before successful raw release')
  s.update(previous=previous,stream=stream,children=children,ordinal=ordinal+1,processed=s['processed']+len(path))
  return report

 def retire(self,rank,value):
  s=self.active[rank];C.need(s is not None,'real current request before retirement')
  retirement=value['retirement'];ordinal=s['ordinal']
  C.need(2<=ordinal<=G2.MAX_OUTPUT-1 and len(s['stream'])==G2.MAX_OUTPUT and s['processed']==G2.MAX_OUTPUT-1 and
         value['output_token_ids']==s['stream']and value['request']==s['raw']['request']and
         retirement['request']==s['request']and retirement['generation']==s['generation']and
         retirement['steps']==ordinal and retirement['next_counter_acknowledgements']==s['acks']and len(s['acks'])==ordinal-1 and
         retirement['final_ack_by_retirement_pending']is True and
         retirement['last_publication']==s['previous']['publication'],
         'every actual step consumed and exact fixed output reached before native removal')
  summary=dict(request=s['request'],generation=s['generation'],output_token_ids=s['stream'],steps=ordinal,
      prefix_token_ids=s['raw']['actual_native_prefill_ids'].tolist(),
      processed_tokens=s['processed'],next_counter_ACKs=ordinal-1,component_checks_pass=True,observation=s['observation'])
  self.completed[rank].append(summary);self.active[rank]=None
  return summary

 @staticmethod
 def coverage(kind,value):
  if kind=='open':return dict(generation=value['request']['generation'],request=value['request']['request'])
  if kind=='step':return dict(generation=value['owner']['generation'],request=value['owner']['request'],
      ordinal=value['owner']['version'],length=value['owner']['length'],
      emitted_tokens=list(value['publication']['emitted_tokens']),processed_nodes=list(value['publication']['processed_nodes']))
  if kind=='retire':return dict(generation=value['request']['generation'],request=value['request']['request'],
      steps=len(value['steps']),output_tokens=len(value['output_token_ids']))
  C.need(kind=='close','only complete recognized actual frame')
  return dict(request_count=len(value['requests']),output_budget=G2.MAX_OUTPUT)

 def consume_batch(self,kind,values):
  C.need(len(values)==4 and not self.closed,'all four actual rank frames required')
  if kind=='open':
   policies=[v['native_logits_policy']for v in values]
   C.need(all(v==policies[0]for v in policies),'all4 exact native vocabulary policy')
   for local,global_ in(('initial_root_local_logits','initial_root_logits'),):
    N.tp_logits(self.t,[{'local':v[local],'global':v[global_]}for v in values],policies[0])
   N.tp_logits(self.t,[{'local':v['initial_draft']['first_local_logits'],'global':v['initial_draft']['first_logits']}for v in values],policies[0])
   return[self.open(rank,value)for rank,value in enumerate(values)]
  if kind=='step':
   C.need(all(v['owner']==values[0]['owner']and v['tokens']==values[0]['tokens']and
      v['scheduled_nodes']==values[0]['scheduled_nodes']and v['remaining_output']==values[0]['remaining_output']for v in values),
      'all4 same actual target owner/tree/admission/budget')
   policy=self.active[0]['raw']['native_logits_policy']
   N.tp_logits(self.t,[{'local':v['target_local_logits'],'global':v['target_logits']}for v in values],policy)
   N.tp_logits(self.t,[{'local':v['next_mtp']['first_local_logits'],'global':v['next_mtp']['first_logits']}for v in values],policy)
   return[self.step(rank,value)for rank,value in enumerate(values)]
  if kind=='retire':return[self.retire(rank,value)for rank,value in enumerate(values)]
  C.need(kind=='close'and all(s is None for s in self.active)and all(len(v)==2 for v in self.completed),
         'close only after both actual requests on all four ranks')
  C.need(all([x['output_token_ids']for x in v]==[x['output_token_ids']for x in self.completed[0]]for v in self.completed),
         'all4 exact emitted streams across both complete lifecycles')
  self.closed=True
  return[dict(requests=v,complete=True)for v in self.completed]

