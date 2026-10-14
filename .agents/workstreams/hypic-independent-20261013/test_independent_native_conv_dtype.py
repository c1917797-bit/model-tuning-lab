import unittest,torch
from independent_native_boundary import private_conv_buffer
class ConvDtypeTests(unittest.TestCase):
    def test_float_public_tail_to_native_bf16_private(self):
        tail=torch.ones(3,7,dtype=torch.float32)
        projected=torch.zeros(8,7,dtype=torch.bfloat16)
        private=private_conv_buffer(tail,projected)
        self.assertEqual(private.dtype,torch.bfloat16)
        self.assertEqual(private.shape,(1,3,7))
        private.zero_();self.assertTrue(tail.bool().all())
if __name__=='__main__':unittest.main()
