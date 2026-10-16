"""Mechanical source-only metadata refresh; no resource/device operation."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 import packet_contract as C
 b=(P/'external_output_policy.py').read_bytes();assert len(b)==7175 and hashlib.sha256(b).hexdigest()=='f85f745cb9362d69e70cfd35a9c894d97fc7069297d3694c8b8c57107126191f'
 old='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-model-precast-smoke-new48h-v1-045-repair1'
 p=P/'COMMANDS.json';v=json.loads(p.read_bytes())
 def walk(x):
  if type(x)is str:return x.replace(old,C.ROOT)
  if type(x)is list:return[walk(y)for y in x]
  if type(x)is dict:return{k:walk(y)for k,y in x.items()}
  return x
 v=walk(v);v.update(output=C.OUTPUT,external_output_enable='MXR_DL_EXTERNAL_OUTPUT008_ENABLE=1',Docker_reserve_GiB=8.5,opt_workspace_GiB=32,opt_reserve_GiB=8.5,sameimage_CPU_pending=True)
 v['execute']['environment']={'MXR_DL_EXTERNAL_OUTPUT008_ENABLE':'1'}
 p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
 p=P/'RESOURCE_PREPARATION.json';v=json.loads(p.read_bytes());v.update(pending_shared_helper_final=False,helper_sha256='f85f745cb9362d69e70cfd35a9c894d97fc7069297d3694c8b8c57107126191f',source_only_prepared=True,sameimage_CPU_pending=True,actual_resource_admission=False);p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
if __name__=='__main__':main()
