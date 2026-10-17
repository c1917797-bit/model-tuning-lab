"""Default OFF, native-only diagnostic. No DeltaLog installer is called."""
import base64,hashlib,inspect,json,os
from pathlib import Path
_registration_state="disabled"
def register():
 global _registration_state
 if os.environ.get('DL101R12_NATIVE_OBSERVATION_ENABLE')!='1':return
 import owner_overlay as O,bootstrap101r9 as B,native_footprint101r12 as F
 sr=json.loads(os.environ['DL101R12_SOURCE_REF']);m=O.current(sr);B.install(m,Path(__file__).resolve().parent)
 O.need(O.obj_file(m['files']['native_observer_plugin101r12.py'])==Path(__file__).resolve(),'actual sole observer plugin')
 O.need(os.environ.get('QWEN36_DELTALOG_SERVICE023_ENABLE')=='0'and os.environ.get('QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE')=='0'and os.environ.get('QWEN36_DELTALOG_TENSOR026_ENABLE')=='0','native-only no service/mirror/tensor hook')
 # Exact official dependency order used by the actual R11 runtime registration.
 from vllm_ascend.utils import enable_custom_op
 import vllm_ascend.ops.gdn as native_gdn
 from vllm.v1.worker import mamba_utils as native_mamba
 from vllm_ascend.worker.model_runner_v1 import NPUModelRunner as N
 from vllm_ascend.worker.block_table import BlockTable
 from vllm.forward_context import get_forward_context
 from vllm.distributed.parallel_state import get_tensor_model_parallel_rank
 import torch_npu
 proof=dict(runner=F.source_file(N,F.RUNNER_SHA),block_table=F.source_file(BlockTable,F.BLOCK_SHA))
 _,layout_bytes=F.exact(m['files']['LAYOUT_SOURCE_EVIDENCE101R12.json']);layout=json.loads(layout_bytes);header=base64.b64decode(layout['acl_base_rt.h']['base64']);O.need(hashlib.sha256(header).hexdigest()==F.ACL_SHA and b'ACL_FORMAT_ND = 2' in header,'actual exact ACL enum ND2 source')
 init_path=Path(torch_npu.__file__);init=init_path.read_bytes();O.need((len(init),hashlib.sha256(init).hexdigest())==(layout['torch_npu_init.py']['bytes'],layout['torch_npu_init.py']['sha256']),'actual same-image torch_npu package source');proof['torch_npu_package_ref']=dict(path=str(init_path),bytes=len(init),sha256=hashlib.sha256(init).hexdigest())
 op=getattr(torch_npu,'get_npu_format',None);schema=dict(available=op is not None,python_type=str(type(op)),schemas={str(k):str(v)for k,v in getattr(op,'_schemas',{}).items()})
 print('DL101R12_ACTUAL_FORMAT_API '+json.dumps(schema),flush=True);O.need(callable(op),'actual sameimage get_npu_format dispatcher missing; no model load')
 proof.update(layout_source_ref=m['files']['LAYOUT_SOURCE_EVIDENCE101R12.json'],acl_header_sha256=F.ACL_SHA,actual_format_api=schema)
 O.need(N._prepare_inputs.__code__.co_filename==proof['runner']['path']and N._model_forward.__code__.co_filename==proof['runner']['path']and not getattr(N,'_deltalog023_wired',False)and not getattr(N,'_dl025_trace',False),'original direct native prepare/forward methods, no wrapped DL transform')
 F.exact(m['files']['native_footprint101r12.py']);F.install(N,get_forward_context,sr,get_tensor_model_parallel_rank,proof,op);N._native_format_api101r12=schema
 _registration_state='native-installed'
 print('DL101R12_NATIVE_INSTALLED '+json.dumps(dict(source=sr,proof=proof,pid=os.getpid(),qualified=False)),flush=True)
