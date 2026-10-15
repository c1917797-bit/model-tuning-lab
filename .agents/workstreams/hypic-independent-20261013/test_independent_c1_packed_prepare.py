import unittest
from types import SimpleNamespace
from dataclasses import replace
from contextlib import ExitStack,contextmanager
from unittest.mock import patch
import torch
import test_independent_c1_packed_backend as fixture
from independent_c1_packed_prepare import prepare_packed_layer
from independent_compact_material_pool import CompactLinearMaterialPool,CompactLinearBody
from independent_hybrid_material import MaterialIdentity
from independent_c1_reference import SegmentAffine

class PackedPreparationTests(unittest.TestCase):
    def test_unique_material_lease_and_private_state_reset(self):
        f=fixture.PackedBackendTests()
        plans,assoc,layout,initial,cached,data,maps=f.fixture()
        digest="a"*64
        plans=tuple(replace(p,tokens_sha256=digest) if row<2 else p for row,p in enumerate(plans))
        x,b,a,tail,ct=f.inputs(layout)
        identity=MaterialIdentity("m","c","l",0,digest,10,3)
        body=CompactLinearBody(identity,SegmentAffine(cached["shared"].transition.float(),
            cached["shared"].zero_state.float()),ct["shared"])
        pool=CompactLinearMaterialPool(1024*1024);pool.publish(body)
        stage=SimpleNamespace(compact_store=pool,identity=lambda layer,rank:identity,boundary=3)
        # Deliberately nonzero actual slots for no-initial row: preparation resets privately.
        conv_cache=torch.ones(4,3,16);state_cache=torch.ones(4,2,3,5)
        layer=SimpleNamespace(prefix="l",kv_cache=(conv_cache,state_cache))
        original=pool.acquire_private;counts={"calls":0,"active":0}
        @contextmanager
        def counted(*args,**kwargs):
            counts["calls"]+=1;counts["active"]+=1
            try:
                with original(*args,**kwargs) as value:yield value
            finally:counts["active"]-=1
        pool.acquire_private=counted
        def backend(layer,given,x,b,a,states,tails,materials,**kw):
            self.assertEqual(set(materials),{digest})
            self.assertEqual(counts,{"calls":1,"active":1})
            self.assertEqual(float(states[0].abs().sum()),0)
            self.assertEqual(float(tails[0].abs().sum()),0)
            self.assertEqual(float(states[1].min()),1)
            self.assertEqual(float(tails[1].min()),1)
            return {"0":"private-result"}
        with patch("independent_c1_packed_prepare.run_packed_c1",backend):
            with ExitStack() as leases:
                result,leased,got=prepare_packed_layer(layer,stage,plans,assoc,x,b,a,leases,
                    {"official":object()})
                self.assertEqual(result,{"0":"private-result"})
                self.assertEqual(set(leased),{"0","1"})
                self.assertEqual(leased["0"][1],leased["1"][1])
                self.assertEqual(counts["active"],1)
        self.assertEqual(counts,{"calls":1,"active":0})
        self.assertTrue(torch.equal(conv_cache,torch.ones_like(conv_cache)))
        self.assertTrue(torch.equal(state_cache,torch.ones_like(state_cache)))
        # A later backend failure also releases the unique lease and writes nothing.
        with patch("independent_c1_packed_prepare.run_packed_c1",side_effect=RuntimeError("late")):
            with self.assertRaises(RuntimeError):
                with ExitStack() as leases:
                    prepare_packed_layer(layer,stage,plans,assoc,x,b,a,leases,{"official":object()})
        self.assertEqual(counts["active"],0)
        self.assertTrue(torch.equal(conv_cache,torch.ones_like(conv_cache)))

if __name__=="__main__":unittest.main()
