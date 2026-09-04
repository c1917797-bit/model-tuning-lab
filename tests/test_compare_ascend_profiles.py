#!/usr/bin/env python3

import json
import tempfile
from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "compare_ascend_profiles", ROOT / "scripts/compare_ascend_profiles.py"
)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def report(source_hash, category_us, kernel_us):
    return {
        "schema": "qwen35-ascend-profile-hotspots/v1",
        "measurement_semantics": {"not_wall_time": True},
        "files": [{"sha256": source_hash}],
        "summary": {
            "total_kernel_duration_us": category_us,
            "kernel_calls": 2,
            "categories": [
                {"name": "gdn_prefill", "calls": 2, "duration_us": category_us}
            ],
            "top_kernels": [
                {"name": "ChunkGatedDeltaRule", "calls": 2, "duration_us": kernel_us}
            ],
        },
    }


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    baseline_path = root / "baseline.json"
    candidate_path = root / "candidate.json"
    baseline_path.write_text(json.dumps(report("a" * 64, 100.0, 80.0)))
    candidate_path.write_text(json.dumps(report("b" * 64, 60.0, 48.0)))
    result = MODULE.compare(baseline_path, candidate_path, 10)
    assert result["diagnostic_only"] is True
    assert result["acceptance_evidence"] is False
    assert result["diagnostic_total_duration_ratio"] == 0.6
    assert result["categories"][0]["duration_delta_us"] == -40.0
    assert result["top_kernel_deltas"][0]["duration_ratio"] == 0.6

    candidate_path.write_text(json.dumps(report("a" * 64, 60.0, 48.0)))
    try:
        MODULE.compare(baseline_path, candidate_path, 10)
    except ValueError as error:
        assert "identical profile inputs" in str(error)
    else:
        raise AssertionError("identical profile inputs were accepted")

print("PASS: compare_ascend_profiles")
