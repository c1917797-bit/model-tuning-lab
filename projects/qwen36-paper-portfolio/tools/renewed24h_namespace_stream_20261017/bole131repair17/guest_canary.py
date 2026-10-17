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
 with a.output.open('x',encoding='utf8')as f:json.dump(dict(schema='mxr.actual-owned-all4-tiny/v1',pid=os.getpid(),rows=rows,physical_proven_by_this_child=False,NPU=True,model=False),f);f.write('\n')
if __name__=='__main__':main()


