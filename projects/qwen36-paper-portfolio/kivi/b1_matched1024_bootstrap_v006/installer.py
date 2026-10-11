"""DEFAULT-OFF per-instance Qwen eager packed-output installer.
No controller, model authority, allocation replacement or Python-on-replay shim.
Existing full-pool owner/layout/zeroer and compiled-numerical qualification are required.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path
import types
import time

MEMORY_SHA="b489a7dc22b77d5f50b3329801fe64cb4c7f908cf2abaea75c0efbd7f4c436c1"

FLAG="QWEN36_KIVI_PACKED_QKAV_QWEN_INSTALLER"
PROVENANCE_SHA="a93894bbbd0d73b72c9bc43664a121106525fa5a27bca0d361aff9a2ba00def7"
WRITER_SHA="051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b"
RUNNER_SHA="94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
PUBLIC_SHA="06f49836a73d058c6d38f826bc6c794c3b7ae9751d12d71dfff9e5c2dbdbcd28"
QWEN_SHA="21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3"
QWEN_BASE_SHA="8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae"
IMPL_SHA="80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"
CONTEXT_SHA="1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5"
BLOCK_SHA="8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
BATCH_FLAG="QWEN36_KIVI_PACKED_QKAV_OWNED_SEAM"
KERNEL_FLAG="QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE"
BOOK_SHA="6488a5ca3fb6f606bbb82bf86e226fc30741e8dc7288ff03e3e5e8b71cec07c7"
SPANS_SHA="77b678af5eea524c59405d98a3681415810e2e77b7f8cf9cde9fd241b28d4157"
INGRESS_SHA="71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99"
PRODUCER_SHA="1687f25252dc5ca94c69b666e1307f5721e83a81da74cccfa4c7e25a3ed2e726"
TIMING_FLAG="QWEN36_KIVI_OBSERVER_OFF_TIMING"
FORMAL_SHA="d9e8dd2fa2656c79616e3576a2e58b3ce82a113f6c5fd55e4b41e504ae246841"
CALLBACK_SHA="291eb417eaecf97b4199072ae62012180c18af44b5a5d2c5c92c1060e3d38f5e"
CRITICAL_SHA={"kernel":"ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a",
    "metadata":"e1a07bf5cac73bc689130e2a68ba54297e11f2513610d1e2003ba4bb545df539",
    "lifecycle":"20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533",
    "callback":CALLBACK_SHA}

def need(v,m):
    if not v: raise ValueError(m)

def raw_decode_capture(capture_raw,first_decode_only,positions):
    """Explicit diagnostic sampling, never numerical coverage or timing authority."""
    need(type(capture_raw) is bool and type(first_decode_only) is bool and
         (not first_decode_only or capture_raw),"typed explicit diagnostic capture policy")
    if not capture_raw:return False
    if not first_decode_only:return True # preserve original full-raw behavior
    need(type(positions) is tuple and 1<=len(positions)<=16 and
         all(type(p) is int and 32768<=p<33792 for p in positions),"actual formal decode positions")
    selected=any(p==32768 for p in positions)
    need(not selected or all(p==32768 for p in positions),
         "first-decode diagnostic requires aligned actual batch; never silently omit a new owner")
    return selected

def start_buffer_alias(torch,tensor,base,n,device):
    need(tensor.device.type==base.device.type==device and tensor.device==base.device
         and tensor.dtype==base.dtype==torch.int32 and tensor.ndim==base.ndim==1
         and tensor.shape[0]>=n and base.shape[0]>=n and tensor.is_contiguous() and base.is_contiguous()
         and tensor.stride()==base.stride()==(1,)
         and tensor.untyped_storage().data_ptr()==base.untyped_storage().data_ptr()
         and tensor.untyped_storage().nbytes()==base.untyped_storage().nbytes()
         and tensor.storage_offset()==base.storage_offset() and tensor.data_ptr()==base.data_ptr(),
         "actual common query-start buffer alias, not copied/shifted metadata")

def timing_partition(torch,runner,meta,frame,proof,callback):
    """Real source-pinned builder output, not a guessed runner GPU alias.
    80005a builder makes a separate H2D query-start tensor from actual CPU starts.
    Its exact return object/tensor is retained only for this frame, without copies.
    """
    n=len(frame["req_ids"])+1; cpu=runner.query_start_loc.cpu
    need(type(proof) is dict and proof["epoch"]==frame["epoch"] and proof["meta"] is meta
         and proof["query"] is meta.query_start_loc and proof["starts"]==frame["query_start_loc"],
         "exact current-frame source-bound metadata builder return")
    need(meta.causal is True and meta.num_actual_tokens==frame["total_tokens"]
         and type(meta.actual_seq_lengths_q) is list and meta.actual_seq_lengths_q==frame["query_start_loc"][1:],
         "actual builder whole token partition")
    need(cpu.device.type=="cpu" and cpu.dtype==torch.int32 and cpu.ndim==1
         and cpu[:n].tolist()==frame["query_start_loc"]
         and [int(x) for x in runner.query_start_loc.np[:n].tolist()]==frame["query_start_loc"],
         "actual published CPU partition from source-bound prepare")
    layer=meta.query_start_loc
    need(layer.device.type=="npu" and layer.dtype==torch.int32 and layer.ndim==1
         and tuple(layer.shape)==(n,) and layer.is_contiguous() and layer.stride()==(1,)
         and callback.scalar_tensor(layer)==proof["query_descriptor"],
         "same actual builder NPU query-start tensor layout")

def timing_cached_ingress(bindings,scheduler,scheduler_type,ident,rank):
    need(type(scheduler) is scheduler_type and type(scheduler).__module__=="vllm.v1.core.sched.output"
         and type(scheduler).__name__=="SchedulerOutput" and
         bindings.owner["rank_bindings"][str(rank)]==ident,"unchanged source-qualified scheduler/owner")
    need(not scheduler.scheduled_new_reqs and not scheduler.finished_req_ids
         and not scheduler.scheduled_spec_decode_tokens and not scheduler.preempted_req_ids
         and not scheduler.scheduled_cached_reqs.resumed_req_ids
         and set(scheduler.scheduled_cached_reqs.req_ids)<=bindings.seen,
         "no unseen cached owner/spec/resume/native lifecycle bypass")
    return []

def timing_layout(runner,event,contexts,callback):
    # Current thin mode deliberately supports only the separately qualified absent
    # zeroer/no-spec no-op. An initialized/appearing zeroer needs a later reviewed mode.
    need(not hasattr(runner,"_kv_block_zeroer") and runner.speculative_config is None,
         "timing supports actual source-qualified absent zeroer only")
    native=[]; compact=[]
    def flatten(value):
        if type(value) in (tuple,list):
            return [tensor for item in value for tensor in flatten(item)]
        need(callable(getattr(value,"untyped_storage",None)),"real initialized native tensor leaf")
        return [value]
    need(len(event["layers"])==64 and len(contexts)==16,"all64 native/all16 compact layout stamp")
    for name,row in sorted(event["layers"].items()):
        value=runner.compilation_config.static_forward_context[name].kv_cache
        views=[value[0],value[1]] if row["kind"]=="FA" else flatten(value)
        descriptors=[callback.scalar_tensor(tensor) for tensor in views]
        need(len(descriptors)==len(row["views"]) and
             all(all(desc[key]==expected[key] for key in desc)
                 for desc,expected in zip(descriptors,row["views"])),
             "all64 actual native typed views still match qualified event")
        native.append((name,descriptors))
    for name,ctx in sorted(contexts.items()):
        pool=ctx["arena"].pool
        counters={field:pool[field] for field in ("allocated_bytes","dense_shadow_bytes")}
        need(all(type(value) is int for value in counters.values())
             and counters["allocated_bytes"]==ctx["arena"].pool_bytes>0
             and counters["dense_shadow_bytes"]==0,"actual compact accounting integers, no dense shadow")
        fields={key:value for key,value in pool.items() if key not in counters}
        need(set(fields)=={"key_codes","key_scales","key_minima","value_codes","value_scales",
             "value_minima","key_residual","value_residual","shifts"},"all nine actual compact tensors")
        compact.append((name,id(pool),counters,[(field,callback.scalar_tensor(value)) for field,value in sorted(fields.items())]))
    return native,compact

def callable_pin(fn,sha):
    raw=inspect.unwrap(getattr(fn,"__func__",fn))
    p=Path(inspect.getfile(raw))
    need(p.is_absolute() and not p.is_symlink() and p.resolve()==p
         and hashlib.sha256(p.read_bytes()).hexdigest()==sha, "actual loaded callable whole-file source")
    return str(p)

def allocator_observer(torch,rank,publish,enabled=True):
    """Diagnostic CPU counters only. No synchronization/reset/cache mutation.
    Counters cover the caching allocator, not physical HBM or an admission proof.
    """
    need(type(enabled) is bool,"explicit allocator diagnostic switch")
    if not enabled:return lambda label:None
    need(type(rank) is int and rank in range(4) and torch.npu.is_initialized()
         and torch.npu.current_device()==rank,"initialized actual rank before allocator observation")
    fn=torch.npu.memory_stats
    source=callable_pin(fn,MEMORY_SHA)
    nested=getattr(fn,"__globals__",{}).get("memory_stats_as_nested_dict")
    need(callable(nested),"actual allocator Python wrapper")
    need(callable_pin(nested,MEMORY_SHA)==source,"same source-qualified nested allocator wrapper")
    keys=("allocated_bytes.all.current","allocated_bytes.all.peak",
          "reserved_bytes.all.current","reserved_bytes.all.peak")
    def snapshot(label):
        need(type(label) is str and label and torch.npu.current_device()==rank,
             "actual allocator diagnostic stage/rank")
        values=fn(device=rank)
        need(all(key in values and type(values[key]) is int and values[key]>=0 for key in keys),
             "actual nonnegative allocator counters; missing is not zero")
        row={"schema":"kivi.actual-allocator-observation/v1","rank":rank,"stage":label,
             "time_ns":time.time_ns(),"source_sha256":MEMORY_SHA,"runtime_path":source,
             "bytes":{key:values[key] for key in keys},"physical_hbm":False,
             "synchronized":False,"peaks_reset":False,"diagnostic_only":True,
             "model_ready":False,"run_authority":False}
        return publish(label,row)
    return snapshot

def bound(ref,maximum=8*1024**2):
    need(type(ref) is dict and set(ref)=={"path","bytes","sha256"}, "exact3 actual immutable Ref")
    p=Path(ref["path"])
    need(p.is_absolute() and not p.is_symlink() and p.resolve()==p and type(ref["bytes"]) is int
         and 0<ref["bytes"]<=maximum and type(ref["sha256"]) is str and len(ref["sha256"])==64,
         "absolute bounded Ref")
    b=p.read_bytes()
    need(len(b)==ref["bytes"] and hashlib.sha256(b).hexdigest()==ref["sha256"], "actual Ref bytes/SHA")
    return b

def install(runner, *, torch, forward_context, capture, callback, formal, book_module,
            producer_module, owner, owner_ref, event, event_ref, layer_contexts,
            qualify, identity, rank, publish, writer_guard, ingress_bindings=None, capture_raw=False, raw_root=None,
            provenance=None, first_decode_capture_only=False, diagnostic=True, model_qualify=None):
    if os.environ.get(FLAG)!="1": return None
    need(os.environ.get(BATCH_FLAG)=="1" and os.environ.get(KERNEL_FLAG)=="1", "explicit shared critical algorithm opt-in")
    need(callable(qualify) and callable(writer_guard) and callable(identity) and callable(publish)
         and type(rank) is int and rank in range(4) and type(capture_raw) is bool, "real supplied owner hooks")
    need(type(first_decode_capture_only) is bool and (not first_decode_capture_only or capture_raw),
         "first-decode diagnostic requires explicit raw capture; never a performance mode")
    need(type(diagnostic) is bool and (diagnostic or
         (os.environ.get(TIMING_FLAG)=="1" and capture_raw is False and
          first_decode_capture_only is False and callable(model_qualify))),
         "explicit timing mode requires raw OFF and independent real model consumer")
    # Independent actual compiled/numeric/layout/resource authority is supplied, never made here.
    callable_pin(book_module.Book,BOOK_SHA); callable_pin(producer_module.PackedBatch,PRODUCER_SHA)
    callable_pin(formal.gather_native,FORMAL_SHA); callable_pin(callback.scalar_tensor,CALLBACK_SHA)
    callable_pin(getattr(writer_guard,"func",writer_guard),SPANS_SHA)
    need(os.environ.get("QWEN36_KIVI_ACTUAL_INGRESS_BINDING")=="1" and ingress_bindings is not None,
         "actual assignment/ingress adapter is explicit opt-in, never future-ID assertion")
    callable_pin(type(ingress_bindings),INGRESS_SHA)
    if capture_raw:
        need(provenance is not None,"original full prefill provenance module required for raw model capture")
        callable_pin(provenance.capture_tiles,PROVENANCE_SHA)
        callable_pin(producer_module.RawSink,PRODUCER_SHA)
    qualify()
    ident=identity()
    need(json.loads(bound(owner_ref))==owner and json.loads(bound(event_ref))==event, "whole immutable owner/layout")
    need(owner["schema"]=="kivi.actual-packed-installer-owner/v1" and owner["image_id"]==IMAGE
         and owner["rank_bindings"][str(rank)]==ident and event["rank"]==rank and event["identity"]==ident
         and type(owner["container_id"]) is str and len(owner["container_id"])==64
         and owner["container_id"] in ident["cgroup"] and owner["physical_devices"]==[4,5,6,7]
         and owner["logical_to_physical"]=={"0":4,"1":5,"2":6,"3":7}, "actual owned TP4 identity/mapping input")
    for key in ("actual_assignment_protocol_ref","capacity_receipt_ref","layout_consumer_ref","zeroer_writer_receipt_ref"):
        bound(owner[key])
    need(runner.model_config.enforce_eager is True and not runner.use_cp
         and runner.pcp_size==runner.dcp_size==1 and not runner.use_async_scheduling
         and runner.speculative_config is None and not runner.use_compress and not runner.use_sparse
         and runner.parallel_config.data_parallel_size==runner.parallel_config.pipeline_parallel_size==1
         and not runner.parallel_config.enable_dbo and runner.cache_config.enable_prefix_caching is False,
         "eager/no spec/CP/async/prefix sharing/recompute only, not FULL support")
    need(type(runner.scheduler_config.max_num_batched_tokens) is int and
         1<=runner.scheduler_config.max_num_batched_tokens<=32768,
         "bounded actual chunked-prefill journal; full context is not one unbounded frame")
    for name in ("_prepare_inputs","_update_states","execute_model","_dummy_run","_build_attention_metadata"):
        callable_pin(getattr(runner,name),RUNNER_SHA)
    callable_pin(type(runner),RUNNER_SHA)
    callable_pin(forward_context.get_forward_context,CONTEXT_SHA)
    need(set(layer_contexts)=={name for name,x in event["layers"].items() if x["kind"]=="FA"}
         and len(layer_contexts)==16 and len(event["layers"])==64, "all64 layout/all16 actual FA")
    ingress_bindings.matches_install_owner(owner,rank,ident)
    need(not runner.requests and runner.input_batch.num_reqs==0,"install before first real model request")
    book=book_module.Book(owner["declared_passed_request_ids"],owner["prompt_lengths"],1024)
    need(all(name not in vars(runner) for name in ("_prepare_inputs","_update_states","execute_model","_dummy_run","_build_attention_metadata")),
         "no existing per-instance runner hook to stack or overwrite")
    members={}
    for member in runner.model.modules():
        attn=getattr(member,"attn",None)
        name=getattr(attn,"layer_name",None)
        if name not in layer_contexts: continue
        need(name not in members and "forward" not in vars(member) and "forward" not in vars(attn),
             "unique actual member; no stacked/foreign per-instance hook")
        callable_pin(type(member),QWEN_BASE_SHA); callable_pin(member.forward,QWEN_SHA)
        callable_pin(attn.forward,PUBLIC_SHA); callable_pin(type(attn.impl),IMPL_SHA)
        need(attn.num_heads==member.num_heads==6 and attn.num_kv_heads==member.num_kv_heads==1
             and attn.head_size==attn.head_size_v==member.head_dim==256 and attn.impl.scale==1/16
             and attn.attn_type is type(attn.attn_type).DECODER
             and attn.impl.attn_type is attn.attn_type and attn.kv_sharing_target_layer_name is None
             and attn.impl.kv_sharing_target_layer_name is None and not attn.calculate_kv_scales
             and attn.query_quant is None and attn.impl.sliding_window is None and attn.impl.sinks is None
             and attn.impl.alibi_slopes is None and attn.impl.enable_c8_quant is False
             and attn.impl.enable_hamming_sparse is False, "same source-qualified regular Qwen FA")
        ctx=layer_contexts[name]; a=ctx["arena"]; batch=ctx["packed_batch"]
        for module_name,source_sha in CRITICAL_SHA.items():
            need(batch.refs[module_name]["sha256"]==source_sha,"frozen critical producer dependency, no substitution")
            producer_module.source(batch.modules[module_name],batch.refs[module_name])
        if capture_raw:
            callable_pin(batch.modules["lifecycle"].seal_k_into,WRITER_SHA)
            callable_pin(batch.modules["lifecycle"].seal_v_into,WRITER_SHA)
        need(batch.diagnostic is diagnostic and
             (diagnostic or batch.model_qualify is model_qualify),"same explicit producer mode/real model consumer")
        need(type(a) is batch.modules["lifecycle"].CompactArena,"actual donor arena class before dense prefill")
        need(type(batch) is producer_module.PackedBatch and batch.arena is None and batch.qualify is qualify
             and batch.rank==rank and not a.active and a.bits in (2,4) and a.pool["key_residual"].shape[0]==16,
             "actual fresh source-bound persistent arena/producer; not a recreated per-token pool")
        for key in ("before_bind_ref","actual_format_ref","geometry_ref"): bound(ctx[key])
        native=attn.kv_cache
        need((type(native) in (tuple,list) and len(native)==2) or
             (hasattr(native,"shape") and native.shape[0]==2), "actual bound native K/V, not placeholder")
        key,value=native[0],native[1]
        need(capture.descriptor(key,batch.format)==event["layers"][name]["views"][0]
             and capture.descriptor(value,batch.format)==event["layers"][name]["views"][1],
             "unchanged original native cache ownership")
        need(key.shape==value.shape and key.ndim==4 and tuple(key.shape[2:])==(1,256), "real native prefill cache")
        members[name]=(member,attn,key,value)
    need(set(members)==set(layer_contexts), "complete actual FA16 membership")
    timing_builders=[]
    if not diagnostic:
        covered=set()
        for groups in runner.attn_groups:
            for group in groups:
                names=tuple(name for name in group.layer_names if name in members)
                if not names:continue
                need(set(names)==set(group.layer_names) and not covered.intersection(names),
                     "exact nonmixed FA builder membership")
                builder=group.get_metadata_builder(0)
                need("build" not in vars(builder),"no foreign per-instance metadata hook")
                callable_pin(type(builder),IMPL_SHA);callable_pin(builder.build,IMPL_SHA)
                metadata_type=inspect.getmodule(type(builder)).AscendMetadata
                callable_pin(metadata_type,IMPL_SHA)
                timing_builders.append((names,builder,metadata_type));covered.update(names)
        need(covered==set(members) and len({id(b) for _,b,_ in timing_builders})==len(timing_builders),
             "all16 unique source-bound FA metadata builders")
    # Must consume actual ALL64 typed extents plus the deployed Ascend zeroer footprint.
    # The old layout proposal alone excludes neither dense FA nor zeroer writers.
    writer_guard(runner,event,layer_contexts,owner["zeroer_writer_receipt_ref"])
    if not diagnostic:
        initial_layout=timing_layout(runner,event,layer_contexts,callback)
        for ctx in layer_contexts.values():ctx["packed_batch"].qualify_boundary()
    else:initial_layout=None
    changes=[]; state={"frame":None,"frame_ref":None,"active":None,"dummy_depth":0,"failed":False,"epoch":0,"update_seq":0,
        "scheduler_type":None,"metadata_proofs":{},"block_types":{}}
    layer_names=tuple(members)
    original_prefills={} # immutable host evidence Refs only; no retained tensor
    def method(obj,name,fn):
        existed=name in vars(obj); old=vars(obj).get(name); original=getattr(obj,name)
        replacement=types.MethodType(fn,obj); setattr(obj,name,replacement)
        changes.append((obj,name,replacement,existed,old,original))
    def send(label,body):
        need(identity()==ident,"same actual worker before publication")
        return publish("PACKED-QWEN-r%d-%s"%(rank,label),body)
    allocator_sample=allocator_observer(torch,rank,send,diagnostic)
    allocator_sample("ALLOCATOR-INSTALLED")
    def output_event(name,f,out,native_calls,substituted):
        if not diagnostic:return None
        return send("%s-e%06d-OUTPUT"%(name,f["epoch"]),
            {"schema":"kivi.actual-packed-qwen-output/v1","rank":rank,"identity":ident,"layer":name,
             "frame_ref":state["frame_ref"],"epoch":f["epoch"],"kind":f["kind"],
             "original_attention_calls":native_calls,"output_substituted":substituted,
             "original_cache_update_suppressed":substituted,"output":callback.scalar_tensor(out),
             "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             "model_ready":False,"run_authority":False,"graph_checked":False})
    def release(rid,slot,epoch):
        expected=book.live[rid]["length"]
        need(all(slot in layer_contexts[name]["arena"].active for name in layer_names),
             "all16 actual compact states exist before finished release")
        for name in layer_names:
            a=layer_contexts[name]["arena"]
            if slot in a.active:
                r=a.active[slot]; a.owned(r)
                need(r.owner==rid and r.epoch==epoch and r.length==expected and not r.pending,
                     "actual owner/epoch/length before native finish release")
                a.release(r)
                if capture_raw:
                    del original_prefills[(name,rid,epoch)]
        send("RETIRE-%s"%rid,{"schema":"kivi.actual-packed-qwen-retire/v1","rank":rank,"identity":ident,
             "request_id":rid,"slot":slot,"epoch":epoch,"actual_native_finished":True,"model_ready":False})
    orig_update=runner._update_states; orig_prepare=runner._prepare_inputs
    orig_execute=runner.execute_model; orig_dummy=runner._dummy_run
    def update(self,scheduler):
        need(state["active"] is None and not state["failed"],"no update during/after uncertain candidate")
        before=list(self.requests); finished=list(scheduler.finished_req_ids)
        boundary=state["scheduler_type"] is None or bool(scheduler.scheduled_new_reqs) or bool(finished)
        if not diagnostic:
            need(timing_layout(self,event,layer_contexts,callback)==initial_layout,
                 "actual all64/compact allocation changed; invalidate and require new owned install")
        if diagnostic or boundary:
            writer_guard(self,event,layer_contexts,owner["zeroer_writer_receipt_ref"])
            need(identity()==ident,"same actual worker at lifecycle qualification boundary")
            ingress_refs=ingress_bindings.check_new(scheduler,ident,rank,publish)
            state["scheduler_type"]=type(scheduler)
            if not diagnostic:
                for ctx in layer_contexts.values():ctx["packed_batch"].qualify_boundary()
        else:
            ingress_refs=timing_cached_ingress(ingress_bindings,scheduler,state["scheduler_type"],ident,rank)
        answer=orig_update(scheduler) # real native even finished-only, preserve deferred callable
        row={"schema":"kivi.actual-packed-qwen-update/v1","rank":rank,"identity":ident,
             "new_ingress_refs":ingress_refs,"finished_req_ids":finished,"requests_before":before,"requests_after":list(self.requests),
             "batch_after":list(self.input_batch.req_ids),"runner_source_sha256":RUNNER_SHA,"model_ready":False}
        state["update_seq"]+=1
        if diagnostic or boundary:send("UPDATE-%06d"%state["update_seq"],row)
        book.retire(finished,row["requests_after"],row["batch_after"],release)
        need(set(book.live)<=set(self.requests),"preemption/removal without native finish unsupported")
        state["frame"]=None; state["frame_ref"]=None; state["metadata_proofs"].clear()
        return answer
    def prepare(self,scheduler,scheduled):
        need(state["active"] is None and not state["failed"] and not scheduler.scheduled_spec_decode_tokens,
             "one real non-speculative prepare")
        answer=orig_prepare(scheduler,scheduled); n=self.input_batch.num_reqs
        ids=list(self.input_batch.req_ids)
        counts=[int(scheduler.num_scheduled_tokens[rid]) for rid in ids]
        need(len(ids)==n and [int(x) for x in scheduled.tolist()]==counts,"real whole batch ordering")
        need(set(ids)<=ingress_bindings.seen,"actual post-assignment/native ingress BEFORE Book.plan")
        state["epoch"]+=1
        f={"epoch":state["epoch"],"req_ids":ids,"req_id_to_index":dict(self.input_batch.req_id_to_index),
           "scheduled_counts":counts,"computed_tokens":[int(x) for x in self.input_batch.num_computed_tokens_cpu[:n].tolist()],
           "query_start_loc":[int(x) for x in self.query_start_loc.np[:n+1].tolist()],
           "positions":[int(x) for x in self._positions_np_buf[:scheduler.total_num_scheduled_tokens].tolist()],
           "total_tokens":int(scheduler.total_num_scheduled_tokens)}
        for rid in ids:
            need(rid in self.requests and len(self.requests[rid].prompt_token_ids)==book.prompts[rid],
                 "real request prompt length, not metadata label")
        f["kind"]=book.plan(f); state["frame"]=f
        state["frame_ref"]=send("FRAME-%06d"%f["epoch"],dict(f,schema="kivi.actual-packed-qwen-frame/v1",
             rank=rank,identity=ident,model_ready=False,run_authority=False)) if diagnostic else None
        return answer
    def execute(self,*args,**kwargs):
        try:
            answer=orig_execute(*args,**kwargs)
            if state["frame"] is not None: book.complete(state["frame"],layer_names)
            return answer
        except BaseException:
            state["failed"]=True
            if not diagnostic:
                for ctx in layer_contexts.values():ctx["packed_batch"].invalidate()
            raise
    def dummy(self,*args,**kwargs):
        need(state["frame"] is None and state["active"] is None and not state["failed"],"real source-bound startup only")
        state["dummy_depth"]+=1
        try:return orig_dummy(*args,**kwargs)
        finally:state["dummy_depth"]-=1
    def metadata_factory(names,original,metadata_type):
        def build(self,common_prefix_len,common_attn_metadata,fast_build=False):
            if state["dummy_depth"]:
                return original(common_prefix_len,common_attn_metadata,fast_build=fast_build)
            f=state["frame"];cm=common_attn_metadata
            need(f is not None and state["active"] is None and not state["failed"]
                 and common_prefix_len==0 and fast_build is False,"source-bound eager metadata construction")
            n=len(f["req_ids"])+1
            need(cm.num_reqs==n-1 and cm.num_actual_tokens==f["total_tokens"] and cm.causal is True,
                 "no padded/mixed/spec metadata substituted for actual whole frame")
            start_buffer_alias(torch,cm.query_start_loc_cpu,runner.query_start_loc.cpu,n,"cpu")
            start_buffer_alias(torch,cm.query_start_loc,runner.query_start_loc.gpu,n,"npu")
            starts=cm.query_start_loc_cpu[:n].tolist()
            need(starts==f["query_start_loc"] and not any(name in state["metadata_proofs"] for name in names),
                 "one actual complete FA builder publication per frame")
            result=original(common_prefix_len,cm,fast_build=fast_build)
            need(type(result) is metadata_type,"exact real source-pinned AscendMetadata result")
            proof={"epoch":f["epoch"],"meta":result,"query":result.query_start_loc,
                   "starts":starts,"query_descriptor":callback.scalar_tensor(result.query_start_loc)}
            timing_partition(torch,runner,result,f,proof,callback)
            for name in names:state["metadata_proofs"][name]=proof
            return result
        return build
    def caller_factory(name,original):
        def caller(self,positions,output,hidden_states):
            ctx=forward_context.get_forward_context()
            if state["dummy_depth"]:
                return original(positions,output,hidden_states)
            need(state["frame"] is not None and state["active"] is None and not state["failed"]
                 and ctx.cudagraph_runtime_mode.name=="NONE" and ctx.capturing is False
                 and ctx.in_profile_run is False and not ctx.flash_comm_v1_enabled and not ctx.flashcomm_v2_enabled,
                 "actual eager caller; no Python replay or startup bypass guessed from absent frame")
            state["active"]=(name,positions)
            try:return original(positions,output,hidden_states) # real RoPE, sigmoid gate, o_proj untouched
            finally:state["active"]=None
        return caller
    def attention_factory(name,original):
        def attention(self,q,k,v,output_shape=None):
            if state["dummy_depth"]:return original(q,k,v,output_shape=output_shape)
            need(state["active"] is not None and state["active"][0]==name
                 and (not diagnostic or identity()==ident),"real post-RoPE caller")
            if diagnostic:qualify()
            else:layer_contexts[name]["packed_batch"].hot_qualify()
            f=state["frame"]; book_module.frame_valid(f); total=f["total_tokens"]
            meta=forward_context.get_forward_context().attn_metadata[name]
            need(callable(getattr(torch.npu,"is_current_stream_capturing",None))
                 and torch.npu.is_current_stream_capturing() is False,"actual eager stream only")
            if diagnostic:
                need(meta.causal is True and meta.num_actual_tokens==total and
                     meta.query_start_loc.to("cpu").tolist()[:len(f["req_ids"])+1]==f["query_start_loc"],
                     "real layer metadata/whole token partition")
            else:
                timing_partition(torch,runner,meta,f,state["metadata_proofs"].get(name),callback)
            enum=type(meta.attn_state)
            allowed=(enum.PrefillNoCache,enum.PrefillCacheHit,enum.ChunkedPrefill) if f["kind"]=="prefill" else (enum.DecodeOnly,)
            need(meta.attn_state in allowed,"homogeneous deployed metadata, not mixed/spec")
            need(tuple(q.shape) in ((total,1536),(total,6,256)) and
                 tuple(k.shape)==tuple(v.shape) and tuple(k.shape) in ((total,256),(total,1,256))
                 and q.dtype==k.dtype==v.dtype and q.device==k.device==v.device
                 and (output_shape is None or tuple(output_shape)==(total,1536)),"actual complete Qwen Q6/KV1/D256/output")
            ctx=layer_contexts[name]; a=ctx["arena"]; batch=ctx["packed_batch"]
            native_key,native_value=members[name][2:]
            need(q.device==k.device==v.device==a.device and q.dtype==k.dtype==v.dtype==a.dtype,
                 "actual pool/query dtype/device, not marketing identity")
            # Native pointers/extents stay unchanged. All compact fields remain charged original layout.
            need(capture.descriptor(self.kv_cache[0],batch.format)==event["layers"][name]["views"][0]
                 and capture.descriptor(self.kv_cache[1],batch.format)==event["layers"][name]["views"][1],
                 "no native cache rebinding or hidden allocation replacement")
            if f["kind"]=="prefill":
                allocator_sample("%s-e%06d-ALLOCATOR-BEFORE-NATIVE"%(name,f["epoch"]))
                out=original(q,k,v,output_shape=output_shape) # exactly once: original dense prefill/cache update
                allocator_sample("%s-e%06d-ALLOCATOR-AFTER-NATIVE"%(name,f["epoch"]))
                need(tuple(out.shape)==(total,1536),"real original dense prefill output unchanged")
                gid=[i for i,g in enumerate(runner.kv_cache_config.kv_cache_groups) if name in g.layer_names]
                need(len(gid)==1,"unique actual FA group")
                bt=runner.input_batch.block_table[gid[0]]
                if diagnostic or name not in state["block_types"]:
                    callable_pin(type(bt),BLOCK_SHA)
                    state["block_types"][name]=type(bt)
                need(type(bt) is state["block_types"][name],"same source-bound native block table")
                for i,rid in enumerate(f["req_ids"]):
                    c,n=f["computed_tokens"][i],f["scheduled_counts"][i]
                    if c+n==book.prompts[rid]:
                        x=book.live[rid]; r=a.acquire(x["slot"],rid)
                        need(r.epoch==x["epoch"],"actual same slot epoch across all16 FA")
                        blocks=[int(z) for z in bt.block_table.np[i,:int(bt.num_blocks_per_row[i])].tolist()]
                        # Existing source-bound gather reads original real completed cache in128 tiles.
                        tiles=formal.gather_native(torch,native_key,native_value,blocks,c+n)
                        completed={}
                        if capture_raw:
                            need((name,rid,r.epoch) not in original_prefills,"one original prefill per live owner epoch")
                            tiles=provenance.capture_tiles(tiles,torch=torch,producer=producer_module,
                                callback=callback,root=raw_root,
                                sequence="r%d-%s-e%06d-s%02d-PREFILL"%(rank,name.replace(".","-"),f["epoch"],r.slot),
                                context={"rank":rank,"identity":ident,"layer":name,"request_id":rid,
                                    "slot":r.slot,"slot_epoch":r.epoch,"prompt_length":c+n,"bits":a.bits,
                                    "frame_ref":state["frame_ref"],"event_ref":event_ref,
                                    "geometry_ref":ctx["geometry_ref"],
                                    "native_views":event["layers"][name]["views"],
                                    "native_shape":list(native_key.shape),"native_block_row":blocks,
                                    "original_attention_calls":1,"allocation_replaced":False,"graph_checked":False,
                                    "installer_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                                publish=lambda label,body:send("%s-e%06d-s%02d-%s"%(name,f["epoch"],r.slot,label),body),
                                completed=completed)
                        parts=list(tiles)
                        if capture_raw:
                            original_prefills[(name,rid,r.epoch)]=completed["ref"]
                        whole_k=torch.cat([row[2] for row in parts],0)
                        whole_v=torch.cat([row[3] for row in parts],0)
                        del parts
                        allocator_sample("%s-e%06d-s%02d-ALLOCATOR-GATHERED"%(name,f["epoch"],r.slot))
                        a.prefill_after_dense(r,whole_k,whole_v); del whole_k,whole_v
                        allocator_sample("%s-e%06d-s%02d-ALLOCATOR-SEALED"%(name,f["epoch"],r.slot))
                        need(r.length==book.prompts[rid] and not r.pending,"actual completed prefix+author residual seal")
                    book.layer_done(rid,f["epoch"],name)
                output_event(name,f,out,1,False)
                return out
            capture_this_decode=raw_decode_capture(capture_raw,first_decode_capture_only,tuple(f["computed_tokens"]))
            requests=[]; pre=[]
            for i,rid in enumerate(f["req_ids"]):
                x=book.live[rid]; r=a.active[x["slot"]]; a.owned(r)
                need(r.owner==rid and r.epoch==x["epoch"] and r.length==f["computed_tokens"][i],
                     "actual persistent assigned owner/slot/computed position")
                refs=None
                if diagnostic:
                    refs={"before_bind":ctx["before_bind_ref"],"actual_format":ctx["actual_format_ref"],
                         "post_rope":send("%s-e%06d-r%02d-POSTROPE"%(name,f["epoch"],i),
                           {"schema":"kivi.actual-qwen-postrope/v1","rank":rank,"identity":ident,"layer":name,
                            "frame_ref":state["frame_ref"],"query":callback.scalar_tensor(q),
                            "key":callback.scalar_tensor(k),"value":callback.scalar_tensor(v),"model_ready":False}),
                         "slot_owner":send("%s-e%06d-r%02d-OWNER"%(name,f["epoch"],i),
                           {"schema":"kivi.actual-qwen-slot-owner/v1","rank":rank,"identity":ident,"request_id":rid,"layer":name,
                            "slot":r.slot,"epoch":r.epoch,"generation":r.generation,"computed":r.length,
                            "frame_ref":state["frame_ref"],"model_ready":False,
                            **({"original_prefill_ref":original_prefills[(name,rid,r.epoch)]} if capture_raw else {})})}
                requests.append(r); pre.append(refs)
            result=batch.append_read(a,tuple(requests),q.reshape(total,6,256).contiguous(),
                k.reshape(total,256).contiguous(),v.reshape(total,256).contiguous(),
                tuple(f["computed_tokens"]),pre_refs=tuple(pre) if diagnostic else None,capture_raw=capture_this_decode,raw_root=raw_root,
                sequence="r%d-%s-e%06d"%(rank,name.replace(".","-"),f["epoch"]))
            need(result is not None and tuple(result.shape)==(total,6,256),"whole actual packed result, never fallback")
            for rid in f["req_ids"]:book.layer_done(rid,f["epoch"],name)
            # Return BEFORE public Attention.forward: no duplicate original FA or its cache update.
            out=result.reshape(total,1536)
            output_event(name,f,out,0,True)
            return out
        return attention
    try:
        for names,builder,metadata_type in timing_builders:
            method(builder,"build",metadata_factory(names,builder.build,metadata_type))
        method(runner,"_update_states",update); method(runner,"_prepare_inputs",prepare)
        method(runner,"execute_model",execute); method(runner,"_dummy_run",dummy)
        for name,(member,attn,_,_) in members.items():
            method(member,"forward",caller_factory(name,member.forward))
            method(attn,"forward",attention_factory(name,attn.forward))
    except BaseException:
        for obj,key,repl,existed,old,_ in reversed(changes):
            if getattr(obj,key) is repl:
                if existed:setattr(obj,key,old)
                else:delattr(obj,key)
        raise
    def restore():
        # Actual finished-only evidence is mandatory. No fake abort/retire or unsafe pending recycle.
        book.close(); need(not state["failed"] and state["active"] is None,"complete unchanged owned branch")
        for obj,key,repl,existed,old,original in reversed(changes):
            need(getattr(obj,key) is repl,"only exact own replacement restore")
            if existed:setattr(obj,key,old)
            else:delattr(obj,key)
            need(getattr(obj,key)==original,"actual original callable restored")
        return {"schema":"kivi.actual-packed-qwen-installer-final/v1","rank":rank,"identity":ident,
                "finished":sorted(book.finished),"owner_ref":owner_ref,"event_ref":event_ref,
                "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "model_ready":False,"run_authority":False,"allocation_replaced":False,"graph_checked":False,
                "diagnostic":diagnostic,"timing_model_prerequisite_external":not diagnostic}
    return restore
