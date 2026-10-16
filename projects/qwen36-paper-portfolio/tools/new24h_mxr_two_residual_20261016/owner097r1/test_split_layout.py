"""Actual entry and all eight controls in physically disjoint roots."""
import hashlib,importlib.util,json,os,shutil,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
with tempfile.TemporaryDirectory()as td:
 root=Path(td);g=root/'guest-v1';o=root/'owned-v1';g.mkdir();o.mkdir()
 gm=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());om=json.loads((P/'OWNED_SOURCE_MANIFEST.json').read_bytes())
 for d,m in((g,gm),(o,om)):
  for n in m['files']:
   p=d/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/n,p);m['files'][n]=ref(p)
  m['root']=str(d)
 (g/'SOURCE_MANIFEST.json').write_text(json.dumps(gm));om['guest_source']=ref(g/'SOURCE_MANIFEST.json')
 (o/'SOURCE_MANIFEST.json').write_text(json.dumps(om));sr=ref(o/'SOURCE_MANIFEST.json')
 assert not(g/'owner097.py').exists()and not(o/'two_residual097.py').exists()
 E=load(o/'cpu_entry097.py','_split_entry');original=E.load;reached=[]
 class Boundary(Exception):pass
 def checkedload(r,n):
  v=original(r,n)
  if n=='_092_unchanged084':
   def stop():
    assert sys.argv[0]==gm['files']['guest_core.py']['path'];assert sys.argv[1]=='--cpu-preflight';reached.append(True);raise Boundary('real guest extraction boundary; no frame data locally')
   v.main=stop
  return v
 E.load=checkedload;os.environ['TORCH_DEVICE_BACKEND_AUTOLOAD']='0';os.environ['ASCEND_RT_VISIBLE_DEVICES']='';sys.argv=['cpu_entry097.py','--execute','--source-ref',json.dumps(sr),'--output',str(root/'out')]
 try:E.main()
 except Boundary:pass
 assert reached==[True]
 T=load(g/'test097.py','_split_test');T.OWN=om
 for bad in('missing','changed'):
  p=o/'owner097.py';saved=p.read_bytes()
  if bad=='missing':p.unlink()
  else:p.write_bytes(saved+b'\n')
  try:
   try:T.owner_file('owner097.py')
   except(FileNotFoundError,ValueError):pass
   else:raise AssertionError('bad declared owner Ref accepted')
  finally:p.write_bytes(saved)
print('split entry:15guard+8math PASS; real frame boundary reached; missing/hash negative PASS; no actual frame or NPU claim')
