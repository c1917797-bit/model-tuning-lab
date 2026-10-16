import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
import torch
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('codec011',P/'lossless_raw.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
class Tests(unittest.TestCase):
 def fixture(self):
  x=dict(v=torch.arange(24,dtype=torch.bfloat16).reshape(1,3,2,4),g=torch.tensor([[float('nan'),-0.0,1.]]),beta=torch.ones(1,3),initial_state=torch.zeros(1,2,4,4),cu_seqlens=torch.tensor([0,3]),q=torch.ones(1,3,1,4))
  return dict(inputs=x,normalized_inputs={k:v.clone()for k,v in x.items()},output=torch.zeros(1,3,2,4))
 def test_exact_roundtrip_and_persisted_alias(self):
  d=self.fixture();before=[(p,C.descriptor(torch,t))for p,t in C.leaves(torch,d)]
  with tempfile.TemporaryDirectory()as td:
   path=Path(td)/'RAW.pt';m=C.write(torch,path,d);restored=C.read(torch,path)
   self.assertEqual(before,[(p,C.descriptor(torch,t))for p,t in C.leaves(torch,restored)]);self.assertEqual(len(m['aliases']),5);self.assertGreater(m['exact_alias_saved_bytes'],0)
 def test_unequal_not_deduped(self):
  d=self.fixture();d['normalized_inputs']['v'][0,0,0,0]=2;b=C.prepare(torch,d);self.assertNotIn(['normalized_inputs','v'],[a['path']for a in b['manifest']['aliases']])
 def test_corrupt_leaf_rejected(self):
  b=C.prepare(torch,self.fixture());side=copy.deepcopy(b['manifest']);b['payload']['output'][0,0,0,0]=1
  with self.assertRaises(ValueError):C.restore(torch,b,side)
 def test_forged_alias_rejected(self):
  b=C.prepare(torch,self.fixture());b['manifest']['aliases'][0]['target']=['inputs','q']
  with self.assertRaises(ValueError):C.restore(torch,b,b['manifest'])
 def test_sidecar_corruption_rejected(self):
  b=C.prepare(torch,self.fixture());side=copy.deepcopy(b['manifest']);side['exact_alias_saved_bytes']+=1
  with self.assertRaises(ValueError):C.restore(torch,b,side)
if __name__=='__main__':unittest.main()
