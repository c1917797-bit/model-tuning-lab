import unittest
from independent_compact_activation import c2_install_route
class Route(unittest.TestCase):
    def test_default_keeps_original(self):
        c,fn,enabled=c2_install_route({"model_identity":"x"})
        self.assertFalse(enabled);self.assertEqual(fn.__module__,"independent_compact_c2_hook")
        self.assertEqual(c,{"model_identity":"x"})
    def test_explicit_true_selects_candidate_without_mutating_caller(self):
        original={"c2_layer_completion_barrier":True,"model_identity":"x"}
        c,fn,enabled=c2_install_route(original)
        self.assertTrue(enabled);self.assertEqual(fn.__module__,"experimental_c2_layer_barrier")
        self.assertEqual(c,{"model_identity":"x"});self.assertTrue(original["c2_layer_completion_barrier"])
    def test_ambiguous_flags_rejected(self):
        for flag in (1,0,"1",None):
            with self.assertRaises(ValueError):c2_install_route({"c2_layer_completion_barrier":flag})
if __name__=="__main__":unittest.main()

