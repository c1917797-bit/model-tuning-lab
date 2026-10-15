"""Actual CPU arithmetic controls only; separate real NPU replay is mandatory."""
import copy,importlib,sys,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.path.insert(0,'C:/Users/Huawei/AppData/Local/Temp/deltalog-service-composite-new48h-20261015-023-repair1')
from qwen36_deltalog_screen import primitives as L,health
from qwen36_deltalog_service import primitives as D
torch.set_num_threads(1)
def state():
 g=torch.Generator().manual_seed(20261015033)
 return dict(base=torch.randn((3,12,128,128),generator=g)*.001,k_log=torch.randn((3,4,7,128),generator=g).bfloat16()*.01,u_log=torch.randn((3,12,7,128),generator=g)*.001,lambda_log=torch.zeros((3,12,16)),decay=torch.zeros((3,12,16)),length=torch.zeros((3,12,16),dtype=torch.int32))
def apply(fn,s):fn(torch,SimpleNamespace(prefix='CPU-control-not-NPU',kv_cache=[None,s['base']]),s,torch.tensor([0],dtype=torch.int32),'CPU-control')
def same(a,b):return all(a[n].dtype==b[n].dtype and torch.equal(a[n].contiguous().view(torch.uint8),b[n].contiguous().view(torch.uint8))for n in a)
class Tests(unittest.TestCase):
 def setUp(self):
  # Test isolation only; no reset function is exported to the runtime.
  health._FLAGS={};health._OBSERVATIONS={}
 def test_finite_same_arithmetic(self):
  a=state();a['length'][0,:,0]=3;b=copy.deepcopy(a);apply(D._flush_slots,a);apply(L._flush_slots,b);self.assertTrue(same(a,b));self.assertTrue(health.snapshot(torch,outside_timing=True)['all_finite'])
 def test_dead_nan_valid(self):
  a=state()
  for n in('k_log','u_log','lambda_log'):a[n][0].fill_(float('nan'))
  b=copy.deepcopy(a);apply(D._flush_slots,a);apply(L._flush_slots,b);self.assertTrue(same(a,b));self.assertTrue(health.snapshot(torch,outside_timing=True)['all_finite'])
 def test_invalid_live_flag_cannot_recover(self):
  a=state();a['length'][0,:,0]=1;a['u_log'][0,0,0,0]=float('nan');b=copy.deepcopy(a)
  with self.assertRaisesRegex(RuntimeError,'non-finite'):apply(D._flush_slots,a)
  apply(L._flush_slots,b);self.assertFalse(health.snapshot(torch,outside_timing=True)['all_finite'])
  health.observe(torch,torch.ones(3));self.assertFalse(health.snapshot(torch,outside_timing=True)['all_finite'])
 def test_no_inside_timing_read(self):
  health.observe(torch,torch.ones(3))
  with self.assertRaises(RuntimeError):health.snapshot(torch)
 def test_multistep_reuse_and_inactive_bytes(self):
  a=state();b=copy.deepcopy(a);inactive={n:t[1:].clone()for n,t in a.items()}
  for step in range(10):
   for s in(a,b):s['length'][0,:,0]=step%8;s['decay'][0,:,0]=-.1
   apply(D._flush_slots,a);apply(L._flush_slots,b);self.assertTrue(same(a,b))
  self.assertTrue(all(torch.equal(b[n][1:].view(torch.uint8),v.view(torch.uint8))for n,v in inactive.items()))
 def test_math_projection_actual_sources(self):
  from mechanical import compare
  self.assertIn('B010_OP_ABI',compare('C:/Users/Huawei/AppData/Local/Temp/deltalog-service-composite-new48h-20261015-023-repair1/qwen36_deltalog_service',str(P/'qwen36_deltalog_screen')))
if __name__=='__main__':unittest.main()
