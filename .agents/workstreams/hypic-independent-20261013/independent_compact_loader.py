"""Hash-bound worker loader for the independent compact hook chain."""
import hashlib,json,os,sys,threading
from pathlib import Path
import importlib.abc,importlib.machinery
_finder=None
_stop=None


def enable():
    global _finder
    if os.environ.get('INDEPENDENT_COMPACT_HYPIC')!='1':return
    manifest_path=Path(os.environ['INDEPENDENT_COMPACT_MANIFEST'])
    manifest=json.loads(manifest_path.read_text());base=manifest_path.parent.resolve()
    for name,digest in manifest['source_sha256'].items():
        path=(base/name).resolve()
        if not path.is_relative_to(base) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('compact package source drift: '+name)
    config_path=(base/manifest['config']).resolve()
    if not config_path.is_relative_to(base):raise ValueError('config outside package')
    config=json.loads(config_path.read_text())
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
            def emit(event):
                nonlocal count,size
                event=dict(event,pid=os.getpid(),manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest())
                data=(json.dumps(event,sort_keys=True)+'\n').encode()
                with lock:
                    if count>=10000 or size+len(data)>33554432:raise ValueError('compact evidence bound exceeded')
                    view=memoryview(data)
                    while view:
                        n=os.write(fd,view)
                        if n<=0:raise OSError('short evidence write')
                        view=view[n:]
                    os.fsync(fd);count+=1;size+=len(data)
            try:
                from independent_compact_activation import activate_compact_hypic
                _stop=activate_compact_hypic(config,enabled=True,emit=emit)
            except BaseException:
                os.close(fd);raise
            sys.meta_path.remove(_finder)
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname!='vllm_ascend.worker.model_runner_v1':return None
            spec=importlib.machinery.PathFinder.find_spec(fullname,path)
            if spec is None or spec.loader is None:raise ImportError(fullname)
            spec.loader=Loader(spec.loader);return spec
    if _finder is not None:raise RuntimeError('compact import loader already installed')
    _finder=Finder();sys.meta_path.insert(0,_finder)
