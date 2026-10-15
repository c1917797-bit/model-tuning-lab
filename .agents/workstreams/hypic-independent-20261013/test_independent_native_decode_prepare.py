import unittest
from types import SimpleNamespace
from unittest.mock import patch
import torch
from independent_mixed_query_plan import NativeQueryPlan
from independent_native_decode_prepare import prepare_native_decode,shadow_metrics
from independent_compact_activation import c1_install_route

class PrepareTests(unittest.TestCase):
    def case(self):
        plans=[NativeQueryPlan("a",0,4,0,12,1,"decode"),
               SimpleNamespace(request_id="hot",retained_offsets=(0,1),scheduled_tokens=32),
               NativeQueryPlan("b",0,4,33,13,1,"decode")]
        assoc=[SimpleNamespace(state_slot=i,has_initial_state=True) for i in range(3)]
        layer=SimpleNamespace(prefix="layer",kv_cache=(torch.ones(3,3,6),torch.ones(3,2,3,5)))
        return layer,plans,assoc,torch.ones(4,6),torch.ones(4,2),torch.ones(4,2),SimpleNamespace(non_spec_state_indices_tensor=torch.zeros(3,dtype=torch.int32))
    def test_selection_shadow_then_no_repeat(self):
        args=self.case();seen=[];shadowed=set();packed_calls=[]
        def backend(layer,packed,**kw):
            packed_calls.append([r.projected_offset for r in packed.rows])
            return {r.request_id:(torch.ones(2,3),torch.ones(2,5,3),torch.ones(3,6)) for r in packed.rows}
        def boundary(*args,**kwargs):
            return lambda initial:(torch.ones(1,2,3),torch.ones(2,5,3),torch.ones(3,6))
        with patch("independent_native_decode_prepare.run_private_native_decode",backend),patch("independent_native_boundary.make_boundary_runner",boundary):
            first=prepare_native_decode(*args,shadowed=shadowed,emit=seen.append)
            second=prepare_native_decode(*args,shadowed=shadowed,emit=seen.append)
        self.assertEqual(set(first),{"a","b"});self.assertEqual(set(second),{"a","b"})
        self.assertEqual(packed_calls,[[0,3],[0,3]])
        self.assertEqual(sum(x["event"]=="native_decode_batch_shadow_checked" for x in seen),1)
        self.assertTrue(all(x.get("passed",True) for x in seen))
    def test_failed_shadow_stays_unverified(self):
        args=self.case();shadowed=set();events=[]
        def backend(layer,packed,**kw):
            return {r.request_id:(torch.ones(2,3)*2,torch.ones(2,5,3),torch.ones(3,6)) for r in packed.rows}
        def boundary(*args,**kwargs):
            return lambda initial:(torch.ones(1,2,3),torch.ones(2,5,3),torch.ones(3,6))
        with patch("independent_native_decode_prepare.run_private_native_decode",backend),patch("independent_native_boundary.make_boundary_runner",boundary):
            with self.assertRaises(ValueError):prepare_native_decode(*args,shadowed=shadowed,emit=events.append)
        self.assertFalse(shadowed);self.assertFalse(events[-1]["passed"])
    def test_shadow_nonfinite(self):
        with self.assertRaises(ValueError):shadow_metrics(torch.tensor([float("nan")]),torch.ones(1))
    def test_default_off_and_explicit_route(self):
        calls=[]
        def install(stage,**kw):calls.append(kw);return lambda:None
        with patch("independent_compact_gdn_hook.install_compact_gdn",install):
            cfg,fn,on=c1_install_route({"x":1});self.assertFalse(on);self.assertEqual(cfg,{"x":1});fn(None)
            cfg,fn,on=c1_install_route({"native_decode_batch":True});self.assertTrue(on);fn(None,enabled=True,emit=print)
            with self.assertRaises(ValueError):c1_install_route({"native_decode_batch":"1"})
        self.assertFalse(calls[0]["native_decode_batch"]);self.assertTrue(calls[1]["native_decode_batch"])

if __name__=="__main__":unittest.main()
