"""Default-OFF owned worker lifecycle seam, not a container/service controller.
Retains actual raw arguments at the frozen native reshape seam; no fabricated raw
storage view, copied allocator, cache replacement, or dynamic worker-name guess.
"""
import json, os
def need(v,m):
    if not v:raise ValueError(m)
def make_worker(native_worker_cls,mods,adapter,bridge,torch,torch_npu,tp,kv_spec,context,*,
                layout_owner,layout_owner_ref,layout_mf,post_owner=None,post_owner_ref=None,
                resolve_post_owner=None,native_initialize=None,native_initialize_sha=None):
    if os.environ.get(bridge.FLAG)!="1":return native_worker_cls
    need((post_owner is None and post_owner_ref is None and callable(resolve_post_owner)) or
         (resolve_post_owner is None and type(post_owner) is dict and type(post_owner_ref) is dict),
         "one actual static input or initialized source-bound resolver")
    capture=mods["layout"][1];base=mods["base"]
    capture.source_file(native_worker_cls,adapter.WORKER_SHA)
    original=native_worker_cls.initialize_from_config
    capture.source_file(original,adapter.WORKER_SHA)
    need(native_worker_cls.__name__=="NPUWorker","actual original platform-selected NPUWorker class")
    need(callable(native_initialize) and type(native_initialize_sha)is str,
         "explicit source-qualified provider initializer required")
    capture.source_file(native_initialize,native_initialize_sha)
    class OwnedKiviPostRopeWorker(native_worker_cls):
        def initialize_from_config(self,config):
            ident=capture.identity();adapter.validate_owner(layout_owner,ident,layout_mf)
            need(json.loads(adapter.bound(layout_owner_ref).read_bytes())==layout_owner,"actual immutable layout input")
            if resolve_post_owner is None:
                need(json.loads(adapter.bound(post_owner_ref).read_bytes())==post_owner,"actual immutable static post input")
            need(self.model_runner.model_config.enforce_eager is True,"future diagnostic owner explicitly eager before initialize")
            rank=tp.get_tensor_model_parallel_rank()
            need(tp.get_tensor_model_parallel_world_size()==4 and type(rank)is int and rank in range(4),
                 "actual TP4 before native initialization")
            need(os.environ.get("QWEN36_KIVI_LAYOUT_DIAGNOSTIC")=="1"and adapter._ACTIVE is None,
                 "original source-bound layout opt-in and no active collector")
            collector=adapter.Collector(base,capture,layout_owner,layout_owner_ref,layout_mf,rank,ident)
            retained={};restore_layout=None;outer=None;donor=None;layout_final_ref=None
            runner_cls=type(self.model_runner);primary=None;secondary=[];returned=False;restored=False
            def emit(kind,event):
                collector.emit(kind,event)
                need(retained.get("runner")is self.model_runner and "raw"in retained,
                     "event emitted synchronously inside actual raw reshape call")
                retained["event"]=event;retained["event_ref"]=collector.layout_ref
            try:
                collector.bind(torch_npu);adapter._ACTIVE=collector
                restore_layout=capture.install(runner_cls,kv_spec,tp,format_probe=adapter.probe,
                    format_probe_ref=collector.probe_ref,emit=emit)
                need(callable(restore_layout),"frozen before-bind collector installed")
                donor=runner_cls._reshape_kv_cache_tensors
                # Outer callback retains only references to already allocated original raw.
                def outer(runner,actual_config,raw):
                    need(runner is self.model_runner and not retained,"one actual owned initialization")
                    retained.update(runner=runner,raw=raw,config=actual_config)
                    result=donor(runner,actual_config,raw)
                    need("event"in retained,"complete synchronous original all64 layout")
                    return result
                runner_cls._reshape_kv_cache_tensors=outer
                result=native_initialize(self,config);returned=True
                need(retained.get("config")is self.model_runner.kv_cache_config,
                     "same actual KVCacheConfig preserved after initialize")
            except BaseException as error:primary=repr(error);raise
            finally:
                adapter._ACTIVE=None
                if outer is not None:
                    try:
                        need(runner_cls._reshape_kv_cache_tensors is outer,"exact owned raw retention wrapper")
                        runner_cls._reshape_kv_cache_tensors=donor
                    except BaseException as error:secondary.append({"phase":"restore-raw-retention","error":repr(error)})
                if restore_layout is not None and not secondary:
                    try:restore_layout();restored=True
                    except BaseException as error:secondary.append({"phase":"restore-frozen-layout","error":repr(error)})
                try:layout_final_ref=collector.finish(primary,secondary,restored,returned)
                except BaseException as error:secondary.append({"phase":"original-layout-final","error":repr(error)})
                if primary is None and secondary:raise RuntimeError(repr(secondary))
            event=retained["event"]
            if resolve_post_owner is not None:
                actual_post,actual_post_ref=resolve_post_owner(self.model_runner,event,retained["event_ref"],
                    collector.publish,layout_final_ref,retained["raw"])
            else:actual_post,actual_post_ref=post_owner,post_owner_ref
            need(type(actual_post) is dict and type(actual_post_ref) is dict and
                 json.loads(adapter.bound(actual_post_ref).read_bytes())==actual_post,
                 "immutable actual initialized post input")
            need(actual_post["rank_bindings"][str(rank)]==ident and actual_post["container_id"]==layout_owner["container_id"]
                 and actual_post["run_id"]==layout_owner["run_id"] and
                 actual_post["diagnostic_root"]==layout_owner["diagnostic_root"],
                 "two explicit immutable owner inputs refer to same existing owned run/worker")
            names={n for n,l in event["layers"].items()if l["kind"]=="FA"}
            need(set(actual_post["regions"])==names and len(names)==16,
                 "all16 explicit provider allocations, not native padding")
            regions={}
            for name in names:
                proposal=dict(actual_post["regions"][name])
                need(set(proposal)=={"pages","bits","allocation_ref"}
                     and proposal["allocation_ref"]==actual_post["explicit_allocation_ref"],
                     "explicit allocation Ref only; no caller tensor or invented padding")
                regions[name]=proposal
            # Original native storage remains live; compact storage is separately
            # allocated and charged by the source-qualified same-budget provider.
            self._kivi_postrope_restore=bridge.install(self.model_runner,mods,adapter,torch,torch_npu,tp,context,
                owner=actual_post,owner_ref=actual_post_ref,event=event,event_ref=retained["event_ref"],
                regions=regions,publish=collector.publish,layout_final_ref=layout_final_ref)
            need(callable(self._kivi_postrope_restore),"post-RoPE diagnostic installed, no silent skip")
            self._kivi_retained_original_raw=retained["raw"]
            return result
        def close_kivi_postrope_diagnostic(self):
            """Existing exact owner calls after its real request/capture completes.
            No destructor/automatic completion, and no scheduler finish authority.
            """
            restore=getattr(self,"_kivi_postrope_restore",None)
            need(callable(restore),"actual installed owned seam required")
            ref=restore();self._kivi_postrope_restore=None
            # Retain original raw references until exact owner cleanup; no reclaim claim.
            return ref
    return OwnedKiviPostRopeWorker
