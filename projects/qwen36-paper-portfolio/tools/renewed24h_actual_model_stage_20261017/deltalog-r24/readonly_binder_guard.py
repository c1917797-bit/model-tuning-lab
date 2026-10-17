"""Exact isolated binder Ref-data exception, never a PID/FD/maps exemption."""
import ast,hashlib,json,os,sys
from pathlib import Path

OPTIONS=('--template-sha256','--bridge-source-ref','--bridge-owner-ref','--component-cpu-owner-ref','--closed-evidence-ref')
CLAUSE="need(not any(t.startswith(prefix+b'/')or any(x.encode()in t for x in paths)for t in b.split(b'\\0')),'original088 command still active')"
REPLACEMENT='_readonly_original_command_gate(p,b,prefix,paths)'

def original_match(argv,prefix,paths):
 return any(t.startswith(prefix+b'/')or any(x.encode()in t for x in paths)for t in argv)

def parse_arguments(argv,program,template):
 # Exact approved CLI, including isolated interpreter flags. Unknown options,
 # wrappers/-c/-m and even extra positional args retain the original rejection.
 if len(argv)!=15 or argv[:4]!=['/usr/bin/python3','-I','-B',program]or argv[4]!='--execute':return False
 if argv[5::2]!=list(OPTIONS)or argv[6]!=template['sha256']:return False
 for token in argv[8::2]:
  try:r=json.loads(token)
  except (ValueError,TypeError):return False
  if not(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and r['path'].startswith('/')and '..'not in Path(r['path']).parts and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64 and all(x in'0123456789abcdef'for x in r['sha256'])):return False
 return True

class Guard:
 def __init__(self,O,m,template):
  self.O=O;self.program=m['files']['bind_source.py'];self.template=template
  O.obj_file(self.program);O.obj(template)
  self.argv=['/usr/bin/python3','-I','-B',*sys.argv]
  O.need(parse_arguments(self.argv,self.program['path'],template),'exact approved source-bound binder argv')
  for token in self.argv[8::2]:O.obj(json.loads(token))
  self.pid=os.getpid();current=Path('/proc')/str(self.pid)
  self.start=(current/'stat').read_text().rsplit(')',1)[1].split()[19]
  self.exe=Path(os.readlink(current/'exe')).resolve();O.need(self.exe==Path(sys.executable).resolve(),'actual current isolated binder executable')
  self.verified=[]
 def accept(self,p,b):
  if p.name!=str(self.pid):return False
  argv=[x.decode('utf8')for x in b.split(b'\0')if x]
  if argv!=self.argv or not parse_arguments(argv,self.program['path'],self.template):return False
  before=(p/'stat').read_text();start=before.rsplit(')',1)[1].split()[19]
  if start!=self.start:return False
  if Path(os.readlink(p/'exe')).resolve()!=self.exe:return False
  self.O.obj_file(self.program);self.O.obj(self.template)
  for token in argv[8::2]:self.O.obj(json.loads(token))
  self.O.need((p/'cmdline').read_bytes()==b and(p/'stat').read_text().rsplit(')',1)[1].split()[19]==self.start and Path(os.readlink(p/'exe')).resolve()==self.exe,'stable actual current binder PID/start/argv/exe')
  self.verified.append(dict(pid=int(p.name),start_ticks=int(start),executable=str(self.exe),program_ref=self.program,argv_sha256=hashlib.sha256(b).hexdigest()))
  return True
 def install(self,seal):
  original=seal.canonical
  def canonical(sr):
   K,m=original(sr) # Full frozen canonical source validation first.
   raw=Path(K.__file__).read_text(encoding='utf8');body=seal.failclosed_tree(raw)
   K.need(body.count(CLAUSE)==1,'one exact original command predicate')
   changed=body.replace(CLAUSE,REPLACEMENT)
   K.need(changed.replace(REPLACEMENT,CLAUSE)==body,'whole canonical command-only inverse')
   def gate(p,b,prefix,paths):
    # All original FD access flags and shared-writable maps below this line
    # remain byte-identical and still inspect the admitted binder itself.
    K.need(not original_match(b.split(b'\0'),prefix,paths)or self.accept(p,b),'original088 command still active')
   K._readonly_original_command_gate=gate
   node=[n for n in ast.parse(changed).body if isinstance(n,ast.FunctionDef)and n.name=='no_writers'];K.need(len(node)==1,'exact original no_writers body')
   exec(compile(ast.Module(body=node,type_ignores=[]),K.__file__+'#exact-readonly-binder','exec'),K.__dict__)
   return K,m
  seal.canonical=canonical
