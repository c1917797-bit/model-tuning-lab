"""One default-OFF HF32 policy plugin, required identically for BOTH pair arms."""
import hashlib,json,os
from pathlib import Path
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if not p.is_absolute()or p.is_symlink()or(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('exact common-policy source')
 return b
def environment(base,arm,receipt_root,source_ref):
 if arm not in('dense','candidate'):raise ValueError('paired arm only')
 e=dict(base);legacy={'mxr_observerless','mxr_diag16_gdn_shadow','mxr_source_bound_capture','mxr_source_bound_solve','mxr_block_refinement044'};plugins=[x for x in e.get('VLLM_PLUGINS','').split(',')if x and x not in legacy]
 plugins+=['mxr_common_precision044']+(['mxr_block_refinement044']if arm=='candidate'else[])
 e.update(MXR_COMMON_PRECISION044_ENABLE='1',MXR_COMMON_PRECISION044_SOURCE_REF=json.dumps(source_ref,separators=(',',':')),MXR_COMMON_PRECISION044_RECEIPT_ROOT=str(receipt_root),MXR_COMMON_PRECISION044_ARM=arm,VLLM_PLUGINS=','.join(dict.fromkeys(plugins)),MXR_OBSERVERLESS_ENABLE='1'if arm=='candidate'else'0',MXR_BLOCK_REFINEMENT044_ENABLE='1'if arm=='candidate'else'0',MXR_OBSERVERLESS_SOURCE_REF=json.dumps(source_ref,separators=(',',':')))
 e.update(MXR_ONCE_CORRECTNESS_ENABLE='0',MXR_DIAG16_GDN_SHADOW_ENABLE='0',MST_MXR_CAPTURE_ENABLE='0',MST_MXR_SOLVE_ENABLE='0')
 return e
def apply(torch):
 matmul=getattr(getattr(torch,'npu',None),'matmul',None)
 if matmul is None or type(getattr(matmul,'allow_hf32',None))is not bool:raise ValueError('actual registered torch.npu.matmul.allow_hf32 API')
 before=matmul.allow_hf32;matmul.allow_hf32=False
 if matmul.allow_hf32 is not False:raise ValueError('real policy readback failed')
 return dict(before=before,allow_hf32=False,scope='common Torch matmul policy, not vendor-internal precision theorem')
def pair_gate(receipts,expected_pids,source_ref):
 for arm in('dense','candidate'):
  wanted=expected_pids[arm]
  if len(set(wanted))!=4:raise ValueError('actual four worker PID mapping required')
  rows=[r for r in receipts if r['arm']==arm and r['pid']in wanted]
  if len(rows)!=4 or{r['pid']for r in rows}!=set(wanted):raise ValueError('all4 effective policy receipts for BOTH arms')
  if any(r['source']!=source_ref or r['schema']!='mxr.common-HF32OFF/v044'or r['allow_hf32']is not False for r in rows):raise ValueError('shared source/readback drift')
 return dict(common_HF32OFF_all4_both_arms=True,numerical_qualification=False,performance_result=False)
def register():
 if os.environ.get('MXR_COMMON_PRECISION044_ENABLE')!='1':return None
 sr=json.loads(os.environ['MXR_COMMON_PRECISION044_SOURCE_REF']);m=json.loads(checked(sr));own=m['files']['common_precision.py']
 if m['schema']!='mxr.observerless-source/v1'or m['default_enabled']is not False:raise ValueError('actual defaultOFF source manifest')
 if Path(own['path']).resolve()!=Path(__file__).resolve():raise ValueError('same deployed common policy module')
 checked(own)
 import torch,torch_npu
 value=apply(torch);pid=os.getpid();arm=os.environ['MXR_COMMON_PRECISION044_ARM']
 if arm not in('dense','candidate'):raise ValueError('actual declared paired arm')
 root=Path(os.environ['MXR_COMMON_PRECISION044_RECEIPT_ROOT'])
 if not root.is_absolute()or not root.is_dir()or root.is_symlink():raise ValueError('actual owned existing receipt leaf')
 target=root/('common-precision-%d.json'%pid);row=dict(value,schema='mxr.common-HF32OFF/v044',source=sr,pid=pid,arm=arm,stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),model_ready=False)
 if target.exists():
  old=json.loads(target.read_bytes())
  if any(old[k]!=row[k]for k in('source','pid','arm','allow_hf32')):raise ValueError('common policy receipt cannot be rebound')
  return old
 with target.open('x')as f:json.dump(row,f,sort_keys=True);f.write('\n')
 return row
