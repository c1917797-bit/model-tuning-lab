#!/usr/bin/env python3
"""Stdlib-only software-contract checks. NO torch, Docker, build, NPU or Git."""
import ast
import copy
from pathlib import Path
import time
from types import SimpleNamespace
import unittest

from general_sr_contract import (ANCHOR_VARIANTS, GENERAL_VARIANTS, LIMITS,
                                 NATIVE_COMMIT, NATIVE_HEADER_SHA, STEPS,
                                 PREPARE_INPUT_NAMES,
                                 assert_matrix_order, validate_device_proof,
                                 validate_source_manifest)

HERE = Path(__file__).resolve().parent


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.now = time.time_ns()
        self.proof = {"physical_npu_ids": [4], "logical_to_physical": {"0": 4},
                      "privileged": False, "exclusive_resource_check_passed": True,
                      "observed_at_unix_ns": self.now}
        self.references, self.candidates = {"ref.h": "a"*64}, {"kernel.h": "b"*64}
        self.manifest = {"native_commit": NATIVE_COMMIT, "native_header_sha256": NATIVE_HEADER_SHA,
            "reference_source_hashes": self.references, "candidate_source_hashes": self.candidates,
            "image_id": "sha256:"+"c"*64, "native_runtime_library_path": "/audited/native.so",
            "native_runtime_library_sha256": "d"*64, "source_contract_passed": True}
        self.anchors = [{"stage": "anchor", "batch": b, "variant": v, "status": "passed"}
                        for b in (1, 16) for v in ANCHOR_VARIANTS]

    def test_limits_frozen(self):
        self.assertEqual(STEPS, 160)
        self.assertEqual(LIMITS, {"state": 1e-5, "output": 0.00303})

    def test_device_proof_valid(self):
        self.assertTrue(validate_device_proof(self.proof, self.now))

    def test_device_proof_failclosed(self):
        cases = [("physical_npu_ids", [0, 4]), ("physical_npu_ids", [4, 4]),
                 ("logical_to_physical", {"0": 5}), ("privileged", True),
                 ("exclusive_resource_check_passed", False),
                 ("observed_at_unix_ns", self.now+1),
                 ("observed_at_unix_ns", self.now-1800*10**9-1)]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                proof = copy.deepcopy(self.proof); proof[key] = value
                with self.assertRaises(ValueError):
                    validate_device_proof(proof, self.now)

    def test_source_provenance(self):
        self.assertTrue(validate_source_manifest(self.manifest, self.references, self.candidates))
        for key in self.manifest:
            with self.subTest(missing=key):
                changed = copy.deepcopy(self.manifest); changed.pop(key)
                with self.assertRaises(ValueError):
                    validate_source_manifest(changed, self.references, self.candidates)

    def test_all_anchors_before_general(self):
        self.assertTrue(assert_matrix_order(self.anchors, True))
        general = {"stage": "general", "batch": 1, "variant": GENERAL_VARIANTS[0], "status": "running"}
        self.assertTrue(assert_matrix_order(self.anchors+[general], True))
        for cases in ([general], self.anchors[:-1]+[general],
                      self.anchors+[general, self.anchors[0]], self.anchors+[self.anchors[0]]):
            with self.subTest(cases=cases):
                with self.assertRaises(ValueError):
                    assert_matrix_order(cases, True)
        failed = copy.deepcopy(self.anchors); failed[1]["status"] = "failed"
        with self.assertRaises(ValueError):
            assert_matrix_order(failed+[general], True)

    def test_real_native_call_keyword_boundary(self):
        tree = ast.parse((HERE/"general_sr_native_gate.py").read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
                 isinstance(node.func, ast.Name) and node.func.id == "native"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0].args), 4)
        self.assertEqual([kw.arg for kw in calls[0].keywords], [
            "beta", "scale", "actual_seq_lengths", "ssm_state_indices",
            "num_accepted_tokens", "g", "gk"])

    def test_no_candidate_or_trace_or_CPU_recurrence_golden(self):
        source = (HERE/"general_sr_native_gate.py").read_text()
        tree = ast.parse(source)
        imported = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertNotIn("native_compressed_golden", imported)
        for forbidden in ("compressed_step", "uncompressed_step", "qwen36_damp_trace",
                          "load_candidate", "torch.mv(", "torch.matmul("):
            self.assertNotIn(forbidden, source)
        self.assertIn("q.repeat_interleave(3, 1)", source)
        self.assertIn("k.repeat_interleave(3, 1)", source)
        self.assertIn("state_selected", source)
        self.assertIn("calibrated_plan_count", source)

    def prepare_guard_fixture(self):
        """Execute only the guard AST with fake tensors; no torch import."""
        tree = ast.parse((HERE/"general_sr_native_gate.py").read_text())
        function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and
                        x.name == "invoke_prepare_guard")
        sync = []
        env = {"PREPARE_INPUT_NAMES": PREPARE_INPUT_NAMES,
               "REGIONS": ("high", "low", "scales"),
               "torch": SimpleNamespace(npu=SimpleNamespace(synchronize=lambda: sync.append(True))),
               "exact": lambda x, y: x.value == y.value}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<guard-stdlib-test>", "exec"), env)
        class FakeTensor:
            def __init__(self, value, pointer):
                self.value, self.pointer = value, pointer
            def cpu(self):
                return self
            def clone(self):
                return FakeTensor(self.value, self.pointer)
            def data_ptr(self):
                return self.pointer
        class FakeGate:
            def __init__(self):
                self.fixture, self.checks = {}, []
            def require(self, name, passed, details):
                self.checks.append((name, passed, details))
                if not passed:
                    raise AssertionError(name)
        inputs = [FakeTensor(i, 100+i) for i in range(6)]
        arena = [inputs[1], FakeTensor(6, 106), FakeTensor(7, 107)]
        return env["invoke_prepare_guard"], FakeGate(), inputs, arena, sync

    def test_prepare_guard_checks_every_input_and_buffer(self):
        invoke, gate, inputs, arena, sync = self.prepare_guard_fixture()
        invoke(gate, lambda *args: None, inputs, arena)
        self.assertEqual(len(sync), 1)
        self.assertEqual(set(gate.fixture["prepare_inputs_before"]), set(PREPARE_INPUT_NAMES))
        self.assertEqual(set(gate.fixture["prepare_inputs_after"]), set(PREPARE_INPUT_NAMES))
        self.assertTrue(all(gate.checks[0][2]["guards"].values()))
        for target in range(8):
            with self.subTest(mutated=target):
                invoke, gate, inputs, arena, sync = self.prepare_guard_fixture()
                obj = inputs[target] if target < 6 else arena[target-5]
                def corrupt(*args):
                    obj.value += 1
                with self.assertRaises(AssertionError):
                    invoke(gate, corrupt, inputs, arena)
                self.assertEqual(len(sync), 1)
                self.assertIn("prepare_inputs_after", gate.fixture)

    def test_prepare_guard_rejects_pointer_or_return_changes(self):
        for target in range(8):
            with self.subTest(pointer=target):
                invoke, gate, inputs, arena, _ = self.prepare_guard_fixture()
                obj = inputs[target] if target < 6 else arena[target-5]
                def corrupt(*args):
                    obj.pointer += 1
                with self.assertRaises(AssertionError):
                    invoke(gate, corrupt, inputs, arena)
        invoke, gate, inputs, arena, _ = self.prepare_guard_fixture()
        with self.assertRaises(AssertionError):
            invoke(gate, lambda *args: "unexpected-output", inputs, arena)

    def test_prepare_exception_retains_before_snapshots(self):
        invoke, gate, inputs, arena, sync = self.prepare_guard_fixture()
        def rejected(*args):
            raise RuntimeError("explicit prepare rejection")
        with self.assertRaisesRegex(RuntimeError, "explicit prepare rejection"):
            invoke(gate, rejected, inputs, arena)
        self.assertEqual(set(gate.fixture["prepare_inputs_before"]), set(PREPARE_INPUT_NAMES))
        self.assertEqual(set(gate.fixture["prepare_arena_before"]), {"high", "low", "scales"})
        self.assertEqual(sync, [])

    def test_reference_source_pin_values_match_real_files(self):
        tree = ast.parse((HERE/"general_sr_native_gate.py").read_text())
        pins = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in ("REFERENCE_HASHES", "CANDIDATE_HASHES"):
                    pins[node.targets[0].id] = ast.literal_eval(node.value)
        import hashlib
        project = HERE.parent
        for filename, expected in pins["REFERENCE_HASHES"].items():
            data = (project/"operator/reference"/filename).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, filename)
        for filename, expected in pins["CANDIDATE_HASHES"].items():
            data = (project/"operator"/filename).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, filename)

    def reference_guard_fixture(self):
        """Run only guard functions with fake tensors; never import torch."""
        tree = ast.parse((HERE/"general_sr_native_gate.py").read_text())
        functions = [x for x in tree.body if isinstance(x, ast.FunctionDef) and
                     x.name in ("storage_disjoint", "invoke_reference")]
        class FakeTensor:
            def __init__(self, pointer, shape=(1,), dtype="float32", finite=True, fmt=2):
                self.pointer, self.shape, self.dtype = pointer, shape, dtype
                self.device, self.finite, self.fmt = "npu:0", finite, fmt
            def cpu(self):
                return self
            def clone(self):
                return FakeTensor(self.pointer, self.shape, self.dtype, self.finite, self.fmt)
            def data_ptr(self):
                return self.pointer
            def numel(self):
                import math
                return math.prod(self.shape)
            def element_size(self):
                return 2 if self.dtype == "bfloat16" else 4
            def bfloat16(self):
                return FakeTensor(self.pointer, self.shape, "bfloat16", self.finite, self.fmt)
        def clone(value):
            if isinstance(value, FakeTensor):
                return value.clone()
            if isinstance(value, (list, tuple)):
                return [clone(x) for x in value]
            return value
        env = {"torch": SimpleNamespace(
            npu=SimpleNamespace(synchronize=lambda: None), float32="float32",
            bfloat16="bfloat16", isfinite=lambda x: SimpleNamespace(all=lambda: x.finite)),
            "cpu_clone": clone, "exact": lambda a,b: a.shape == b.shape and a.dtype == b.dtype}
        exec(compile(ast.Module(body=functions, type_ignores=[]),
                     "<reference-guard-stdlib-test>", "exec"), env)
        inputs = [FakeTensor(1000+i*10000) for i in range(5)]
        selected = FakeTensor(2000000, (1,12,128,128))
        plans = [FakeTensor(3000000+i*10000) for i in range(3)]
        sr = FakeTensor(4000000)
        outputs = [FakeTensor(100000,(1,12,128,128)),
                   FakeTensor(1000000,(1,12,128)),
                   FakeTensor(1100000,(1,12,128),"bfloat16")]
        gate = SimpleNamespace(fixture={})
        return env, FakeTensor, gate, inputs, selected, plans, sr, outputs

    def test_reference_raw_after_retained_before_rejection(self):
        import sys
        from unittest.mock import patch
        for failure in ("nonfinite", "format", "input_alias", "output_alias", "pointer"):
            with self.subTest(failure=failure):
                env, _, gate, inputs, selected, plans, sr, outputs = self.reference_guard_fixture()
                def ref(*args):
                    if failure == "nonfinite":
                        outputs[0].finite = False
                    elif failure == "format":
                        outputs[0].fmt = 0
                    elif failure == "input_alias":
                        outputs[0].pointer = inputs[0].pointer+4
                    elif failure == "output_alias":
                        outputs[1].pointer = outputs[0].pointer+4
                    else:
                        inputs[0].pointer += 32
                    return outputs
                with patch.dict(sys.modules, {"torch_npu": SimpleNamespace(get_npu_format=lambda x: x.fmt)}):
                    with self.assertRaises(RuntimeError):
                        env["invoke_reference"](gate, ref, inputs, selected, plans, sr, lambda x:x)
                self.assertEqual(len(gate.fixture["reference_raw_outputs"]), 3)
                self.assertEqual(len(gate.fixture["reference_inputs_after"]), 10)
                self.assertIn("reference_input_pointers_after", gate.fixture)

    def test_complete_byte_interval_overlap_guard(self):
        env, FakeTensor, *_ = self.reference_guard_fixture()
        a = FakeTensor(1000,(16,))
        self.assertFalse(env["storage_disjoint"](a, FakeTensor(1004,(4,))))
        self.assertTrue(env["storage_disjoint"](a, FakeTensor(1064,(4,))))

    def test_candidate_raw_after_precedes_unpack_assertions(self):
        tree = ast.parse((HERE/"general_sr_native_gate.py").read_text())
        general = next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="general_case")
        updates = [x for x in ast.walk(general) if isinstance(x,ast.Call) and
                   isinstance(x.func,ast.Attribute) and x.func.attr=="update" and
                   {"candidate_after","candidate_output"}.issubset({k.arg for k in x.keywords})]
        unpack = [x for x in ast.walk(general) if isinstance(x,ast.Call) and
                  isinstance(x.func,ast.Name) and x.func.id=="unpack_value_major" and
                  isinstance(x.args[0],ast.Name) and x.args[0].id=="actual"]
        self.assertTrue(updates and unpack)
        self.assertLess(min(x.lineno for x in updates), min(x.lineno for x in unpack))

    def test_anchor_only_does_not_dispatch_known_failed_candidate(self):
        source = (HERE/"general_sr_native_gate.py").read_text()
        branch = source.index("if args.anchor_only:")
        stop = source.index("return", branch)
        dispatched = source.index('report["compressed_candidate_dispatched"] = True', branch)
        self.assertLess(stop, dispatched)
        self.assertIn('"compressed_candidate_dispatched": False', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
