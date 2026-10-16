import copy,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bind_source as B,packet_predecessor as R
class Tests(unittest.TestCase):
 def test_actual_binding_body_rejects_oldR2_and_incompleteR3(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());oldpath=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair2/SOURCE_TEMPLATE.json')if sys.platform=='linux'else P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair2/SOURCE_TEMPLATE.json';newpath=Path(R.TEMPLATE_REF['path'])if sys.platform=='linux'else P.parent/'deltalog-sameinitial-native-contract-new24h-088-repair6-repair2/SOURCE_TEMPLATE.json';old=json.loads(oldpath.read_bytes());new=json.loads(newpath.read_bytes());old['prepared_only']=False;old['prepared_template']=dict(path=old['root']+'/SOURCE_TEMPLATE.json',bytes=59455,sha256='425e0842b8c33425ce024f2e70b03735a3646005858df76487f45b8b6cd84192')
  with patch.object(B.O,'obj',return_value=new):
   with self.assertRaisesRegex(ValueError,'source/reference'):B.bind_actual_bridge(copy.deepcopy(m),{'software':'oldR2-evidence-negative-only'},old)
   # A prepared-only R3 source is not an actual bound source receipt.
   bad=copy.deepcopy(new);bad['prepared_template']=R.TEMPLATE_REF
   with self.assertRaisesRegex(ValueError,'source/reference'):B.bind_actual_bridge(copy.deepcopy(m),{'software':'pendingR3-negative-only'},bad)
 def test_real_cold_ON_wrong_source_hash_no_backend(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'bind_source.py'),'--execute','--template-sha256','0'*64],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(r.returncode,0);self.assertIn('MAIN reviewed053 template',r.stderr);self.assertNotIn('torch_npu',r.stderr)
if __name__=='__main__':unittest.main()
