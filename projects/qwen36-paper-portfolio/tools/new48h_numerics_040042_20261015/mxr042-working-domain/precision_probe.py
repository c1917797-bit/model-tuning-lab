"""Explicit Devices[] actual vendor API check, not FP32 arithmetic proof."""
import json,os,sys
from pathlib import Path
def main():
 if '--execute'not in sys.argv:print('{"enabled":false,"NPU":false}');return 0
 if list(Path('/dev').glob('davinci*'))or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0':raise RuntimeError('Devices[] actual noautoload preflight only')
 import torch,torch_npu
 matmul=getattr(getattr(torch,'npu',None),'matmul',None)
 if matmul is None or type(getattr(matmul,'allow_hf32',None))is not bool:raise RuntimeError('actual HF32 policy API missing: NPU correction not admitted')
 before=matmul.allow_hf32;matmul.allow_hf32=False
 if matmul.allow_hf32 is not False:raise RuntimeError('actual HF32-off readback failed')
 matmul.allow_hf32=before
 print(json.dumps(dict(schema='mxr.cpu-vendor-precision-API/v042',allow_hf32_API=True,before=before,roundtrip=True,FP32_NPU_arithmetic_qualified=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
