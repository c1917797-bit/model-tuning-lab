"""DEFAULT-OFF owned calibration taps. No imports of Torch/vLLM on import.
MAIN alone invokes RPC functions in its already admitted real TP4 model workers.
"""
import inspect,json,os,sys,traceback,types
from pathlib import Path
from io_contract import *
from tp_provider import module_origin,RankProvider
from post_rope_live import OUTER_NAMES,CaptureProvider,receiver
from raw_sink import RawSink
HERE=Path(__file__).resolve().parent
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
PINS=json.loads((BASE/"source_pins.json").read_text())
def deployed_sources():
    out={}
    for p in PINS["sources"]:
        m=sys.modules.get(p["module"])
        r=module_origin(m,p["module"],p["sha256"])
        if p["runtime"] is not None:require(Path(r["path"]).resolve()==Path(p["runtime"]),"exact runtime source mapping")
        out[p["module"]]=r
    return out
def actual_worker(target):
    wb=sys.modules.get("vllm.v1.worker.worker_base");nw=sys.modules.get("vllm_ascend.worker.worker")
    # Actual copied source runtime is worker.py or npu_worker.py; origin comes
    # from source_pins rather than spelling a guessed class module.
    require(wb is not None,"actual worker_base loaded")
    if type(target) is wb.WorkerWrapperBase:target=target.worker
    require(type(target).__name__=="NPUWorker" and type(target).__module__ in
      ("vllm_ascend.worker.worker","vllm_ascend.worker.npu_worker"),"actual NPUWorker receiver")
    require(inspect.getsourcefile(type(target))==sys.modules[type(target).__module__].__file__,"actual worker class source")
    require(sha_file(inspect.getsourcefile(type(target)))=="c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3","copied actual NPUWorker bytes")
    return target
def check_config(w):
    c=w.vllm_config;p=c.parallel_config;s=c.scheduler_config;m=c.model_config
    require(p.tensor_parallel_size==4 and p.pipeline_parallel_size==1 and p.data_parallel_size==1 and
      p.prefill_context_parallel_size==1 and p.decode_context_parallel_size==1,"actual TP4/PP1/DP1/PCP1/DCP1")
    require(c.speculative_config is None and c.kv_transfer_config is None and c.lora_config is None,"no speculative/transfer/LoRA")
    require(m.enforce_eager is True and c.compilation_config.mode.name=="NONE","owned eager uncompiled capture")
    require(m.model==MODEL and m.max_model_len==4097 and str(m.dtype) in ("torch.float16","torch.bfloat16"),"actual frozen A16 model protocol")
    require(c.cache_config.enable_prefix_caching is False and c.cache_config.cache_dtype=="auto","native dense cache/no prefix")
    require(s.max_num_seqs==1 and s.max_num_batched_tokens==4096 and s.enable_chunked_prefill is True,"chunking enabled but actual one complete4096 fresh request required")
    require(c.model_config.hf_text_config.num_hidden_layers==64 and
      c.model_config.hf_text_config.num_attention_heads==24 and
      c.model_config.hf_text_config.num_key_value_heads==4 and
      c.model_config.hf_text_config.head_dim==256,"actual Qwen FA geometry")
    for name,sha in HASHES.items():require(sha_file(Path(MODEL)/name)==sha,"actual frozen metadata")
    return c
def registry_for(w):
    q35=sys.modules["vllm.model_executor.models.qwen3_5"];nxt=sys.modules["vllm.model_executor.models.qwen3_next"]
    patch=sys.modules["vllm_ascend.patch.worker.patch_qwen3_5"]
    model=w.get_model()
    require(type(model) is q35.Qwen3_5ForConditionalGeneration and w.model_runner.get_model() is model,
      "real source-bound model ownership")
    require(type(model.language_model) is q35.Qwen3_5ForCausalLM and
      type(model.language_model.model) is q35.Qwen3_5Model,"actual Qwen nested text model")
    text=model.language_model.model
    require(text.start_layer==0 and text.end_layer==64 and len(text.layers)==64 and
      model.language_model.vllm_config is w.vllm_config,"actual all64 current worker layers")
    registry={};linear=[]
    for i,layer in enumerate(text.layers):
        require(type(layer) is q35.Qwen3_5DecoderLayer and layer.layer_idx==i and
          layer.forward.__func__ is patch.AscendQwen3_5DecoderLayer.forward,"actual copied decoder receiver")
        if i%4==3:
            require(layer.layer_type=="full_attention" and type(layer.self_attn) is nxt.Qwen3NextAttention,"exact16 actual full attention members")
            outer=layer.self_attn;child=outer.attn
            receiver(outer,child)
            require(child.layer_name.endswith(".layers."+str(i)+".self_attn.attn"),"actual constructor-derived child prefix")
            registry["model.layers."+str(i)+".self_attn"]=(outer,child)
        else:
            require(layer.layer_type=="linear_attention" and not hasattr(layer,"self_attn"),"48 GDN not FA tap targets")
            linear.append((layer.linear_attn,id(layer.linear_attn),layer.linear_attn.forward.__func__))
    require(set(registry)==set(OUTER_NAMES) and len({id(c.impl) for _,c in registry.values()})==16,"disjoint sixteen real backend instances")
    return model,registry,linear
