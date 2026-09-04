#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "render_qwen35_runtime", ROOT / "scripts/render_qwen35_runtime.py"
)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

result = MODULE.render(ROOT / "configs/qwen35-query-rewrite-baseline.yaml")
argv = result["argv"]
assert result["schema"] == "qwen35-query-rewrite-runtime-manifest/v1"
assert argv[argv.index("--data-parallel-size") + 1] == "2"
assert argv[argv.index("--tensor-parallel-size") + 1] == "4"
assert "--async-scheduling" in argv
assert "--enable-prefix-caching" in argv
assert result["environment"]["ASCEND_RT_VISIBLE_DEVICES"] == "0,1,2,3,4,5,6,7"
assert result["benchmark"]["concurrency"] == [1, 5, 8, 16]
assert result["benchmark"]["repetitions"] == 3
assert result["benchmark"]["target_ttft_ratio"] == 0.5
assert result["benchmark"]["target_tpot_ratio"] == 0.5
assert len(result["runtime_sha256"]) == 64

print("PASS: render_qwen35_runtime")
