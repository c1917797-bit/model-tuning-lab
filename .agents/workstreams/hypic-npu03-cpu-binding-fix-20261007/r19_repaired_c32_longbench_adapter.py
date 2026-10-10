#!/usr/bin/env python3
"""Prospective max-2048/c32 LongBench pair for the known HYPIC race repair."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

from r16_original_source_full_adapter import configure as configure_r16


HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R19_REPAIRED_C32_2048_PREREGISTRATION_20261010.json"
SOURCE_ROOT = "/cache/cch/hypic_vllm_ascend-hotproof-20261008"
SOURCE_COMMIT = "4429e35177979c874bf053ab29789e4773f39b22"
ROOT_NAME = "hotpath-cache10r19-c32-full"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_preregistration() -> dict:
    contract = json.loads(PREREG.read_text(encoding="utf-8"))
    if (contract.get("schema") != "hypic-r19-repaired-c32-2048-preregistration/v1"
            or contract.get("source_root") != SOURCE_ROOT
            or contract.get("source_commit") != SOURCE_COMMIT
            or contract.get("physical_npus") != [0, 1, 2, 3]
            or contract.get("longbench", {}).get("samples") != 127
            or contract.get("longbench", {}).get("repetitions") != 3
            or contract.get("longbench", {}).get("concurrency") != 32
            or contract.get("max_output_tokens") != 2048):
        raise RuntimeError("r19 preregistration identity drift")
    required = {
        "r19_repaired_c32_longbench_adapter.py",
        "r19_repaired_c32_longbench_audit.py",
        "r16_original_source_full_adapter.py",
        "hotpath_quality_full.py",
        "binding_off_quality.py",
    }
    files = contract.get("file_sha256", {})
    if not required.issubset(files):
        raise RuntimeError("r19 preregistered controller/auditor file set incomplete")
    for name, expected in files.items():
        if _sha(HERE / name) != expected:
            raise RuntimeError(f"r19 preregistered file drift: {name}")
    return contract


def _canary(quality, arm: str) -> None:
    prompt = "Return the single digit 7 and nothing else."
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128, "temperature": 0, "seed": 0,
        "ignore_eos": False, "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    responses = []
    for _ in range(3):
        request = Request(
            quality.BASE_URL + "/v1/chat/completions", data=encoded,
            headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=180) as response:
            body = json.load(response)
        used = (body.get("usage") or {}).get("completion_tokens")
        if not isinstance(used, int) or not 0 <= used <= 128:
            raise RuntimeError("r19 canary output-token accounting drift")
        responses.append(str(body["choices"][0]["message"].get("content") or ""))
    record = {
        "schema": "hypic-r19-short-canary/v1", "arm": arm,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "request_sha256": hashlib.sha256(encoded).hexdigest(),
        "max_output_tokens": 128, "responses": responses,
        "response_sha256": [hashlib.sha256(x.encode()).hexdigest() for x in responses],
        "within_arm_exact": len(set(responses)) == 1,
    }
    quality.write_json(quality.QROOT / arm / "r19-short-canary.json", record)
    if not record["within_arm_exact"]:
        raise RuntimeError("r19 deterministic canary varies within arm")
    if arm == "hypic-only":
        baseline = json.loads(
            (quality.ROOT / f"quality-context-41984-{ROOT_NAME}-baseline"
             / "no-cache" / "r19-short-canary.json").read_text(encoding="utf-8"))
        if (baseline.get("request_sha256") != record["request_sha256"]
                or baseline.get("response_sha256") != record["response_sha256"]):
            raise RuntimeError("r19 candidate short canary differs from baseline")


def configure(arm: str):
    controller = configure_r16(arm)
    quality = controller.quality
    # r16 freezes the historical controller bytes; replace only its selected
    # plugin source, before any preflight, spec, create, or source attestation.
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE_ROOT
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = SOURCE_COMMIT
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"{ROOT_NAME}-{suffix}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r19 attempt collides with an existing controller")
    quality.ATTEMPT_ROOTS[attempt] = f"quality-context-41984-{attempt}"
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / quality.ATTEMPT_ROOTS[attempt]
    quality.EXPERIMENT = f"hypic-npu03-repaired-2048-c32-20261010-{suffix}"
    controller.CAMPAIGN = "cache10r19-c32"
    controller.CONCURRENCY = 32

    original_start = quality.start

    def start_with_canary(*args, **kwargs):
        original_start(*args, **kwargs)
        _canary(quality, arm)

    quality.start = start_with_canary
    original_monitored = controller.monitored_samples

    def staged_scoring(items, evaluator, guard, container_id, accept):
        if len(items) <= 32:
            return original_monitored(items, evaluator, guard, container_id, accept)
        original_monitored(items[:32], evaluator, guard, container_id, accept)
        guard.assert_clean()
        evidence = quality.QROOT / arm / "hypic-evidence.jsonl"
        quality.write_json(quality.QROOT / "capacity-wave.json", {
            "schema": "hypic-r19-c32-integrated-wave/v1",
            "scored_sample_indexes": [item["index"] for item in items[:32]],
            "concurrency": 32,
            "guard_samples_so_far": guard.samples,
            "event_summary_so_far": controller.event_summary(controller.events(evidence)),
        })
        return original_monitored(items[32:], evaluator, guard, container_id, accept)

    controller.monitored_samples = staged_scoring
    return controller


def main() -> int:
    if sys.argv[1:] not in (["--check"], ["--run"]):
        raise RuntimeError("r19 requires --check or --run")
    prereg = check_preregistration()
    arm = os.environ.get("HYPIC_R19_ARM", "")
    controller = configure(arm)
    quality = controller.quality
    if quality.QROOT.exists():
        raise RuntimeError("r19 result root already exists; never overwrite")
    cases, _ = controller.cases()
    fingerprint = quality.preflight()
    if (str(quality.QROOT) != prereg["arm_roots"][arm]["longbench"]
            or len(cases) != 127 or controller.REPETITIONS != 3
            or controller.CONCURRENCY != 32 or controller.MAX_OUTPUT != 2048
            or fingerprint["source_commit"] != SOURCE_COMMIT
            or fingerprint["plugin_source_root"] != SOURCE_ROOT
            or fingerprint["physical_npus"] != [0, 1, 2, 3]
            or fingerprint["max_output_tokens"] != 2048
            or fingerprint["gpu_memory_utilization"] != 0.85
            or fingerprint["material_cache_max_mb"] != 3584
            or fingerprint["max_materialized_segments"] != 10
            or fingerprint["image"] != prereg["image"]
            or fingerprint["model_index_sha256"] != prereg["model_index_sha256"]
            or fingerprint["evaluator_sha256"] != prereg["evaluator_sha256"]
            or fingerprint["datasets"]["longbenchv2"]["sha256"]
                != prereg["longbench"]["dataset_sha256"]):
        raise RuntimeError("r19 LongBench offline invariant drift")
    if sys.argv[1:] == ["--run"]:
        return controller.main()
    print(json.dumps({
        "arm": arm, "root": str(quality.QROOT), "preregistration_valid": True,
        "device_run_started": False, "source_commit": SOURCE_COMMIT,
        "sample_count": len(cases), "repetitions": controller.REPETITIONS,
        "concurrency": controller.CONCURRENCY,
        "max_output_tokens": controller.MAX_OUTPUT,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
