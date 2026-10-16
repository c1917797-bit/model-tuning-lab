import unittest
from audit_formal_pdc_terminal import validate_contract

class PDCContractTest(unittest.TestCase):
    def test_no_pdc_rejected(self):
        with self.assertRaises(ValueError):validate_contract({}, ".")
    def test_native_only_g2_not_misclassified(self):
        with self.assertRaises(ValueError):
            validate_contract(dict(performance_group="G2",enable_prefix_caching=True,
                cache_diagnostic={"compact_manifest":"x"},formal_performance=True), ".")
    def test_missing_source_bindings(self):
        with self.assertRaises(ValueError):
            validate_contract(dict(performance_group="G4",enable_prefix_caching=True,
                cache_diagnostic={"compact_manifest":"x"},formal_performance=True), ".")
if __name__=="__main__":unittest.main()
