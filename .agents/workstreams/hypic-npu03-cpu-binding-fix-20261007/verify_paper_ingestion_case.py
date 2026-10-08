#!/usr/bin/env python3
"""Offline replay of bounded HYPIC paper-ingestion provenance and model fit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
MAIN = "ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2"
MODEL = Path("/cache/efim/Qwen3.6-27B")
PLUGIN = Path("/cache/cch/hypic_vllm_ascend-v0.8.5")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=cwd, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def checked_bytes(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected,
            f"SHA256 drift: {path}")
    return data


def main() -> int:
    require(git(REPO, "rev-parse", "origin/main") == MAIN, "main changed")
    for path, blob in (
        (".agents/skills/paper-ingestion/SKILL.md",
         "69edbce77685c9ae4cc20a22bbca403bbbd4e390"),
        (".agents/skills/paper-ingestion/references/selection-baseline-lessons.md",
         "1bd43ec9c2bf50882a8b16a0835d3102ba01f848"),
        (".agents/skills.registry.yaml",
         "2611864bbcf719d57920aae03ff9eb85521526b4"),
    ):
        require(git(REPO, "rev-parse", f"{MAIN}:{path}") == blob,
                f"exact-main ingestion contract drift: {path}")
    branch_skill = git(REPO, "rev-parse", "HEAD:.agents/skills/paper-ingestion/SKILL.md")
    require(branch_skill == "beeb050718caa697097e254a7d3fafb3e557c473"
            and branch_skill != "69edbce77685c9ae4cc20a22bbca403bbbd4e390",
            "branch/main ingestion Skill version boundary changed")

    config = json.loads(checked_bytes(
        MODEL / "config.json",
        "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"))
    text = config["text_config"]
    types = text["layer_types"]
    require(config["model_type"] == "qwen3_5"
            and config["architectures"] == ["Qwen3_5ForConditionalGeneration"]
            and text["num_hidden_layers"] == 64
            and text["dtype"] == "bfloat16"
            and types.count("linear_attention") == 48
            and types.count("full_attention") == 16,
            "current model architecture or dtype drift")
    checked_bytes(
        MODEL / "model.safetensors.index.json",
        "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b")
    require(git(PLUGIN, "rev-parse", "HEAD") ==
            "3ad0967589304cd8fc4e7cff02f48ecc6125c89f",
            "retrospective derivative Git HEAD changed")
    fit = checked_bytes(
        HERE / "PAPER_ARCHITECTURE_FIT.md",
        "d93107c4f69c1a30511183acb0dde1e31f3e9bcf41b2721d983e2e8daf6c6f31").decode()
    require("hot-reuse` PASS" in fit
            and "paper-complete` FAIL" in fit
            and "C3" in fit
            and "retrospective" in fit,
            "retrospective source-audit boundary changed")

    note = " ".join((HERE / "PAPER_INGESTION_CASE_20261009.md")
                    .read_text().lower().split())
    for marker in ("arxiv:2607.01299v2", "redai-studio/HYPIC",
                   "redai-infra/HYPIC", "upstream Git commit",
                   "C1, linear attention", "C2, full attention",
                   "C3, cold prefill", "48 linear and 16 full attention",
                   "retrospectively", "not accepted for", "not implemented/tested"):
        require(" ".join(marker.lower().split()) in note,
                f"ingestion note omitted boundary: {marker}")
    print(json.dumps({
        "schema": "paper-ingestion-real-task-case/v1",
        "paper_version": "2607.01299v2",
        "target_model_type": config["model_type"],
        "target_linear_layers": 48,
        "target_full_layers": 16,
        "branch_skill_differs_from_main": True,
        "paper_c3_in_target": False,
        "exact_upstream_commit_pinned": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
