"""Same source-pinned common precision for BOTH worker roles, outside timing."""
import functools,json,os
from pathlib import Path
def register():
 if os.environ.get('DL122_COMMON_ENABLE')!='1':return
 import api122 as A
 sr=json.loads(os.environ['DL122_PAIR_SOURCE_REF']);m=A.source(sr,pair=True);A.qualify_production(m);A.bootstrap_cann(m)
 import torch,torch_npu
 from vllm_ascend.worker.model_runner_v1 import NPUModelRunner as R
 import inspect
 A.need(A.ref(inspect.getfile(R))['sha256']=='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968','exact installed660 model runner')
 original=R.load_model
 @functools.wraps(original)
 def load(self,*a,**kw):
  with A.context(m)as(v,pm):policy=v['common106'].apply_precision(torch)
  value=original(self,*a,**kw)
  A.need(torch.npu.matmul.allow_hf32 is False and torch.npu.conv.allow_hf32 is False,'botharm common precision survives load')
  A.write(Path(os.environ['DL122_RECEIPTS'])/('common-policy-%d.json'%os.getpid()),dict(schema='deltalog.common-precision-worker/v122',source=sr,pid=os.getpid(),logical=int(torch.npu.current_device()),policy=dict(matmul_allow_hf32=False,conv_allow_hf32=False),phase='after-model-load-before-request',arm=os.environ['DL122_ARM']))
  return value
 R.load_model=load
 if os.environ['DL122_ARM']=='candidate':
  from qwen36_deltalog_production106 import register as install
  import qwen36_deltalog_production106 as package
  pm=A.obj(m['production_source_ref']);A.need(A.ref(package.__file__)==pm['files']['qwen36_deltalog_production106/__init__.py'],'same exact106 production module, not ambient alias')
  install()
