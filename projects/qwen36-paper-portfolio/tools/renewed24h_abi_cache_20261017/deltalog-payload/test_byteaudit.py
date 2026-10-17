import os
from pathlib import Path
import tempfile
import unittest
import sys
P = Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import byteaudit as B


class Tests(unittest.TestCase):
    def test_actual_CPU_storage_alias_offset_extent_prefix_tail(self):
        import torch
        base=torch.arange(70,dtype=torch.float32)
        view=base[3:17]
        alias=B.whole_storage_bytes(torch,view,lambda t:2,device='cpu')
        self.assertIs(alias.untyped_storage(),base.untyped_storage())
        self.assertEqual(alias.data_ptr(),base.untyped_storage().data_ptr())
        self.assertEqual(alias.numel(),280)
        self.assertEqual(alias.storage_offset(),0)
        with tempfile.TemporaryDirectory() as d:
            store=B.Store(Path(d)/'new',4*B.CHUNK_BYTES)
            read=lambda a,b:B.chunk_bytes(torch,alias,a,b,device='cpu')
            store.before('pool',alias.numel(),read)
            view[2]=-4.25
            self.assertTrue(store.compare('pool',read,((12,68),))['bytewise_inactive_equal'])
            store.before('tail',alias.numel(),read)
            base[-1]=-17  # Exemplar excludes this tail; whole storage MUST see it.
            with self.assertRaises(B.ByteMismatch):store.compare('tail',read,((12,68),))
            self.assertTrue((store.root/'tail.before.bin').is_file())
            self.assertTrue((store.root/'tail.diff-before.bin').is_file())
            self.assertTrue((store.root/'tail.diff-after.bin').is_file())

    def test_format_or_fake_or_wrong_device_rejected(self):
        import torch
        t=torch.zeros(4)
        with self.assertRaisesRegex(B.Refusal,'explicit test/native device'):B.whole_storage_bytes(torch,t,lambda t:2)
        with self.assertRaisesRegex(B.Refusal,'ND2'):B.whole_storage_bytes(torch,t,lambda t:29,device='cpu')
        with self.assertRaises(B.Refusal):B.whole_storage_bytes(torch,object(),lambda t:2,device='cpu')

    def test_streaming_chunks_and_union_including_gap(self):
        size=B.CHUNK_BYTES+13
        data=bytes((x%251 for x in range(size)))
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            s=B.Store(Path(d)/'new',5*B.CHUNK_BYTES)
            s.before('pool',size,lambda a,b:(calls.append((a,b)) or data[a:b]))
            self.assertEqual(calls,[(0,B.CHUNK_BYTES),(B.CHUNK_BYTES,size)])
            after=bytearray(data);after[3]^=1;after[-1]^=1
            s.compare('pool',lambda a,b:bytes(after[a:b]),((2,4),(size-1,size)))

    def test_baseline_tamper_not_accepted_even_inside_allowed_write(self):
        with tempfile.TemporaryDirectory() as d:
            s=B.Store(Path(d)/'new',4*B.CHUNK_BYTES)
            s.before('pool',8,lambda a,b:b'01234567'[a:b])
            with(s.root/'pool.before.bin').open('r+b') as f:f.write(b'X')
            with self.assertRaisesRegex(B.Refusal,'stable inode/size/time'):
                s.compare('pool',lambda a,b:b'01234567'[a:b],((0,8),))

    def test_budget_exact32_80_reserve_not_bool_or_grant(self):
        sizes={r:[6*B.GIB]for r in range(4)}
        plan=B.plan_budget(sizes,40*B.GIB,50*B.GIB)
        self.assertFalse(plan['admitted'])
        self.assertEqual(plan['payload_bytes'],24*B.GIB)
        for s,committed,free in (({r:[9*B.GIB]for r in range(4)},0,80*B.GIB),
                                  (sizes,60*B.GIB,80*B.GIB),(sizes,0,24*B.GIB),
                                  (sizes,True,80*B.GIB)):
            with self.assertRaises(B.Refusal):B.plan_budget(s,committed,free)

    def test_cap_shortread_nooverwrite_or_unknown_tail_reject(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'new';s=B.Store(p,4*B.CHUNK_BYTES)
            with self.assertRaises(B.Refusal):s.before('pool',2*B.CHUNK_BYTES,lambda a,b:b'')
            s.before('short',8,lambda a,b:b'01234567'[a:b])
            with self.assertRaises(B.Refusal):s.compare('short',lambda a,b:b'',())
            with self.assertRaises(B.Refusal):s.before('../outside',8,lambda a,b:b'01234567')
            with self.assertRaises(B.Refusal):B.Store(p,4*B.CHUNK_BYTES)


if __name__=='__main__':unittest.main(verbosity=2)