class Session:
    def __init__(self,w,input_path,root):
        require(os.environ.get("QWEN36_SKVQ_TP4_CAPTURE_ENABLE")=="1","explicit opt-in")
        self.w=w;self.input_path=str(Path(input_path));self.inputs=load_inputs(input_path);self.input_ref=reference(input_path)
        self.sources=deployed_sources();check_config(w)
        self.model,self.registry,self.linear=registry_for(w)
        self.provider=CaptureProvider(self.registry);self.rank=RankProvider();self.identity=self.rank()
        require(w.rank==self.identity["public_TP_rank"],"actual worker/group rank equality")
        self.sink=RawSink(root,w.rank);self.active=None;self.next_id=0;self.seen=set()
        self.poisoned=False;self.closed=False;self.in_forward=False;self.patches=[];self.primary=None;self.secondary=[]
        self.original_root=self.model.forward
        require(self.original_root.__func__ is sys.modules["vllm.model_executor.models.qwen3_5"].Qwen3_5ForConditionalGeneration.forward,"unmodified root actual forward")
        try:self.install()
        except BaseException:
            self.restore();raise
    def bind(self,obj,name,fn):
        require(name not in obj.__dict__,"no overlapping instance-owned patch")
        original=getattr(obj,name);bound=types.MethodType(fn,obj)
        obj.__dict__[name]=bound;self.patches.append((obj,name,bound,original))
    def install(self):
        session=self
        for logical,(outer,child) in self.registry.items():
            original=child.impl.reshape_and_cache
            backend=sys.modules["vllm_ascend.attention.attention_v1"]
            require(original.__func__ is backend.AscendAttentionBackendImpl.reshape_and_cache,"original source-bound cache-write seam")
            def make(name,old):
                def tap(impl,query,key,value,kv_cache,attn_metadata,output):
                    require(session.in_forward and session.active is not None and not session.poisoned,"owned active real input before any cache write")
                    require(name not in session.seen,"exact one capture per active FA")
                    proof=session.provider(name,query,key,value,attn_metadata)
                    proof["actual_input"]={"input_ref":session.input_ref,"sample_id":session.active,
                      "token_ids_sha256":session.inputs["samples"][session.active]["token_ids_sha256"],
                      "actual_forward_tokens_equals_frozen_sample":True,"actual_positions_zero_to4095":True,
                      "runtime_child_layer_name":session.registry[name][1].layer_name}
                    proof["runtime_source_bindings"]=session.sources
                    session.sink.capture(session.active,name,proof,query,key,value)
                    session.seen.add(name)
                    return old(query,key,value,kv_cache,attn_metadata,output)
                return tap
            self.bind(child.impl,"reshape_and_cache",make(logical,original))
        def forward(model,*args,**kwargs):
            require(not session.poisoned and not session.closed and session.active is not None and not session.in_forward,"only armed owned full request; no nested/unarmed model use")
            session.in_forward=True
            try:
                bound=inspect.signature(session.original_root).bind(*args,**kwargs);bound.apply_defaults()
                ids=bound.arguments["input_ids"];positions=bound.arguments["positions"]
                require(bound.arguments["intermediate_tensors"] is None and bound.arguments["inputs_embeds"] is None,"real token-ID text path only; no PP/embedding/media substitution")
                expected=sample_ids(session.input_path,session.active)
                require(tuple(ids.shape)==(4096,) and ids.device.type=="npu" and ids.detach().cpu().tolist()==expected,"actual root input IDs equal full frozen TRAIN window")
                pos=positions.detach().cpu().tolist()
                require(pos==list(range(4096)) or pos==[list(range(4096))]*3,"actual text RoPE positions, no prefix/pad/media")
                session.context_guard()
                require(deployed_sources()==session.sources,"runtime source stability")
                session.seen=set()
                result=session.original_root(*args,**kwargs)
                require(session.seen==set(OUTER_NAMES),"every one of16 actualFA before-cache capture executed")
                session.active=None;session.next_id+=1
                return result
            except BaseException as e:
                session.poisoned=True;session.primary={"type":type(e).__name__,"message":str(e),"traceback":traceback.format_exc()}
                secondary=session.restore()
                record_failure(session.sink.path/"SESSION_FAILED.json",{"status":"CAPTURE_SESSION_FAILED",
                  "primary":session.primary,"secondary":secondary,"sample_id":session.active,"events":session.sink.events},e)
                raise
            finally:session.in_forward=False
        self.bind(self.model,"forward",forward)
    def context_guard(self):
        fc=sys.modules["vllm.forward_context"].get_forward_context()
        extra=sys.modules["vllm_ascend.ascend_forward_context"]._EXTRA_CTX
        require(fc.cudagraph_runtime_mode.name=="NONE" and fc.dp_metadata is None and fc.ubatch_slices is None,
          "actual eager no microbatch/data split")
        for k in ("capturing","in_profile_run","is_draft_model","flash_comm_v1_enabled","flashcomm_v2_enabled"):
            require(getattr(extra,k) is False,"actual context must expose false: "+k)
        require(extra.num_tokens==4096 and extra.pad_size==0,"actual full unpadded eager tokens")
        require(type(fc.attn_metadata) is dict,"actual v1 metadata map")
        for logical,(_,child) in self.registry.items():
            require(fc.no_compile_layers.get(child.layer_name) is child and child.layer_name in fc.attn_metadata,"actual source-bound static layer identity")
            md=fc.attn_metadata[child.layer_name]
            require(md.attn_state.name=="PrefillNoCache" and md.num_actual_tokens==4096 and md.num_prefills==1 and
              md.num_decodes==0 and md.num_decode_tokens==0 and md.seq_lens_list==[4096] and
              md.actual_seq_lengths_q==[4096],"all16 real fresh unchunked metadata before first model compute")
    def arm(self,i):
        require(not self.poisoned and not self.closed and self.active is None and i==self.next_id and i<256,"strict full256 once-only scheduler")
        require(reference(self.input_path)==self.input_ref,"frozen full input manifest unchanged")
        self.rank();check_config(self.w);self.active=i
        return {"rank":self.w.rank,"sample_id":i,"input_token_sha256":self.inputs["samples"][i]["token_ids_sha256"]}
    def restore(self):
        secondary=[]
        for obj,name,bound,original in reversed(self.patches):
            try:
                require(obj.__dict__.get(name) is bound,"exact owned patch retained; do not overwrite foreign mutation")
                del obj.__dict__[name]
                restored=getattr(obj,name)
                require(restored.__func__ is original.__func__ and restored.__self__ is original.__self__,"original binding restored")
            except BaseException as e:secondary.append({"hook":name,"type":type(e).__name__,"message":str(e)})
        self.patches=[];self.closed=True;self.secondary=secondary
        for obj,oid,fn in self.linear:
            if id(obj)!=oid or obj.forward.__func__ is not fn:secondary.append({"hook":"GDN","message":"untouched GDN identity changed"})
        return secondary
    def finish(self):
        require(not self.poisoned and self.next_id==256 and self.active is None,"all256 full forward calls")
        self.rank();require(deployed_sources()==self.sources,"final actual source stability")
        secondary=self.restore();require(not secondary,"owned exact restoration failures")
        return self.sink.finish(self.identity,{"all_owned_instance_hooks_restored":True,"GDN48_untouched":True,"secondary":secondary})
def install_rpc(target,input_path,root):
    w=actual_worker(target);require(not hasattr(w,"_skvq_capture_session"),"single owner session")
    w._skvq_capture_session=Session(w,input_path,root)
    return {"rank":w.rank,"installed":True,"sources":w._skvq_capture_session.sources,"identity":w._skvq_capture_session.identity}
def arm_rpc(target,i):return actual_worker(target)._skvq_capture_session.arm(i)
def finish_rpc(target):return actual_worker(target)._skvq_capture_session.finish()
def restore_rpc(target):
    w=actual_worker(target);s=getattr(w,"_skvq_capture_session",None)
    if s is None:return {"rank":w.rank,"no_session":True,"secondary":[]}
    errors=s.restore() if not s.closed else s.secondary
    return {"rank":w.rank,"closed":s.closed,"primary":s.primary,"secondary":errors,"events":len(s.sink.events)}
