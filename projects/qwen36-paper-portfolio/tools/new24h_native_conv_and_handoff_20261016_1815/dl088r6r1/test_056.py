"""Actual archive JSON/source controls; no new Meta/NPU/library qualification."""
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import window056 as W,historical022056 as H
def actual(n):return json.loads((P/n).read_bytes())
class NewWindow(unittest.TestCase):
 def test_actual_new_authority_positive_and_old_reject(self):
  a=actual('NEW24H_AUTHORITY.json');self.assertEqual(W.require_current(W.AUTH,lambda r:a,now=W.START+1),a)
  for now in(W.START-1,W.CUT-2880,W.CUT,W.CUT+1):
   with self.assertRaises(ValueError):W.require_current(W.AUTH,lambda r:a,now=now)
  with self.assertRaises(ValueError):W.require_current(H.OLD_AUTH,lambda r:actual('OLD48H_AUTHORITY.json'),now=W.START+1)
 def test_actual_old_source_window_is_history_not_newauthority(self):
  m=actual('OLD022_SOURCE.json');a=actual('OLD48H_AUTHORITY.json')
  self.assertTrue(H.historical_window(m,lambda r:a))
  for field,val in(('authority_ref',W.AUTH),('window',dict(start=W.START,cutoff=W.CUT))):
   b=copy.deepcopy(m);b[field]=val
   with self.assertRaises(ValueError):H.historical_window(b,lambda r:a)
 def test_actual_old_released_owner_positive_and_wrongoldauthority(self):
  path=P/'dependencies/old022_composite.py';s=importlib.util.spec_from_file_location('_actual_old022_source',path);M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
  owner=actual('OLD022_OWNER.json');sr=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-composite-admission-new48h-v1-022/BOUND_SOURCE.json',bytes=162171,sha256='b5f4c0798f2fab7fb3c706666c38b6eab7318fa6a55e40191dd419bb6aaacb6c')
  M.terminal(owner,sr,'cpu',cpu=True)
  bad=copy.deepcopy(owner);bad['authority']=W.AUTH
  with self.assertRaises(ValueError):M.terminal(bad,sr,'cpu',cpu=True)
 def test_exact_function_source_inverse(self):
  raw=(P/'dependencies/old022_composite.py').read_bytes();f=H.derive(raw,{})
  self.assertEqual(f.__name__,'admit_receipt');self.assertEqual(hashlib.sha256(raw).hexdigest(),H.OLD_API_SHA)
  with self.assertRaises(ValueError):H.derive(raw+b'\n',{})
 def test_auth_copy_bytes_exact(self):
  for name,r in(('NEW24H_AUTHORITY.json',W.AUTH),('OLD48H_AUTHORITY.json',H.OLD_AUTH)):
   b=(P/name).read_bytes();self.assertEqual(len(b),r['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),r['sha256'])
 def test_all_current_outer_inner_gates_and_build_preserved(self):
  m=actual('SOURCE_TEMPLATE.json');self.assertEqual(m['window'],dict(start=W.START,cutoff=W.CUT));self.assertEqual(m['authority_ref'],W.AUTH)
  self.assertEqual(m['reviewed_split_build_ref']['sha256'],'3010d9b0a73d2f7b62b6294c8c01fa68176f1e911bee4b43ca7b1ac72bf00a68')
  self.assertEqual(actual('ACTUAL051_BUILD.json')['authority'],H.OLD_AUTH)
  for n in('host.py','bridge_io.py','qwen36_deltalog_fresh/provider.py','run031.py'):
   text=(P/n).read_text();self.assertNotIn('1792135097',text,n);self.assertNotIn(H.OLD_AUTH['sha256'],text,n)
  for n in('entry.py','producer.py'):self.assertIn('C.window(ar)',(P/n).read_text())
 def test_defaultoff_real_cold_callers(self):
  for n in('run052.py','bind052.py'):
   v=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(v.returncode,0,v.stderr)
if __name__=='__main__':unittest.main()
