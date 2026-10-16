"""Explicit008 disk-only successor; all scanner identity fences preserved."""
import hashlib,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent
def install(base,S):
 original=(P/'actual011/output_budget.py').read_bytes();derived=(P/'DERIVED_output_budget.py').read_bytes()
 if hashlib.sha256(original).hexdigest()!='44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad' :raise ValueError('actual original scanner bytes')
 # Caller additionally checks the exact frozen source manifest before this.
 if original.decode().count('LIMIT=32*1024**3')!=1 or derived.decode().replace('LIMIT=3*1024**3','LIMIT=32*1024**3')!=original.decode():raise ValueError('disk cap sole reversible source delta')
 s=importlib.util.spec_from_file_location('_long008_disk_scanner',P/'DERIVED_output_budget.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 def output_scan(root):
  parents=[Path(root)/n for n in('cpu-preflight','candidate')if(Path(root)/n).is_dir()]
  raw=v.scan(root,socket_parent=parents,ipc_source=v.IPC_SOURCE);return raw,v.consume(raw,root)
 base.output_scan=output_scan;S.c.output_scan=output_scan;S.WORKSPACE=3*base.GIB
 return dict(schema='mxr.long008.disk-contract/v1',output_GiB=3,reserve_GiB=8.5,original_scanner_sha256=hashlib.sha256(original).hexdigest(),registered_constant_deltas=1,identity_socket_inode_fences_unchanged=True)
