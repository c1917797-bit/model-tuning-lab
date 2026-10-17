"""Thin reuse of existing packed3 exclusive-stage/link/fsync publisher."""
import hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent
DONOR_SHA='996122e469ec64fc2c8bc1c0bfb077c1b675cb07c157206c697e02feb67a3dde'
def donor():
 p=P/'dependencies/publication_common.py';b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=DONOR_SHA:raise ValueError('exact repository existing publication donor')
 s=importlib.util.spec_from_file_location('_existing_packed3_atomic_snapshot',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def publish(path,value):
 raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 if len(raw)>256*1024:raise ValueError('existing snapshot output accounting: max256KiB each; retained stage counted')
 # No final pathname exists until complete exclusive stage has been fsynced.
 # Existing binary retains staging on success/failure; never overwrites final.
 return donor().binary(Path(path),[raw],len(raw))
