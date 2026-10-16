"""Native identity/precision receipt only on host-owned outside-timing signal."""
import hashlib,importlib,inspect,json,os,signal,time
from pathlib import Path
from contract090 import source,write,need
from snapshot_publication import publish as atomic_publish
PINS={'vllm_ascend.ops.gdn':'d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816','vllm_ascend.ops.triton.fla.chunk':'6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5','vllm_ascend.ops.triton.fla.solve_tril':'2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0','vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn':'885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'}
def register():
 if os.environ.get('DENSE_OPPORTUNITY090_ENABLE')!='1':return None
 sr=json.loads(os.environ['DENSE_OPPORTUNITY090_SOURCE_REF']);source(sr);root=Path(os.environ['DENSE_OPPORTUNITY090_RECEIPT_ROOT']);need(root.is_dir(),'owned receipt root')
 import torch,torch_npu
 torch.npu.matmul.allow_hf32=False;need(torch.npu.matmul.allow_hf32 is False,'actual common HF32OFF readback')
 prior=signal.getsignal(signal.SIGUSR1)
 if callable(prior):
  need(getattr(prior,'_dense090_source',None)==sr and inspect.getsourcefile(prior)==__file__,'never clobber foreign signal handler')
  if prior._dense090_pid==os.getpid():return prior
  # Fork may inherit only this exact owned source handler. New worker PID gets
  # its own ordinal; an unrelated handler/source is never silently replaced.
 else:need(prior in(signal.SIG_DFL,signal.SIG_IGN),'no foreign signal clobber')
 ordinal=0
 def publish(*_):
  nonlocal ordinal
  modules={};sources={}
  for name,digest in PINS.items():
   mod=importlib.import_module(name);p=Path(inspect.getsourcefile(mod)).resolve();b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==digest,'actual native framework source');modules[name]=mod;sources[name]=dict(path=str(p),bytes=len(b),sha256=digest)
  g=modules['vllm_ascend.ops.gdn'];chunk=modules['vllm_ascend.ops.triton.fla.chunk'];solve=modules['vllm_ascend.ops.triton.fla.solve_tril'];target=modules['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn'].QwenGatedDeltaNetAttention
  need(target._forward_core is g.AscendGatedDeltaNetAttention._forward_core and inspect.unwrap(target._forward_core)is target._forward_core,'actual copied Qwen target is unwrapped original native core')
  need(chunk.solve_tril is solve.solve_tril and inspect.getsourcefile(inspect.unwrap(chunk.solve_tril))==solve.__file__,'actual original native inverse, not candidate')
  need(torch.npu.matmul.allow_hf32 is False,'same actualHF32 policy throughout measurement')
  ordinal+=1;atomic_publish(root/('worker-%d-snapshot-%d.json'%(os.getpid(),ordinal)),dict(schema='dense.native-worker-snapshot/v090',source_ref=sr,pid=os.getpid(),ordinal=ordinal,proc_stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),framework_sources=sources,native_core=True,native_inverse=True,allow_hf32=False,observed_epoch=time.time(),tensor_capture=False,qualification=False))
 publish._dense090_source=sr;publish._dense090_pid=os.getpid()
 signal.signal(signal.SIGUSR1,publish);return publish
