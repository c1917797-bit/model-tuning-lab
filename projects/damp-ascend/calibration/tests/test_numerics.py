"""Real CPU Torch equation checks; same-image run is explicitly required separately."""
import math
import os
import struct
import unittest
from damp_calibrate.rules import RECIPROCAL,f32
from damp_calibrate.numerics import storage_errors,mixed_cost
try:
    import torch
except ModuleNotFoundError:
    if os.environ.get('DAMP_REQUIRE_TORCH_TESTS') == '1': raise
    torch = None

@unittest.skipIf(torch is None,'requires explicit same-image CPU Torch; no NPU substitute')
class NumericsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): torch.set_num_threads(2)

    def test_original_coordinate_scalar_oracle_nonidentity_sr_pv(self):
        state = torch.tensor([[[.2,3.,-2.],[.8,-1.,.4],[2.,.6,-.5],[.3,-2.,.7]]],dtype=torch.float32)
        sr = torch.tensor([[1.3,.7,2.1,.9]],dtype=torch.float32)
        pv = torch.tensor([[2,0,3,1]],dtype=torch.int32)
        e8,e16 = storage_errors(state,sr,pv,torch,group=2)
        expected8 = [0.]*3; expected16 = [0.]*3
        raw = state[0].tolist(); c = sr[0].tolist(); order = pv[0].tolist()
        for key in range(3):
            for start in (0,2):
                originals = order[start:start+2]
                values = [f32(raw[v][key]/c[v]) for v in originals]
                maximum = max(abs(x) for x in values)
                scale = f32(maximum*RECIPROCAL) if maximum else 1.
                for v,x in zip(originals,values):
                    code = max(-127,min(127,round(f32(x/scale))))
                    restored8 = f32(f32(code*scale)*c[v])
                    restored16 = f32(struct.unpack('<e',struct.pack('<e',x))[0]*c[v])
                    expected8[key] += (restored8-raw[v][key])**2
                    expected16[key] += (restored16-raw[v][key])**2
        for got,want in zip(e8[0].tolist(),expected8): self.assertAlmostEqual(got,want,places=15)
        for got,want in zip(e16[0].tolist(),expected16): self.assertAlmostEqual(got,want,places=15)

    def test_zero_groups_exact(self):
        state = torch.zeros(2,4,3,dtype=torch.float32)
        sr = torch.tensor([[1.,1.3,.7,4.]]*2,dtype=torch.float32)
        pv = torch.tensor([[2,0,3,1]]*2,dtype=torch.int32)
        errors = storage_errors(state,sr,pv,torch,group=2)
        self.assertTrue(all(torch.equal(e,torch.zeros(2,3,dtype=torch.float64)) for e in errors))

    def test_group_scale_underflow_is_not_clamped(self):
        tiny = struct.unpack('<f',struct.pack('<I',1))[0]
        state = torch.full((1,2,2),tiny,dtype=torch.float32)
        with self.assertRaises(ValueError):
            storage_errors(state,torch.ones(1,2),torch.tensor([[0,1]],dtype=torch.int32),torch,group=2)

    def test_fp16_error_counts_only_protected_channels(self):
        e8 = torch.tensor([[2.,3.]],dtype=torch.float64)
        e16 = torch.tensor([[.1,float('inf')]],dtype=torch.float64)
        cost = mixed_cost(e8,e16,torch.tensor([10.]),torch.tensor([[True,False]]),torch)
        self.assertAlmostEqual(float(cost[0]),31.)
        bad = mixed_cost(e8,e16,torch.tensor([10.]),torch.tensor([[False,True]]),torch)
        self.assertTrue(math.isinf(float(bad[0])))

    def test_wrong_scale_and_permutation_fail_closed(self):
        state = torch.ones(1,4,3)
        for sr,pv in ((torch.tensor([[1.,-1.,1.,1.]]),torch.tensor([[0,1,2,3]],dtype=torch.int32)),
                      (torch.ones(1,4),torch.tensor([[0,0,2,3]],dtype=torch.int32))):
            with self.assertRaises(ValueError): storage_errors(state,sr,pv,torch,group=2)

    def test_validation_does_not_change_frozen_plan(self):
        from damp_calibrate.pipeline import validation
        state = torch.arange(12*128*128,dtype=torch.float32).reshape(12,128,128)/100000.
        pv = torch.arange(127,-1,-1,dtype=torch.int32).repeat(12,1)
        plan = dict(sr=torch.full((12,128),1.3),pv=pv,pk=torch.arange(128,dtype=torch.int32).repeat(12,1))
        before = {k:v.clone() for k,v in plan.items()}; high = torch.zeros(12,128,dtype=torch.bool); high[:,:16] = True
        data = [(state,torch.full((256,12),-.1))]*72
        report = validation(data,plan,high,torch)
        self.assertIs(report['feedback_to_selection'],False)
        self.assertTrue(all(torch.equal(v,before[k]) for k,v in plan.items()))

    def test_fit_tune_full_geometry_stable_ties(self):
        from damp_calibrate.pipeline import select
        # Synthetic software fixture, not a model-derived calibration result.
        state = torch.zeros(12,128,128,dtype=torch.float32)
        future = torch.zeros(256,12,dtype=torch.float32)
        plan,high,report = select({'fit':[(state,future)]*72,'tune':[(state,future)]*72},torch)
        self.assertEqual(report['selected_candidates'],[0]*12)
        self.assertEqual(report['protected_original_keys'],[list(range(16))]*12)
        self.assertTrue(torch.equal(plan['sr'],torch.ones(12,128)))
        self.assertTrue(torch.equal(plan['pk'],torch.arange(128,dtype=torch.int32).repeat(12,1)))
        self.assertTrue(torch.equal(plan['pv'],torch.arange(128,dtype=torch.int32).repeat(12,1)))
        self.assertTrue(torch.equal(high.sum(1),torch.full((12,),16)))
        self.assertNotIn('validation',report)

if __name__ == '__main__': unittest.main()
