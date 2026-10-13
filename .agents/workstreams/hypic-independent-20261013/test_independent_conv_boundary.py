import unittest,torch
from independent_conv_boundary import stitch_conv_boundary
from independent_c2_reference import causal_conv_reference
class ConvBoundaryTests(unittest.TestCase):
    def test_live_warmup_matches_full_nonzero_tail(self):
        torch.manual_seed(413);x=torch.randn(17,12);w=torch.randn(12,4);tail=torch.randn(3,12)
        public,_=causal_conv_reference(x,w,activation='silu');saved=public.clone()
        private,final,n=stitch_conv_boundary(x,public,w,tail,activation='silu')
        expected,expected_tail=causal_conv_reference(x,w,tail,activation='silu')
        torch.testing.assert_close(private,expected);torch.testing.assert_close(final,expected_tail)
        self.assertEqual(n,3);self.assertTrue(torch.equal(public,saved))
        self.assertGreater(float((public[:3]-expected[:3]).abs().max()),.01)
        self.assertNotEqual(private.data_ptr(),public.data_ptr())
    def test_short_segment_fails_closed(self):
        with self.assertRaises(ValueError):stitch_conv_boundary(torch.zeros(2,3),torch.zeros(2,3),torch.zeros(3,4),torch.zeros(3,3))
if __name__=='__main__':unittest.main()
