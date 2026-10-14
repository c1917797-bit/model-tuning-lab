"""Opt-in worker loader: install observer only after official runner import."""
import importlib.abc
import importlib.machinery
import json
import os
from pathlib import Path
import sys
_finder=None
_stop=None

def enable():
    global _finder
    if os.environ.get("INDEPENDENT_CACHE_DIAGNOSTIC")!="1":return
    raw=Path(os.environ["INDEPENDENT_DIAGNOSTIC_ROOT"])
    if not raw.is_absolute() or not raw.is_dir():
        raise ValueError("diagnostic root must already exist")
    maximum=int(os.environ.get("INDEPENDENT_DIAGNOSTIC_BATCHES","2"))
    if not 1<=maximum<=4:raise ValueError("diagnostic batch bound")
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):
            return self.original.create_module(spec) if hasattr(self.original,"create_module") else None
        def exec_module(self,module):
            global _stop
            self.original.exec_module(module)
            from independent_runtime_adapter import activate_cache_diagnostic
            path=raw/("cache-association-"+str(os.getpid())+".jsonl")
            # One file per worker, never overwrite an earlier attempt.
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            def emit(event):
                data=(json.dumps(event)+"\n").encode()
                view=memoryview(data)
                while view:
                    n=os.write(fd,view)
                    if n<=0:raise OSError("short diagnostic write")
                    view=view[n:]
                os.fsync(fd)
            try:
                _stop=activate_cache_diagnostic(enabled=True,emit=emit,max_batches=maximum)
                emit({"event":"observer_installed","pid":os.getpid(),"technique_enabled":False})
                public_config=os.environ.get("INDEPENDENT_PUBLIC_STAGE_CONFIG")
                if public_config:
                    from independent_public_stage import CanonicalPublicStage
                    config=json.loads(Path(public_config).read_text())
                    stage=CanonicalPublicStage(**config)
                    def publish(material):
                        generation=stage.publish(material)
                        from dataclasses import asdict
                        emit({"event":"public_linear_material_published","pid":os.getpid(),
                              "identity":asdict(material.identity),"generation":generation,
                              "transition_shape":list(material.affine.transition.shape),
                              "core_body_shape":list(material.core_outputs.shape)})
                    from independent_public_gdn_hook import install_public_gdn_producer
                    producer_stop=install_public_gdn_producer(
                        enabled=True,select_public=stage.select_public,publish=publish)
                    context_stop=_stop
                    private_stop=lambda:None
                    c2_stop=lambda:None
                    stage.c2_enabled=os.environ.get("INDEPENDENT_C2_KV")=="1"
                    if stage.c2_enabled:
                        from independent_c2_kv_hook import install_c2_kv
                        c2_stop=install_c2_kv(stage,enabled=True,emit=emit)
                        emit({"event":"c2_kv_installed","pid":os.getpid()})
                    if os.environ.get("INDEPENDENT_PRIVATE_C1")=="1":
                        from independent_private_gdn_hook import install_private_c1
                        private_stop=install_private_c1(stage,enabled=True,emit=emit)
                        emit({"event":"private_c1_installed","pid":os.getpid(),"c2_enabled":False})
                    def combined_stop():
                        c2_stop()
                        private_stop()
                        producer_stop()
                        context_stop()
                    _stop=combined_stop
                    emit({"event":"public_producer_installed","pid":os.getpid(),
                          "tokens_sha256":stage.digest,"length":len(stage.tokens),
                          "private_reuse_enabled":False})
            except BaseException:
                os.close(fd)
                raise
            sys.meta_path.remove(_finder)
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname!="vllm_ascend.worker.model_runner_v1":return None
            spec=importlib.machinery.PathFinder.find_spec(fullname,path)
            if spec is None or spec.loader is None:raise ImportError(fullname)
            spec.loader=Loader(spec.loader)
            return spec
    if _finder is not None:raise RuntimeError("diagnostic finder already installed")
    _finder=Finder()
    sys.meta_path.insert(0,_finder)
