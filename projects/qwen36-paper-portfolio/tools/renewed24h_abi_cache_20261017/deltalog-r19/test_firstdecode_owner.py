import ast,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path,PurePosixPath
from unittest.mock import patch
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import postconsume_recipe as R,firstdecode_output_policy as F
import postwork_verify as V
def module(name):
 s=importlib.util.spec_from_file_location('_owner_control_'+name,P/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Owner(unittest.TestCase):
 def test_child900_dynamic(self):self.assertEqual(R.cap(0,0,0,10000),900.)
 def test_child_remaining_margin(self):self.assertEqual(R.cap(1100,0,0,10000),340.)
 def test_child_cut_and_exhausted(self):
  self.assertEqual(R.cap(0,0,0,1300),40.)
  with self.assertRaises(ValueError):R.cap(1441,0,0,10000)
 def test_postverify_order_and_no_live_writer(self):
  events=[];lease=types.SimpleNamespace(close=lambda released:events.append('fullhash')or{},final_metadata=lambda:events.append('fresh-metadata'))
  h=types.SimpleNamespace(need=lambda v,m:None if v else (_ for _ in()).throw(ValueError(m)),CUTOFF=10000,HERE=P,frozen_directory=lambda *a:events.append('source-after'))
  sig=types.SimpleNamespace(SIGALRM=14,ITIMER_REAL=0,getsignal=lambda *a:None,getitimer=lambda *a:(0.,0.),signal=lambda *a:None,setitimer=lambda *a:None)
  with patch.object(V,'signal',sig),patch.object(V.time,'monotonic',return_value=100.),patch.object(V.time,'time',return_value=100.):
   with self.assertRaises(ValueError):V.run(h,lease,{'sha256':'x'},{'end':2700},0,False,lambda:[])
   self.assertEqual(events,[])
   result=V.run(h,lease,{'sha256':'x'},{'end':2700},0,True,lambda:events.append('fresh-CID')or[])
   self.assertEqual(events,['fullhash','source-after','fresh-CID','fresh-metadata']);self.assertEqual(result['actual_cap_seconds'],900.)
 def test_work_reserves_postverify_but_cleanup_unchanged(self):
  class Owned:
   def remaining(self,cleanup=False,cap=30):return cap
  V.protect(Owned,{},0,10000)
  with patch.object(V.time,'monotonic',return_value=1500.),patch.object(V.time,'time',return_value=100.):
   with self.assertRaises(ValueError):Owned().remaining(cap=999)
   self.assertEqual(Owned().remaining(cleanup=True,cap=60),60)
 def policy(self):
  e=module('external_output_policy');real=e.environment;e.install=lambda *a:{}
  class Owned:
   def __init__(self,leaf):pass
  S=types.SimpleNamespace(create_argv=lambda e:e)
  # Metadata-only Linux path fixture; no resource/filesystem admission mocked.
  with patch.object(F,'Path',PurePosixPath):F.install(e,S,Owned,None,'/opt/host/vnf/austinov/test','unused','/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-20261017-001')
  return e.environment
 def value(self):
  return dict(external_output_policy=True,external_output_root='/opt/host/vnf/austinov/test',mounts={'/opt/host/vnf/austinov/test/candidate':('/opt/host/vnf/austinov/test/candidate',True),'/adakv-results':('/opt/host/vnf/austinov/test/candidate',True),'/adakv-results/model/capture':('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061/first-real-decode-model-snapshots-renew24h-20261017-001',True)})
 def test_exact_nested_rw(self):
  x=self.value();self.assertEqual(len(x['mounts']),3);self.assertEqual(len({p for p,w in x['mounts'].values()if w}),2)
  self.assertEqual(self.policy()(x)['TMPDIR'],'/adakv-results')
 def test_third_rw_rejected(self):
  x=self.value();x['mounts']['/third']=('/opt/foreign',True)
  with self.assertRaises(ValueError):self.policy()(x)
 def test_wrong_payload_rejected(self):
  x=self.value();x['mounts']['/adakv-results/model/capture']=('/opt/foreign',True)
  with self.assertRaises(ValueError):self.policy()(x)
 def test_default_off_actual_cli(self):
  for entry in('host_ticket.py','postconsume_entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/entry)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),dict(enabled=False,NPU=False))
 def test_missing_actual_evidence_cold(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind_source.py'),'--execute'],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('--closed-evidence-ref',r.stderr)
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertIn('payload_cold_readset_preflight.json',m['files'])
  self.assertNotIn("p['files']['COLD_READSET_PREFLIGHT.json']",(P/'payload_cpu_preflight.py').read_text())
if __name__=='__main__':unittest.main()
