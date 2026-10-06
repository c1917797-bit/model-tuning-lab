import importlib.util
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"plugin"))
from kvbuffer_parallel.contract import *

class ContractTests(unittest.TestCase):
    def test_native_text_mask_none(self):
        admit_text_request([11,12,13],None,[],None)
    def test_native_text_mask_all_true(self):
        admit_text_request([11,12,13],None,[],[True,True,True])
    def test_native_text_mask_false_rejected(self):
        with self.assertRaises(ValueError):
            admit_text_request([11,12,13],None,[],[True,False,True])
    def test_native_text_mask_wrong_length_rejected(self):
        for mask in ([],[True],[True]*4):
            with self.assertRaises(ValueError):
                admit_text_request([11,12,13],None,[],mask)
    def test_native_text_mask_nonbool_rejected(self):
        for mask in ([True,1,True],[True,"True",True],[True,None,True],(True,)*3):
            with self.assertRaises(ValueError):
                admit_text_request([11,12,13],None,[],mask)
    def test_native_text_embeds_and_mm_still_rejected(self):
        for ids,embeds,mm,mask in (([11],object(),[],None),([11],None,[object()],None),
                                  ([],None,[],None),([True],None,[],None)):
            with self.assertRaises(ValueError):admit_text_request(ids,embeds,mm,mask)
    def test_cann91_prelaunch_dependency_fixes(self):
        src=(ROOT/"operator/op_kernel/qwen36_gdn_kvbuffer_parallel.h").read_text()
        self.assertIn("broadcastTmpUb_ = tmpBuff_.GetWithOffset<uint8_t>(4096, offset)",src)
        calls=[line for line in src.splitlines() if "Broadcast<float,2,1>(" in line]
        self.assertEqual(len(calls),4)
        self.assertTrue(all(", broadcastTmpUb_);" in line for line in calls))
        for producer,consumer in (
            ("ReduceRows(qDotsUb_, dotBatchUb_, LOG_CAPACITY);","MatVecMul(kBatchUb_, kUb_"),
            ("Duplicate(scalarUb_, value, 8);","Exp(scalarUb_"),
            ("ReduceRows(deltaUb_, broadUb_, V_STEP);","MatVecMul(stateUb_, qUb_"),
            ("LoadBf16Vector(keyGm_, sourceOffset, kLogUb_, kInQueue_, HEAD_DIM);","LocalTensor<bfloat16_t> local"),
            ("ReduceRows(attnUb_, broadUb_, V_STEP);\n            // RAW:", "StoreBase(baseOffset, V_STEP)"),
            ("DataCopy(kTileUb_, kBatchUb_[ks], DataCopyParams{16,8,8,0});","for (uint32_t v = 0"),
            ("Duplicate(attnUb_, 0.0f, V_STEP);","for (uint32_t vs=0")):
            middle=src.split(producer,1)[1].split(consumer,1)[0]
            self.assertIn("PipeBarrier<PIPE_V>();",middle)
        patch=(ROOT/"plugin/kvbuffer_parallel/patch.py").read_text()
        self.assertIn("admit_text_request(request.prompt_token_ids",patch)
        self.assertNotIn("request.prompt_is_token_ids and",patch)
    def test_native_lengths_not_cumsum(self):
        self.assertEqual(admit_lengths([0,1,1,1],[2,3,4],3,7,3),(2,3,4))
        with self.assertRaises(ValueError):admit_lengths([0,1,2,3],[2,3,4],3,7)
    def test_graph_dummy_zero_does_not_own_slot(self):
        self.assertEqual(admit_lengths([0,1,0,0],[0,0,0],3,5),(0,))
        self.assertEqual(admit_lengths([0,0,0,0],[0,0,0],3,5),())
    def test_reject_nonprefix_duplicate_and_oob(self):
        for seq,ids in (([0,0,1],[0,1]),([0,1,1],[2,2]),([0,1,0],[8,0]),
                        ([1,1,0],[2,0]),([0,1,0],[2,-1]),([0,True,0],[2,0])):
            with self.assertRaises(ValueError):admit_lengths(seq,ids,2,4)
    def test_aux_bytes(self):
        self.assertEqual(aux_bytes(1),119296*48)
        self.assertEqual(aux_bytes(455),2605424640)
        with self.assertRaises(ValueError):aux_bytes(1,1)
    def test_nd_and_device_are_distinct(self):
        specs=[dict(dtype="bf16",device="npu:0",contiguous=True,format=2,
                    ptr=1000,bytes=100,mutable=False),
               dict(dtype="fp32",device="npu:0",contiguous=True,format=2,
                    ptr=2000,bytes=100,mutable=True)]
        admission_specs(specs)
        for change in ({"format":29},{"device":"npu:1"},{"ptr":1050}):
            modified=[dict(s) for s in specs];modified[1].update(change)
            with self.assertRaises(ValueError):admission_specs(modified)
    def classes(self):
        class Donor:
            def forward(self):pass
            def _forward_core(self):pass
        class Target:pass
        Target.forward=Donor.forward
        Target._forward_core=Donor._forward_core
        return Donor,Target
    def test_receiver_alias_copy_bug_and_double_bind(self):
        d,t=self.classes()
        old=t._forward_core
        def wrapper(self):pass
        d._forward_core=wrapper
        self.assertIs(t._forward_core,old) # donor-only patch does not propagate
        with self.assertRaises(ValueError):verify_alias(d,t)
        d._forward_core=old
        self.assertIs(bind(d,t,wrapper),old)
        self.assertIs(t._forward_core,wrapper)
        self.assertIs(d._forward_core,wrapper)
        with self.assertRaises(ValueError):bind(d,t,wrapper)
    def test_all48_actual_instances(self):
        d,t=self.classes()
        def wrapper(self):pass
        bind(d,t,wrapper)
        mapping={}
        for layer in LAYERS:
            obj=t();obj.prefix="model.layers.%d.linear_attn"%layer
            mapping[obj.prefix]=obj
        self.assertEqual(len(live_bindings(mapping,d,t,wrapper)),48)
        mapping.pop(next(iter(mapping)))
        with self.assertRaises(ValueError):live_bindings(mapping,d,t,wrapper)
    def test_disabled_plugin_does_not_import_runtime(self):
        import os
        from unittest.mock import patch
        from kvbuffer_parallel.patch import register
        with patch.dict(os.environ,{},clear=True):
            register()
    def test_kernel_sole_change_parallel_logs(self):
        src=(ROOT/"operator/op_kernel/qwen36_gdn_kvbuffer_parallel.h").read_text()
        self.assertNotIn("for (uint32_t entry",src)
        self.assertNotIn("lambdaLogGm_.GetValue",src)
        self.assertIn("TreeFold(outerLeftUb_, outerRightUb_, 8*64)",src)
        dummy=src.index("const int32_t n = actualSeqLengthsGm_.GetValue(token+1)")
        state=src.index("const int32_t sv = stateIndicesGm_.GetValue(token)",dummy)
        self.assertLess(src.index("if (n <= 0)",dummy),state)
        self.assertIn("Exp(coeffUb_, coeffUb_, length)",src)
    def test_ub_ledger(self):
        used=3*128*4+3*32*4+2*16*4+2*32*128*4+32*4
        used+=2*16*128*4+2*16*32*4+2*16*8*64*4+16*64*4+16*8*4+6*32*4
        self.assertEqual(used,126336)
        queues=128*2+16*128*2+32*2+16*2+2*32*128*4+32*4+32*2+128*2
        self.assertEqual(queues,37664)
        # Public Broadcast temporary is disjoint and fits the existing reservation.
        self.assertEqual(used+4096,130432)
        self.assertLessEqual(used+4096,128*1024)
        self.assertLess(128*1024+queues,192*1024)
    def test_no_lazy_upload_decode_and_public_format(self):
        src=(ROOT/"operator/op_extension/qwen36_gdn_kvbuffer_parallel_torch.cpp").read_text()
        decode=src.split("at::Tensor qwen36_gdn_kvbuffer_parallel_decode(",1)[1]
        self.assertNotIn("aclrtMemcpy",decode)
        self.assertIn("cold geometry: call prepare outside capture",decode)
        self.assertIn("at_npu::native::custom_ops::get_npu_format",src)
        self.assertIn("getCurrentNPUStream().stream(false)",src)
    def probe_module(self):
        spec=importlib.util.spec_from_file_location("kvbp_probe_stdlib",ROOT/"tools/native_oracle_probe.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    def test_probe_metrics_cpu_first(self):
        import ast
        src=(ROOT/"tools/native_oracle_probe.py").read_text()
        tree=ast.parse(src)
        rel_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="rel")
        doubles=[n for n in ast.walk(rel_fn) if isinstance(n,ast.Call) and
                 isinstance(n.func,ast.Attribute) and n.func.attr=="double"]
        self.assertEqual(len(doubles),2)
        for node in doubles:
            self.assertIsInstance(node.func.value,ast.Call)
            self.assertEqual(node.func.value.func.attr,"cpu")
        self.assertNotIn(".double().cpu()",src)
    def test_probe_raw_saved_before_diagnostics(self):
        import ast
        src=(ROOT/"tools/native_oracle_probe.py").read_text()
        tree=ast.parse(src)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_case")
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
        raw=next(n for n in calls if isinstance(n.func,ast.Attribute) and
                 isinstance(n.func.value,ast.Name) and n.func.value.id=="torch" and n.func.attr=="save")
        diagnostic=[]
        for node in calls:
            if isinstance(node.func,ast.Name) and node.func.id in ("logical","rel","output_error","check_logs"):
                diagnostic.append(node)
            elif isinstance(node.func,ast.Attribute) and node.func.attr=="isfinite":
                diagnostic.append(node)
        self.assertTrue(diagnostic)
        self.assertTrue(all(raw.lineno<node.lineno for node in diagnostic))
        for field in ("before","after","native_before","native","inputs","input_before",
                      "actual","expected","guards_before","guards","pointers"):
            self.assertIn('"'+field+'":',src)
        fail=src.index("if not passed:")
        self.assertLess(fail,src.index("raw_path.unlink()",fail))
        self.assertIn('sha(raw_path)==raw_receipt["sha256"]',src)
        self.assertNotIn("glob(",src)
    def test_probe_nonfinite_json_preserves_failure(self):
        import json
        probe=self.probe_module()
        original={"status":"failed","finite":False,"metric_finite":False,
                  "output_error":math.nan,"state_error":math.inf,
                  "nested":[-math.inf,1.25],"raw_step":{"retained":True}}
        clean=probe.finite_json(original)
        self.assertEqual(json.loads(json.dumps(clean,allow_nan=False)),
            {"status":"failed","finite":False,"metric_finite":False,
             "output_error":None,"state_error":None,
             "nested":[None,1.25],"raw_step":{"retained":True}})
        self.assertTrue(math.isnan(original["output_error"]))
    def test_probe_nonfinite_aggregate_is_null(self):
        probe=self.probe_module()
        self.assertIsNone(probe.metric_max(0.,math.nan))
        self.assertIsNone(probe.metric_max(0.,math.inf))
        self.assertIsNone(probe.metric_max(None,0.01))
        self.assertEqual(probe.metric_max(0.01,0.02),0.02)
    def test_source_pins_and_no_success_claim(self):
        self.assertEqual(len(SOURCES),4)
        self.assertEqual(len(LAYERS),48)
        readme=(ROOT/"README.md").read_text()
        self.assertIn("BUILT + LOAD/META / NPU-UNVERIFIED",readme)
        self.assertIn("Meta negative validation is not implemented",readme)
        self.assertIn("physical_nd_proven=false and graph_proven=false",readme)
        self.assertIn("P2",readme)

if __name__=="__main__":unittest.main()
