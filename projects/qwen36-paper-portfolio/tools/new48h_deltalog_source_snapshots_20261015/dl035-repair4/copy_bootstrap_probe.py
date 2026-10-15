"""Actual Devices[] installed official-module import only; no NPU allocation."""
import argparse,json,os,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 if list(Path('/dev').glob('davinci*'))or os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='':raise RuntimeError('actual Devices[] empty visibility required')
 if a.output is None or not a.output.is_dir():raise RuntimeError('existing sole owned output')
 import torch,torch_npu
 from vllm.v1.worker import mamba_utils as mu
 sys.path.insert(0,str(Path(__file__).resolve().parent));import copy_bootstrap as B
 value=B.install(mu,a.output,execute=True)
 print('MAIN_DL_COPY_IMPORT '+json.dumps(dict(actual_official_import=value,Devices=[],NPU=False,copy_executed=False),sort_keys=True),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
