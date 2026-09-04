#!/usr/bin/env python3

from importlib.util import module_from_spec, spec_from_file_location
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "run_qwen35_candidate_quick32",
    ROOT / "scripts/run_qwen35_candidate_quick32.py",
)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

with tempfile.TemporaryDirectory() as directory:
    artifact = Path(directory) / "c5-r1.json"
    payload = {
        "schema": "qwen35-query-rewrite-benchmark/v1",
        "concurrency": 5,
        "repeat_index": 1,
        "dataset_sha256": MODULE.DATASET_SHA256,
        "model": MODULE.MODEL,
        "seed": 1024,
        "requests": 32,
        "completed": 32,
        "errors": 0,
        "natural_eos": True,
        "finish_reasons": {"stop": 32},
        "max_tokens": "per-request model context remainder",
        "response_sha256": ["a" * 64] * 32,
    }
    artifact.write_text(json.dumps(payload))
    validated = MODULE.validate_cell(artifact, 5)
    assert validated["completed"] == 32
    payload["requests"] = 31
    artifact.write_text(json.dumps(payload))
    try:
        MODULE.validate_cell(artifact, 5)
    except ValueError as error:
        assert "requests must be 32" in str(error)
    else:
        raise AssertionError("non-quick32 candidate was accepted")

print("PASS: candidate quick32 validation")
