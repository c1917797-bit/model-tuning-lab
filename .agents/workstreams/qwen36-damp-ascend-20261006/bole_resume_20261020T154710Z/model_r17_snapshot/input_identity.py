"""Observe source-proved native pure-text ID/embedding inputs BEFORE forward.

Native arguments/results are untouched. Recovered IDs serve diagnostics only.
No multimodal/soft-prompt input or inferred token length is accepted.
"""
import inspect
from model_entry import need,code_source
from worker_entry import actual_logits_head

def capture(C,worker,inner,input_ids,inputs_embeds,intermediate,refs):
 import torch as t
 runner=worker.model_runner;outer=worker._bole_model_objects['outer']
 need(intermediate is None,'actual PP1 native prefill only')
 code_source(C,runner._preprocess,refs['runner'])
 bases=[cls for cls in type(runner).__mro__ if cls.__name__=='GPUModelRunner']
 need(len(bases)==1,'actual unique native base input runner')
 for name in('_preprocess','_prepare_mm_inputs'):code_source(C,getattr(bases[0],name),refs['base_runner'])
 ids=[r for r in runner.input_batch.req_ids if r is not None]
 need(len(ids)==1 and ids[0]in runner.requests and runner.input_batch.req_id_to_index[ids[0]]==0,'actual C1 request/CPU row')
 request=runner.requests[ids[0]];prompt=request.prompt_token_ids
 need(type(prompt)is list and len(prompt)==131 and all(type(x)is int and x>=0 for x in prompt), 'exact actual131-token prompt, not string length')
 need(request.prompt_embeds is None and not request.mm_features and
      (request.prompt_is_token_ids is None or list(request.prompt_is_token_ids)==[True]*131),
      'no native multimodal features, soft prompts or non-token prompt inputs')
 gpu=runner.input_ids.gpu[:131]
 cpu=runner.input_batch.token_ids_cpu[0,:131].tolist()
 need(gpu.dtype==t.int32 and tuple(gpu.shape)==(131,)and gpu.detach().cpu().tolist()==prompt==cpu,
      'native GPU token buffer, actual CPU batch row and strong request all exact')
 result=dict(actual_token_ids=gpu.detach().clone(),actual_CPU_token_ids=cpu,request_prompt_token_ids=list(prompt),
             sources={k:refs[k]for k in('runner','base_runner','qwen35','qwen_next')},request_id=ids[0],
             no_mm_features=True,no_soft_prompt=True)
 if inputs_embeds is None:
  need(input_ids is not None and input_ids.dtype==t.int32 and t.equal(input_ids,gpu),'actual native direct token IDs')
  result.update(actual_input_mode='native-token-ids',actual_input_id_argument=input_ids.detach().clone())
 else:
  need(runner.supports_mm_inputs is True and not runner.enable_prompt_embeds and not runner.model_config.is_encoder_decoder,
       'actual native pure-text multimodal-model embedding route only')
  if input_ids is not None:need(t.equal(input_ids,gpu),'optional native raw ID argument agrees with real tokens')
  head=actual_logits_head(C,outer,inner,refs['qwen35']).__self__
  code_source(C,head.embed_input_ids,refs['qwen35']);code_source(C,inner.embed_input_ids,refs['qwen_next'])
  expected=head.embed_input_ids(gpu)
  need(inputs_embeds.shape==expected.shape==(131,5120)and inputs_embeds.dtype==expected.dtype==t.bfloat16 and
       t.equal(inputs_embeds.contiguous().view(t.uint8),expected.contiguous().view(t.uint8)),
       'actual native input embeddings equal source-pinned genuine token embedding before forward')
  result.update(actual_input_mode='native-text-embeddings',actual_input_id_argument=None if input_ids is None else input_ids.detach().clone(),
                actual_native_embeddings=inputs_embeds.detach().clone(),independent_token_embeddings=expected.detach().clone())
 return result
