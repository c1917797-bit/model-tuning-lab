import copy,importlib.util,json,unittest
from pathlib import Path
import frame,entry
P=Path(__file__).resolve().parent
class Controls(unittest.TestCase):
 def fixture(self):
  import torch as T
  s=36;st=dict(base=T.zeros(s,12,128,128),k_log=T.zeros(s,4,7,128,dtype=T.bfloat16),u_log=T.zeros(s,12,7,128),lambda_log=T.zeros(s,12,16),decay=T.zeros(s,12,16),length=T.zeros(s,12,16,dtype=T.int32));i=dict(query=T.ones(16,4,128,dtype=T.bfloat16),key=T.zeros(16,4,128,dtype=T.bfloat16),value=T.zeros(16,12,128,dtype=T.bfloat16),g=T.zeros(16,12),beta=T.zeros(16,12,dtype=T.bfloat16),actual_seq_lengths=T.tensor([0]+[1]*16,dtype=T.int32),ssm_state_indices=T.arange(16,dtype=T.int32),scale=128**-.5)
  st['conv']=T.zeros(s,3,2560,dtype=T.bfloat16)
  out=T.zeros(16,12,128,dtype=T.bfloat16);cap=dict(before=st,inputs=i,output=out);raw=dict(native_conv=st['conv'].clone(),kind='mixed',step=80,identity=(16,'eager','mixed-prefill-decode'),ids=T.arange(17,dtype=T.int32),captures=dict(decode=[cap]),candidate_output=T.zeros(80,12,128,dtype=T.bfloat16),state=st)
  return T,raw,cap,st,i,out
 def test_full16_geometry(self):
  T,r,c,s,i,o=self.fixture();self.assertEqual(frame.unpack(T,r)[2],list(range(16)))
 def test_request_slice_refused(self):
  T,r,c,s,i,o=self.fixture();c['inputs']['query']=i['query'][10:11]
  with self.assertRaises(ValueError):frame.unpack(T,r)
 def test_sequence_abi_refused(self):
  T,r,c,s,i,o=self.fixture();i['actual_seq_lengths']=T.arange(17,dtype=T.int32)
  with self.assertRaises(ValueError):frame.unpack(T,r)
 def test_wrong_scale_refused(self):
  T,r,c,s,i,o=self.fixture();i['scale']=1.
  with self.assertRaises(ValueError):frame.unpack(T,r)
 def test_bitwise_not_equal_signedzero_nan(self):
  import torch as T
  self.assertFalse(frame.bits(T,T.tensor([0.]),T.tensor([-0.])));a=T.tensor([float('nan')]);self.assertTrue(frame.bits(T,a,a.clone()))
 def test_transparency_inactive_and_pointer_negatives(self):
  T,r,c,s,i,o=self.fixture();after={a:{n:v.clone()for n,v in s.items()}for a in('production','debug')};inp={n:v for n,v in i.items()if isinstance(v,T.Tensor)}
  checks=lambda:frame.transparency(T,r,s,dict(production=o,debug=o.clone()),after,inp,inp,[True],{'actual':1},{'actual':1})
  self.assertTrue(all(checks().values()));after['production']['base'][16,0,0,0]=1.;self.assertFalse(checks()['inactive_state']);self.assertFalse(checks()['production_debug_state'])
 def test_host_entry_real_report_ABI(self):
  for kind in('cpu-preflight','numeric'):
   v=entry.stage_report({'source':1},{'authority':1},kind,pass_gate=kind=='cpu-preflight');self.assertEqual(v['source'],{'source':1});self.assertEqual(v['authority'],{'authority':1});self.assertIs(v['observation_complete'],True);self.assertIsNone(v['primary']);self.assertEqual(v['steps'],0 if kind=='cpu-preflight'else 1);self.assertEqual(v['records'],v['steps']);self.assertFalse(v['qualification'])
  host=(P/'host.py').read_text();self.assertIn("v['authority']==ar",host);self.assertIn("dv['plan']==self.plan_ref",host);self.assertIn('lifecycle_gate_pass=False',host);self.assertIn("'deltalog.single-frame-sidecar-independent/v040'",host)
 def test_actual_metadata_and_source_identity(self):
  m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());self.assertEqual(m['root'],'/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-single-frame-sidecar-new48h-v1-040-repair1');self.assertEqual(m['software_cases'],14);self.assertTrue(m['diagnostic040']);self.assertFalse(m['default_enabled']);self.assertEqual(m['failed160_owner_ref']['sha256'],'825cfa7ac6246ebb839192e39898d405dedd9ab71746dea2b6874e0f23ce8fc9')
  self.assertTrue(all('run-dl-frame040repair1-'in x for x in m['outputs'].values()));self.assertTrue(all(r['path']==m['root']+'/'+k for k,r in m['files'].items()));self.assertIn("OWNER='deltalog-single-frame-sidecar-new48h-MAIN-040-repair1'",(P/'host.py').read_text())
  self.assertEqual(m['files']['proof015/kernel/SOURCE_MANIFEST.json']['sha256'],m['debug_kernel_source_ref']['sha256'])
 def test_actual015_inverse_all8(self):
  spec=importlib.util.spec_from_file_location('_040_inverse_controls',P/'proof015/verify_inverse.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);self.assertEqual(len(v.verify(P/'proof015')),8)
 def test_exact013_rounding_controls(self):
  import torch as T,direct_round
  self.assertTrue(direct_round.controls(T)['direct_RNE'])

 def test_real_fixture_capture_seven_fields(self):
  T,r,c,s,i,o=self.fixture();self.assertEqual(set(c['before']),set(frame.CAPTURE_FIELDS));self.assertEqual(set(frame.FIELDS),set(c['before'])-{'conv'});self.assertEqual(tuple(c['before']['conv'].shape),(36,3,2560));self.assertEqual(frame.unpack(T,r)[2],list(range(16)))
  source=(P.parent/'deltalog-diagnostic-bridge-owned-new48h-20261015-035-repair4/qwen36_deltalog_fresh/native_fixture.py')
  if source.exists():
   text=source.read_text();self.assertIn('state["conv"]=conv',text);self.assertIn('before={k:v.cpu() for k,v in state.items()}',text)
 def test_missing_conv_refused(self):
  T,r,c,s,i,o=self.fixture();del c['before']['conv']
  with self.assertRaisesRegex(ValueError,'seven-field'):frame.unpack(T,r)
 def test_unknown_capture_field_refused(self):
  T,r,c,s,i,o=self.fixture();c['before']['other']=T.zeros(1)
  with self.assertRaisesRegex(ValueError,'seven-field'):frame.unpack(T,r)
 def test_conv_wrong_provenance_geometry_refused(self):
  T,r,c,s,i,o=self.fixture();c['before']['conv']=T.zeros(36,3,2560)
  with self.assertRaisesRegex(ValueError,'conv arena'):frame.unpack(T,r)
