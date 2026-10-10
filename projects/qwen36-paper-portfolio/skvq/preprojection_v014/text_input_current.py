"""Source-qualified native pure-text embeddings, DEFAULT-OFF on import.
Keeps the original embedding call/return and root call unchanged. No tensor clone,
new embedding computation, hardware import or controller is introduced here.
"""
import importlib,inspect,json,sys
from pathlib import Path
import current_contract as C
SCHEMA="skvq.native-text-input-provenance/v1"
GPU="vllm.v1.worker.gpu_model_runner"
NPU="vllm_ascend.worker.model_runner_v1"
QWEN="vllm.model_executor.models.qwen3_5"
METHODS={GPU:("GPUModelRunner",("_preprocess","_prepare_mm_inputs","_gather_mm_embeddings")),
 NPU:("NPUModelRunner",("_preprocess","_model_forward")),
 QWEN:("Qwen3_5ForConditionalGeneration",("embed_input_ids","forward"))}
def qualified(source):
    C.checked(source);manifest=json.loads(Path(source["path"]).read_bytes())
    rows=manifest["native_text_input_runtime_sources"];origins={};functions={}
    C.require(type(rows)is list and {x["module"]for x in rows}==set(METHODS)and len(rows)==3,
      "one exact original text-input runtime closure")
    for row in rows:
        C.checked(row["snapshot"]);module=importlib.import_module(row["module"])
        origin=C.reference(module.__file__);spec=module.__spec__
        C.require(spec is not None and spec.name==row["module"]and
          Path(spec.origin).resolve()==Path(module.__file__).resolve()and
          origin==dict(path=row["runtime_path"],bytes=row["snapshot"]["bytes"],sha256=row["snapshot"]["sha256"]),
          "whole original text-input module source")
        cls_name,names=METHODS[row["module"]];cls=getattr(module,cls_name)
        C.require(cls.__module__==row["module"]and inspect.getsourcefile(cls)==origin["path"],
          "original source-qualified runner/model class")
        metadata={}
        for name in names:
            fn=getattr(cls,name)
            C.require(inspect.isfunction(fn)and fn.__module__==row["module"]and
              fn.__qualname__==cls_name+"."+name and
              inspect.getsourcefile(fn)==origin["path"]and fn.__code__.co_filename==origin["path"],
              "original text-input method; no foreign wrapper")
            functions[(row["module"],name)]=fn
            metadata[name]={"qualname":fn.__qualname__,"first_line":fn.__code__.co_firstlineno}
        origins[row["module"]]={"origin":origin,"methods":metadata}
    return origins,functions
def preweights(source,destination,publish):
    origins,_=qualified(source)
    return publish(destination,{"schema":"skvq.native-text-input-source-preweights/v1",
      "source_ref":source,"runtime_sources":origins,"actual_tensor_path_pending":True,
      "capture_ready":False,"model_ready":False})
def describe(value):
    if value is None:return {"kind":"None"}
    torch=sys.modules.get("torch")
    if torch is not None and isinstance(value,torch.Tensor):
        from post_rope_current import tensor_description
        return {"kind":"tensor","view":tensor_description(value)}
    return {"kind":"unsupported","type":type(value).__module__+"."+type(value).__qualname__}
def view(value):
    result=describe(value);C.require(result["kind"]=="tensor","actual native tensor, no substitute")
    return result["view"]
def id_values(value):
    torch=sys.modules.get("torch")
    C.require(torch is not None and isinstance(value,torch.Tensor)and
      tuple(value.shape)==(4096,)and value.device.type=="npu"and
      value.dtype in (torch.int32,torch.int64),"actual full4096 native integer token IDs")
    return value.detach().cpu().tolist()
def scheduler_record(runner,frame):
    output=frame.f_locals.get("scheduler_output")
    if output is None:return {"present":False}
    batch=list(runner.input_batch.req_ids)
    return {"present":True,"batch_request_ids":batch,
      "num_scheduled_tokens":dict(output.num_scheduled_tokens),
      "total_num_scheduled_tokens":output.total_num_scheduled_tokens,
      "num_input_tokens":frame.f_locals.get("num_input_tokens"),
      "scheduled_encoder_inputs":output.scheduled_encoder_inputs,
      "intermediate_tensors_is_none":frame.f_locals.get("intermediate_tensors")is None}
