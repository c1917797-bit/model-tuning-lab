import copy,json,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import diagnose as D
class Controls(unittest.TestCase):
 def fixture(self):
  ps=['layer%d'%i for i in range(48)];rows=[dict(prefix=p,prefill_tokens=2048,step=s,pass_gate=i>=34)for i,(p,s)in enumerate((p,s)for p in ps for s in range(9))]
  return dict(capture_source=D.SOURCE,worker_root=D.WORKER,layer_prefixes=ps,decode_rows=rows)
 def test_all432_select_exact34(self):self.assertEqual(len(D.select(self.fixture())),34)
 def test_missing_duplicate_or_wrongsource_reject(self):
  for mutate in(lambda x:x['decode_rows'].pop(),lambda x:x['decode_rows'].__setitem__(431,x['decode_rows'][0]),lambda x:x.__setitem__('capture_source',{}),lambda x:x['decode_rows'][0].__setitem__('pass_gate',True)):
   x=self.fixture();mutate(x)
   with self.assertRaises(ValueError):D.select(x)
 def test_real_integer_round_boundary_controls(self):
  import torch as t,direct_round as R
  self.assertTrue(R.controls(t)['double_round_negative_control'])
 def test_direct_round_not_torch_double_round(self):
  import torch as t,direct_round as R
  x=t.tensor([1+2**-8+2**-30,-1-2**-8-2**-30],dtype=t.float64);a=R.round_bf16(t,x);b=x.float().bfloat16()
  self.assertFalse(t.equal(a.view(t.int16),b.view(t.int16)));self.assertEqual(a.double().tolist(),[1+2**-7,-1-2**-7])
 def test_signedzero_inf_subnormal_bits(self):
  import torch as t,direct_round as R
  x=t.tensor([-0.,0.,2**-133,-2**-133,2**128,-2**128],dtype=t.float64)
  self.assertEqual((R.round_bf16(t,x).view(t.int16).to(t.int32)&65535).tolist(),[32768,0,1,32769,32640,65408])
 def test_owner_mechanical_inverse(self):
  r=json.loads((P/'OWNER_INVERSE.json').read_bytes());s=(P/'owned_cpu.py').read_text()
  for c in reversed(r['changes']):self.assertEqual(s.count(c['new']),1);s=s.replace(c['new'],c['old'])
  self.assertEqual(s.encode(),Path(r['donor']['path']).read_bytes())
if __name__=='__main__':unittest.main()
