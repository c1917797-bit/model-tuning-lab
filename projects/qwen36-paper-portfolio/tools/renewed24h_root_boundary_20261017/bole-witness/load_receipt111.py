"""Default-OFF native-MTP LOAD evidence only; never a BOLE algorithm plugin.

No forward, parameter value, sampler or scheduler mutation. Caller must use
an existing owned worker and a new sole-owned receipt directory.
"""
import functools,hashlib,importlib,inspect,json,os,time
from pathlib import Path
EXPECTED=dict(path='/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5_mtp.py',bytes=17170,sha256='99c19c38107a3cade90aa5a0f86396f6a25b2defcf8a538fbed521f7567eb743')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def publish(root,payload):
 need(root.is_dir()and root.is_absolute()and not any(p.is_symlink()for p in(root,*root.parents)),'precreated sole-owned non-symlink receipt directory')
 final=root/('MTP-LOAD-%d-%d.json'%(os.getpid(),time.time_ns()));stage=final.with_suffix('.stage')
 with stage.open('x',encoding='utf-8',newline='\n')as f:json.dump(payload,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.link(stage,final);fd=os.open(str(root),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return ref(final)
def install(cls,root,source_ref):
 """Dependency-injected class seam for tests; production register pins real class."""
 old=cls.load_weights;need(not hasattr(old,'_bole111_load_receipt'),'single receipt installer')
 @functools.wraps(old)
 def load(self,weights):
  selected=[]
  def observed():
   for name,value in weights:
    if name.startswith('mtp.'):
     need(len(selected)<128,'bounded actual MTP weight metadata')
     selected.append(dict(name=name,shape=list(value.shape),dtype=str(value.dtype),numel=value.numel()))
    yield name,value
  result=old(self,observed())
  need(type(result)is set and all(type(n)is str for n in result),'actual original loader loaded-name return ABI')
  publish(root,dict(schema='bole.native-MTP-load-observation/v111',pid=os.getpid(),actual_class=type(self).__module__+'.'+type(self).__qualname__,actual_original_source=source_ref,observer_source=ref(Path(__file__).resolve()),input_mtp_weights=selected,loaded_names=sorted(result),method='native-linear-MTP-baseline',BOLE=False,forward_modified=False,model_or_numerical_qualified=False))
  return result
 load._bole111_load_receipt=True;cls.load_weights=load
 def restore():
  need(cls.load_weights is load,'no foreign modification before restore');cls.load_weights=old
 return restore
def register():
 if os.environ.get('BOLE111_MTP_LOAD_AUDIT_ENABLE')!='1':return
 source=json.loads(os.environ['BOLE111_MTP_SOURCE_REF']);need(source==EXPECTED,'exact actual660 Qwen MTP source')
 p=Path(source['path']);need(ref(p)==source,'actual installed MTP source bytes/SHA')
 module=importlib.import_module('vllm.model_executor.models.qwen3_5_mtp');cls=module.Qwen3_5MTP
 need(Path(inspect.getsourcefile(cls.load_weights)).resolve()==p.resolve(),'actual MTP class loader receiver')
 return install(cls,Path(os.environ['BOLE111_MTP_LOAD_RECEIPT_ROOT']),source)
