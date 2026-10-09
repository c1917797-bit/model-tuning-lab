#!/usr/bin/env python3
"""Read-only disproof of the non-strict combined-Prefill hypothesis for r13."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
QUALITY_SHA = "f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b"
EVIDENCE_SHA = "0fff15b2c17a8b9a013dc670cfef87cad824546f6a470bca5659b8c0a60b44ad"
SOURCE = "c12060cd47e7575ead059983d7a8bb4704165c98"
PLUGIN = Path("/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialization_producers(rows: list[dict]) -> Counter[str]:
    return Counter(
        str(row["producer_kind"])
        for row in rows
        if row.get("event") == "position_independent_materialization_candidate"
    )


def replay(script: str) -> dict:
    result = subprocess.run((sys.executable, "-B", str(HERE / script)),
                            cwd=REPO, text=True, capture_output=True,
                            check=False)
    require(result.returncode == 0, f"{script}: {result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> int:
    source = replay("verify_ascend_source_map_case.py")
    benchmark = replay("verify_benchmark_evidence_r13_case.py")
    require(source["plugin_commit"] == SOURCE
            and source["r13_actual_bind_and_python_digest_verified"] is True
            and benchmark["quality_pair"] == "127x3 each arm, REJECT_OR_QUALIFY"
            and benchmark["strict_quality_hot"] == "368/381 FAIL",
            "source or quality pair did not independently replay")

    # Inspect the frozen controller's inherited environment, not today's
    # container declaration. The auditor already proves the two r13 arms
    # differed only by enablement and evidence-file path.
    expected_env = {
        "HYPIC_QUALITY_ATTEMPT": "hotpath-cache10r13-full-hypic",
        "HYPIC_QUALITY_PLUGIN_REPO": str(PLUGIN),
        "HYPIC_QUALITY_PLUGIN_COMMIT": SOURCE,
    }
    for key, value in expected_env.items():
        require(os.environ.get(key, value) == value, f"unexpected {key}")
        os.environ[key] = value
    import binding_off_quality as quality

    require(quality.ATTEMPT == expected_env["HYPIC_QUALITY_ATTEMPT"],
            "candidate controller attempt drift")
    env_by_arm = {}
    for arm in ("no-cache", "hypic-only"):
        env = dict(entry.split("=", 1) for entry in quality.spec(arm)[2])
        require(env.get("VLLM_ASCEND_HYPIC_TRUE_POSITION_INDEPENDENT") == "1"
                and env.get("VLLM_ASCEND_HYPIC_ENABLE") ==
                ("1" if arm == "hypic-only" else "0"),
                f"{arm}: strict-mode/enablement environment drift")
        env_by_arm[arm] = env
    candidate = RAW / "quality-context-41984-hotpath-cache10r13-full-hypic"
    result = json.loads((candidate / "arm-result.json").read_text())
    evidence = candidate / "hypic-only/hypic-evidence.jsonl"
    require(digest(evidence) == EVIDENCE_SHA
            and result["hypic_evidence_sha256"] == EVIDENCE_SHA,
            "candidate runtime evidence hash drift")
    rows = [json.loads(line) for line in evidence.open(encoding="utf-8")]
    producers = materialization_producers(rows)
    require(producers == Counter({"zero_start": 140}),
            f"non-strict/interior materialization observed: {producers}")
    source_text = (PLUGIN / "hypic_vllm_ascend/position_independent.py").read_text()
    require("if config.true_position_independent and not independent:" in source_text
            and 'guards[seg_hash.hex()] = "nonzero_start_in_strict_mode"' in source_text
            and '"combined_prefill_approximation"' in source_text,
            "source strict/compatibility split drift")
    audit = RAW / "hotpath-quality-cache10r13-dual-audit.json"
    require(digest(audit) == QUALITY_SHA, "frozen quality audit hash drift")
    checked = json.loads(audit.read_text())
    require(checked["evidence_valid"] is True
            and checked["pair_seam"]["enable"] == ["0", "1"]
            and checked["pair_seam"]["binds_equal"] is True
            and checked["deployed_quality_decision"] == "REJECT_OR_QUALIFY",
            "r13 pair/negative verdict drift")
    print(json.dumps({
        "schema": "hypic-r13-strict-path-disproof/v1",
        "strict_mode_both_arms": all(
            env["VLLM_ASCEND_HYPIC_TRUE_POSITION_INDEPENDENT"] == "1"
            for env in env_by_arm.values()),
        "observed_materialization_producers": dict(producers),
        "non_strict_combined_prefill_observed": False,
        "quality_decision": "REJECT_OR_QUALIFY",
        "quality_root_cause_identified": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
