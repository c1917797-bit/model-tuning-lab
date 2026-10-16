"""Actual dispatcher reflection only; no device selection or tensor operation."""
import os
from pathlib import Path
from probe115 import checked,ref,write,REQUIRED


def select(packet,required,operator_name):
    family=packet._schemas
    if not isinstance(family,dict):raise ValueError('actual OpOverloadPacket._schemas must be dict')
    matches=[]
    for overload,schema in family.items():
        if schema.name==operator_name and set(required)<={arg.name for arg in schema.arguments}and schema.is_mutable is False:
            matches.append((overload,schema))
    chosen=next((row for row in matches if row[0]==''),None)
    if chosen is None:
        if len(matches)!=1:raise ValueError('unambiguous functional actual overload required')
        chosen=matches[0]
    return chosen,dict((name,str(schema))for name,schema in family.items())


def record(t,torch_npu,sr,header_ref,out):
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci*')):raise ValueError('actual Devices[] ABI environment')
    header=checked(header_ref)
    if not str(header).startswith('/usr/local/Ascend/cann-9.1.0/')or 'fused_infer_attention_score'not in header.name:raise ValueError('actual installed CANN9.1 header')
    (overload,schema),family=select(t.ops.npu.npu_fused_infer_attention_score,REQUIRED,'npu::npu_fused_infer_attention_score')
    if not callable(getattr(torch_npu,'npu_fused_infer_attention_score',None)):raise ValueError('actual TorchNPU functional entry missing')
    fds=[]
    for path in Path('/proc/self/fd').iterdir():
        try:value=os.readlink(path)
        except FileNotFoundError:continue
        if any(x in value for x in('davinci','devmm_svm','hisi_hdc')):fds.append(value)
    if fds:raise ValueError('Devices[] ABI probe opened device FDs')
    value=dict(schema='bole.actual-FIA-installed-ABI/v115',source=sr,NPU=False,Devices=[],no_device_fds=True,operator=schema.name,overload=overload,argument_names=[arg.name for arg in schema.arguments],actual_schema=str(schema),schema_family=family,header_ref=header_ref,torch_npu_python_ref=ref(torch_npu.__file__),torch_python_ref=ref(t.__file__),torch_version=t.__version__,operator_executed=False,arbitrary_mask_supported_on_NPU=None)
    write(out,value);return value


def runtime(t,abi):
    (overload,schema),family=select(t.ops.npu.npu_fused_infer_attention_score,REQUIRED,'npu::npu_fused_infer_attention_score')
    if overload!=abi['overload']or str(schema)!=abi['actual_schema']or family!=abi['schema_family']:raise ValueError('runtime actual schema family differs from releasedCPU ABI')
    return schema