class TextInputs:
    def __init__(self,session,source,publish):
        self.s=session;self.source=source;self.publish=publish;self.pending=None;self.current_ref=None
        self.origins,self.functions=qualified(source);self.runner=session.w.model_runner
        self.original=session.model.embed_input_ids
        C.require(self.runner.model is session.model and
          self.original.__func__ is self.functions[(QWEN,"embed_input_ids")]and
          session.original_root.__func__ is self.functions[(QWEN,"forward")]and
          self.runner._preprocess.__func__ is self.functions[(NPU,"_preprocess")]and
          self.runner._model_forward.__func__ is self.functions[(NPU,"_model_forward")],
          "same real root/runner owns all original calls")
    def path(self,label):
        return self.s.sink.path/("sample-%03d-%s.json"%(self.s.active,label))
    def begin(self,frame,input_ids,multimodal_embeddings,is_multimodal):
        s=self.s
        # Publish actual representation BEFORE enforcing its semantic gates.
        raw={"schema":"skvq.native-text-embed-raw/v1","source_ref":self.source,
          "rank":s.w.rank,"identity":s.identity,"sample_id":s.active,
          "input_ids":describe(input_ids),"is_multimodal":describe(is_multimodal),
          "multimodal_embeddings_type":type(multimodal_embeddings).__name__,
          "multimodal_embeddings_count":len(multimodal_embeddings)if type(multimodal_embeddings)is list else None,
          "caller":{"qualname":self.functions[(GPU,"_preprocess")].__qualname__ if
              frame.f_code is self.functions[(GPU,"_preprocess")].__code__ else
              getattr(frame.f_code,"co_qualname",frame.f_code.co_name),"file":frame.f_code.co_filename,
            "line":frame.f_lineno,"same_runner":frame.f_locals.get("self")is self.runner},
          "scheduler":scheduler_record(self.runner,frame),"runtime_sources":self.origins}
        raw_ref=self.publish(self.path("EMBED_RAW_BEFORE"),raw)
        C.require(not s.poisoned and not s.closed and s.active is not None and not s.in_forward and self.pending is None,
          "one armed original text embedding before root")
        C.require(frame.f_code is self.functions[(GPU,"_preprocess")].__code__ and
          frame.f_locals.get("self")is self.runner,"actual original GPU superclass preprocess caller")
        schedule=raw["scheduler"];batch=schedule["batch_request_ids"]
        C.require(len(batch)==1 and schedule["num_scheduled_tokens"]=={batch[0]:4096}and
          schedule["total_num_scheduled_tokens"]==schedule["num_input_tokens"]==4096 and
          schedule["scheduled_encoder_inputs"]=={}and schedule["intermediate_tensors_is_none"]is True,
          "one complete fresh native text schedule; no encoder/PP/padding")
        request=self.runner.requests[batch[0]]
        from io_contract import sample_ids
        expected=sample_ids(s.input_path,s.active);actual=id_values(input_ids)
        C.require(actual==expected and request.prompt_token_ids==expected and request.prompt_embeds is None and
          request.mm_features==[]and request.num_computed_tokens==0 and
          not self.runner.input_batch.req_prompt_embeds and
          self.runner.supports_mm_inputs is True and self.runner.enable_prompt_embeds is False and
          self.runner.model_config.is_encoder_decoder is False,
          "frozen token-ID request only; no external embeddings or media")
        torch=sys.modules["torch"]
        C.require(type(multimodal_embeddings)is list and not multimodal_embeddings and
          isinstance(is_multimodal,torch.Tensor)and tuple(is_multimodal.shape)==(4096,)and
          is_multimodal.device.type=="cpu"and is_multimodal.dtype==torch.bool and
          is_multimodal.tolist()==[False]*4096,"native empty media list and exact all-false CPU mask")
        record={"raw_ref":raw_ref,"actual_token_ids":actual,"request_id":batch[0],
          "token_ids_sha256":s.inputs["samples"][s.active]["token_ids_sha256"],
          "actual_request_prompt_token_ids":list(request.prompt_token_ids),
          "actual_mm_mask":is_multimodal.tolist(),
          "prompt_embeds_is_none":True,"mm_features_empty":True,"mm_embeddings_empty":True,
          "all4096_mm_mask_false":True,"num_computed_tokens":0}
        return record
    def returned(self,record,result):
        descriptor=view(result)
        C.require(descriptor["shape"]==[4096,self.runner.inputs_embeds_size]and
          descriptor["dtype"]in ("torch.float16","torch.bfloat16")and
          descriptor["device"].startswith("npu"),"original native text embedding result")
        self.pending=(record,result,descriptor)
        return result
    def root(self,bound):
        s=self.s;a=bound.arguments;ids=a["input_ids"];embeds=a["inputs_embeds"];positions=a["positions"]
        raw={"schema":"skvq.native-root-input-raw/v1","source_ref":self.source,
          "rank":s.w.rank,"identity":s.identity,"sample_id":s.active,
          "input_ids":describe(ids),"inputs_embeds":describe(embeds),"positions":describe(positions),
          "intermediate_tensors":describe(a["intermediate_tensors"]),
          "pending_original_embedding":self.pending is not None,"runtime_sources":self.origins}
        raw_ref=self.publish(self.path("ROOT_RAW_BEFORE"),raw)
        C.require(a["intermediate_tensors"]is None,"actual PP1 root intermediate must be None")
        C.require(self.pending is not None,"source-qualified original text embedding required before root")
        record,original,returned=self.pending
        native=self.runner.inputs_embeds.gpu[:4096];root_view=view(embeds);buffer_view=view(native)
        C.require(root_view==buffer_view and root_view["shape"]==returned["shape"]and
          root_view["dtype"]==returned["dtype"],"root exact native embeddings buffer typed alias")
        torch=sys.modules["torch"]
        C.require(torch.equal(embeds,original)is True,"root bitwise equals unmodified original text embedding return")
        requires_ids=self.s.model.requires_raw_input_tokens
        C.require(type(requires_ids)is bool,"original model raw-token policy bool")
        if requires_ids:
            C.require(view(ids)==view(self.runner.input_ids.gpu[:4096])and id_values(ids)==record["actual_token_ids"],
              "native requires-raw-ID policy same original token buffer")
        else:C.require(ids is None,"original native no-raw-token policy; no foreign root IDs")
        pos=positions.detach().cpu().tolist()
        C.require(pos==list(range(4096))or pos==[list(range(4096))]*3,
          "actual text positions zero..4095; no prefix/pad/media")
        value={"schema":SCHEMA,"source_ref":self.source,"rank":s.w.rank,"identity":s.identity,
          "sample_id":s.active,"input_ref":s.input_ref,"runtime_sources":self.origins,
          "embed_raw_ref":record["raw_ref"],"root_raw_ref":raw_ref,
          "actual_token_ids":record["actual_token_ids"],"token_ids_sha256":record["token_ids_sha256"],
          "request_id":record["request_id"],
          "actual_request_prompt_token_ids":record["actual_request_prompt_token_ids"],
          "actual_mm_mask":record["actual_mm_mask"],"request_checks":{k:record[k]for k in
            ("prompt_embeds_is_none","mm_features_empty","mm_embeddings_empty","all4096_mm_mask_false","num_computed_tokens")},
          "original_embedding_return":returned,"root_embedding_view":root_view,
          "runner_embedding_buffer_view":buffer_view,"original_embedding_return_bitwise_equal":True,
          "requires_raw_input_tokens":requires_ids,"root_input_ids_is_none":ids is None,
          "actual_positions":pos,"actual_positions_zero_to4095":True,
          "retained_original_tensor_no_clone":True,"capture_ready":False,"model_ready":False}
        self.current_ref=self.publish(self.path("TEXT_INPUT_PROVENANCE"),value)
        return self.current_ref
    def release(self):
        self.pending=None;self.current_ref=None

