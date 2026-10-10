"""Actual source/receiver/caller-frame + alias evidence. No automatic patch/install/import.
Invoke only from an explicit owned pre-cache capture tap in MAIN's admitted eager run.
"""
import inspect,sys
from pathlib import Path
from tp_provider_current import require,file_sha,module_origin,RankProvider
PATCH_MODULE="vllm_ascend.patch.worker.patch_qwen3_5"
PATCH_RUNTIME="/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py"
PATCH_SHA="21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3"
ATTENTION_MODULE="vllm.model_executor.layers.attention.attention"
ATTENTION_SHA="06f49836a73d058c6d38f826bc6c794c3b7ae9751d12d71dfff9e5c2dbdbcd28"
BACKEND_MODULE="vllm_ascend.attention.attention_v1"
BACKEND_SHA="80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
OUTER_NAMES=tuple("model.layers."+str(i)+".self_attn" for i in range(3,64,4))
def tensor_description(t):
    torch=sys.modules.get("torch");require(torch is not None and isinstance(t,torch.Tensor),"actual already-loaded Torch tensor")
    storage=t.untyped_storage()
    return {"shape":list(t.shape),"stride":list(t.stride()),"dtype":str(t.dtype),"device":str(t.device),
            "storage_data_ptr":storage.data_ptr(),"storage_nbytes":storage.nbytes(),
            "storage_offset_elements":t.storage_offset(),"element_size":t.element_size(),
            "numel":t.numel(),"data_ptr":t.data_ptr()}
def receiver(outer,child):
    patch=sys.modules.get(PATCH_MODULE);origin=module_origin(patch,PATCH_MODULE,PATCH_SHA)
    require(Path(origin["path"]).resolve()==Path(PATCH_RUNTIME),"exact deployed patch source mapping")
    nxt=sys.modules.get("vllm.model_executor.models.qwen3_next")
    q35=sys.modules.get("vllm.model_executor.models.qwen3_5")
    require(nxt is not None and q35 is not None,"actual loaded Qwen model receivers")
    donor=patch.AscendQwen3NextAttention.forward
    require(inspect.isfunction(donor) and inspect.getsourcefile(donor)==origin["path"] and
            nxt.Qwen3NextAttention.forward is donor and isinstance(outer,nxt.Qwen3NextAttention) and
            inspect.ismethod(outer.forward) and outer.forward.__self__ is outer and
            outer.forward.__func__ is donor,"actual copied donor function is live receiver")
    alias=getattr(q35,"Qwen3NextAttention",None)
    require(alias is None or alias is nxt.Qwen3NextAttention,"exposed Qwen3_5 receiver alias must match")
    require(outer.attn is child and "qwen3_5" in outer.config.model_type and
            outer.num_heads==6 and outer.num_kv_heads==1 and outer.head_dim==256,
            "actual Qwen3_5 TP4 attention object relationship")
    attn=sys.modules.get(ATTENTION_MODULE);ao=module_origin(attn,ATTENTION_MODULE,ATTENTION_SHA)
    backend=sys.modules.get(BACKEND_MODULE);bo=module_origin(backend,BACKEND_MODULE,BACKEND_SHA)
    require(type(child) is attn.Attention and inspect.ismethod(child.forward) and
            child.forward.__func__ is attn.Attention.forward and type(child.impl) is backend.AscendAttentionBackendImpl,
            "actual unmodified general Attention and deployed Ascend FA")
    require(child.num_heads==6 and child.num_kv_heads==1 and child.head_size==256 and
            child.head_size_v==256 and child.query_quant is None and child.calculate_kv_scales is False and
            child.sliding_window is None and child.kv_sharing_target_layer_name is None and
            child.attn_backend.forward_includes_kv_cache_update is True and
            child.impl.enable_c8_quant is False,"A16 dense include-write capture only")
    return donor,{"patch":origin,"attention":ao,"backend":bo,
                  "qwen3_5_exposed_alias_is_original":alias is nxt.Qwen3NextAttention,
                  "actual_instance_forward_is_donor":outer.forward.__func__ is donor,
                  "outer_class":type(outer).__module__+"."+type(outer).__qualname__,
                  "child_attention_layer_name":child.layer_name}
