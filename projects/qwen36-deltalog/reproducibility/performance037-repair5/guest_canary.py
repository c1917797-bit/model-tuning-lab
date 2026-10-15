"""Real mapped all-four device smoke; never model/algorithm qualification."""
import json,os
from pathlib import Path
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='0,1,2,3':raise ValueError('actual owned mapping required')
 import torch,torch_npu
 if torch.npu.device_count()!=4:raise ValueError('actual all-four logicaldevices')
 rows=[]
 for logical in range(4):
  device='npu:'+str(logical);out=(torch.tensor([1.,2.],device=device)+3).cpu().tolist()
  if out!=[4.,5.]:raise ValueError('actual tinycanary')
  rows.append(dict(logical=logical,values=out))
 torch.npu.synchronize()
 # True installed parser, after genuine hardware canary and BEFORE allocation.
 # No fake architecture/module stubs and no full model/EngineArgs construction.
 from vllm.engine.arg_utils import EngineArgs
 from vllm.utils.argparse_utils import FlexibleArgumentParser
 parser=EngineArgs.add_cli_args(FlexibleArgumentParser())
 parsed=parser.parse_args(['--no-async-scheduling','--enforce-eager','--mamba-cache-mode','none','--no-enable-prefix-caching'])
 if parsed.async_scheduling is not False or parsed.enforce_eager is not True or parsed.mamba_cache_mode!='none' or parsed.enable_prefix_caching is not False:raise ValueError('actual sync/eager/PDCoff parser ABI')
 with a.output.open('x',encoding='utf8')as f:json.dump(dict(schema='deltalog.actual-owned-all4-canary/v033',pid=os.getpid(),rows=rows,physical_proven_by_this_child=False,NPU=True,model=False,actual_sync_parser_pass=True),f);f.write('\n')
if __name__=='__main__':main()


