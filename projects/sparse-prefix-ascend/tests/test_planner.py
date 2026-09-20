import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path

from sparse_prefix_ascend.planner import (
    PlacementPlan,
    balanced_plan,
    overlap_histogram,
    solve_distribution_aware,
)
from sparse_prefix_ascend.runtime import _load_plan
import sparse_prefix_ascend.runtime as runtime


class PlannerTests(unittest.TestCase):
    def test_distribution_plan_is_deterministic_aligned_and_budgeted(self):
        hist = overlap_histogram(
            [0, 128, 128, 512, 512, 512, 1024, 2048],
            max_length=2048,
            block_size=128,
            decay=0.99,
        )
        first = solve_distribution_aware(
            hist, checkpoint_budget=4, block_size=128
        )
        second = solve_distribution_aware(
            hist, checkpoint_budget=4, block_size=128
        )
        self.assertEqual(first, second)
        self.assertLessEqual(len(first.positions), 4)
        self.assertTrue(all(position % 128 == 0 for position in first.positions))

    def test_balanced_control_uses_same_budget(self):
        plan = balanced_plan(
            max_length=4096, checkpoint_budget=4, block_size=128
        )
        self.assertEqual(len(plan.positions), 4)
        plan.validate()

    def test_plan_rejects_unaligned_position(self):
        with self.assertRaises(ValueError):
            PlacementPlan((130,), 1, 128, 1024).validate()

    def test_runtime_plan_is_fail_closed(self):
        payload = {
            "schema": "sparse-prefix-placement/v1",
            "positions": [128, 512],
            "checkpoint_budget": 2,
            "block_size": 128,
            "max_length": 1024,
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(_load_plan(str(path)).positions, (128, 512))

    def test_runtime_wraps_only_checkpoint_placement(self):
        payload = {
            "schema": "sparse-prefix-placement/v1",
            "positions": [128, 512],
            "checkpoint_budget": 2,
            "block_size": 128,
            "max_length": 1024,
        }
        scheduler = types.ModuleType("hypic_vllm_ascend.patches.scheduler")

        def original(request, token_ids, config, *, block_size, segments=None):
            return (1024,)

        scheduler._candidate_prefix_ends_for_request = original
        patches = types.ModuleType("hypic_vllm_ascend.patches")
        patches.scheduler = scheduler
        package = types.ModuleType("hypic_vllm_ascend")
        package.patches = patches
        saved_modules = {
            name: sys.modules.get(name)
            for name in (
                "hypic_vllm_ascend",
                "hypic_vllm_ascend.patches",
                "hypic_vllm_ascend.patches.scheduler",
            )
        }
        old_env = {
            key: os.environ.get(key)
            for key in (
                "VLLM_ASCEND_HYPIC_ENABLE",
                "VLLM_ASCEND_SPARSE_PREFIX_ENABLE",
                "VLLM_ASCEND_SPARSE_PREFIX_PLAN",
            )
        }
        try:
            sys.modules["hypic_vllm_ascend"] = package
            sys.modules["hypic_vllm_ascend.patches"] = patches
            sys.modules["hypic_vllm_ascend.patches.scheduler"] = scheduler
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "plan.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                os.environ["VLLM_ASCEND_HYPIC_ENABLE"] = "1"
                os.environ["VLLM_ASCEND_SPARSE_PREFIX_ENABLE"] = "1"
                os.environ["VLLM_ASCEND_SPARSE_PREFIX_PLAN"] = str(path)
                runtime._INSTALLED = False
                runtime.register()
                config = types.SimpleNamespace(min_rewrite_tokens=1)
                selected = scheduler._candidate_prefix_ends_for_request(
                    object(),
                    tuple(range(1025)),
                    config,
                    block_size=128,
                )
                self.assertEqual(selected, (512, 128))
                with self.assertRaises(RuntimeError):
                    scheduler._candidate_prefix_ends_for_request(
                        object(),
                        tuple(range(1025)),
                        config,
                        block_size=256,
                    )
        finally:
            runtime._INSTALLED = False
            for name, module in saved_modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
