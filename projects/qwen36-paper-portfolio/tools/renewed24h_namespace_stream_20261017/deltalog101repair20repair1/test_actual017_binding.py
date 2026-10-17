"""Actual frozen metadata -> exact017 adapt/bind, not a fabricated same-ID fixture.

No source qualifier, resource owner, container, device or model is executed.
Windows translates only the lexical Linux paths and exact source reads needed
to compile the private host; Linux sameimage uses ordinary actual deployed paths.
"""
import ast,copy,hashlib,importlib.util,json,os,pathlib,types,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent
import owner_overlay as O
from packet_contract import ROOT,OUTPUT,IDENTITY

def exact_local(r,fallback):
 q=pathlib.Path(r['path'])
 if os.name=='nt':q=pathlib.Path(fallback)
 b=q.read_bytes();O.need((len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'actual pinned source local/host bytes')
 return q,b

class ActualBinding(unittest.TestCase):
 def test_real_template_original017_adapt_and_private_bind(self):
  manifest=P/'SOURCE_MANIFEST.json'
  if not manifest.exists():manifest=P/'SOURCE_TEMPLATE.json'
  body=manifest.read_bytes();m=json.loads(body);self.assertEqual(m['runtime_identity'],IDENTITY)
  self.assertEqual(m['root'],ROOT);self.assertEqual(m['output_root'],OUTPUT)
  self.assertEqual(IDENTITY['owner'],IDENTITY['run_id'])
  oldpath,oldbody=exact_local(m['host017_ref'],P/'software_dependencies/host017.py')
  donorpath,donor=exact_local(m['donor008_host_ref'],P/'software_dependencies/donor008.py')
  self.assertEqual((len(oldbody),hashlib.sha256(oldbody).hexdigest()),(14117,'f29d8d5717baf61ca6ebf4728123afa1483f3bbd9888f4c93b10c09d75f3d3fc'))
  spec=importlib.util.spec_from_file_location('_MODEL058_actual017_binding',oldpath);H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
  obs_path,obs_body=exact_local(m['owner017_files']['ownership_observation.py'],P/'software_dependencies/ownership_observation017.py')
  s=importlib.util.spec_from_file_location('_MODEL058_actual017_ownership',obs_path);obs=importlib.util.module_from_spec(s);s.loader.exec_module(obs)
  if os.name=='nt':
   class HostPath(pathlib.PurePosixPath):
    def resolve(self,*a,**kw):return self
    def read_bytes(self):
     O.need(str(self)==ROOT+'/SOURCE_MANIFEST.json','only actual current manifest lexical path translated');return body
   H.Path=HostPath;H.HERE=HostPath(ROOT);H.DEPLOY=HostPath(ROOT);H.OUT=HostPath(OUTPUT);H.DONOR=HostPath(H.DONOR.as_posix())
  else:
   HostPath=pathlib.Path;H.HERE=P;H.DEPLOY=P;H.OUT=pathlib.Path(OUTPUT)
  H.leaf=lambda name:obs if name=='ownership_observation.py'else (_ for _ in()).throw(ValueError('unexpected leaf'))
  original_exact=H.exact
  H.exact=lambda r:donor if r==H.HOST_REF else original_exact(r)
  original_adapt=H.adapt
  import window_overlay as W
  W.install(H,m)
  fn=next(n for n in ast.walk(ast.parse((P/'host_ticket.py').read_bytes()))if isinstance(n,ast.FunctionDef)and n.name=='adapted')
  scope=dict(original_adapt=original_adapt,m=m,HERE=H.HERE,O=O,Path=HostPath,json=json,W=W,active_output=OUTPUT)
  exec(compile(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[]),str(P/'host_ticket.py')+'::actualadapt','exec'),scope);H.adapt=scope['adapted']
  sr=dict(path=ROOT+'/'+manifest.name,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
  if os.name=='nt':
   with patch.object(pathlib,'Path',HostPath):bound,pairs=H.bind(sr,m['bridge024_owner_ref'],[m['host017_ref']])
  else:bound,pairs=H.bind(sr,m['bridge024_owner_ref'],[m['host017_ref']])
  self.assertEqual(str(bound.HERE),ROOT);self.assertEqual(str(bound.DEPLOY),ROOT);self.assertEqual(str(bound.OUT),OUTPUT)
  self.assertEqual(bound.START,1792226600);self.assertEqual(bound.CUTOFF,1792313000);self.assertEqual(bound.PHASE,2700);self.assertEqual(bound.CLEANUP_TOTAL,270)
  self.assertEqual(json.loads(bound._SOURCE_JSON),sr);self.assertGreater(len(pairs),20)
  # This is construction of the real private host only, NOT running main,
  # source admission, resources, cleanup, a container or actual hardware.
  self.assertTrue(callable(bound.main));self.assertTrue(callable(bound.safety))

if __name__=='__main__':unittest.main()
