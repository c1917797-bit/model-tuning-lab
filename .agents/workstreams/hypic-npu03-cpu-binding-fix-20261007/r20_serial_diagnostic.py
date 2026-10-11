#!/usr/bin/env python3
"""Three-sample, source-matched serial HYPIC diagnostic; not a quality pass."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

import r19_repaired_c32_longbench_adapter as r19

HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R20_SERIAL_DIAGNOSTIC_PREREGISTRATION_20261011.json"
ROOT_NAME = "hotpath-cache10r20-serial"
INDEXES = (59, 82, 126)


def preregistration() -> dict:
    contract = json.loads(PREREG.read_text(encoding="utf-8"))
    if (
        contract.get("schema") != "hypic-r20-serial-diagnostic-preregistration/v1"
        or contract.get("sample_indexes_in_order") != list(INDEXES)
        or contract.get("source_root") != r19.SOURCE_ROOT
        or contract.get("source_commit") != r19.SOURCE_COMMIT
        or contract.get("arms") != ["no-cache", "hypic-only"]
        or contract.get("physical_npus") != [0, 1, 2, 3]
        or contract.get("max_output_tokens") != 2048
        or contract.get("repetitions_per_sample") != 3
        or contract.get("sample_concurrency") != 1
        or contract.get("warm_requests_per_sample") != 2
    ):
        raise RuntimeError("r20 diagnostic preregistration drift")
    if contract.get("execution_state") != "frozen-offline-preflight-pending":
        raise RuntimeError("r20 frozen execution state drift")
    required_files = {
        "r20_serial_diagnostic.py",
        "r20_serial_diagnostic_audit.py",
        "test_r20_serial_diagnostic.py",
    }
    file_hashes = contract.get("file_sha256", {})
    if set(file_hashes) != required_files:
        raise RuntimeError("r20 controller/auditor/test hash set incomplete")
    for name, expected in file_hashes.items():
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"r20 frozen file drift: {name}")
    return contract


def configure(arm: str, prereg: dict):
    if arm not in prereg["arms"]:
        raise RuntimeError("r20 arm must be no-cache or hypic-only")
    r19.check_preregistration()
    r19.ROOT_NAME = ROOT_NAME
    controller = r19.configure(arm)
    quality = controller.quality
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"{ROOT_NAME}-{suffix}"
    if (
        quality.ATTEMPT != attempt
        or str(quality.QROOT) != prereg["arm_roots"][arm]
        or controller.REPETITIONS != 3
        or controller.MAX_OUTPUT != 2048
    ):
        raise RuntimeError("r20 controller attempt/cap drift")
    quality.EXPERIMENT = f"hypic-npu03-r20-serial-20261011-{suffix}"
    controller.CAMPAIGN = "cache10r20-serial"
    controller.CONCURRENCY = 1
    original_cases = controller.cases

    def selected_cases():
        all_cases, evaluator = original_cases()
        selected = [all_cases[index] for index in INDEXES]
        for item, frozen in zip(selected, prereg["sample_identity"]):
            if any(item.get(key) != frozen[key] for key in frozen):
                raise RuntimeError(f"r20 sample identity drift at {item['index']}")
        return selected, evaluator

    controller.cases = selected_cases
    return controller


def offline_check(arm: str, prereg: dict, controller) -> dict:
    quality = controller.quality
    if quality.QROOT.exists():
        raise RuntimeError("r20 immutable output root already exists")
    items, _ = controller.cases()
    fp = quality.preflight()
    if (
        len(items) != 3
        or fp["source_commit"] != prereg["source_commit"]
        or fp["plugin_source_root"] != prereg["source_root"]
        or fp["image"] != prereg["image"]
        or fp["model_index_sha256"] != prereg["model_index_sha256"]
        or fp["evaluator_sha256"] != prereg["evaluator_sha256"]
        or fp["datasets"]["longbenchv2"]["sha256"] != prereg["dataset_sha256"]
        or fp["physical_npus"] != prereg["physical_npus"]
        or fp["max_model_len"] != prereg["max_model_len"]
        or fp["max_output_tokens"] != prereg["max_output_tokens"]
        or fp["gpu_memory_utilization"] != prereg["gpu_memory_utilization"]
        or fp["material_cache_max_mb"] != prereg["material_cache_max_mb"]
        or fp["max_materialized_segments"] != prereg["max_materialized_segments"]
        or controller.CONCURRENCY != prereg["sample_concurrency"]
    ):
        raise RuntimeError("r20 offline environment or workload identity drift")
    spec = quality.spec(arm)
    if not spec or len(spec) != 4:
        raise RuntimeError("r20 service spec unavailable")
    return {
        "arm": arm,
        "root": str(quality.QROOT),
        "source_commit": fp["source_commit"],
        "sample_indexes": [item["index"] for item in items],
        "concurrency": controller.CONCURRENCY,
        "repetitions": controller.REPETITIONS,
        "max_output_tokens": controller.MAX_OUTPUT,
        "preregistration_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "device_run_started": False,
    }


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r20 requires --check or --run")
    prereg = preregistration()
    arm = os.environ.get("HYPIC_R20_ARM", "")
    controller = configure(arm, prereg)
    check = offline_check(arm, prereg, controller)
    if sys.argv[1:] == ["--check"]:
        print(json.dumps(check, sort_keys=True))
        return 0
    return controller.main()


if __name__ == "__main__":
    raise SystemExit(main())
