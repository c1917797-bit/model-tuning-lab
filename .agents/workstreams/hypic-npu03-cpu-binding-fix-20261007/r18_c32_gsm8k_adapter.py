#!/usr/bin/env python3
"""Original-source max-2048/c32 GSM8K quality safety arm on NPU0–3.

GSM8K has no explicit reusable segment boundary. It measures the deployed
runtime's off-path quality safety and must not be called HYPIC hot-path proof.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from r16_original_source_full_adapter import SOURCE_COMMIT, configure as configure_r16


HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R18_GSM8K_PHASE_PREREGISTRATION_20261010.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_preregistration() -> dict:
    contract = json.loads(PREREG.read_text(encoding="utf-8"))
    if (contract.get("schema") != "hypic-r18-gsm8k-phase/v1"
            or contract.get("source_commit") != SOURCE_COMMIT
            or contract.get("physical_npus") != [0, 1, 2, 3]
            or contract.get("sample_count") != 1319
            or contract.get("repetitions") != 3
            or contract.get("concurrency") != 32
            or contract.get("max_output_tokens") != 2048):
        raise RuntimeError("r18 GSM8K phase identity drift")
    files = contract.get("file_sha256", {})
    required = {"r18_c32_gsm8k_adapter.py", "r16_original_source_full_adapter.py",
                "hotpath_quality_full.py", "binding_off_quality.py"}
    if not required.issubset(files):
        raise RuntimeError("r18 GSM8K controller hash set incomplete")
    for name, expected in files.items():
        if _sha(HERE / name) != expected:
            raise RuntimeError(f"r18 GSM8K preregistered file drift: {name}")
    return contract


def configure(arm: str):
    controller = configure_r16(arm)
    quality = controller.quality
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"hotpath-cache10r18-c32-gsm8k-{suffix}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r18 GSM8K attempt collides with existing controller")
    quality.ATTEMPT_ROOTS[attempt] = f"quality-context-41984-{attempt}"
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / quality.ATTEMPT_ROOTS[attempt]
    quality.EXPERIMENT = f"hypic-npu03-original-2048-c32-gsm8k-20261010-{suffix}"
    quality.UNIT_ORDER = tuple(("gsm8k", repeat) for repeat in range(1, 4))
    return quality


def _run_unit(quality, arm: str, repeat: int, container_id: str, guard) -> dict:
    """Monitor an exact owned evaluator process while scored requests are live."""
    directory = quality.QROOT / "quality" / arm
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"gsm8k.run{repeat}"
    log_path = directory / f"{stem}.log"
    command = [
        "python3", str(quality.EVALUATOR), "--dataset", "gsm8k", "--data",
        str(quality.DATASETS["gsm8k"][0]), "--base-url", quality.BASE_URL,
        "--model", quality.MODEL_NAME, "--output-dir", str(directory),
        "--run-id", f"run{repeat}", "--concurrency", "32",
        "--max-out-len", "2048", "--seed", "0", "--timeout", "2400",
        "--retries", "2",
    ]
    guard.assert_clean()
    quality.status(arm, "unit-running", dataset="gsm8k", run=repeat)
    started = time.monotonic()
    with log_path.open("ab") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            while True:
                try:
                    code = process.wait(timeout=10)
                    break
                except subprocess.TimeoutExpired:
                    guard.assert_clean()
            guard.assert_clean()
            if code:
                raise RuntimeError(f"{stem}: evaluator exit {code}")
        except Exception:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=30)
            quality.stop_owned_for_abort(arm, container_id)
            raise
    summary_path = directory / f"{stem}.summary.json"
    details_path = directory / f"{stem}.jsonl"
    summary = quality.validate_unit(arm, "gsm8k", repeat)
    receipt = {
        "schema": "hypic-bindingoff-quality-unit/v1", "arm": arm,
        "dataset": "gsm8k", "run": repeat, "container_id": container_id,
        "duration_s": time.monotonic() - started,
        "summary_sha256": quality.sha256(summary_path),
        "details_sha256": quality.sha256(details_path),
        "correct": summary["correct"], "requests": summary["requests"],
    }
    quality.write_json(directory / f"{stem}.receipt.json", receipt)
    quality.status(arm, "unit-verified", dataset="gsm8k", run=repeat,
                   accuracy_pct=summary["accuracy_pct"])
    return receipt


def run_arm(quality, arm: str, fingerprint: dict) -> int:
    quality.assert_lane_available()
    quality.QROOT.mkdir(parents=True)
    with (quality.QROOT / "controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM, quality.interrupt)
        signal.signal(signal.SIGINT, quality.interrupt)
        quality.write_json(quality.QROOT / "contract.json", {
            "schema": "hypic-r18-c32-gsm8k-arm-contract/v1", "arm": arm,
            "fingerprint": fingerprint, "dataset_sha256": quality.DATASETS["gsm8k"][2],
            "evaluator_sha256": quality.EVALUATOR_SHA,
            "repetitions": 3, "concurrency": 32, "max_output_tokens": 2048,
            "temperature": 0, "seed": 0, "ignore_eos": False,
            "enable_thinking": False, "sample_count": 1319,
            "classification": "off-path runtime-enabled safety",
        })
        container_id = ""
        guard = None
        receipts = []
        error = None
        try:
            quality.status(arm, "service-starting", fingerprint=fingerprint)
            container_id = quality.create(arm)
            guard = quality.ForeignProcessGuard(arm, {}, owned_container_id=container_id)
            guard.start()
            quality.start(arm, container_id, fingerprint, guard=guard)
            start = json.loads((quality.QROOT / arm / "service-start.json").read_text())
            guard.set_expected_workers(start["worker_pid_by_physical_npu"])
            for repeat in range(1, 4):
                receipts.append(_run_unit(quality, arm, repeat, container_id, guard))
            guard.assert_clean()
            quality.status(arm, "all-units-verified")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            quality.status(arm, "failed-or-incomplete", error=error)
        finally:
            if guard is not None:
                try:
                    guard.close()
                except Exception as exc:
                    error = f"{error}; guard close {exc}" if error else f"guard close {exc}"
            if container_id:
                try:
                    quality.cleanup(arm, container_id)
                except Exception as exc:
                    error = f"{error}; cleanup {exc}" if error else f"cleanup {exc}"
            result = {
                "schema": "hypic-r18-c32-gsm8k-arm-result/v1", "arm": arm,
                "contract_sha256": quality.sha256(quality.QROOT / "contract.json"),
                "container_id": container_id, "completed_units": len(receipts),
                "unit_receipts": receipts, "error": error,
            }
            for name, path in {
                "service_stop": quality.QROOT / arm / "service-stop.json",
                "lane_guard": quality.QROOT / arm / "lane-guard.json",
            }.items():
                if path.exists():
                    result[name] = json.loads(path.read_text())
                    result[name + "_sha256"] = quality.sha256(path)
            quality.write_json(quality.QROOT / "arm-result.json", result)
    if error:
        raise RuntimeError(error)
    return 0


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r18 GSM8K requires --check or --run")
    prereg = check_preregistration()
    arm = os.environ.get("HYPIC_R18_GSM8K_ARM", "")
    quality = configure(arm)
    if quality.QROOT.exists():
        raise RuntimeError("r18 GSM8K result root exists; never overwrite")
    fingerprint = quality.preflight()
    if (str(quality.QROOT) != prereg["arm_roots"][arm]
            or fingerprint["source_commit"] != SOURCE_COMMIT
            or fingerprint["image"] != prereg["image"]
            or fingerprint["model_index_sha256"] != prereg["model_index_sha256"]
            or fingerprint["evaluator_sha256"] != prereg["evaluator_sha256"]
            or fingerprint["datasets"]["gsm8k"]["sha256"] != prereg["dataset_sha256"]
            or fingerprint["physical_npus"] != [0, 1, 2, 3]
            or fingerprint["max_output_tokens"] != 2048
            or fingerprint["gpu_memory_utilization"] != 0.85
            or fingerprint["material_cache_max_mb"] != 3584
            or fingerprint["max_materialized_segments"] != 10
            or fingerprint["unit_order"] != [("gsm8k", i) for i in range(1, 4)]):
        raise RuntimeError("r18 GSM8K offline invariant drift")
    if sys.argv[1:] == ["--check"]:
        print(json.dumps({"arm": arm, "root": str(quality.QROOT),
                          "device_run_started": False, "source_commit": SOURCE_COMMIT,
                          "dataset": "gsm8k", "samples": 1319,
                          "repetitions": 3, "concurrency": 32,
                          "max_output_tokens": 2048}, sort_keys=True))
        return 0
    return run_arm(quality, arm, fingerprint)


if __name__ == "__main__":
    raise SystemExit(main())
