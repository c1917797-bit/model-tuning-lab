import unittest
import torch
import torch.nn.functional as F
from independent_c2_reference import rotate_partial_neox,relocate_keys,causal_conv_reference

torch.set_num_threads(1)

class IndependentC2Tests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(2031)
    def test_relative_rotation_matches_new_absolute_anchor(self):
        keys=torch.randn(17,4,256,dtype=torch.float64)
        freq=1.0/(10000000.0**(torch.arange(0,64,2,dtype=torch.float64)/64))
        old=torch.arange(17)+1024;new=torch.arange(17)+7168
        stored=rotate_partial_neox(keys,old,freq)
        actual=relocate_keys(stored,old,new,freq)
        expected=rotate_partial_neox(keys,new,freq)
        torch.testing.assert_close(actual,expected,rtol=1e-9,atol=1e-9)
    def test_public_cache_is_immutable_and_nonrotary_tail_exact(self):
        keys=torch.randn(9,4,256,dtype=torch.float64);snapshot=keys.clone()
        freq=torch.randn(32,dtype=torch.float64)
        private=relocate_keys(keys,torch.zeros(9,dtype=torch.int64),torch.ones(9,dtype=torch.int64)*2048,freq)
        self.assertNotEqual(keys.data_ptr(),private.data_ptr())
        self.assertTrue(torch.equal(keys,snapshot))
        self.assertTrue(torch.equal(keys[...,64:],private[...,64:]))
    def test_opposite_rotation_sign_is_detected(self):
        keys=torch.randn(9,4,256,dtype=torch.float64);freq=torch.rand(32,dtype=torch.float64)
        old=torch.arange(9);new=old+512
        expected=rotate_partial_neox(keys,new,freq)
        wrong=relocate_keys(rotate_partial_neox(keys,old,freq),new,old,freq)
        self.assertGreater(torch.linalg.vector_norm(wrong-expected).item(),1.0)
    def test_conv_matches_independent_torch_convolution(self):
        x=torch.randn(19,11,dtype=torch.float64);w=torch.randn(11,4,dtype=torch.float64);b=torch.randn(11,dtype=torch.float64)
        actual,tail=causal_conv_reference(x,w,bias=b,activation="silu")
        expected=F.silu(F.conv1d(F.pad(x.T.unsqueeze(0),(3,0)),w[:,None,:],bias=b,groups=11)).squeeze(0).T
        torch.testing.assert_close(actual,expected,rtol=1e-10,atol=1e-10)
        torch.testing.assert_close(tail,x[-3:])
    def test_two_segments_with_warm_tail_match_full_conv(self):
        x=torch.randn(19,11,dtype=torch.float64);w=torch.randn(11,4,dtype=torch.float64)
        full,_=causal_conv_reference(x,w)
        first,tail=causal_conv_reference(x[:7],w)
        second,_=causal_conv_reference(x[7:],w,tail)
        torch.testing.assert_close(torch.cat((first,second)),full,rtol=1e-10,atol=1e-10)
    def test_only_boundary_tokens_depend_on_prior_conv_tail(self):
        x=torch.randn(19,11,dtype=torch.float64);w=torch.randn(11,4,dtype=torch.float64)
        _,tail=causal_conv_reference(x[:7],w)
        warm,_=causal_conv_reference(x[7:],w,tail)
        cold,_=causal_conv_reference(x[7:],w)
        self.assertGreater(torch.linalg.vector_norm(warm[:3]-cold[:3]).item(),0.1)
        torch.testing.assert_close(warm[3:],cold[3:],rtol=1e-10,atol=1e-10)
    def test_invalid_conv_tail_rejected(self):
        with self.assertRaises(ValueError):
            causal_conv_reference(torch.zeros(5,11),torch.zeros(11,4),torch.zeros(4,11))
if __name__=="__main__":unittest.main()
