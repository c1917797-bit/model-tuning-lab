#!/usr/bin/env python3

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/qwen35_query_rewrite_bench.py"
spec = importlib.util.spec_from_file_location("qwen35_bench", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.normalize_reference_text("  a\n b\t") == "a b"
summary = module.summarize([0.0, 0.5, 1.0])
assert summary["p50"] == 0.5
assert summary["min"] == 0.0
assert summary["max"] == 1.0

print("PASS: query_rewrite semantic metric helpers")
