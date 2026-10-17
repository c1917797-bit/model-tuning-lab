"""Source-bound real after-load registry. No model invocation or device setup."""
import inspect,os,functools
from model_entry import need,code_source,patched_source

def discover(C,outer,qwen35_ref,qwen_next_ref,patch_ref=None):
 candidates=[]
 for name,obj in outer.named_modules():
  if type(obj).__module__=='vllm.model_executor.models.qwen3_5'and type(obj).__name__=='Qwen3_5Model':
   need(C.ref(inspect.getsourcefile(type(obj)))==qwen35_ref,'actual loaded Qwen3_5Model class source')
   code_source(C,obj.forward,qwen_next_ref);candidates.append((name,obj))
 need(len(candidates)==1,'unique actual full target inner model, not draft/shape alias')
 name,model=candidates[0]
 need(model.start_layer==0 and model.end_layer==64 and len(model.layers)==64,'full64 loaded target, no PP/missing layers')
 rows=[];counts={'gdn':0,'fa':0};seen=set()
 for index,layer in enumerate(model.layers):
  need(layer.layer_idx==index,'actual model layer index order')
  if patch_ref is not None:patched_source(C,layer.forward,patch_ref,'decoder')
  if layer.layer_type=='linear_attention':
   obj=layer.linear_attn;kind='gdn';prefix=obj.prefix
  elif layer.layer_type=='full_attention':
   obj=layer.self_attn;kind='fa';prefix=obj.attn.layer_name
   if patch_ref is None:code_source(C,obj.forward,qwen_next_ref)
   else:patched_source(C,obj.forward,patch_ref,'fa')
  else:raise ValueError('actual target layer kind')
  need(type(prefix)is str and prefix and prefix not in seen,'actual unique native layer prefix')
  counts[kind]+=1;seen.add(prefix)
  rows.append(dict(index=index,kind=kind,prefix=prefix,actual_class=type(obj).__module__+'.'+type(obj).__qualname__,object_id=id(obj)))
 need(counts==dict(gdn=48,fa=16),'actual48GDN/16FA')
 return model,dict(schema='bole.actual-loaded-model-registry/source-prep-v1',target_module=name,rows=rows,counts=counts,model_forward_executed=False,model_ready=False)

def actual_logits_head(C,outer,inner,qwen35_ref):
 """Find the source-proved native CausalLM head by actual child identity."""
 heads=[]
 for _,obj in outer.named_modules():
  if getattr(obj,'model',None)is inner and callable(getattr(obj,'compute_logits',None)):
   code_source(C,obj.compute_logits,qwen35_ref);heads.append(obj)
 need(len(heads)==1,'unique actual native LM head owning this target inner model')
 return heads[0].compute_logits

def actual_vocabulary(C,outer,inner,drafter,*,qwen35_ref,mtp_ref):
 """Actual unique LM owner, not the multimodal wrapper's top-level config."""
 method=actual_logits_head(C,outer,inner,qwen35_ref);head=method.__self__
 need((outer is head or getattr(outer,'language_model',None)is head)and head.model is inner,
      'actual loaded outer owns the unique source-bound target LM head')
 need(C.ref(inspect.getsourcefile(type(head)))==qwen35_ref and
      type(head).__name__=='Qwen3_5ForCausalLM','exact actual target LM-head class source')
 text=head.config
 need(inner.config is text and text is head.model_config.hf_text_config,
      'native LM head and actual target inner share the same real text config')
 size=text.vocab_size
 need(type(size)is int and size>0 and inner.vocab_size==size,'actual target embedding and LM-head vocabulary identity')
 draft=drafter.model
 need(type(draft).__name__=='Qwen3_5MTP'and C.ref(inspect.getsourcefile(type(draft)))==mtp_ref,
      'actual independently loaded MTP model class source')
 code_source(C,draft.compute_logits,mtp_ref)
 need(type(draft.config.vocab_size)is int and draft.config.vocab_size==size,
      'actual MTP text config matches actual target vocabulary')
 return size

