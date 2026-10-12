#!/usr/bin/env python3
"""Offline replay of bounded HYPIC paper-ingestion provenance and model fit."""

from __future__ import annotations

import ast
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
    pin = json.loads((HERE / "PAPER_AUTHOR_REFERENCE_FULL_PIN_20261012.json").read_text())
    require(pin["commit"] == "98147c01909004e66d98bcb18b886927d41b0ee5",
            "author reference revision drift")
    snapshot = Path(pin["snapshot_root"])
    require(git(snapshot, "rev-parse", "HEAD") == pin["commit"], "snapshot HEAD drift")
    available = set(git(snapshot, "cat-file", "--batch-all-objects",
                        "--batch-check=%(objectname)").splitlines())
    require(len(pin["files"]) == 10 and pin["matched"] == 10 and pin["missing"] == 0,
            "source audit coverage changed without a new receipt")
    upstream = ast.parse(git(PLUGIN, "show", "HEAD:hypic_vllm_ascend/upstream_parity.py"))
    expected = next(ast.literal_eval(n.value) for n in upstream.body
                    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                    and n.target.id == "UPSTREAM_REFERENCE_HASHES")
    require(len(pin["files"]) == len(expected)
            and {r["path"] for r in pin["files"]} == set(expected),
            "reference path coverage/uniqueness drift")
    for row in pin["files"]:
        require(row["expected_sha256"] == expected[row["path"]]
                and row["local"] and row["match"], "historical reference hash drift")
        require(git(snapshot, "rev-parse", pin["commit"] + ":" + row["path"]) == row["blob"],
                "author tree path/blob drift")
        if row["local"]:
            require(row["blob"] in available, "reviewed author blob unavailable")
            data = subprocess.check_output(("git", "cat-file", "blob", row["blob"]),
                                           cwd=snapshot, timeout=10)
            require(hashlib.sha256(data).hexdigest() == row["sha256"] ==
                    row["expected_sha256"], "author reference bytes drift")
        else:
            require(row["sha256"] is None and row["match"] is None,
                    "missing bytes must not be asserted equal")
    require(len(pin["extra_files"]) == 5, "reference/license inventory drift")
    for row in pin["extra_files"]:
        require(row["blob"] in available, "reference object unavailable")
        require(git(snapshot, "rev-parse", pin["commit"] + ":" + row["path"]) == row["blob"],
                "reference object path drift")
        data = subprocess.check_output(("git", "cat-file", "blob", row["blob"]),
                                       cwd=snapshot, timeout=10)
        require(hashlib.sha256(data).hexdigest() == row["sha256"],
                "reference/license bytes drift")
    case = json.loads((HERE / "skill-cases/paper-ingestion.json").read_text())
    require(case["current_evidence_supplement"]["r19_full_paired_quality_complete"]
            and case["current_evidence_supplement"]["ingestion_does_not_require_new_quality_run"]
            and case["long_term_acceptance"] == "verified",
            "current ingestion scope/status drift")

    print(json.dumps({
        "schema": "paper-ingestion-real-task-case/v1",
        "paper_version": "2607.01299v2",
        "target_model_type": config["model_type"],
        "target_linear_layers": 48,
        "target_full_layers": 16,
        "branch_skill_differs_from_main": True,
        "paper_c3_in_target": False,
        "historical_upstream_origin_commit_proven": False,
        "current_author_reference_commit": pin["commit"],
        "reference_files_byte_matched": 10,
        "reference_files_unverified": 0,
        "long_term_acceptance": "verified",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
