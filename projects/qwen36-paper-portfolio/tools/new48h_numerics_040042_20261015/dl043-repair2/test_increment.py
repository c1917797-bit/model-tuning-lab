import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import torch
from consume_increment import check
class Checks(unittest.TestCase):
 def row(self):
  b=dict(base=torch.ones(3,12,2,2),k_log=torch.full((3,4,7,2),float('nan'),dtype=torch.bfloat16),u_log=torch.full((3,12,7,2),float('nan')),lambda_log=torch.full((3,12,16),float('nan')),decay=torch.zeros(3,12,16),length=torch.zeros(3,12,16,dtype=torch.int32))
  return dict(before=b,after={n:x.clone()for n,x in b.items()},ids=torch.tensor([0]),actual_NPU=True)
 def test_zero_dead_nan(self):self.assertTrue(check(torch,self.row())['length0'])
 def test_wrong_live_base(self):
  r=self.row();r['after']['base'][0]*=2
  with self.assertRaises(ValueError):check(torch,r)
 def test_foreign_signedzero(self):
  r=self.row();r['before']['decay'][2,0,0]=0.;r['after']['decay'][2,0,0]=-0.
  with self.assertRaises(ValueError):check(torch,r)
 def test_payload_mutation(self):
  r=self.row();r['after']['u_log'][0,0,0,0]=0.
  with self.assertRaises(ValueError):check(torch,r)
if __name__=='__main__':unittest.main()
