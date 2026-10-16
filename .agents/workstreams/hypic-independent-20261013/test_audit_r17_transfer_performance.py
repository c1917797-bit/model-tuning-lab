import unittest
from audit_r17_transfer_performance import validate_transfer_mode
class TransferTimedModeTests(unittest.TestCase):
    def test_three_explicit_arms(self):
        for mode in ('native','blocking','async'):
            c={'transfer_treatment':mode,'performance_group':'G1'if mode=='native'else 'G3'}
            cfg={'c1_async_material_transfer':mode=='async','c1_async_material_verify':False}
            self.assertEqual(validate_transfer_mode(c,cfg),mode)
    def test_copy_verification_forbidden_in_timing(self):
        with self.assertRaises(ValueError):
            validate_transfer_mode({'transfer_treatment':'async','performance_group':'G3'},
                {'c1_async_material_transfer':True,'c1_async_material_verify':True})
    def test_wrong_group_or_missing_mode_rejected(self):
        for c in ({'transfer_treatment':'async','performance_group':'G1'},
                  {'performance_group':'G3'}):
            with self.assertRaises(ValueError):
                validate_transfer_mode(c,{'c1_async_material_transfer':True,'c1_async_material_verify':False})
    def test_non_boolean_or_wrong_transfer_rejected(self):
        for value in (1,'true',False,None):
            with self.subTest(value=value),self.assertRaises(ValueError):
                validate_transfer_mode({'transfer_treatment':'async','performance_group':'G3'},
                    {'c1_async_material_transfer':value,'c1_async_material_verify':False})
if __name__=='__main__':unittest.main()
