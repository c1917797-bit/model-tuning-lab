#!/usr/bin/env python3
"""Read-only, fail-closed readiness check for the current G1-G4 piercing run."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_NPUS = [0, 1, 2, 3]
EXPECTED_CPU_SET = "112-191"
EXPECTED_IMAGE_DIGEST = (
    "sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a"
)
EXPECTED_DATASETS = {"NIAH+", "LongBench v2", "GSM8K", "CEval"}
AUTHORIZATION = "I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT"
FORBIDDEN_PROBES = ("speed-oracle", "gdn-dk64-l1")
CAPTURE_ENVIRONMENT = (
    "VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE",
    "VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR",
    "VLLM_ASCEND_GDN_RRQR_MAX_TOKENS",
    "VLLM_ASCEND_GDN_RRQR_MAX_CAPTURES_PER_LAYER",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def unresolved(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(unresolved(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(unresolved(child, f"{path}[{index}]"))
    elif isinstance(value, str) and "REQUIRED" in value:
        errors.append(f"{path} contains unresolved placeholder: {value}")
    return errors


def load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"{label} missing: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def container_state(name: str, errors: list[str]) -> str | None:
    result = subprocess.run(
        ["docker", "inspect", name, "--format", "{{.State.Status}}"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        errors.append(f"cannot inspect baseline container {name}: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def verify_treatments(
    matrix_path: Path, verifier: Path, errors: list[str]
) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(verifier), "--matrix", str(matrix_path)],
        check=False,
        text=True,
        capture_output=True,
    )
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        errors.append(
            "treatment verifier did not emit JSON: "
            + (result.stderr.strip() or result.stdout.strip())
        )
        return {}
    if result.returncode != 0 or report.get("valid") is not True:
        errors.append(
            "treatment matrix verification failed: "
            + "; ".join(str(item) for item in report.get("errors", []))
        )
    return report


def parse_checkpoint_specs(specs: list[str], errors: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            errors.append(f"DRRQR checkpoint must use MODEL_ID=/absolute/path: {spec}")
            continue
        model_id, raw_path = spec.split("=", 1)
        if not model_id or not raw_path:
            errors.append(f"invalid DRRQR checkpoint mapping: {spec}")
            continue
        if model_id in parsed:
            errors.append(f"duplicate DRRQR checkpoint mapping: {model_id}")
            continue
        parsed[model_id] = Path(raw_path)
    return parsed


def verify_drrqr(
    model: dict[str, Any], checkpoint: Path, errors: list[str]
) -> None:
    model_id = str(model.get("id"))
    checkpoint_text = str(checkpoint)
    if any(marker in checkpoint_text for marker in FORBIDDEN_PROBES):
        errors.append(f"{model_id}: speed-oracle/L1 checkpoint is forbidden as DRRQR")
    manifest_path = checkpoint / "drrqr_manifest.json"
    manifest = load_json(manifest_path, f"{model_id} DRRQR manifest", errors)
    if manifest.get("schema") != "paper-to-ascend-drrqr-checkpoint/v1":
        errors.append(f"{model_id}: DRRQR manifest schema mismatch")
    if manifest.get("method") != "DRRQR":
        errors.append(f"{model_id}: checkpoint method must be exactly DRRQR")
    if manifest.get("model_id") != model_id:
        errors.append(f"{model_id}: DRRQR manifest model_id mismatch")
    config_path = Path(str(model.get("path", ""))) / "config.json"
    if not config_path.is_file():
        errors.append(f"{model_id}: source config missing: {config_path}")
    elif manifest.get("source_config_sha256") != sha256(config_path):
        errors.append(f"{model_id}: DRRQR manifest source config hash mismatch")
    for path_field, hash_field, label in (
        ("selection_evidence_path", "selection_evidence_sha256", "selection evidence"),
        ("calibration_dataset_path", "calibration_dataset_sha256", "calibration dataset"),
    ):
        evidence_path = Path(str(manifest.get(path_field, "")))
        expected_hash = manifest.get(hash_field)
        if not evidence_path.is_file() or evidence_path.stat().st_size <= 0:
            errors.append(f"{model_id}: {label} missing or empty: {evidence_path}")
        elif expected_hash != sha256(evidence_path):
            errors.append(f"{model_id}: {label} SHA256 mismatch")

    checkpoint_config = checkpoint / "config.json"
    checkpoint_index = checkpoint / "model.safetensors.index.json"
    if not checkpoint_config.is_file():
        errors.append(f"{model_id}: checkpoint config missing: {checkpoint_config}")
    elif manifest.get("checkpoint_config_sha256") != sha256(checkpoint_config):
        errors.append(f"{model_id}: checkpoint config SHA256 mismatch")
    index = load_json(checkpoint_index, f"{model_id} checkpoint index", errors)
    if checkpoint_index.is_file() and manifest.get("checkpoint_index_sha256") != sha256(
        checkpoint_index
    ):
        errors.append(f"{model_id}: checkpoint index SHA256 mismatch")
    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        errors.append(f"{model_id}: checkpoint weight_map is missing or empty")
    else:
        for shard in sorted({str(value) for value in weight_map.values()}):
            shard_path = checkpoint / shard
            if not shard_path.is_file() or shard_path.stat().st_size <= 0:
                errors.append(f"{model_id}: checkpoint shard missing or empty: {shard_path}")

    if manifest.get("changed_layers") != model.get("linear_attention_layers"):
        errors.append(
            f"{model_id}: changed_layers must equal all GDN layers "
            f"({model.get('linear_attention_layers')})"
        )
    if not isinstance(manifest.get("changed_tensor_count"), int) or manifest.get(
        "changed_tensor_count", 0
    ) <= 0:
        errors.append(f"{model_id}: changed_tensor_count must be a positive integer")
    if manifest.get("target_head_k_dim") != 64:
        errors.append(f"{model_id}: target_head_k_dim must be 64")
    if manifest.get("converter_version") in (None, "", "REQUIRED"):
        errors.append(f"{model_id}: converter_version is unresolved")


def verify_frozen_inputs(
    frozen: dict[str, Any], runtime_path: Path, runtime: dict[str, Any], errors: list[str]
) -> None:
    if frozen.get("schema") != "paper-to-ascend-frozen-inputs/v1":
        errors.append("frozen inputs schema mismatch")
    if frozen.get("freeze_complete") is not True:
        errors.append("frozen inputs are not marked complete")
    if runtime_path.is_file():
        if frozen.get("runtime_config_sha256") != sha256(runtime_path):
            errors.append("frozen runtime config file hash differs from current runtime config")
        if frozen.get("runtime_config_canonical_sha256") != canonical_sha256(runtime):
            errors.append("frozen runtime config canonical hash differs from current config")
    rows = frozen.get("datasets")
    if not isinstance(rows, list):
        errors.append("frozen datasets must be a list")
        return
    observed: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("each frozen dataset row must be an object")
            continue
        name = str(row.get("name"))
        if name in observed:
            errors.append(f"duplicate frozen dataset: {name}")
        observed.add(name)
        path = Path(str(row.get("path", "")))
        if not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"frozen dataset missing or empty: {name}={path}")
            continue
        if row.get("size_bytes") != path.stat().st_size:
            errors.append(f"frozen dataset size changed: {name}")
        if row.get("sha256") != sha256(path):
            errors.append(f"frozen dataset SHA256 changed: {name}")
    if observed != EXPECTED_DATASETS:
        errors.append(
            f"frozen dataset names must be exactly {sorted(EXPECTED_DATASETS)}; "
            f"observed={sorted(observed)}"
        )


def verify_capture_disabled(runtime: dict[str, Any], errors: list[str]) -> None:
    benchmark_environment = runtime.get("benchmark_environment")
    if not isinstance(benchmark_environment, dict):
        errors.append("runtime benchmark_environment must be an object")
        return
    for name in CAPTURE_ENVIRONMENT:
        if name not in benchmark_environment:
            errors.append(f"runtime benchmark_environment must explicitly disable {name}")
        elif benchmark_environment[name] not in (None, "", False):
            errors.append(f"runtime benchmark environment arms capture: {name}")
        if os.environ.get(name) not in (None, ""):
            errors.append(f"preflight process environment still contains capture variable: {name}")


def verify_measurement_protocol(runtime: dict[str, Any], errors: list[str]) -> None:
    performance = runtime.get("performance_sampling")
    quality = runtime.get("quality_generation")
    lifecycle = runtime.get("phase_lifecycle")
    if not isinstance(performance, dict):
        errors.append("runtime performance_sampling must be an object")
    else:
        if performance.get("temperature") != 0 or performance.get("seed") != 0:
            errors.append("performance sampling must be deterministic (seed=0, temperature=0)")
        if performance.get("ignore_eos") is not True:
            errors.append("performance sampling must use ignore_eos=true for fixed output load")
    if not isinstance(quality, dict):
        errors.append("runtime quality_generation must be an object")
    else:
        expected_quality = {
            "seed": 0,
            "temperature": 0,
            "ignore_eos": False,
            "enable_thinking": False,
            "trust_remote_code": False,
            "prediction_postprocessor": "extract_non_reasoning_content",
        }
        for name, expected in expected_quality.items():
            if quality.get(name) != expected:
                errors.append(f"quality_generation.{name} must equal {expected!r}")
    if not isinstance(lifecycle, dict):
        errors.append("runtime phase_lifecycle must be an object")
    else:
        for name in (
            "health_200_before_each_phase",
            "restart_same_group_between_performance_and_quality",
        ):
            if lifecycle.get(name) is not True:
                errors.append(f"phase_lifecycle.{name} must be true")
        for name in ("performance_repetitions", "quality_repetitions"):
            if lifecycle.get(name) != 3:
                errors.append(f"phase_lifecycle.{name} must equal 3")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-config", required=True, type=Path)
    parser.add_argument("--frozen-inputs", required=True, type=Path)
    parser.add_argument("--treatment-matrix", required=True, type=Path)
    parser.add_argument(
        "--drrqr-checkpoint",
        required=True,
        action="append",
        help="Repeat as MODEL_ID=/absolute/checkpoint/path for every matrix model.",
    )
    parser.add_argument("--baseline-container", default="qwen38_paper_baseline_npu0_3")
    parser.add_argument("--replacement-authorization", default="")
    args = parser.parse_args()

    errors: list[str] = []
    runtime = load_json(args.runtime_config, "runtime config", errors)
    frozen = load_json(args.frozen_inputs, "frozen inputs", errors)
    errors.extend(unresolved(runtime, "runtime"))
    errors.extend(unresolved(frozen, "frozen"))
    verify_frozen_inputs(frozen, args.runtime_config, runtime, errors)

    if runtime.get("host_npus") != EXPECTED_NPUS:
        errors.append(f"host_npus must be exactly {EXPECTED_NPUS}")
    if runtime.get("cpu_set") != EXPECTED_CPU_SET:
        errors.append(f"cpu_set must be exactly {EXPECTED_CPU_SET}")
    if runtime.get("container_image_digest") != EXPECTED_IMAGE_DIGEST:
        errors.append("container image digest differs from the verified baseline")
    if runtime.get("tensor_parallel_size") != 4:
        errors.append("tensor_parallel_size must remain 4")
    verify_capture_disabled(runtime, errors)
    verify_measurement_protocol(runtime, errors)

    here = Path(__file__).resolve().parent
    treatment_report = verify_treatments(
        args.treatment_matrix, here / "verify_treatment_matrix.py", errors
    )
    models = treatment_report.get("models", [])
    checkpoints = parse_checkpoint_specs(args.drrqr_checkpoint, errors)
    expected_ids = {str(model.get("id")) for model in models if isinstance(model, dict)}
    if set(checkpoints) != expected_ids:
        errors.append(
            f"DRRQR checkpoint ids must exactly match matrix models: "
            f"expected={sorted(expected_ids)}, observed={sorted(checkpoints)}"
        )
    for model in models:
        if isinstance(model, dict) and str(model.get("id")) in checkpoints:
            verify_drrqr(model, checkpoints[str(model.get("id"))], errors)

    state = container_state(args.baseline_container, errors)
    if state == "running" and args.replacement_authorization != AUTHORIZATION:
        errors.append(
            "NPU0-3 baseline is running; explicit replacement authorization was not supplied"
        )

    report = {
        "schema": "paper-to-ascend-preflight/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "ready": not errors,
        "read_only": True,
        "baseline_container": args.baseline_container,
        "baseline_state": state,
        "runtime_config_sha256": sha256(args.runtime_config) if args.runtime_config.is_file() else None,
        "frozen_inputs_sha256": sha256(args.frozen_inputs) if args.frozen_inputs.is_file() else None,
        "treatment_matrix_sha256": treatment_report.get("matrix_sha256"),
        "drrqr_checkpoint_ids": sorted(checkpoints),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
