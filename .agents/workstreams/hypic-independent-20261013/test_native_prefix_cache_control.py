"""Host controls for the native PDC launcher switch; not serving proof."""
import unittest
from native_tp4_smoke import prefix_cache_flag

class PrefixCacheControl(unittest.TestCase):
    def test_historical_default_disabled(self):
        self.assertEqual(prefix_cache_flag({}),"--no-enable-prefix-caching")
    def test_explicit_switches(self):
        self.assertEqual(prefix_cache_flag({"enable_prefix_caching":False}),"--no-enable-prefix-caching")
        self.assertEqual(prefix_cache_flag({"enable_prefix_caching":True}),"--enable-prefix-caching")
    def test_reject_truthy_configuration(self):
        for value in ("false","true",0,1,None,[],{}):
            with self.subTest(value=value),self.assertRaises(ValueError):
                prefix_cache_flag({"enable_prefix_caching":value})

if __name__=="__main__":unittest.main()
