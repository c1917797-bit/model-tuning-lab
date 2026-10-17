import unittest
from independent_compact_activation import c2_install_route
from independent_layer_finite_guard import LayerFiniteGuard
from unittest.mock import patch
import torch

class Route(unittest.TestCase):
    def test_default_off(self):
        remaining,install,barrier=c2_install_route({'c2_layer_completion_barrier':True,'kept':1})
        self.assertFalse(install.c2_layer_finite_gate)
        self.assertEqual(remaining,{'kept':1});self.assertTrue(barrier)
    def test_enabled_route(self):
        _,install,_=c2_install_route({'c2_layer_completion_barrier':True,'c2_layer_finite_gate':True})
        with patch('experimental_c2_layer_barrier.install_compact_c2') as target:
            # Resolve again while patched: route must pass the explicit mode.
            _,install,_=c2_install_route({'c2_layer_completion_barrier':True,'c2_layer_finite_gate':True})
            install('stage',enabled=True,emit='sink')
            target.assert_called_once_with('stage',enabled=True,emit='sink',finite_gate=True)
    def test_requires_barrier(self):
        with self.assertRaises(ValueError):c2_install_route({'c2_layer_finite_gate':True})
    def test_rejects_non_boolean(self):
        for value in (1,0,None,'true'):
            with self.assertRaises(ValueError):
                c2_install_route({'c2_layer_completion_barrier':True,'c2_layer_finite_gate':value})
    def test_all_request_kv_checked_with_one_scalar_wait(self):
        guard=LayerFiniteGuard();waits=[];original=torch.Tensor.item
        for _ in range(4):guard.collect(torch.ones(3),torch.ones(3))
        def item(tensor,*args):
            waits.append(1);return original(tensor,*args)
        with patch.object(torch.Tensor,'item',item):
            self.assertEqual(guard.validate(),8)
        self.assertEqual(waits,[1])
    def test_late_nonfinite_request_rejected(self):
        guard=LayerFiniteGuard()
        guard.collect(torch.ones(3),torch.ones(3))
        guard.collect(torch.ones(3),torch.tensor([float('inf')]))
        with self.assertRaises(ValueError):guard.validate()

if __name__=='__main__':unittest.main()
