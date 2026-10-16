import unittest
import torch
from independent_prepared_initial_snapshot import initial_snapshot

class ForbiddenRead:
    def __getitem__(self,index):
        raise AssertionError("unused real cache read")

class SnapshotTests(unittest.TestCase):
    def test_prepared_without_shadow_reads_nothing(self):
        self.assertIsNone(initial_snapshot(ForbiddenRead(),ForbiddenRead(),3,
            has_initial_state=True,prepared_result=True,serial_shadow=False))
    def test_serial_shadow_still_snapshots(self):
        s=torch.arange(24.).reshape(2,3,4);c=torch.arange(12.).reshape(2,2,3)
        a,b=initial_snapshot(s,c,1,has_initial_state=True,
            prepared_result=True,serial_shadow=True)
        self.assertTrue(torch.equal(a,s[1].transpose(-1,-2)))
        a.zero_();b.zero_()
        self.assertGreater(s[1].abs().sum().item(),0)
        self.assertGreater(c[1].abs().sum().item(),0)
    def test_unprepared_snapshots(self):
        s=torch.ones(2,3,4);c=torch.ones(2,2,3)
        a,b=initial_snapshot(s,c,0,has_initial_state=True,
            prepared_result=False,serial_shadow=False)
        self.assertEqual(tuple(a.shape),(4,3));self.assertEqual(tuple(b.shape),(2,3))
    def test_no_initial_state_zeros_only_private(self):
        s=torch.ones(2,3,4);c=torch.ones(2,2,3)
        a,b=initial_snapshot(s,c,0,has_initial_state=False,
            prepared_result=False,serial_shadow=False)
        self.assertEqual(a.sum().item()+b.sum().item(),0)
        self.assertEqual(s.sum().item()+c.sum().item(),36)
    def test_reject_ambiguous_policy_before_cache_read(self):
        for key in ("has_initial_state","prepared_result","serial_shadow"):
            kw=dict(has_initial_state=True,prepared_result=True,serial_shadow=False)
            kw[key]=1
            with self.assertRaises(ValueError):
                initial_snapshot(ForbiddenRead(),ForbiddenRead(),0,**kw)
    def test_reject_invalid_slot_even_if_unused(self):
        for slot in (-1,True,"0"):
            with self.assertRaises(ValueError):
                initial_snapshot(ForbiddenRead(),ForbiddenRead(),slot,
                    has_initial_state=True,prepared_result=True,serial_shadow=False)
