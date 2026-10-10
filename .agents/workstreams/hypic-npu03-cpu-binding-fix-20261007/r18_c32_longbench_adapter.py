#!/usr/bin/env python3
"""Original HYPIC source, max-2048/c32 explicit-segment LongBench arm.

This only changes the client concurrency from the r16 original-source
controller. A separate prospective contract binds the result root and inputs.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

from r16_original_source_full_adapter import SOURCE_COMMIT, configure as configure_r16


HERE = Path(__file__).resolve().parent
PREREG = HERE / "HYPIC_R18_C32_2048_PREREGISTRATION_20261010.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canary(quality, arm: str) -> None:
    """Short deterministic safety oracle on the already-started quality service."""
    prompt = "Return the single digit 7 and nothing else."
    payload = {
        "model": quality.MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 128,
        "temperature": 0,
        "seed": 0,
        "ignore_eos": False,
        "stream": False,
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
        usage = body.get("usage") or {}
        if (not isinstance(usage.get("completion_tokens"), int)
                or not 0 <= usage["completion_tokens"] <= 128):
            raise RuntimeError("r18 canary output-token accounting drift")
        responses.append(str(body["choices"][0]["message"].get("content") or ""))
    record = {
        "schema": "hypic-r18-short-canary/v1", "arm": arm,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "request_sha256": hashlib.sha256(encoded).hexdigest(),
        "max_output_tokens": 128, "responses": responses,
        "response_sha256": [hashlib.sha256(x.encode()).hexdigest() for x in responses],
        "within_arm_exact": len(set(responses)) == 1,
    }
    quality.write_json(quality.QROOT / arm / "r18-short-canary.json", record)
    if not record["within_arm_exact"]:
        raise RuntimeError("r18 deterministic canary varies within arm")
    if arm == "hypic-only":
        baseline = json.loads((quality.ROOT / "quality-context-41984-"
                               "hotpath-cache10r18-c32-full-baseline" / "no-cache" /
                               "r18-short-canary.json").read_text(encoding="utf-8"))
        if (baseline.get("request_sha256") != record["request_sha256"]
                or baseline.get("response_sha256") != record["response_sha256"]):
            raise RuntimeError("r18 candidate short canary differs from baseline")


def check_preregistration() -> dict:
    contract = json.loads(PREREG.read_text(encoding="utf-8"))
    if (contract.get("schema") != "hypic-r18-c32-2048-preregistration/v1"
            or contract.get("source_commit") != SOURCE_COMMIT
            or contract.get("physical_npus") != [0, 1, 2, 3]
            or contract.get("longbench", {}).get("samples") != 127
            or contract.get("longbench", {}).get("repetitions") != 3
            or contract.get("longbench", {}).get("concurrency") != 32
            or contract.get("max_output_tokens") != 2048):
        raise RuntimeError("r18 preregistration identity drift")
    files = contract.get("file_sha256", {})
    required = {"r18_c32_longbench_adapter.py", "r16_original_source_full_adapter.py",
                "hotpath_quality_full.py", "binding_off_quality.py"}
    if not required.issubset(files):
        raise RuntimeError("r18 preregistered controller file set incomplete")
    for name, expected in files.items():
        if _sha(HERE / name) != expected:
            raise RuntimeError(f"r18 preregistered file drift: {name}")
    return contract


def configure(arm: str):
    controller = configure_r16(arm)
    quality = controller.quality
    suffix = "baseline" if arm == "no-cache" else "hypic"
    attempt = f"hotpath-cache10r18-c32-full-{suffix}"
    if attempt in quality.ATTEMPT_ROOTS:
        raise RuntimeError("r18 attempt collides with an existing controller")
    quality.ATTEMPT_ROOTS[attempt] = f"quality-context-41984-{attempt}"
    quality.RESERVE_ATTEMPTS = quality.RESERVE_ATTEMPTS | {attempt}
    quality.ATTEMPT = attempt
    quality.QROOT = quality.ROOT / quality.ATTEMPT_ROOTS[attempt]
    quality.EXPERIMENT = f"hypic-npu03-original-2048-c32-20261010-{suffix}"
    controller.CAMPAIGN = "cache10r18-c32"
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
        # The first 32 distinct requests are scored rows, not an extra pilot.
        original_monitored(items[:32], evaluator, guard, container_id, accept)
        guard.assert_clean()
        evidence = quality.QROOT / arm / "hypic-evidence.jsonl"
        quality.write_json(quality.QROOT / "capacity-wave.json", {
            "schema": "hypic-r18-c32-integrated-wave/v1",
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
        raise RuntimeError("r18 requires --check or --run")
    prereg = check_preregistration()
    arm = os.environ.get("HYPIC_R18_ARM", "")
    controller = configure(arm)
    quality = controller.quality
    if quality.QROOT.exists():
        raise RuntimeError("r18 result root already exists; never overwrite")
    cases, _ = controller.cases()
    fingerprint = quality.preflight()
    expected_root = prereg["arm_roots"][arm]["longbench"]
    if (str(quality.QROOT) != expected_root
            or len(cases) != 127
            or controller.REPETITIONS != 3
            or controller.CONCURRENCY != 32
            or controller.MAX_OUTPUT != 2048
            or fingerprint["source_commit"] != SOURCE_COMMIT
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
        raise RuntimeError("r18 LongBench offline invariant drift")
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
