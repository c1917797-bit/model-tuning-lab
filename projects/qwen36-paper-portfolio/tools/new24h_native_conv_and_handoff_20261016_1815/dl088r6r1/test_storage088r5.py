import copy,importlib.util,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C,storage_bridge121 as B,storage061 as S
class Tests(unittest.TestCase):
 def test_same_original_limits_and_independent_commitment(self):
  self.assertEqual((S.LIMIT,S.FREE),(80*2**30,100*2**30));self.assertEqual(S.committed_bytes(10,[6],[8]),12)
  #11closed are actual retained, newCPU/N16/N160 each retain original budgets.
  self.assertEqual(S.committed_bytes(7*2**30,[6*2**30,0,0,0],[6*2**30,1*2**30,33*2**30,33*2**30]),74*2**30)
 def test_actual_121_required_not_old119_or_missing(self):
  for value in(None,'{}',json.dumps(dict(path=str(B.ROOT/'seal-evidence119-MAIN-001/EVIDENCE119.json'),bytes=1,sha256='0'*64))):
   with self.assertRaises((ValueError,KeyError)):B.require_evidence(C,value)
 def test_sourcebound_helper_refuses_wrong_source_before_loading(self):
  with self.assertRaisesRegex(ValueError,'reviewed121'):B.api(C,dict(storage121_source_ref=B.SOURCE119))
 def test_actual121_whole_ref_bytes_and_sha_not_path_only(self):
  for field,value in(('bytes',7330),('sha256','0'*64)):
   r=dict(B.ACTUAL_EVIDENCE);r[field]=value
   with self.assertRaisesRegex(ValueError,'bytes/hash'):B.require_evidence(C,json.dumps(r))
 def test_original_math_all_bytes(self):
  O=P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair4'if sys.platform!='linux'else Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair4')
  for n in('producer.py','consumer088.py','capture088.py','run_consumer088.py','oracle.py','precast.py','direct_round.py','preregister.py','qwen36_deltalog_fresh/native_fixture.py'):
   self.assertEqual((P/n).read_bytes(),(O/n).read_bytes(),n)
 def test_closed_stat_detects_inode_or_byte_size_change(self):
  snap=dict(files=[dict(relative_path='a',bytes=3,mtime_ns=1,inode=2,device=4,sha256='x')]);row=dict(tree_ref={},leaf='/exact',frozen_bytes=3)
  proxy=types.SimpleNamespace(read=lambda r:snap,need=C.need,prior=lambda:types.SimpleNamespace(tree=lambda *a:[dict(relative_path='a',bytes=3,mtime_ns=1,inode=2,device=4)]));B.closed_stat(proxy,row)
  proxy.prior=lambda:types.SimpleNamespace(tree=lambda *a:[dict(relative_path='a',bytes=3,mtime_ns=1,inode=9,device=4)])
  with self.assertRaises(ValueError):B.closed_stat(proxy,row)
 def test_actual_cold_run052_to_run031_frontdoor_no_backend(self):
  tr=json.dumps(C.ref(P/'SOURCE_TEMPLATE.json'))
  with tempfile.TemporaryDirectory()as folder:
   code="import sys;sys.path.insert(0,"+repr(str(P))+");import run052 as R;R.OUT="+repr(folder)+";sys.argv="+repr(['run052.py','--execute','--phase','cpu','--template-ref',tr,'--host-cpu','166','--guest-cpu','0'])+";raise SystemExit(R.main())"
   x=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(x.returncode,0);self.assertIn('SOURCE_MANIFEST.json',x.stderr);self.assertNotIn('torch_npu',x.stderr)
 def test_real_cold_bind_missing121_refuses(self):
  x=subprocess.run([sys.executable,'-I','-B',str(P/'run052.py'),'--execute','--phase','bind','--template-ref',json.dumps(C.ref(P/'SOURCE_TEMPLATE.json'))],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(x.returncode,0);self.assertIn('actual121 evidence mandatory',x.stderr);self.assertNotIn('torch_npu',x.stderr)
if __name__=='__main__':unittest.main()
