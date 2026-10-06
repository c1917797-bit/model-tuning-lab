"""Optional real-Torch CPU mapping test; never an Ascend numerical result."""
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from damp_integration.state import pack_native

class PrefillPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("torch") is None:
            raise unittest.SkipTest("real Torch unavailable; CPU pack parity unverified here")
        import torch
        cls.torch = torch
        path = Path(__file__).resolve().parents[2] / "tests" / "independent_oracle.py"
        spec = importlib.util.spec_from_file_location("damp_integration_independent_oracle", path)
        cls.oracle = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.oracle
        spec.loader.exec_module(cls.oracle)

    def test_value_major_nonidentity_mapping(self):
        torch, oracle = self.torch, self.oracle
        gen = torch.Generator().manual_seed(9182)
        state = torch.randn(1,12,128,128,generator=gen) * 0.03
        pv = torch.stack([torch.randperm(128,generator=gen) for _ in range(12)]).int()
        pk = torch.stack([torch.randperm(128,generator=gen) for _ in range(12)]).int()
        c = torch.linspace(-0.2,0.2,128).exp().repeat(12,1)
        layout = oracle.OracleLayout(c, pv, pk)
        plan = SimpleNamespace(sr=c,pv=pv,pk=pk)
        actual = pack_native(state,plan,torch)
        expected = oracle.pack_value_major(oracle.transform_state(state,layout),layout)
        for a,e in zip(actual,(expected.high,expected.low,expected.scales)):
            self.assertEqual(tuple(a.shape),tuple(e.shape))
            self.assertEqual(a.dtype,e.dtype)
            self.assertTrue(torch.equal(a.view(torch.uint8),e.view(torch.uint8)))

    def test_zero_groups(self):
        torch = self.torch
        zero = torch.zeros(1,12,128,128)
        perm = torch.arange(128,dtype=torch.int32).repeat(12,1)
        hi,lo,scale = pack_native(zero,SimpleNamespace(sr=torch.ones(12,128),pv=perm,pk=perm),torch)
        self.assertTrue(bool((hi==0).all()))
        self.assertTrue(bool((lo==0).all()))
        self.assertTrue(bool((scale==1).all()))

if __name__ == "__main__":
    unittest.main()