def actual_call_proof(outer_name,outer,child,query,key,value):
    require(outer_name in OUTER_NAMES,"one exact actual model full-attention object")
    donor,sources=receiver(outer,child)
    frame=inspect.currentframe();found=None
    try:
        frame=frame.f_back
        while frame is not None:
            if frame.f_code is donor.__code__ and frame.f_locals.get("self") is outer:
                require(found is None,"no nested same receiver frame")
                found=frame
            frame=frame.f_back
        require(found is not None and found.f_lineno==81,"actual live self.attn(q,k,v) frame after fused norm/MRoPE")
        raw={s:found.f_locals[s] for s in ("q","k","v")}
        descriptors={};observed={"q":query,"k":key,"v":value}
        for side,heads in (("q",6),("k",1),("v",1)):
            a=tensor_description(raw[side]);b=tensor_description(observed[side])
            require(b["shape"]==[4096,heads,256] and a["numel"]==b["numel"]==4096*heads*256 and
                    a["dtype"]==b["dtype"] and a["device"]==b["device"] and
                    a["data_ptr"]==b["data_ptr"] and
                    a["storage_data_ptr"]==b["storage_data_ptr"] and
                    a["storage_offset_elements"]==b["storage_offset_elements"],
                    "actual Qwen output is native Attention.view input, not substituted:"+side)
            descriptors[side]={"qwen_live_output":a,"pre_cache_input":b,"live_storage_alias_observed":True}
        require(str(query.dtype) in ("torch.float16","torch.bfloat16"),"actual A16 snapshots")
        return {"schema":"SKVQ_POSTROPE_ACTUAL_CALL_V1","outer_name":outer_name,
                "runtime_sources":sources,"caller_line":81,"actual_receiver_function_bound":True,
                "capture_stage_source_and_frame_observed":"post-qk-norm-rope",
                "live_tensors":descriptors,"snapshot_clones_are_not_live_alias_proof":True,
                "raw_values_not_yet_persisted":True,"physical_card_lease_pending":True,
                "actual_token_input_binding_pending":True,"calibration_pending":True,
                "native_ready":False,"model_ready":False}
    finally:
        del frame
        if found is not None:del found
class CaptureProvider:
    """Composition callback from actual owned reshape_and_cache.before-original.
    No owned wrapper installation here: MAIN must first bind actual scheduler
    token input, eager/no-prefix/lease guard and raw snapshot sink sources.
    """
    def __init__(self,registry):
        require(type(registry) is dict and set(registry)==set(OUTER_NAMES),"all16 actual outer/child object pairs")
        self.registry=registry;self.rank=RankProvider();self.poisoned=False
    def __call__(self,outer_name,query,key,value,metadata):
        require(not self.poisoned,"latched capture provider failure")
        try:
            rank=self.rank()
            require(metadata is not None and metadata.attn_state.name=="PrefillNoCache" and
                    metadata.num_actual_tokens==4096 and metadata.num_prefills==1 and
                    metadata.num_decodes==0 and metadata.num_decode_tokens==0 and
                    metadata.seq_lens_list==[4096] and metadata.actual_seq_lengths_q==[4096],
                    "one real full fresh4096 prefill, not graph/chunk/decode/prefix dummy")
            outer,child=self.registry[outer_name]
            call=actual_call_proof(outer_name,outer,child,query,key,value)
            return {"schema":"SKVQ_LIVE_CAPTURE_PROVIDER_COMPONENTS_V1","rank":rank,"post_rope":call,
                    "token_input_provider_pending":True,"raw_snapshot_sink_pending":True,
                    "native_ready":False,"model_ready":False}
        except BaseException:
            self.poisoned=True;raise

