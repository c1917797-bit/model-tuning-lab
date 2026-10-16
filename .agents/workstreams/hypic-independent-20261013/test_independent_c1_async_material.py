"""Host ordering/lifetime controls; not evidence of actual NPU copy semantics."""
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from independent_compact_material_pool import (
    CompactLinearMaterialPool,transfer_private_material)
from independent_compact_stage import CompactCanonicalStage

class FakeTensor:
    def __init__(self,log,name,fail=False):
        self.log=log;self.name=name;self.fail=fail
    def to(self,**kwargs):
        self.log.append(('copy',self.name,kwargs))
        if self.fail:raise ValueError('copy failed')
        return ('device-private',self.name)

class FakeStream:
    def __init__(self,log,fail=False):self.log=log;self.fail=fail
    def synchronize(self):
        self.log.append('stream-sync')
        if self.fail:raise ValueError('stream failed')

class FakeEvent:
    def __init__(self,log,*,record_fail=False,sync_fail=False):
        self.log=log;self.record_fail=record_fail;self.sync_fail=sync_fail
    def record(self,stream):
        self.log.append(('event-record',stream))
        if self.record_fail:raise ValueError('record failed')
    def synchronize(self):
        self.log.append('event-sync')
        if self.sync_fail:raise ValueError('event failed')

class FakeRuntime:
    def __init__(self,log,*,record_fail=False,event_fail=False,stream_fail=False):
        self.log=log;self.copy_stream=FakeStream(log,stream_fail)
        self.event=FakeEvent(log,record_fail=record_fail,sync_fail=event_fail)
    @contextmanager
    def device(self,device):
        self.log.append(('device-enter',device))
        try:yield
        finally:self.log.append('device-exit')
    def current_stream(self):return self.copy_stream
    def Event(self):return self.event
    @contextmanager
    def stream(self,stream):
        self.log.append('stream-enter')
        try:yield
        finally:self.log.append('stream-exit')

