"""Exact V16 timing-independent RAM/cache diagnostic source delta."""
from pathlib import Path
import copy,hashlib

ROOT=Path(__file__).resolve().parent
PARENT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_profile_disk_ledger_v16_prepare_20261024/prepared-source-short8-v16")
def need(v,s):
 if not v:raise ValueError(s)
def adapt(files):
 out=dict(files);delta={}
 for n in ('fa_block_store.py','worker_resource_v2.py','ram_terminal_join.py'):
  need(out[n]==(PARENT/n).read_bytes(),'exact V16 operand '+n)
  out[n]=(ROOT/n).read_bytes()
 out['fa_cache_advisory.py']=(ROOT/'fa_cache_advisory.py').read_bytes()
 text=out['server090.py'].decode()
 before=" arm=m.get('performance_arm')\n"
 after=before+""" if m.get('own_fa_cache_advisory')is not None:
  import fa_cache_advisory as CACHE
  C.need(C.ref(CACHE.__file__)==m['files']['fa_cache_advisory.py'] and
         m['own_fa_cache_advisory']==CACHE.CONTRACT and arm=='bole',
         'actual source-owned qualification FA cache opt-in')
  e[CACHE.FLAG]='1'
"""
 need(text.count(before)==1,'one actual server environment seam');out['server090.py']=text.replace(before,after,1).encode()
 text=out['preflight114.py'].decode()
 before=" conv_geometry=CR.preflight(C,m,sr,expected)\n"
 after=before+" import fa_cache_advisory as CACHE\n cache_advisory_preflight=CACHE.preflight(C,m,sr)\n"
 need(text.count(before)==1,'one actual preflight seam');text=text.replace(before,after,1)
 before="return dict(native_conv_geometry=conv_geometry,"
 need(text.count(before)==1,'one actual preflight result')
 out['preflight114.py']=text.replace(before,"return dict(own_fa_cache_contract=cache_advisory_preflight,native_conv_geometry=conv_geometry,",1).encode()
 for n,b in out.items():
  if files.get(n)!=b:delta[n]=dict(before=files.get(n),after=b)
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,row in delta.items():
  need(out[n]==row['after'],'exact cache delta inverse '+n)
  if row['before']is None:del out[n]
  else:out[n]=row['before']
 return out
