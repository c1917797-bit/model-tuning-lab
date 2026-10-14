"""Host selection/pin controls with explicit fake inventory/material entries."""
import unittest
from types import SimpleNamespace
from independent_catalog_stage import CatalogCompactStage
from independent_request_map import RequestSlice
from independent_linear_material_pool import identity_key
from independent_mixed_query_plan import NativeQueryPlan
class CatalogStageTests(unittest.TestCase):
    def stage(self):
        return CatalogCompactStage(public_segments=[range(16),range(100,124)],
            model_identity="m",code_identity="c",capacity_bytes=4096,
            kv_capacity_bytes=4096,boundary_tokens=8,enable_mixed=True,allow_public_tail=True)
    def model(self):
        layers=[SimpleNamespace(layer_type="linear_attention",
                  linear_attn=SimpleNamespace(prefix="linear"+str(i))) for i in range(48)]
        layers += [SimpleNamespace(layer_type="full_attention",
                   self_attn=SimpleNamespace(attn=SimpleNamespace(layer_name="kv"+str(i)))) for i in range(16)]
        return SimpleNamespace(start_layer=0,end_layer=64,layers=layers)
    def test_producer_identity_second_segment_and_tail(self):
        s=self.stage();r=SimpleNamespace(rank=2,computed_tokens=0,scheduled_tokens=28)
        i=s.public_identity_for_request("layer",r,tuple(range(100,124))+(999,)*4)
        self.assertEqual(i.length,24)
        with self.assertRaises(ValueError):s.identity("layer",2)
    def test_per_segment_complete_readiness_and_exact_pins(self):
        s=self.stage();model=self.model();linear,full=s.layer_inventory(model)
        digests=list(s.catalog.entries)
        # Dummy entries only test selector/lease accounting, never tensor execution.
        for n in linear:
            for d in digests:
                s.compact_store.pool.entries[identity_key(s.identity(n,0,tokens_sha256=d))]={"pins":0}
        for n in full:
            s.compact_kv_store.entries[identity_key(s.identity(n,0,tokens_sha256=digests[0]))]={"pins":0}
        reqs=[RequestSlice("a",0,1,0,20,0,0,20),RequestSlice("b",0,1,0,28,1,20,48)]
        prompts={"a":(999,)+tuple(range(16))+(999,)*3,
                 "b":(999,)+tuple(range(100,124))+(999,)*3}
        snap=SimpleNamespace(attention_groups=((0,full),),rank=0,sampled_rows=(19,47),
                             cache_slices=(),writable_kv_slots=())
        selection=s.select_mixed(model,reqs,prompts,snap)
        self.assertEqual(selection.plans[0].skipped_tokens,8)
        self.assertIsInstance(selection.plans[1],NativeQueryPlan)
        with selection.material_guard:
            self.assertEqual(sum(e["pins"] for e in s.compact_store.pool.entries.values()),48)
        self.assertEqual(sum(e["pins"] for e in s.compact_store.pool.entries.values()),0)
        for n in full:
            s.compact_kv_store.entries[identity_key(s.identity(n,0,tokens_sha256=digests[1]))]={"pins":0}
        selection=s.select_mixed(model,reqs,prompts,snap)
        self.assertEqual([p.skipped_tokens for p in selection.plans],[8,16])
if __name__=="__main__":unittest.main()
