"""Default-OFF exact official copy patch, without full worker package import."""
import hashlib,importlib,importlib.util,inspect,json,os,time
from pathlib import Path
PATCH='/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_mamba_utils.py'
KERNEL='/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/batch_memcpy.py'
PATCH_SHA='a8862c3509f698c05cdeba5aa408a28e506349eff97801b28161569b8e3c9778'
KERNEL_SHA='c434b023102d1804eec0eb63b6d62b0f9343cb831e6ef82f6151efcdf96c5965'
MU_SHA='1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3'
def checked(path,n,sha):
 p=Path(path);b=p.read_bytes()
 if len(b)!=n or hashlib.sha256(b).hexdigest()!=sha or p.is_symlink():raise RuntimeError('exact actual copy source '+str(p))
 return dict(path=str(p),bytes=len(b),sha256=sha)
def marker(root,stage,**fields):
 p=Path(root)/('COPY_STAGE-'+stage+'-'+str(time.time_ns())+'.json')
 wire=(json.dumps(dict(stage=stage,pid=os.getpid(),time_ns=time.time_ns(),**fields),sort_keys=True,allow_nan=False)+'\n').encode()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:os.write(fd,wire);os.fsync(fd)
 finally:os.close(fd)
 return dict(path=str(p),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
def install(mu,root,*,execute=False):
 if not execute:raise RuntimeError('official copy bootstrap OFF')
 pr=checked(PATCH,12252,PATCH_SHA);kr=checked(KERNEL,1089,KERNEL_SHA)
 mr=checked(mu.__file__,36999,MU_SHA);old=mu.do_mamba_copy_block
 if Path(inspect.getsourcefile(old)).resolve()!=Path(mu.__file__).resolve():raise RuntimeError('must bootstrap before DeltaLog copy wrapper')
 marker(root,'bootstrap-before',patch=pr,kernel=kr,mamba=mr)
 # Execute the COMPLETE installed official module by exact source path. This
 # does not import vllm_ascend.patch.worker.__init__ or fabricate sys.modules.
 s=importlib.util.spec_from_file_location('_dl024_exact_official_mamba_patch',PATCH);p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
 k=importlib.import_module('vllm_ascend.ops.triton.batch_memcpy')
 if p._can_launch_triton_batch_memcpy()is not True:raise RuntimeError('reviewed910B native Triton path only')
 if mu.batch_memcpy is not p._batch_memcpy_triton or mu.batch_memcpy_kernel is not k.batch_memcpy_kernel or p.batch_memcpy_kernel is not k.batch_memcpy_kernel:raise RuntimeError('official actual callable identity')
 if mu.do_mamba_copy_block is not old or old.__globals__['batch_memcpy']is not mu.batch_memcpy:raise RuntimeError('original do-copy must resolve patched native global')
 fn=getattr(k.batch_memcpy_kernel,'fn',k.batch_memcpy_kernel)
 if Path(inspect.getsourcefile(fn)).resolve()!=Path(KERNEL):raise RuntimeError('actual Ascend kernel Python origin')
 checked(PATCH,12252,PATCH_SHA);checked(KERNEL,1089,KERNEL_SHA)
 result=dict(patch=pr,kernel=kr,mamba=mr,batch_memcpy=p._batch_memcpy_triton.__qualname__,kernel_callable=fn.__qualname__,BLOCK_SIZE=8192,official_preprocess_and_postprocess_also_loaded=True,full_worker_parent_import_requested=False,NPU_copy_executed=False)
 marker(root,'bootstrap-after',proof=result);return result
