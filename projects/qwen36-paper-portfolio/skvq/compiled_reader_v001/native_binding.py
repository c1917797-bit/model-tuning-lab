"""Exact image660 runner/scheduler frame binding; no SSE-ID derivation."""
import hashlib,inspect,json,sys
import contract as C
ASCEND="vllm_ascend.worker.model_runner_v1"
GPU="vllm.v1.worker.gpu_model_runner"
INPUT_BATCH="vllm.v1.worker.gpu_input_batch"
ASCEND_SHA="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
GPU_SHA="6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666"
INPUT_BATCH_SHA="caeeb20f5010d74663c45f9419237191e3c0a149f4c7aa25bc1b73b1112d67ae"
def sources():
    result={}
    for name,sha in((ASCEND,ASCEND_SHA),(GPU,GPU_SHA),(INPUT_BATCH,INPUT_BATCH_SHA)):
        m=sys.modules.get(name)
        C.need(m is not None and C.ref(m.__file__)["sha256"]==sha and m.__spec__.name==name,"whole installed native runner source")
        result[name]=C.ref(m.__file__)
    return result
class Bind:
    def __init__(self,worker,source,identity,prompt_ref,*,registry,qualify_rank):
        self.worker=worker;self.source=source;self.identity=identity;self.origins=sources()
        prompt=C.obj(prompt_ref)
        C.need(prompt["schema"]=="skvq.first-decode.prompt/v1"and
          prompt["source_ref"]==source and len(prompt["token_ids"])==32768 and
          all(type(x)is int and 0<=x<2**31 for x in prompt["token_ids"]),
          "frozen actual tokenized32768 prompt, not fabricated tensor")
        C.need(callable(qualify_rank),"actual source-qualified live TP provider")
        self.prompt_ref=prompt_ref;self.prompt=prompt["token_ids"];self.owner=None;self.registry=registry;self.qualify_rank=qualify_rank
    def __call__(self,worker,logical,metadata,q,k,v):
        C.need(worker is self.worker and sources()==self.origins,"same actual worker/native source")
        self.qualify_rank()
        r=worker.model_runner;batch=r.input_batch
        ids=[x for x in batch.req_ids if x is not None]
        C.need(len(ids)==1 and len(r.requests)==1 and ids[0]in r.requests,"one real native request, not guessed engine ID")
        request=ids[0];state=r.requests[request]
        C.need(type(state)is sys.modules[INPUT_BATCH].CachedRequestState and state.req_id==request and
          state.prompt_token_ids==self.prompt and state.prompt_embeds is None and state.mm_features==[] and
          state.num_prompt_tokens==32768,"same source-qualified native full token-ID prompt/state")
        outer,child=self.registry[logical]
        from post_rope_current import receiver
        donor,post_rope_sources=receiver(outer,child)
        frame=inspect.currentframe().f_back;seen=None;actual_qkv=None
        try:
            while frame is not None:
                if frame.f_code.co_name=="execute_model"and frame.f_code.co_filename==self.origins[ASCEND]["path"]and frame.f_locals.get("self")is r:
                    C.need(seen is None,"unique actual installed execute frame");seen=frame
                if frame.f_code is donor.__code__ and frame.f_locals.get("self")is outer:
                    C.need(actual_qkv is None and frame.f_lineno==81,"unique actual original post-QKnorm/RoPE call")
                    actual_qkv={axis:frame.f_locals[axis]for axis in("q","k","v")}
                frame=frame.f_back
            C.need(seen is not None,"actual original Ascend execute_model caller")
            C.need(actual_qkv is not None,"actual native post-RoPE QKV caller, not substituted tensors")
            for axis,t in(("q",q),("k",k),("v",v)):
                original=actual_qkv[axis]
                C.need(original.numel()==t.numel()and original.dtype==t.dtype and original.device==t.device and
                  original.data_ptr()==t.data_ptr()and original.untyped_storage().data_ptr()==t.untyped_storage().data_ptr()and
                  original.storage_offset()==t.storage_offset(),"actual original Qwen live QKV storage alias: "+axis)
            output=seen.f_locals["scheduler_output"]
            C.need(set(output.num_scheduled_tokens)=={request}and not output.finished_req_ids and
              not output.scheduled_encoder_inputs and output.total_num_scheduled_tokens in(32768,1),
              "one actual full prefill/decode schedule, no encoder or synthetic SchedulerOutput")
            count=output.num_scheduled_tokens[request]
            phase="prefill"if count==32768 else"decode"
            C.need((phase=="prefill"and state.num_computed_tokens==0)or
              (phase=="decode"and state.num_computed_tokens in(32768,32769)),
              "real native scheduler computed token extent")
            fc=sys.modules["vllm.forward_context"].get_forward_context()
            C.need(fc.cudagraph_runtime_mode.name=="NONE"and fc.dp_metadata is None and fc.ubatch_slices is None,
              "actual eager no split/data microbatch")
            if self.owner is None:self.owner=request
            C.need(request==self.owner and q.shape[0]==count and k.shape[0]==v.shape[0]==count,"same actual owner/scheduled tensor rows")
            value=dict(schema="skvq.compiled-reader.native-binding/v1",source_ref=self.source,
              rank_identity=self.identity,request_id=request,epoch=1,phase=phase,graph_mode="NONE",
              prompt_ref=self.prompt_ref,actual_runtime_origins=self.origins,num_computed_tokens=state.num_computed_tokens,
              actual_total_scheduled=output.total_num_scheduled_tokens,num_scheduled_tokens=dict(output.num_scheduled_tokens),
              logical_layer=logical,seq_lens_list=list(metadata.seq_lens_list),
              query_lengths=list(metadata.actual_seq_lengths_q),native_finished_pending=True)
            value["actual_post_RoPE_sources"]=post_rope_sources;value["actual_live_post_RoPE_QKV_alias_checked"]=True
            return value
        finally:
            del frame
            if seen is not None:del seen
