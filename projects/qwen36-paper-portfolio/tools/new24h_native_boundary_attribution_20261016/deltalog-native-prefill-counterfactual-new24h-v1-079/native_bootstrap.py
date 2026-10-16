"""Normal package-first import, only called after the real NPU canary."""
import hashlib,importlib,inspect,traceback
from pathlib import Path
ROOT=Path('/vllm-workspace/vllm-ascend/vllm_ascend')
def package_first(importer=importlib.import_module):
 ops=importer('vllm_ascend.ops')
 device=importer('vllm_ascend.device.device_op')
 return ops,device
def actual():
 result=dict(schema='good-enough.actual-native-import/v062',order=['vllm_ascend.ops','vllm_ascend.device.device_op'],fake_modules=False,import_pass=False,error=None,traceback=None,sources={})
 try:
  ops,device=package_first()
  for name,module in(('ops/__init__.py',ops),('device/device_op.py',device)):
   path=Path(inspect.getsourcefile(module)).resolve()
   if path!=ROOT/name:raise ValueError('actual pinned installed package origin')
   wire=path.read_bytes();result['sources'][name]=dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
  if result['sources']['device/device_op.py']['sha256']!='de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47'or not hasattr(device,'DeviceOperator'):raise ValueError('actual full DeviceOperator source/definition')
  # Real worker init_device calls this helper after set_device/distributed init.
  props=importlib.import_module('vllm_ascend.ops.triton.triton_utils')
  path=Path(inspect.getsourcefile(props)).resolve();wire=path.read_bytes()
  if path!=ROOT/'ops/triton/triton_utils.py' or hashlib.sha256(wire).hexdigest()!='f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4':raise ValueError('actual triton properties helper source')
  result['sources']['ops/triton/triton_utils.py']=dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
  props.init_device_properties_triton()
  cores=dict(aicore=props.get_aicore_num(),vectorcore=props.get_vectorcore_num())
  if not all(type(v)is int and v>0 for v in cores.values()):raise ValueError('actual detected positive core counts')
  result['device_properties']=cores
  result['device_properties_initialized']=True
  result['import_pass']=True
 except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc())
 return result
