"""Exact source-owned readset closure; Ref order rebuilt only after full validation."""
import hashlib,json,subprocess
from pathlib import Path
import sourceio as C
READSET_PROGRAM = r'''
import hashlib,json,re,sys
from pathlib import Path

def need(v,s):
 if not v:raise ValueError(s)
def actual(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),"ordinary absolute file/no symlink")
 before=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block);size+=len(block)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and size==after.st_size,"stable file read")
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def check(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),"exact typed Ref3")
 need(actual(r['path'])==r,"exact supplied path/bytes/SHA before any import")
 return Path(r['path'])
provided=json.loads(sys.argv[1]);raw=check(provided).read_bytes();m=json.loads(raw)
root=Path(m['root']);need(root.is_absolute()and root==Path(provided['path']).parent,"source Ref is its exact owned root")
for name,r in m['files'].items():
 need(Path(r['path'])==root/name,"exact source-owned file operand");check(r)
for name in('sourceio.py','bind_model.py','command_contract.py'):need(name in m['files'],"explicit source-owned audit helper pin")
sys.path.insert(0,str(root))
import sourceio as C,bind_model as B,command_contract as CC
for name,module in(('sourceio.py',C),('bind_model.py',B),('command_contract.py',CC)):
 need(actual(module.__file__)==m['files'][name],"imported exact original source-owned helper")
C.checked(provided)
sr=C.ref(provided['path'])
need(sr==provided and list(sr)==['path','bytes','sha256'],"same fully validated Ref rebuilt by exact source-owned C.ref")
commands_ref=C.ref(root/'COMMANDS.json');commands=C.obj(commands_ref)
proofs={}
for key in('model','CPU'):
 argv=commands[key];need(type(argv)is list and argv.count('--source-ref')==1,"single exact source argv")
 value=argv[argv.index('--source-ref')+1]
 need(json.loads(value)==provided,"original COMMANDS argv Ref has same exact source semantics")
 need(value==json.dumps(sr),"original COMMANDS argv remains exact canonical source-owned C.ref serialization")
 proofs[key]=dict(argument=value,semantic_equal=True,literal_equal_to_sourceio_ref=True,
  literal_equal_to_supplied_serialization=value==json.dumps(provided))
# These are the original source functions, with no monkeypatch or relaxed contract.
refs=[*B.readset(sr),*m['dependencies'],*CC.validate(C,sr,m)]
serialization_differs=any(not item['literal_equal_to_supplied_serialization']for item in proofs.values())
try:
 CC.validate(C,provided,m)
except ValueError as error:
 need(serialization_differs,"provided original contract failed beyond the diagnosed serialization order")
 old_call=dict(rejected=True,reason=str(error),serialization_differs=True)
else:
 need(not serialization_differs,"original contract unexpectedly accepted altered literal source argv")
 old_call=dict(rejected=False,reason=None,serialization_differs=False)
by_path={} 
for r in refs:
 check(r);C.checked(r)
 need(r['path']not in by_path or by_path[r['path']]==r,"no conflicting exact prerequisite path")
 by_path[r['path']]=r
for r in by_path.values():check(r)
need(actual(sr['path'])==sr and actual(commands_ref['path'])==commands_ref,"unchanged source and COMMANDS after original functions")
print(json.dumps(dict(source=sr,refs=list(by_path.values()),commands=commands_ref,
 helper_sources={name:m['files'][name]for name in('sourceio.py','bind_model.py','command_contract.py')},
 supplied_key_order=list(provided),sourceio_key_order=list(sr),original_command_source_arguments=proofs,
 source_owned_original_functions=['bind_model.readset','command_contract.validate'],
 serialization_only_reconstruction=True,original_unreconstructed_call=old_call,source_and_commands_unchanged=True)))
'''

def collect(sr):
 C.checked(sr)
 result=subprocess.run(['/usr/bin/python3','-I','-B','-c',READSET_PROGRAM,json.dumps(sr)],capture_output=True,text=True,timeout=120)
 C.need(result.returncode==0,'exact original source-owned command/readset closure '+result.stderr[-6000:])
 value=json.loads(result.stdout);C.need(value['source']==sr,'same exact source returned')
 return value

def unique(refs):
 by_path={}
 for r in refs:
  C.checked(r);C.need(r['path']not in by_path or by_path[r['path']]==r,'one exact Ref for each prerequisite path');by_path[r['path']]=r
 return list(by_path.values())

def audit(sr):
 m=C.obj(sr);p=m['g3_predecessor'];parent=collect(p['source']);current=collect(sr)
 required=unique([*parent['refs'],*p.values()]);actual={r['path']:r for r in current['refs']}
 missing=[r for r in required if actual.get(r['path'])!=r]
 C.need(not missing,'exact full parent prerequisite closure missing/conflicting '+json.dumps(missing))
 return dict(schema='bole.G3-exact-parent-and-current-readset-closure/v3',source=sr,
  parent_source=p['source'],required_refs=required,current_refs=current['refs'],missing=[],
  required_refs_sha256=hashlib.sha256(json.dumps(sorted(required,key=lambda r:r['path']),sort_keys=True).encode()).hexdigest(),
  parent_original_commands=parent['commands'],current_original_commands=current['commands'],
  exact_original_functions=True,verified_sourceio_ref_reconstruction=True,directory_mounts_added=False,NPU=False)
