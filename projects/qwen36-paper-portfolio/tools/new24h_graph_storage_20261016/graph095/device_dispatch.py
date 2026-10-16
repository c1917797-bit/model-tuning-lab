"""Actual original dispatcher, no fake registration or Worker dependency."""
import hashlib,inspect,sys
from pathlib import Path
SHA='de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47'
def prove(module,torch):
 path=Path(inspect.getsourcefile(module)).resolve()
 if hashlib.sha256(path.read_bytes()).hexdigest()!=SHA:raise ValueError('full original device_op source')
 if module.DeviceOperator is not module.get_device_adaptor() or module.DeviceOperator is not module.BaseDeviceAdaptor:raise ValueError('actual910B original BaseDeviceAdaptor')
 methods={}
 for name in ('chunk_scaled_dot_kkt_fwd','solve_tril_16x16'):
  fn=getattr(module.DeviceOperator,name)
  if inspect.getsourcefile(fn)!=str(path)or not callable(fn):raise ValueError('original static dispatcher method')
  methods[name]=dict(module=fn.__module__,name=fn.__qualname__,source=str(path),source_sha256=SHA)
 extension=sys.modules.get('vllm_ascend.vllm_ascend_C')
 if extension is None or not getattr(extension,'__file__',None):raise ValueError('actual native extension loaded by enable_custom_op')
 binary=Path(extension.__file__).resolve()
 identity=dict(path=str(binary),bytes=binary.stat().st_size,sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
 schemas={name:str(getattr(torch.ops._C_ascend,name).default._schema)for name in ('chunk_gated_delta_rule_fwd_h','chunk_fwd_o')}
 return dict(source=str(path),source_sha256=SHA,selected_adaptor=module.DeviceOperator.__name__,worker_initialization_required=False,methods=methods,native_extension=identity,native_schemas=schemas)