def install_after_load(WorkerClass,C,*,worker_ref,qwen35_ref,qwen_next_ref,emit,patch_ref=None):
 if os.environ.get('BOLE_MODEL_OBJECT_AUDIT_ENABLE')!='1':return None
 old=WorkerClass.load_model;code_source(C,old,worker_ref)
 need(not getattr(old,'_bole_model_registry',False),'single source-owned worker load observer')
 @functools.wraps(old)
 def loaded(worker):
  result=old(worker)
  outer=worker.model_runner.get_model()
  if patch_ref is None:inner,receipt=discover(C,outer,qwen35_ref,qwen_next_ref)
  else:inner,receipt=discover(C,outer,qwen35_ref,qwen_next_ref,patch_ref)
  # Strong references are only this actual worker's objects, not a global model.
  worker._bole_model_objects=dict(outer=outer,inner=inner,receipt=receipt)
  emit(worker,dict(receipt,pid=os.getpid(),worker_source=worker_ref,qwen35_source=qwen35_ref,qwen_next_source=qwen_next_ref))
  return result
 loaded._bole_model_registry=True;WorkerClass.load_model=loaded
 def restore():
  need(WorkerClass.load_model is loaded,'no foreign worker wrapper before restoration');WorkerClass.load_model=old
 return restore

def install_after_native_prefill(worker,C,*,qwen_next_ref,get_forward_context,
                                 context_source_ref,callback,callback_source_ref,native_input_source_ref=None):
 """Run once inside the REAL model's still-active native forward context.

 The reviewed callback receives genuine target inputs/hidden/request object and
 metadata. It must bind CPU slot/page metadata and drafter provenance; this
 function never guesses either or publishes a BOLE result by itself.
 """
 need(os.environ.get('BOLE_MODEL_OBJECT_AUDIT_ENABLE')=='1','explicit worker hook opt-in')
 record=worker._bole_model_objects;inner=record['inner'];old=inner.forward
 code_source(C,old,qwen_next_ref);code_source(C,get_forward_context,context_source_ref);code_source(C,callback,callback_source_ref)
 active=False;fired=set()
 @functools.wraps(old)
 def forward(this,input_ids,positions,intermediate_tensors=None,inputs_embeds=None):
  nonlocal active
  observed=None
  if not active and not fired and native_input_source_ref is not None:
   before_ctx=get_forward_context();before_meta=before_ctx.attn_metadata
   if getattr(before_ctx,'in_profile_run',False)is not True and isinstance(before_meta,dict)and any(getattr(v,'num_prefills',0)>0 for v in before_meta.values()):
    import input_identity
    manifest=C.obj(native_input_source_ref)
    need(C.ref(input_identity.__file__)==manifest['files']['input_identity.py'],'exact source-bound native input adapter')
    observed=input_identity.capture(C,worker,inner,input_ids,inputs_embeds,intermediate_tensors,manifest['runtime_sources'])
  hidden=old(input_ids,positions,intermediate_tensors,inputs_embeds)
  if active:return hidden
  ctx=get_forward_context();meta=ctx.attn_metadata
  if getattr(ctx,'in_profile_run',False)is True:return hidden
  if meta is None:return hidden # Real native profile/dummy has no request metadata.
  need(isinstance(meta,dict),'actual hybrid metadata mapping')
  if not any(getattr(v,'num_prefills',0)>0 for v in meta.values()):return hidden
  if native_input_source_ref is not None and fired:return hidden # Single diagnostic trial; native retirement-barrier request is untouched.
  if observed is None:need(input_ids is not None and inputs_embeds is None and intermediate_tensors is None,'first text-only PP1 real prefill')
  else:need(intermediate_tensors is None,'first native text prefill PP1 only')
  runner=worker.model_runner;ids=[x for x in runner.input_batch.req_ids if x is not None]
  need(len(ids)==1 and ids[0]in runner.requests and runner.input_batch.req_id_to_index[ids[0]]==0,'actual C1 request identity/row')
  request=runner.requests[ids[0]];key=(ids[0],id(request))
  if key in fired:return hidden
  fired.add(key);active=True
  try:
   arguments=dict(worker=worker,inner=inner,request_id=ids[0],request=request,input_ids=input_ids if observed is None else observed['actual_token_ids'],positions=positions,hidden=hidden,metadata=meta,forward_context=ctx)
   if observed is not None:arguments['native_input']=observed
   callback(**arguments)
  finally:active=False
  return hidden # Original native output object is not substituted.
 had='forward'in inner.__dict__;prior=inner.__dict__.get('forward');inner.forward=__import__('types').MethodType(forward,inner)
 def restore():
  need(not active and inner.forward.__func__ is forward,'no active/foreign inner-model hook')
  if had:inner.forward=prior
  else:delattr(inner,'forward')
 return restore
