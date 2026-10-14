import unittest
import torch
from independent_kv_slots import install_private_kv_parts


class KVPartsTests(unittest.TestCase):
    def test_real_separate_cache_parts_modified_only_at_owned_rows(self):
        k=torch.zeros(2,4,1,8);v=torch.zeros_like(k)
        pk=torch.ones(2,1,8);pv=pk*3
        install_private_kv_parts(k,v,pk,pv,(1,6),{1,6})
        torch.testing.assert_close(k.reshape(8,1,8)[[1,6]],pk)
        self.assertEqual(float(k.sum()),16.);self.assertEqual(float(v.sum()),48.)
    def test_both_targets_validated_before_any_write(self):
        k=torch.zeros(2,4,1,8);v=torch.zeros(2,4,2,8)
        with self.assertRaises(ValueError):
            install_private_kv_parts(k,v,torch.ones(2,1,8),torch.ones(2,1,8),(1,6),{1,6})
        self.assertEqual(float(k.sum()),0.)
    def test_disabled_c2_does_not_import_device_runtime(self):
        from independent_compact_c2_hook import install_compact_c2
        install_compact_c2(None,enabled=False)()


if __name__=='__main__':unittest.main()
