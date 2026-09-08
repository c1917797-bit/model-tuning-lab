#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = spec_from_file_location(
    "run_qwen35_benchmark_matrix",
    ROOT / "scripts/run_qwen35_benchmark_matrix.py",
)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

runtime = MODULE.render(ROOT / "configs/qwen35-query-rewrite-baseline.yaml")
cells = MODULE.plan(runtime, Path("/immutable/run"))
assert len(cells) == 12
assert [(cell["concurrency"], cell["repetition"]) for cell in cells] == [
    (1, 1), (1, 2), (1, 3),
    (5, 1), (5, 2), (5, 3),
    (8, 1), (8, 2), (8, 3),
    (16, 1), (16, 2), (16, 3),
]
assert len({cell["output"] for cell in cells}) == 12

with tempfile.TemporaryDirectory() as directory:
    artifact = Path(directory) / "cell.json"
    payload = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": 5,
        "repeat_index": 2,
        "dataset_sha256": "a" * 64,
        "model": "model",
        "errors": 0,
        "natural_eos": True,
        "requests": 2,
        "completed": 2,
        "finish_reasons": {"stop": 2},
        "cache_salt_prefix": "control-run",
        "prefix_cache_isolation": True,
        "response_sha256": ["b" * 64, "c" * 64],
    }
    artifact.write_text(json.dumps(payload))
    validated = MODULE.validate_cell(
        artifact,
        concurrency=5,
        repetition=2,
        dataset_sha256="a" * 64,
        model="model",
        requests=2,
        cache_salt_prefix="control-run",
    )
    assert validated["completed"] == 2
    payload["errors"] = 1
    artifact.write_text(json.dumps(payload))
    try:
        MODULE.validate_cell(
            artifact,
            concurrency=5,
            repetition=2,
            dataset_sha256="a" * 64,
            model="model",
            requests=2,
            cache_salt_prefix="control-run",
        )
    except ValueError as error:
        assert "errors must be 0" in str(error)
    else:
        raise AssertionError("invalid cell was accepted")

print("PASS: run_qwen35_benchmark_matrix plan")