class AsyncMaterialTests(unittest.TestCase):
    def setup_case(self,**kwargs):
        log=[];runtime=FakeRuntime(log,**kwargs)
        data={k:FakeTensor(log,k)for k in ('transition','zero_state','conv_tail')}
        return log,runtime,data,[]
    def test_default_no_device_runtime_import_and_old_copy_call(self):
        log=[];data={'x':FakeTensor(log,'x')}
        with patch('independent_compact_material_pool._npu_runtime',side_effect=AssertionError):
            with transfer_private_material(data,device='cpu')as private:
                self.assertEqual(private['x'],('device-private','x'))
        self.assertEqual(log,[('copy','x',{'device':'cpu'})])
    def test_all_copies_record_before_consumer_and_fence_on_exit(self):
        log,rt,data,q=self.setup_case()
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with transfer_private_material(data,device='npu:2',asynchronous=True,quarantine=q)as private:
                self.assertEqual(set(private),set(data))
                self.assertNotIn('event-sync',log)
                self.assertIn(('event-record',rt.copy_stream),log)
                log.append('consumer')
        self.assertLess(log.index('consumer'),log.index('event-sync'))
        self.assertTrue(all(x[2]['non_blocking']is True for x in log if isinstance(x,tuple)and x[0]=='copy'))
        self.assertEqual(q,[])
    def test_consumer_exception_still_fences(self):
        log,rt,data,q=self.setup_case()
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(ValueError,'consumer'):
                with transfer_private_material(data,device='npu',asynchronous=True,quarantine=q):
                    raise ValueError('consumer')
        self.assertIn('event-sync',log);self.assertEqual(q,[])
    def test_partial_copy_failure_fences_before_source_release(self):
        log,rt,data,q=self.setup_case();data['zero_state'].fail=True
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(ValueError,'copy failed'):
                with transfer_private_material(data,device='npu:0',asynchronous=True,quarantine=q):
                    self.fail('must not yield')
        self.assertIn('stream-sync',log)
        self.assertNotIn('event-sync',log);self.assertEqual(q,[])
    def test_record_failure_fences_partial_stream(self):
        log,rt,data,q=self.setup_case(record_fail=True)
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(ValueError,'record failed'):
                with transfer_private_material(data,device='npu:0',asynchronous=True,quarantine=q):
                    self.fail('must not yield')
        self.assertIn('stream-sync',log);self.assertEqual(q,[])
    def test_event_failure_fallback_does_not_silently_accept(self):
        log,rt,data,q=self.setup_case(event_fail=True)
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(ValueError,'event failed'):
                with transfer_private_material(data,device='npu:0',asynchronous=True,quarantine=q):pass
        self.assertEqual(log.count('stream-sync'),1);self.assertEqual(q,[])
    def test_unknown_completion_retains_source_and_destination_references(self):
        log,rt,data,q=self.setup_case(event_fail=True,stream_fail=True)
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(RuntimeError,'sources quarantined'):
                with transfer_private_material(data,device='npu:0',asynchronous=True,quarantine=q)as private:pass
        self.assertEqual(len(q),1)
        self.assertIs(q[0][0],data);self.assertIs(q[0][1],private)
        self.assertIs(q[0][2],rt.event);self.assertIs(q[0][3],rt.copy_stream)
    def test_partial_copy_unknown_completion_quarantines(self):
        log,rt,data,q=self.setup_case(stream_fail=True);data['zero_state'].fail=True
        with patch('independent_compact_material_pool._npu_runtime',return_value=rt):
            with self.assertRaisesRegex(RuntimeError,'sources quarantined'):
                with transfer_private_material(data,device='npu:0',asynchronous=True,quarantine=q):pass
        self.assertIs(q[0][0],data)
        self.assertEqual(set(q[0][1]),{'transition'})
    def test_enabled_requires_npu_target_and_owning_quarantine(self):
        for device in ('cpu','cuda:0','npu:bad','npu:-1'):
            with self.subTest(device=device),self.assertRaises(ValueError):
                with transfer_private_material({},device=device,asynchronous=True,quarantine=[]):pass
        with self.assertRaisesRegex(ValueError,'quarantine'):
            with transfer_private_material({},device='npu',asynchronous=True):pass
    def test_boolean_is_strict_and_pool_default_disabled(self):
        self.assertIs(CompactLinearMaterialPool(1024).async_material_transfer,False)
        for value in (1,0,'true',None):
            with self.subTest(value=value),self.assertRaises(ValueError):
                CompactLinearMaterialPool(1024,async_material_transfer=value)
            with self.subTest(value=value),self.assertRaises(ValueError):
                with transfer_private_material({},device='cpu',asynchronous=value):pass
    def test_stage_routes_explicit_flag_to_pool(self):
        for enabled in (False,True):
            stage=CompactCanonicalStage(model_identity='model',code_identity='source',
                public_tokens=tuple(range(32)),capacity_bytes=1024,
                c1_async_material_transfer=enabled)
            self.assertIs(stage.compact_store.async_material_transfer,enabled)
    def test_unknown_completion_blocks_future_pool_leases(self):
        pool=CompactLinearMaterialPool(1024,async_material_transfer=True)
        pool._quarantined_transfers.append(('retained-source',))
        with self.assertRaisesRegex(RuntimeError,'pool blocked'):
            with pool.acquire_private(None,device='npu:0'):pass
    def test_pool_lease_is_held_until_event_completion(self):
        log,rt,data,q=self.setup_case()
        pool=CompactLinearMaterialPool(1024,async_material_transfer=True)
        @contextmanager
        def acquire(key):
            log.append('lease-enter')
            try:yield 17,data
            finally:log.append('lease-exit')
        with patch.object(pool.pool,'acquire_private',side_effect=acquire),patch(
                'independent_compact_material_pool.identity_key',return_value='identity'),patch(
                'independent_compact_material_pool._npu_runtime',return_value=rt):
            with pool.acquire_private('identity',device='npu:0')as(generation,body):
                self.assertEqual(generation,17)
                self.assertEqual(body.affine.transition,('device-private','transition'))
                self.assertNotIn('lease-exit',log)
        self.assertLess(log.index('event-sync'),log.index('lease-exit'))

if __name__=='__main__':unittest.main()
