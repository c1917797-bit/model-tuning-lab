"""Same-image Devices[] registration/Meta only; actual build refs required."""
import argparse,hashlib,json,os,sys
from pathlib import Path
ARMS=('split_scale_v051','split_scale_sidecar_v051')
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if set(r)!={'path','bytes','sha256'}or len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('exact actual Ref3')
 return p
def run(torch,build_ref,source_ref):
 v=json.loads(checked(build_ref).read_bytes())
 if v['schema']!='deltalog-split-scale-actual-build/v051'or v['primary']is not None or v['source_manifest']!=source_ref or v['Devices']!=[]or v['NPU']is not False or [x['arm']for x in v['artifacts']]!=list(ARMS):raise ValueError('actual successful same-source pair build')
 if not all(x['exit_code']==0 and x['error']is None for x in v['commands']):raise ValueError('actual build commands')
 rows=[]
 for item in v['artifacts']:
  torch.ops.load_library(str(checked(item['library'])));ns='qwen36_deltalog_'+item['arm'];op=getattr(torch.ops,ns).decode
  for key in('Meta','PrivateUse1'):
   if not torch._C._dispatch_has_kernel_for_dispatch_key(ns+'::decode',key):raise ValueError('actual registered '+key)
  for batch in(1,16):
   E=lambda shape,dt:torch.empty(shape,dtype=dt,device='meta')
   args=[E((batch,4,128),torch.bfloat16),E((batch,4,128),torch.bfloat16),E((batch,12,128),torch.bfloat16),E((batch,12),torch.float32),E((batch,12),torch.bfloat16),E((20,12,128,128),torch.float32),E((20,4,7,128),torch.bfloat16),E((20,12,7,128),torch.float32),E((20,12,16),torch.float32),E((20,12,16),torch.float32),E((20,12,16),torch.int32),E((batch+1,),torch.int32),E((batch,),torch.int32)]
   if item['arm']==ARMS[1]:args.append(E((batch,12,128),torch.float32))
   z=op(*args)
   if tuple(z.shape)!=(batch,12,128)or z.dtype!=torch.bfloat16 or z.device.type!='meta':raise ValueError('actual Meta ABI')
   rows.append(dict(arm=item['arm'],batch=batch,arguments=len(args),shape=list(z.shape),dtype=str(z.dtype)))
 return dict(schema='deltalog.split-scale-actual-Meta/v051',build=build_ref,source=source_ref,libraries=[x['library']for x in v['artifacts']],rows=rows,pass_gate=True,NPU=False,numeric_qualified=False,model_ready=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--build-ref');p.add_argument('--source-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 if list(Path('/dev').glob('davinci*'))or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='':raise ValueError('actual Devices[] CPU Meta environment')
 import torch
 v=run(torch,json.loads(a.build_ref),json.loads(a.source_ref));out=Path(a.output)
 with out.open('x',encoding='utf8')as f:json.dump(v,f,sort_keys=True);f.write('\n')
if __name__=='__main__':raise SystemExit(main())
