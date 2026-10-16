"""Standalone small smoke: one complete payload <=3GiB, never long raw."""
import hashlib,importlib.util,shutil
from pathlib import Path
P=Path(__file__).resolve().parent
OUT=Path('/opt/host/vnf/austinov/run-mxr-2k-memory32-model073repair6-main-NEW24H_MXR073R6_001')
def need(v,m):
 if not v:raise ValueError(m)
def preflight(root):
 root=Path(root);need(root==OUT and root.parent.is_dir()and not root.exists(),'new exact absent small-smoke output under existing opt parent')
 need(all(not p.is_symlink()for p in [root.parent,*root.parent.parents]),'no symlink parent')
 free=shutil.disk_usage(root.parent).free;need(free>=32*2**30,'fresh opt free >=32GiB; no automatic long successor')
 return dict(opt_free_bytes=free,required_initial_bytes=32*2**30,total_payload_cap_bytes=12*2**30,reserve_bytes=int(8.5*2**30),long_raw_enabled=False)
def install(base,S,Owned,root):
 original=(P/'actual011/output_budget.py').read_bytes();derived=(P/'DERIVED_output_budget.py').read_bytes()
 need(hashlib.sha256(original).hexdigest()=='44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad','actual original scanner')
 need(derived.decode().replace('LIMIT=12*1024**3','LIMIT=32*1024**3')==original.decode(),'sole scanner cap source inverse')
 s=importlib.util.spec_from_file_location('_short068_disk_scanner',P/'DERIVED_output_budget.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 def output_scan(path):
  parents=[Path(path)/n for n in('cpu-preflight','candidate')if(Path(path)/n).is_dir()]
  raw=v.scan(path,socket_parent=parents,ipc_source=v.IPC_SOURCE);return raw,v.consume(raw,path)
 base.output_scan=output_scan;S.c.output_scan=output_scan;S.WORKSPACE=12*base.GIB
 resource=Owned.resources
 def resources(self,initial=False):
  value=resource(self,initial)
  need(shutil.disk_usage(Path(root).parent).free>=int(8.5*2**30)+(12*2**30 if initial else 0),'original8.5GiB shared reserve plus complete3GiB payload at admission')
  return value
 Owned.resources=resources
 return dict(schema='mxr.small-3GiB-smoke-disk/v068',total_payload_cap_GiB=12,minimum_initial_opt_GiB=32,long_raw_enabled=False,no_automatic_long_successor=True)
