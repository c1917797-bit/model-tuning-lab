"""Draft quality loader; same R7 inference core, not active."""
import hashlib,json,os,sys,threading
from pathlib import Path
import importlib.abc,importlib.machinery
_finder=None
_stop=None
_scheduler_stop=None


def disable():
    global _finder,_stop,_scheduler_stop
    try:
        if _stop is not None:
            stop=_stop;_stop=None;stop()
    finally:
        try:
            if _scheduler_stop is not None:
                stop=_scheduler_stop;_scheduler_stop=None;stop()
        finally:
            if _finder in sys.meta_path:sys.meta_path.remove(_finder)
            _finder=None

def enable():
    global _finder,_scheduler_stop
    if os.environ.get('INDEPENDENT_COMPACT_HYPIC')!='1':return
    if 'vllm_ascend.worker.model_runner_v1' in sys.modules:
        raise RuntimeError('quality worker already imported before bound installation')
    if _finder is not None or _stop is not None:raise RuntimeError('quality loader already owns installation')
    legacy=sys.modules.get('independent_compact_loader')
    if legacy is not None and getattr(legacy,'_finder',None) is not None:
        raise RuntimeError('legacy compact loader already owns installation')
    manifest_path=Path(os.environ['INDEPENDENT_COMPACT_MANIFEST'])
    manifest=json.loads(manifest_path.read_text());base=manifest_path.parent.resolve()
    for name,digest in manifest['source_sha256'].items():
        path=(base/name).resolve()
        if not path.is_relative_to(base) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('compact package source drift: '+name)
    config_path=(base/manifest['config']).resolve()
    if not config_path.is_relative_to(base):raise ValueError('config outside package')
    config=json.loads(config_path.read_text())
    from independent_catalog_artifact import resolve_catalog_config
    config=resolve_catalog_config(config)
    from independent_quality_evidence_policy import QualityEvidencePolicy
    profile=config.pop("evidence_profile","full")
    QualityEvidencePolicy(profile)
    from independent_evidence_limits import evidence_limits
    limits=evidence_limits(config.pop("evidence_limits",None))
    scheduler_enabled=config.pop("scheduler_admission_enabled",False)
    if type(scheduler_enabled) is not bool:raise ValueError('explicit scheduler admission boolean required')
    if 'public_token_artifact' in config:
        if 'public_tokens' in config or 'public_token_recipe' in config:
            raise ValueError('ambiguous public token configuration')
        from independent_public_token_artifact import public_tokens_from_artifact
        config['public_tokens']=public_tokens_from_artifact(config.pop('public_token_artifact'))
    if 'public_token_recipe' in config:
        if 'public_tokens' in config:raise ValueError('ambiguous public token configuration')
        from synthetic_compact_workload import public_tokens_from_recipe
        config['public_tokens']=public_tokens_from_recipe(config.pop('public_token_recipe'))
    raw=Path(os.environ['INDEPENDENT_COMPACT_RAW'])
    if not raw.is_absolute() or not raw.is_dir():raise ValueError('existing absolute raw root required')
    from independent_catalog_scheduler_loader import enable_scheduler
    _scheduler_stop=enable_scheduler(manifest_path,config,raw,enabled=scheduler_enabled,request_limit=limits["max_requests"])
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):
            return self.original.create_module(spec) if hasattr(self.original,'create_module') else None
        def exec_module(self,module):
            global _stop
            self.original.exec_module(module)
            path=raw/('compact-worker-'+str(os.getpid())+'.jsonl')
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            lock=threading.Lock();count=0;size=0
            policy=QualityEvidencePolicy(profile)
            def emit(event):
                nonlocal count,size
                event=policy.select(event)
                if event is None:return
                event=dict(event,pid=os.getpid(),manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())
                data=(json.dumps(event,sort_keys=True)+'\n').encode()
                with lock:
                    if count>=limits["max_events"] or size+len(data)>limits["max_bytes"]:
                        raise ValueError('compact evidence bound exceeded')
                    view=memoryview(data)
                    while view:
                        n=os.write(fd,view)
                        if n<=0:raise OSError('short evidence write')
                        view=view[n:]
                    os.fsync(fd);count+=1;size+=len(data)
            try:
                emit.source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                emit.stage_capture_root=str(raw)
                emit(policy.descriptor())
                from independent_compact_activation import activate_compact_hypic
                worker_stop=activate_compact_hypic(config,enabled=True,emit=emit,
                                           request_progress_limit=limits["max_requests"])
                def stop_worker():
                    try:worker_stop()
                    finally:os.close(fd)
                _stop=stop_worker
            except BaseException:
                os.close(fd);disable();raise
            sys.meta_path.remove(_finder)
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname!='vllm_ascend.worker.model_runner_v1':return None
            spec=importlib.machinery.PathFinder.find_spec(fullname,path)
            if spec is None or spec.loader is None:raise ImportError(fullname)
            spec.loader=Loader(spec.loader);return spec
    if _finder is not None:raise RuntimeError('compact import loader already installed')
    _finder=Finder();sys.meta_path.insert(0,_finder)
