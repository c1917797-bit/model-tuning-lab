"""Stdlib-only preflight. Never imports Torch or validates actual NPU/graphs."""
import ast
import json
from pathlib import Path
import unittest
from contract import (BASE,REPO,layout,protected_ranges,span,disjoint,
                      validate_device,runtime_names,sha,PINNED,LIMITS)

class ContractTests(unittest.TestCase):
    def test_real_slot_sizes(self):
        spec=layout(4,"adjacent")
        expected={"conv":15360,"high":49152,"low":172032,"scales":21504}
        for name,size in expected.items():
            self.assertEqual(spec["regions"][name]["bytes"],4*size)
        self.assertEqual(sum(expected.values()),258048)
    def test_layout_geometry(self):
        for slots in (4,19):
            for kind in ("adjacent","guard_gaps"):
                spec=layout(slots,kind);regions=list(spec["regions"].values())
                self.assertGreater(regions[0]["offset"],0)
                for i,r in enumerate(regions):
                    self.assertEqual(r["offset"]%32,0)
                    self.assertEqual(r["bytes"]%32,0)
                    self.assertLessEqual(r["offset"]+r["bytes"],spec["total_bytes"])
                    for s in regions[:i]:
                        self.assertTrue(disjoint((r["offset"],r["offset"]+r["bytes"]),
                                                 (s["offset"],s["offset"]+s["bytes"])))
                mutable=sum(spec["regions"][n]["bytes"] for n in ("high","low","scales"))
                self.assertEqual(sum(b-a for a,b in protected_ranges(spec))+mutable,spec["total_bytes"])
                if kind=="adjacent":
                    for a,b in zip(regions,regions[1:]):self.assertEqual(a["offset"]+a["bytes"],b["offset"])
    def test_byte_spans_and_true_overlap(self):
        base=4096
        a=span(base+96,1024,2,base,8192,48)
        b=span(base+2144,1024,1,base,8192,2144)
        self.assertTrue(disjoint(a,b))
        self.assertFalse(disjoint(a,(a[1]-32,a[1]+32)))
        self.assertFalse(disjoint(a,a))
    def test_span_rejections(self):
        cases=[(4192,0,2,4096,8192,48),(4193,1024,2,4096,8192,48),
               (4192,1024,2,4096,8192,49),(4192,10000,2,4096,8192,48),
               (4192,2**64,2,4096,8192,48),(4192,1,2,4096,2**64,48),
               (4192,1,2,4096,8192,-1)]
        for args in cases:
            with self.assertRaises(ValueError):span(*args)
    def test_batch_mapping_fail_closed(self):
        for batch,physical in ((1,4),(16,7)):
            proof={"physical_npu_ids":[physical],"logical_to_physical":{"0":physical},
                   "privileged":False,"exclusive_resource_check_passed":True,"observed_at_unix_ns":100}
            self.assertTrue(validate_device(proof,batch,100))
            for key,value in (("physical_npu_ids",[0]),("logical_to_physical",{"0":5}),
                              ("privileged",True),("observed_at_unix_ns",101),
                              ("exclusive_resource_check_passed",False)):
                with self.assertRaises(ValueError):validate_device({**proof,key:value},batch,100)
            with self.assertRaises(ValueError):validate_device(proof,batch,1800*10**9+101)
    def test_frozen_protocol_sha(self):
        for name,digest in PINNED.items():self.assertEqual(sha(REPO/name),digest)
    def test_ast_and_source_seams(self):
        for path in BASE.glob("*.py"):ast.parse(path.read_text(),filename=str(path))
        adapter=(BASE/"arena_adapter.py").read_text()
        runner=(BASE/"run_shared_arena_gate.py").read_text()
        self.assertIn('self.raw[offset:end].view(DTYPES[name]).view(region["shape"])',adapter)
        self.assertNotIn("npu_format_cast(self.views",adapter)
        self.assertIn('gate.fixture[label]=record',adapter)
        self.assertLess(adapter.index('record.update(returns='),adapter.index('if dispatch_error or output_errors'))
        self.assertIn('graph_protocol.graph_case(',runner)
        self.assertIn('choices=(1,16)',runner)
        self.assertIn('len(c["actual_overlap_rejections"])==15',runner)
        self.assertEqual(LIMITS,{"state":1e-5,"output":0.00303})
    def test_runtime_manifest(self):
        manifest=json.loads((BASE/"runtime_manifest.json").read_text())
        self.assertEqual(set(manifest["sources"]),runtime_names())
        for name,digest in manifest["sources"].items():self.assertEqual(sha(REPO/name),digest)

if __name__=="__main__":unittest.main()
