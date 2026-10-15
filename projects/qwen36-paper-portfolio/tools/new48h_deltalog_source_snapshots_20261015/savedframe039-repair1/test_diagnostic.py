import importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('actual039',P/'diagnose.py');D=importlib.util.module_from_spec(s);s.loader.exec_module(D)
class Controls(unittest.TestCase):
 def test_signed_cells_and_midpoint(self):
  a=D.cell(1+2**-8,0x3f80);self.assertEqual(a['midpoint_high'],1+2**-8);self.assertEqual(a['high_minus_truth'],0)
  b=D.cell(-1-2**-8,0xbf80);self.assertEqual(b['midpoint_low'],-1-2**-8);self.assertEqual(b['truth_minus_low'],0)
  for code in(0,0x8000):self.assertTrue(D.cell(0.,code)['truth_within_closed_cell'])
 def test_independent_decimal_column_zero_and_exact_update(self):
  import torch as T
  b=dict(base=T.zeros(1,12,128,128),decay=T.zeros(1,12,16),length=T.zeros(1,12,16,dtype=T.int32),lambda_log=T.zeros(1,12,16),u_log=T.zeros(1,12,7,128),k_log=T.zeros(1,4,7,128,dtype=T.bfloat16))
  i=dict(query=T.zeros(1,4,128,dtype=T.bfloat16),key=T.zeros(1,4,128,dtype=T.bfloat16),value=T.zeros(1,12,128,dtype=T.bfloat16),g=T.zeros(1,12),beta=T.ones(1,12,dtype=T.bfloat16),scale=.5)
  self.assertEqual(D.mp_column(b,i,0,0,0,0,80),0)
  i['query'][0,0,0]=1;i['key'][0,0,0]=1;i['value'][0,0,0]=2
  self.assertEqual(D.mp_column(b,i,0,0,0,0,80),1);self.assertEqual(D.mp_column(b,i,0,0,0,0,100),1)
if __name__=='__main__':unittest.main()
