import unittest,torch
from independent_kv_slots import install_private_kv
class KVSlotTests(unittest.TestCase):
    def test_only_owned_rows_written(self):
        cache=torch.zeros(2,2,4,1,8);k=torch.ones(2,1,8);v=k*2
        install_private_kv(cache,k,v,[1,6],{1,6})
        torch.testing.assert_close(cache[0].reshape(8,1,8)[[1,6]],k)
        self.assertEqual(float(cache[0].sum()),16);self.assertEqual(float(cache[1].sum()),32)
    def test_duplicate_or_unowned_rejected_before_write(self):
        for slots,owned in [([1,1],{1}),([1,6],{1})]:
            cache=torch.zeros(2,2,4,1,8)
            with self.assertRaises(ValueError):install_private_kv(cache,torch.ones(2,1,8),torch.ones(2,1,8),slots,owned)
            self.assertEqual(float(cache.sum()),0)
    def test_wrong_head_layout_rejected(self):
        with self.assertRaises(ValueError):install_private_kv(torch.zeros(2,2,4,1,8),torch.ones(2,2,8),torch.ones(2,2,8),[1,6],{1,6})
if __name__=='__main__':unittest.main()
