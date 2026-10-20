import ast,json,tempfile,unittest
from pathlib import Path
import torch
import sourceio as C,logits_observation131r13 as O
P=Path(__file__).parent
class Tests(unittest.TestCase):
 def test_dtype_vs_nonfinite_distinguished_without_cast(self):
  x=torch.tensor([[1,2,3,4]],dtype=torch.bfloat16);before=x.view(torch.int16).clone()
  r=O.snapshot(torch,x,vocab_size=4,rank=0,reduced=False)
  self.assertEqual(r['subconditions'],dict(ndim2=True,dtypeFP32=False,vocab_positive_int=True,all_finite=True));self.assertTrue(torch.equal(before,x.view(torch.int16)))
 def test_valid_and_padding_nonfinite_are_not_relaxed(self):
  x=torch.tensor([[1.,float('-inf'),float('inf'),float('nan')]])
  r=O.snapshot(torch,x,vocab_size=2,rank=0,reduced=False)
  self.assertEqual(r['valid']['negative_inf'],1);self.assertEqual(r['padding']['positive_inf'],1);self.assertEqual(r['padding']['nan'],1);self.assertFalse(r['subconditions']['all_finite'])
 def test_full_original_dtype_raw_exclusive_and_wrong_root_refuse(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);m=dict(model_receipt_root=str(root),files={'native_logits.py':C.ref(P/'native_logits.py'),'logits_observation131r13.py':C.ref(P/'logits_observation131r13.py')});sr=C.write(root/'SOURCE.json',m);x=torch.arange(8,dtype=torch.bfloat16).reshape(1,8)
   rr=O.record(torch,C,sr,root,0,x,vocab_size=8,reduced=False,ordinal=0);info=C.obj(rr)
   saved=torch.load(C.checked(info['raw']),weights_only=True)['logits'];self.assertEqual(saved.dtype,x.dtype);self.assertTrue(torch.equal(saved.view(torch.int16),x.view(torch.int16)))
   with self.assertRaises(FileExistsError):O.record(torch,C,sr,root,0,x,vocab_size=8,reduced=False,ordinal=0)
   with self.assertRaises(ValueError):O.record(torch,C,sr,root.parent,0,x,vocab_size=8,reduced=False,ordinal=0)
 def test_actual_callback_before_canonical_and_original_body_unchanged(self):
  tree=ast.parse((P/'model_smoke.py').read_bytes());f=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='canonical_logits');s=ast.unparse(f)
  self.assertLess(s.index('LO.record('),s.index('native_logits.canonical('));self.assertNotIn('.float(',s);self.assertNotIn('nan_to_num',s)
  old=P/'evidence'/'HISTORICAL_NATIVE_LOGITS131R12.py'
  self.assertEqual((P/'native_logits.py').read_bytes(),old.read_bytes())
if __name__=='__main__':unittest.main()
