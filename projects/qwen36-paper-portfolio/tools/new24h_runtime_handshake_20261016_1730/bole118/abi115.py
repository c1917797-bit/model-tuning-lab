"""Called inside MAIN's existing Devices[] child after real CANN bootstrap.

No stubs, device selection, runtime availability query or NPU tensor creation.
Import failures must be saved by that child's original failure handling.
"""
import os
from pathlib import Path
from probe115 import checked,ref,write,REQUIRED


def record(torch,torch_npu,header_ref,out):
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci*')):raise ValueError('actual Devices[] CPU visibility contract')
    header=checked(header_ref)
    if not str(header).startswith('/usr/local/Ascend/cann-9.1.0/')or 'fused_infer_attention_score'not in header.name:raise ValueError('actual CANN9.1 FIA installed header')
    schema=torch.ops.npu.npu_fused_infer_attention_score.default._schema
    names=[arg.name for arg in schema.arguments]
    if schema.name!='npu::npu_fused_infer_attention_score'or not set(REQUIRED)<=set(names):raise ValueError('actual installed schema lacks required FIA arguments')
    fds=[]
    for path in Path('/proc/self/fd').iterdir():
        try:value=os.readlink(path)
        except FileNotFoundError:continue
        if any(s in value for s in('davinci','devmm_svm','hisi_hdc')):fds.append(value)
    if fds:raise ValueError('actual CPU ABI probe opened device FDs')
    receipt=dict(schema='bole.actual-FIA-installed-ABI/v115',NPU=False,Devices=[],no_device_fds=True,operator=schema.name,argument_names=names,actual_schema=str(schema),header_ref=header_ref,torch_npu_python_ref=ref(torch_npu.__file__),torch_python_ref=ref(torch.__file__),torch_version=torch.__version__,arbitrary_mask_supported_on_NPU=None)
    write(out,receipt);return receipt
