import unittest
from types import SimpleNamespace as N
from qwen35_prefetch_target import resolve_gateup_weight


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.weights = [object(), object()]
        self.layers = [N(layer_type=t, mlp=N(gate_up_proj=N(weight=w)))
                       for t, w in zip(("linear_attention", "full_attention"), self.weights)]
        self.model = N(model=N(layers=self.layers, start_layer=0, end_layer=2))

    def test_linear(self):
        self.assertIs(resolve_gateup_weight(self.model, "model.layers.0.linear_attn.out_proj"), self.weights[0])

    def test_full(self):
        self.assertIs(resolve_gateup_weight(self.model, "model.layers.1.self_attn.o_proj"), self.weights[1])

    def test_wrapped(self):
        self.assertIs(resolve_gateup_weight(N(language_model=self.model), "language_model.model.layers.0.linear_attn.out_proj"), self.weights[0])

    def test_rejected_prefixes(self):
        for prefix in ("model.layers.0.mlp.down_proj", "model.layers.0.self_attn.o_proj", "model.layers.2.linear_attn.out_proj", "model.layers.-1.linear_attn.out_proj", "model.layers.0.linear_attn.out_proj.extra"):
            with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                resolve_gateup_weight(self.model, prefix)

    def test_partition(self):
        self.model.model.start_layer = 1
        with self.assertRaises(ValueError):
            resolve_gateup_weight(self.model, "model.layers.0.linear_attn.out_proj")

    def test_missing_backbone(self):
        with self.assertRaises(ValueError):
            resolve_gateup_weight(N(), "model.layers.0.linear_attn.out_proj")


if __name__ == "__main__":
    unittest.main()
