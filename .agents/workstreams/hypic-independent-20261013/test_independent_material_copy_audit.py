"""CPU controls for full-transfer audit; actual NPU proof remains separate."""
import unittest
from unittest.mock import patch
from contextlib import contextmanager
import torch
from independent_compact_material_pool import audit_private_material_copy,CompactLinearMaterialPool
from test_independent_c1_async_material import FakeRuntime,FakeTensor

def material():
    return {'transition':torch.arange(32,dtype=torch.float32).reshape(2,4,4),
            'zero_state':torch.arange(24,dtype=torch.bfloat16).reshape(2,4,3),
            'conv_tail':torch.arange(18,dtype=torch.float32).reshape(3,6)}

class MaterialCopyAuditTests(unittest.TestCase):
    def test_all_bytes_and_actual_shapes_not_sampled(self):
        data=material();copies={k:v.clone()for k,v in data.items()}
        metrics=audit_private_material_copy(data,copies,require_npu=False)
        self.assertEqual(sum(m['bytes']for m in metrics),32*4+24*2+18*4)
        self.assertTrue(all(m['all_bytes_equal']for m in metrics))
    def test_last_element_corruption_rejected(self):
        data=material();copies={k:v.clone()for k,v in data.items()}
        copies['conv_tail'][-1,-1]+=1
        with self.assertRaisesRegex(ValueError,'byte mismatch'):
            audit_private_material_copy(data,copies,require_npu=False)
    def test_signed_zero_bit_difference_is_rejected(self):
        data=material();copies={k:v.clone()for k,v in data.items()}
        copies['transition'][0,0,0]=-0.
        self.assertEqual(float(data['transition'][0,0,0]),float(copies['transition'][0,0,0]))
        with self.assertRaisesRegex(ValueError,'byte mismatch'):
            audit_private_material_copy(data,copies,require_npu=False)
    def test_equal_nan_bytes_are_copy_equality_not_numeric_finiteness(self):
        data=material();data['transition'][0,0,0]=float('nan')
        metrics=audit_private_material_copy(data,{k:v.clone()for k,v in data.items()},require_npu=False)
        self.assertEqual(len(metrics),3)
    def test_wrong_dtype_shape_or_key_rejected(self):
        data=material()
        for replacement in (data['zero_state'].float(),data['zero_state'].reshape(2,3,4)):
            copies=dict(data,zero_state=replacement)
            with self.assertRaisesRegex(ValueError,'identity/layout'):
                audit_private_material_copy(data,copies,require_npu=False)
        with self.assertRaisesRegex(ValueError,'key mismatch'):
            audit_private_material_copy(data,{'transition':data['transition']},require_npu=False)
    def test_real_device_required_by_default(self):
        data=material()
        with self.assertRaisesRegex(ValueError,'identity/layout'):
            audit_private_material_copy(data,data)
    def test_verify_flag_requires_explicit_async(self):
        for async_flag,verify_flag in ((False,True),(True,1),(True,'true')):
            with self.assertRaises(ValueError):
                CompactLinearMaterialPool(1024,async_material_transfer=async_flag,
                    verify_async_transfer=verify_flag)
    def test_verify_mode_needs_evidence_sink_before_acquiring(self):
        pool=CompactLinearMaterialPool(1024,async_material_transfer=True,verify_async_transfer=True)
        with self.assertRaisesRegex(ValueError,'evidence sink'):
            with pool.acquire_private(None,device='npu:0'):pass
    def test_verified_receipt_precedes_yield_and_lease_release(self):
        log=[];rt=FakeRuntime(log);data={k:FakeTensor(log,k)for k in material()}
        pool=CompactLinearMaterialPool(1024,async_material_transfer=True,verify_async_transfer=True)
        @contextmanager
        def acquire(key):
            try:yield 19,data
            finally:log.append('lease-exit')
        pool.on_transfer_verified=lambda identity,generation,metrics:log.append(('receipt',identity,generation,metrics))
        with patch.object(pool.pool,'acquire_private',side_effect=acquire),patch(
                'independent_compact_material_pool.identity_key',return_value='k'),patch(
                'independent_compact_material_pool._npu_runtime',return_value=rt),patch(
                'independent_compact_material_pool.audit_private_material_copy',return_value=['full-bytes']):
            with pool.acquire_private('identity',device='npu:0'):
                self.assertIn(('receipt','identity',19,['full-bytes']),log)
                self.assertNotIn('lease-exit',log)
        self.assertLess(log.index('event-sync'),log.index('lease-exit'))

if __name__=='__main__':unittest.main()
