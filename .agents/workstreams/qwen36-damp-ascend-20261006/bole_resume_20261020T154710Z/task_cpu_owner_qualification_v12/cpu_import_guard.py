"""Bounded actual CPython import audit, diagnostic only; never a module stub.
An accelerator import attempt is retained and denied before module execution.
A swallowed denial remains a failed qualification. The hook never fabricates an
availability return, replaces a module/finder, or patches library code.
"""
import json
import hashlib
import os
from pathlib import Path
import sys
import time
FORBIDDEN={'torch_npu','vllm','vllm_ascend','triton'}
ROOTS=FORBIDDEN|{'torch','transformers','tokenizers'}


class ForbiddenImport(RuntimeError):pass


def state():
    names=sorted(k for k in sys.modules if k.split('.')[0]in ROOTS)
    module=sys.modules.get('transformers.utils.import_utils');cached={}
    if module is not None:
        for k in('USE_TORCH','USE_TF','USE_FLAX','USE_TORCH_XLA','_torch_available','_tf_available','_flax_available'):
            value=vars(module).get(k,'ABSENT')
            if type(value)in(str,bool,int,float)or value is None:cached[k]=value
    digest=hashlib.sha256(json.dumps(names,separators=(',',':')).encode()).hexdigest()
    return dict(related_modules_first256=names[:256],related_module_count=len(names),complete_ordered_module_names_sha256=digest,import_utils_plain_cached_attributes=cached)


class Trace:
    def __init__(self,out,source_ref):
        self.path=out/'TOKENIZER_IMPORT_TRACE.jsonl';self.file=self.path.open('xb');self.count=0;self.bytes=0;self.seen=set();self.forbidden=[];self.active=True
        self.emit('entry',dict(source_ref=source_ref,state=state()))
        sys.addaudithook(self.audit)

    def emit(self,kind,value):
        raw=json.dumps(dict(schema='bole.actual-tokenizer-import-audit-event/v1',ordinal=self.count,event=kind,monotonic_ns=time.monotonic_ns(),payload=value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
        if self.count>=256 or len(raw)>65536 or self.bytes+len(raw)>4*2**20:raise RuntimeError('bounded import audit allowance exceeded')
        self.file.write(raw);self.file.flush();os.fsync(self.file.fileno());self.count+=1;self.bytes+=len(raw)

    def audit(self,event,args):
        if not self.active or event!='import' or not args or type(args[0])is not str:return
        name=args[0];root=name.split('.')[0]
        interesting=(name in{'torch','transformers','tokenizers'}or name.startswith(('transformers.models.auto','transformers.models.qwen','transformers.tokenization_utils','transformers.utils.import_utils','transformers.utils.generic','transformers.modeling','transformers.generation')))
        if root not in FORBIDDEN and not interesting:return
        forbidden=root in FORBIDDEN
        if name not in self.seen or forbidden:
            self.seen.add(name);stack=[];frame=sys._getframe(1)
            while frame is not None and len(stack)<48:
                stack.append(dict(file=frame.f_code.co_filename,function=frame.f_code.co_name,line=frame.f_lineno));frame=frame.f_back
            self.emit('forbidden-import-denied'if forbidden else'import-attempt',dict(module=name,filename=args[1]if len(args)>1 and type(args[1])is str else None,stack=stack))
        if forbidden:
            self.forbidden.append(name)
            raise ForbiddenImport('forbidden accelerator/inference import denied before execution: '+name)

    def check(self):
        if self.forbidden:raise ForbiddenImport('a forbidden import was attempted; library swallowing cannot qualify this process')
        if any(k.split('.')[0]in FORBIDDEN for k in sys.modules):raise ForbiddenImport('forbidden backend module exists')

    def close(self):
        if self.active:
            self.emit('closed',dict(state=state(),forbidden_attempts=self.forbidden,accelerator_attempts_denied_before_execution=True,software_qualification_accepted=False))
            self.active=False;self.file.close()
