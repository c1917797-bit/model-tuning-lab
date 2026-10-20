"""Real H8->025->Joint Controller constructors and owned_create name gate.

Only frozen() helper acquisition is a non-resource boundary. No names, ctor,
name predicate or Docker results are mocked. Stop at the first actual call.
"""
import ast,hashlib,json,re,time,types,unittest
from pathlib import Path
import contract090 as C,owned_create as CREATE
P=Path(__file__).resolve().parent
def node(path,kind,name):
 return next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,kind)and n.name==name)
def compiled(path,nodes,scope):
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope)
class DockerBoundary(Exception):pass
class Tests(unittest.TestCase):
 def test_actual_controller_constructor_all_roles_then_original_create_guard(self):
  sources={
   'ORIGINAL_H8_HOST.py':'4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20',
   'ORIGINAL025_HOST.py':'36844e41895b95e810b54ecae32994a96b21258ae8ad8d88fccaac19f035cf8c',
   'ORIGINAL025_SAFETY.py':'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'}
  for name,digest in sources.items():self.assertEqual(hashlib.sha256((P/'evidence'/name).read_bytes()).hexdigest(),digest)
  # All three complete original class/function ASTs execute, not reconstructed
  # ctor statements. frozen() normally hashes/loads remote helper sources; it
  # is the sole software boundary and never used for admission here.
  H8=types.ModuleType('_name_H8');H8.__dict__.update(frozen=lambda:types.SimpleNamespace(),time=time,PHASE_SECONDS=5400)
  compiled(P/'evidence/ORIGINAL_H8_HOST.py',[node(P/'evidence/ORIGINAL_H8_HOST.py',ast.ClassDef,'Controller')],H8.__dict__)
  S=types.ModuleType('_name_025');S.__file__=str(P/'evidence/ORIGINAL025_SAFETY.py');S.__dict__.update(H=H8,PHASE=3600)
  compiled(Path(S.__file__),[node(Path(S.__file__),ast.ClassDef,'Controller')],S.__dict__)
  host=types.ModuleType('_name_joint');compiled(P/'evidence/ORIGINAL025_HOST.py',[node(P/'evidence/ORIGINAL025_HOST.py',ast.FunctionDef,'controller')],host.__dict__)
  Owned=host.controller(S,types.SimpleNamespace())
  commands=json.loads((P/'COMMANDS.json').read_bytes());names=[]
  helper=types.SimpleNamespace(IMAGE='software-only',sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest())
  for mode in('model','CPU'):
   raw=commands[mode][commands[mode].index('--output')+1];output=C.output_argument(raw)
   for role in('cpu-preflight','dense','cpu-consumer'):
    ctl=Owned(types.SimpleNamespace(output_dir=output/role),time.monotonic());ctl.cpu=dict(guest_cpus=[1,2,3,4]);seen=[]
    def stop(label,argv):seen.append((label,argv));raise DockerBoundary()
    ctl.call=stop
    self.assertRegex(ctl.name,r'\A[A-Za-z0-9_-]{1,100}\Z');self.assertLessEqual(len(ctl.name),100)
    with self.assertRaises(DockerBoundary):CREATE.create(helper,types.SimpleNamespace(__file__=S.__file__,DOCKER='/usr/bin/docker'),ctl,{},[],role,P)
    self.assertEqual(seen,[('unique-name',['/usr/bin/docker','ps','-a','--filter','name=^/'+ctl.name+'$','--format','{{.ID}}'])]);self.assertEqual(ctl.expected['name'],ctl.name)
    names.append(ctl.name)
  self.assertEqual(len(set(names)),6)
  # Reproduce actual R4 failure through the SAME constructors and create body:
  old=Path('/opt/host/vnf/austinov/run-bole-root-repeat-witness-repair4-output-contract-20261017-001-MAIN-NEW24H_001')
  ctl=Owned(types.SimpleNamespace(output_dir=old/'cpu-preflight'),time.monotonic());ctl.cpu=dict(guest_cpus=[1]);ctl.call=lambda *a: self.fail('old oversized name must reject before any Docker call')
  self.assertGreater(len(ctl.name),100)
  with self.assertRaisesRegex(ValueError,'new exact bounded name'):CREATE.create(helper,types.SimpleNamespace(__file__=S.__file__,DOCKER='/usr/bin/docker'),ctl,{},[],'cpu-preflight',P)
if __name__=='__main__':unittest.main()
