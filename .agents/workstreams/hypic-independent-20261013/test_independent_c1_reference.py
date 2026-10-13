import unittest
import torch
from independent_c1_reference import accumulate_segment, apply_segment, compose_segments, serial_dense_oracle

torch.set_num_threads(1)

def sample(length=17, hk=2, hv=6, dk=8, dv=7):
    rng = torch.Generator().manual_seed(714)
    k = torch.randn(length, hk, dk, generator=rng, dtype=torch.float64)
    k = k / torch.linalg.vector_norm(k, dim=-1, keepdim=True)
    v = torch.randn(length, hv, dv, generator=rng, dtype=torch.float64)
    beta = torch.rand(length, hv, generator=rng, dtype=torch.float64)
    decay = 0.8 + 0.19 * torch.rand(length, hv, generator=rng, dtype=torch.float64)
    initial = torch.randn(hv, dk, dv, generator=rng, dtype=torch.float64)
    return (k, v, beta, decay), initial

class IndependentC1Tests(unittest.TestCase):
    def test_arbitrary_prefix(self):
        inputs, initial = sample()
        actual = apply_segment(accumulate_segment(*inputs), initial)
        expected = serial_dense_oracle(*inputs, initial)
        torch.testing.assert_close(actual, expected, rtol=1e-10, atol=1e-10)
    def test_three_segments_and_nonzero_prefix(self):
        inputs, initial = sample()
        cuts = (0, 3, 10, 17)
        segments = [accumulate_segment(*(x[a:b] for x in inputs)) for a,b in zip(cuts,cuts[1:])]
        merged = compose_segments(compose_segments(segments[0],segments[1]),segments[2])
        torch.testing.assert_close(apply_segment(merged,initial),serial_dense_oracle(*inputs,initial),rtol=1e-10,atol=1e-10)
    def test_associativity(self):
        inputs, _ = sample()
        a,b,c = [accumulate_segment(*(x[s:e] for x in inputs)) for s,e in [(0,5),(5,11),(11,17)]]
        left=compose_segments(compose_segments(a,b),c)
        right=compose_segments(a,compose_segments(b,c))
        torch.testing.assert_close(left.transition,right.transition,rtol=1e-10,atol=1e-10)
        torch.testing.assert_close(left.zero_state,right.zero_state,rtol=1e-10,atol=1e-10)
    def test_naive_addition_is_detected(self):
        inputs, initial = sample()
        segment=accumulate_segment(*inputs)
        expected=serial_dense_oracle(*inputs,initial)
        self.assertGreater(torch.linalg.vector_norm(initial+segment.zero_state-expected).item(),0.1)
    def test_empty_segment_identity(self):
        inputs,initial=sample(length=0)
        torch.testing.assert_close(apply_segment(accumulate_segment(*inputs),initial),initial)
    def test_tp4_config_dimensions(self):
        inputs,initial=sample(length=11,hk=4,hv=12,dk=128,dv=128)
        torch.testing.assert_close(apply_segment(accumulate_segment(*inputs),initial),serial_dense_oracle(*inputs,initial),rtol=1e-10,atol=1e-10)
    def test_reversed_order_is_detected(self):
        inputs,initial=sample()
        a,b=[accumulate_segment(*(x[s:e] for x in inputs)) for s,e in [(0,5),(5,17)]]
        expected=serial_dense_oracle(*inputs,initial)
        wrong=apply_segment(compose_segments(b,a),initial)
        self.assertGreater(torch.linalg.vector_norm(wrong-expected).item(),0.01)
    def test_invalid_head_grouping(self):
        inputs,_=sample(hk=2,hv=5)
        with self.assertRaises(ValueError):accumulate_segment(*inputs)

if __name__ == "__main__":
    unittest.main()
