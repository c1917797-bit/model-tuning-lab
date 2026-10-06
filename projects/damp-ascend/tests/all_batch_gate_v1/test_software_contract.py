#!/usr/bin/env python3
"""Stdlib-only preparation tests. No Torch import, load, container or NPU proof."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from contract import (BASE,REPO,WRAPPER,OLD,SOURCE_SHA,PINNED,OWN_NAMES,BATCH_GROUPS,
    LIMITS,LAYOUTS,REGION_SPECS,layout,span,disjoint,protected_ranges,validate_device,
    validate_shards,sha,require)
from metadata_contract import metadata_cases,metadata_valid,copy_bounds

def function_node(tree,name):
    return next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)

class PreparationOnly(unittest.TestCase):
    def test_real_shard_partition(self):
        self.assertEqual(sorted(t for group in BATCH_GROUPS.values() for t in group),list(range(1,17)))
        self.assertTrue(all(len(g)==4 and max(g)-min(g)==3 for g in BATCH_GROUPS.values()))
        self.assertEqual(BATCH_GROUPS,{4:(1,2,3,4),5:(5,6,7,8),6:(9,10,11,12),7:(13,14,15,16)})

    def test_byte_layout_every_realT(self):
        per_slot=(15360,49152,172032,21504)
        for t in range(1,17):
            for kind in LAYOUTS:
                spec=layout(t+3,kind)
                self.assertEqual(spec["slots"],t+3)
                self.assertEqual(tuple(r["bytes"]//(t+3) for r in spec["regions"].values()),per_slot)
                previous=0
                for name,region in spec["regions"].items():
                    self.assertGreaterEqual(region["offset"],96)
                    self.assertEqual(region["offset"]%32,0)
                    self.assertEqual(region["bytes"]%32,0)
                    self.assertGreaterEqual(region["offset"],previous)
                    self.assertEqual(region["shape"][0],t+3)
                    previous=region["offset"]+region["bytes"]
                guard=protected_ranges(spec)
                self.assertGreater(sum(b-a for a,b in guard),per_slot[0]*(t+3))
                self.assertTrue(all(b>a for a,b in guard))
                self.assertEqual(spec["total_bytes"]%32,0)
        for bad in (0,3,20,True,4.0):
            with self.assertRaises(ValueError):layout(bad,"adjacent")

    def test_span_math_and_actual_overlap(self):
        base=0x1000;total=0x10000
        a=span(base+96,16,2,base,total,48)
        b=span(base+128,32,1,base,total,128)
        self.assertTrue(disjoint(a,b))
        self.assertFalse(disjoint(a,(a[1]-32,a[1]+64)))
        for fields in ((base+97,16,2,base,total,48),
                       (base+96,16,2,base,total,49),
                       (base+96,2**64,4,base,total,24),
                       (base+96,16,2,base,100,48),
                       (2**64-32,16,2,2**64-32,64,0)):
            with self.assertRaises(ValueError):span(*fields)

    def test_metadata_domain_and_boundary_counts(self):
        counts={}
        for t in range(1,17):
            rows=metadata_cases(t,t+3);counts[t]=len(rows)
            self.assertEqual(len({n for n,_,_ in rows}),len(rows))
            self.assertTrue(metadata_valid([0]+[1]*t,list(range(t)),t+3))
            for name,lengths,indices in rows:
                self.assertEqual(len(lengths),t+1)
                self.assertEqual(len(indices),t)
                self.assertFalse(metadata_valid(lengths,indices,t+3),name)
                self.assertTrue(all(-(2**31)<=v<2**31 for v in lengths+indices))
        self.assertEqual(counts[1],9)
        self.assertEqual({t:counts[t] for t in (2,7,8,9,15)},{2:14,7:14,8:14,9:17,15:20})
        for t in (9,10,15,16):
            labels={name for name,_,_ in metadata_cases(t,t+3)}
            self.assertTrue(any("token_7" in n for n in labels))
            if t>=10:self.assertTrue(any("token_8" in n for n in labels))
        self.assertFalse(metadata_valid([],[],1))
        with self.assertRaises(ValueError):metadata_cases(17,20)

    def test_metadata_copy_capacity(self):
        for t in range(1,17):
            bounds=copy_bounds(t)
            self.assertLessEqual(bounds["indices_copied_int32"],16)
            self.assertLessEqual(bounds["last_local_int32_exclusive"],40)
            self.assertEqual(bounds["tasks"],12*t)
            self.assertGreaterEqual(bounds["indices_copied_int32"],t)
            self.assertGreaterEqual(bounds["lengths_copied_int32"],t+1)
        self.assertEqual(copy_bounds(7)["lengths_copied_int32"],8)
        self.assertEqual(copy_bounds(8)["lengths_copied_int32"],16)
        self.assertEqual(copy_bounds(16)["lengths_copied_int32"],24)

    def test_fresh_resource_authority_partition(self):
        now=10**18
        for physical in BATCH_GROUPS:
            proof={"physical_npu_ids":[physical],"logical_to_physical":{"0":physical},
                "privileged":False,"exclusive_resource_check_passed":True,
                "observed_at_unix_ns":now-10**9}
            self.assertTrue(validate_device(proof,physical,now))
            for key,value in (("physical_npu_ids",[0]),("logical_to_physical",{"0":0}),
                              ("privileged",True),("exclusive_resource_check_passed",False),
                              ("observed_at_unix_ns",now+1),
                              ("observed_at_unix_ns",now-1800*10**9-1)):
                bad=dict(proof);bad[key]=value
                with self.assertRaises(ValueError):validate_device(bad,physical,now)

    def test_exact_frozen_native_math_source_identity(self):
        for name,digest in PINNED.items():self.assertEqual(sha(REPO/name),digest,name)
        manifest=json.loads((WRAPPER/"source_manifest.json").read_text())
        self.assertEqual(sha(WRAPPER/"source_manifest.json"),SOURCE_SHA)
        self.assertEqual(manifest["namespace"],"qwen36_damp_all_batch_v3")
        self.assertEqual(len(manifest["compiled_sources"]),9)
        for name,digest in manifest["compiled_sources"].items():
            self.assertEqual(sha(REPO/name),digest,name)
        self.assertEqual(LIMITS,{"state":1e-5,"output":0.00303})

    def test_unchanged_arena_guard_and_error_observation_ast(self):
        old=ast.parse((BASE.parent/"shared_arena_gate_v1/arena_adapter.py").read_text())
        new=ast.parse((BASE/"arena_adapter.py").read_text())
        for name in ("tensor_span","storage_disjoint","nd_plain","identity","overlap_negatives"):
            self.assertEqual(ast.dump(function_node(new,name)),ast.dump(function_node(old,name)),name)
        for class_name in ("Arena","Registry"):
            old_node=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name==class_name)
            new_node=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name==class_name)
            self.assertEqual(ast.dump(new_node),ast.dump(old_node),class_name)
        # The generic layout changes allocation geometry, not guard/evidence behavior.
        self.assertIn("raw_before",ast.unparse(function_node(new,"observe")))
        self.assertIn("dispatch_error",ast.unparse(function_node(new,"observe")))

    def test_runner_only_explicit_glue_and_realT_call(self):
        source=(BASE/"run_all_batch_gate.py").read_text();tree=ast.parse(source)
        require("DAMP_RUN_ALL_BATCH_GATE_V1" in source and "DAMP_ENABLE_ALL_BATCH_WRAPPER_V3" in source,
                "defaultOFF explicit target")
        attrs=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Attribute) and isinstance(target.value,ast.Name):
                        if target.value.id in ("protocols","graph_protocol"):
                            attrs.append(target.value.id+"."+target.attr)
        self.assertEqual(set(attrs),{"protocols.observe","protocols.storage_disjoint",
            "graph_protocol.observe","graph_protocol.storage_disjoint","graph_protocol.metadata_cases"})
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and
               isinstance(node.func,ast.Attribute) and node.func.attr=="graph_case"]
        self.assertEqual(len(calls),1)
        self.assertEqual(ast.unparse(calls[0].args[-2]),"batch")
        self.assertNotIn("args.batch",source)
        meta=ast.unparse(function_node(ast.parse((BASE/"arena_adapter.py").read_text()),"meta_gate"))
        self.assertIn("range(1, 17)",meta)
        self.assertNotIn("query_B2",meta)
        self.assertIn("query_T0",meta);self.assertIn("query_T17",meta)

    def test_runtime_manifest_bindings_and_no_torch_import(self):
        runtime=json.loads((BASE/"runtime_manifest.json").read_text())
        expected=set(PINNED)|{str((BASE/n).relative_to(REPO)) for n in OWN_NAMES}
        self.assertEqual(runtime["schema"],"damp_all_batch_gate_runtime_v1")
        self.assertEqual(set(runtime["sources"]),expected)
        for name,digest in runtime["sources"].items():self.assertEqual(sha(REPO/name),digest,name)
        self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)

    def test_source_bound_coverage_aggregator_not_sample(self):
        reports=[]
        for physical,group in BATCH_GROUPS.items():
            cases=[]
            for t in group:
                for kind in LAYOUTS:
                    for variant in ("SR1_perHv_permutations","power2_perHv_permutations"):
                        cases.append({"batch":t,"stage":"graph_restricted","status":"passed",
                            "shared_arena_layout":kind,"variant":variant,
                            "steps":[{"passed":True,"indices":list(range(t))} for _ in range(160)],
                            "identical_repeats":8,"warmups":3,"changed_replays":160,
                            "invalid_dynamic_cases":[{"passed":True} for _ in metadata_cases(t,t+3)],
                            "actual_overlap_rejections":[{"guards":{"test_only":True}} for _ in range(15)]})
            reports.append({"schema":"damp_all_batch_restricted_shared_graph_gate_v1",
                "status":"restricted_all_batch_shared_arena_shard_pass","namespace":"qwen36_damp_all_batch_v3",
                "physical_card":physical,"batches":list(group),"npu_executed":True,
                "graph_supported":True,"shared_arena_supported":True,"serving_ready":False,
                "general_sr_supported":False,"limits":LIMITS,"cases":cases,
                "bindings":{"source_manifest_sha256":SOURCE_SHA,"runtime_manifest_sha256":"1"*64,
                            "library_sha256":"2"*64}})
        # These synthetic dictionaries exercise a parser ONLY, never saved as real results.
        self.assertEqual(validate_shards(reports)["cases"],64)
        for bad in (reports[:-1],reports+[reports[0]]):
            with self.assertRaises(ValueError):validate_shards(bad)
        changed=copy.deepcopy(reports);changed[0]["cases"].pop()
        with self.assertRaises(ValueError):validate_shards(changed)
        changed=copy.deepcopy(reports);changed[0]["bindings"]["library_sha256"]="3"*64
        with self.assertRaises(ValueError):validate_shards(changed)

if __name__=="__main__":
    unittest.main()
