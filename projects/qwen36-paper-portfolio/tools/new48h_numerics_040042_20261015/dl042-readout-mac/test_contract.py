import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Contract(unittest.TestCase):
 def test_actual_templates_and_cli(self):
  own=json.loads((P/'build_owner/SOURCE_MANIFEST.json').read_bytes());frame=json.loads((P/'frame/SOURCE_TEMPLATE.json').read_bytes());cmd=json.loads((P/'COMMANDS.json').read_bytes());r=own['root'].rsplit('/build_owner',1)[0]
  self.assertEqual(frame['root'],r+'/frame');self.assertTrue(frame['prepared_only']);self.assertIsNone(frame['production_ref']);self.assertIsNone(frame['debug_library']);self.assertEqual(frame['software_cases'],12);self.assertEqual(own['phase_seconds'],900);self.assertEqual(own['child_cap_seconds'],810)
  for key in ('source_audit','compile'):
   args=cmd[key]['args'];self.assertEqual(args[args.index('--source')+1],own['root']+'/SOURCE_MANIFEST.json');self.assertEqual(args[args.index('--source-sha256')+1],hashlib.sha256((P/'build_owner/SOURCE_MANIFEST.json').read_bytes()).hexdigest())
  for k,v in frame['outputs'].items():self.assertEqual(v,'/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-readout042-frame-'+k+'-new48h-MAIN-20261015-001')
  for k in ('host.py','guest.py','bind_cohort.py','test_owner.py'):
   b=(P/'build_owner'/k).read_bytes();self.assertEqual(own['files'][k],dict(path=own['root']+'/'+k,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 def fixture(self):
  s=importlib.util.spec_from_file_location('_042_bind_contract',P/'bind_frame.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
  m=json.loads((P/'frame/SOURCE_TEMPLATE.json').read_bytes());refs={k:dict(path=k,bytes=1,sha256='a'*64)for k in ('owner','cleanup','child','build','lib','dbg')};owner=dict(schema='deltalog.owned-kdma-build-host/v1',source=m['build_owner_source_ref'],primary=None,secondary=[],NPU=False,cleanup=refs['cleanup'],child=refs['child']);child=dict(source=owner['source'],primary=None,NPU=False,result=dict(build_complete=True,build_result_ref=refs['build']));build=dict(schema='deltalog-readout-mac-actual-build/v042',source_manifest=m['new_kernel_source_ref'],primary=None,Devices=[],NPU=False,artifacts=[dict(arm='readout_mac042',library=refs['lib']),dict(arm='readout_mac042_debug',library=refs['dbg'])],commands=[dict(exit_code=0,error=None)])
  rows=dict(template=m,owner=owner,cleanup=dict(stopped=True,retained=True,errors=[]),child=child,build=build);a.obj=lambda r:copy.deepcopy(rows[r['path']]);a.ref=lambda p:next(r for r in refs.values()if r['path']==p);return a,rows,refs
 def test_typed_build_binding_positive(self):
  a,r,f=self.fixture();v=a.bind(dict(path='template'),f['owner']);self.assertEqual(v['production_ref'],f['lib']);self.assertEqual(v['debug_library'],f['dbg']);self.assertFalse(v['prepared_only']);self.assertFalse(v['qualification'])
 def test_failed_build_not_admitted(self):
  a,r,f=self.fixture();r['owner']['primary']='preserved compile failure'
  with self.assertRaises(ValueError):a.bind(dict(path='template'),f['owner'])
 def test_unreleased_build_not_admitted(self):
  a,r,f=self.fixture();r['cleanup']['stopped']=False
  with self.assertRaises(ValueError):a.bind(dict(path='template'),f['owner'])
 def test_old_single015_build_not_admitted(self):
  a,r,f=self.fixture();r['build']['artifacts']=r['build']['artifacts'][1:]
  with self.assertRaises(ValueError):a.bind(dict(path='template'),f['owner'])
 def test_wrong_build_source_not_admitted(self):
  a,r,f=self.fixture();r['build']['source_manifest']=dict(path='old015',bytes=1,sha256='0'*64)
  with self.assertRaises(ValueError):a.bind(dict(path='template'),f['owner'])
 def test_newseed_and_original_gates_not_reclassified(self):
  m=json.loads((P/'HOLDOUT_REQUIREMENTS.json').read_bytes());self.assertEqual(m['seeds'],[260815535,260815542]);self.assertEqual(m['thresholds'],dict(per_request_output=.00303,state_l2=7.92e-7));self.assertFalse(m['qualified']);self.assertEqual(m['output_parent'],'/opt/host/vnf/austinov/deltalog042-evidence')
