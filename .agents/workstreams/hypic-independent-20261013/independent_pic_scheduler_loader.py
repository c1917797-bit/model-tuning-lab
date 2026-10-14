"""Default-off scheduler import hook for the independent PIC boundary policy."""
import hashlib
import importlib.abc
import importlib.machinery
import json
import os
from pathlib import Path
import sys
import threading
_finder=None
_stop=None

def enable_scheduler(manifest_path,config,raw,*,enabled=False):
    global _finder
    if not enabled:return lambda:None
    if type(enabled) is not bool or _finder is not None:
        raise ValueError("explicit single scheduler enable required")
    module_name="vllm.v1.core.sched.scheduler"
    if module_name in sys.modules:
        raise ValueError("scheduler already imported before bound installation")
    manifest_hash=hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest()
    public=tuple(config["public_tokens"])
    from independent_pic_scheduler_admission import WorkerMaterialReader,PICAdmissionCallback
    from independent_pic_scheduler_hook import install_pic_scheduler
    reader=WorkerMaterialReader(raw,manifest_hash)
    class Loader:
        def __init__(self,original):self.original=original
        def create_module(self,spec):
            return self.original.create_module(spec) if hasattr(self.original,"create_module") else None
        def exec_module(self,module):
            global _stop
            self.original.exec_module(module)
            path=Path(raw)/("compact-scheduler-"+str(os.getpid())+".jsonl")
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            lock=threading.Lock();count=0;size=0
            def emit(event):
                nonlocal count,size
                event=dict(event,pid=os.getpid(),manifest_sha256=manifest_hash,role="scheduler")
                data=(json.dumps(event,sort_keys=True)+"\n").encode()
                with lock:
                    if count>=8192 or size+len(data)>8388608:raise ValueError("scheduler evidence bound exceeded")
                    view=memoryview(data)
                    while view:
                        n=os.write(fd,view)
                        if n<=0:raise OSError("short scheduler evidence write")
                        view=view[n:]
                    os.fsync(fd);count+=1;size+=len(data)
            try:
                callback=PICAdmissionCallback(public,reader,emit=emit)
                remove=install_pic_scheduler(module.Scheduler,enabled=True,
                    expected_source_sha256="9ae1491f57a6294e32416b93ef2ea68107fa0d65c3a4d7f745f1261012f735e9",cap=callback)
                emit({"event":"pic_scheduler_hook_installed","scope":"installation only; actual boundary proof pending"})
            except BaseException:
                os.close(fd);raise
            def stop():
                remove();os.close(fd)
            _stop=stop
            sys.meta_path.remove(_finder)
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname!=module_name:return None
            spec=importlib.machinery.PathFinder.find_spec(fullname,path)
            if spec is None or spec.loader is None:raise ImportError(fullname)
            spec.loader=Loader(spec.loader);return spec
    _finder=Finder();sys.meta_path.insert(0,_finder)
    def uninstall():
        global _finder,_stop
        if _stop is not None:_stop();_stop=None
        elif _finder in sys.meta_path:sys.meta_path.remove(_finder)
        _finder=None
    return uninstall
