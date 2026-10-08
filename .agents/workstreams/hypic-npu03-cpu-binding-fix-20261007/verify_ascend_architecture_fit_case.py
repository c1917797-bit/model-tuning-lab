#!/usr/bin/env python3
"""Read-only HYPIC architecture-fit replay; chronology stays fail-closed."""

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
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=cwd, text=True,
                            capture_output=True, check=False)
    require(result.returncode == 0, result.stderr)
    return result.stdout.strip()


def hashed(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected,
            f"evidence SHA256 drift: {path}")
    return raw


def main() -> int:
    require(git(REPO, "rev-parse", "origin/main") == MAIN, "main moved")
    for path, blob in (
        (".agents/skills/ascend-architecture-fit/SKILL.md",
         "c8da4422b492bb6ca1ae6b40bb2563bd412dde79"),
        (".agents/skills.registry.yaml",
         "2611864bbcf719d57920aae03ff9eb85521526b4"),
    ):
        require(git(REPO, "rev-parse", f"{MAIN}:{path}") == blob,
                f"exact-main architecture Skill drift: {path}")
    require(git(REPO, "rev-parse", "HEAD:.agents/skills/ascend-architecture-fit/SKILL.md")
            == "c8da4422b492bb6ca1ae6b40bb2563bd412dde79",
            "branch Skill differs from main")

    config = json.loads(hashed(
        MODEL / "config.json",
        "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"))
    text = config["text_config"]
    require(config["model_type"] == "qwen3_5"
            and config["architectures"] == ["Qwen3_5ForConditionalGeneration"]
            and text["num_hidden_layers"] == 64
            and text["dtype"] == "bfloat16"
            and text["layer_types"].count("linear_attention") == 48
            and text["layer_types"].count("full_attention") == 16,
            "target architecture drift")
    for name, sha in (
        ("tokenizer_config.json",
         "5186f0defcd7f232382c7f0aebcd2252d073bb921ab240e407b7ae8745d2b29b"),
        ("tokenizer.json",
         "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42"),
        ("model.safetensors.index.json",
         "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b"),
    ):
        hashed(MODEL / name, sha)
    require(git(PLUGIN, "rev-parse", "HEAD") ==
            "3ad0967589304cd8fc4e7cff02f48ecc6125c89f",
            "retrospective plugin source changed")

    fit = hashed(
        HERE / "PAPER_ARCHITECTURE_FIT.md",
        "d93107c4f69c1a30511183acb0dde1e31f3e9bcf41b2721d983e2e8daf6c6f31").decode()
    require("retrospective" in fit.lower()
            and "hot-reuse` PASS" in fit
            and "paper-complete` FAIL" in fit
            and "C3.1-C3.6" in fit,
            "bounded/full-scope source-audit result drift")
    performance = json.loads(hashed(
        RAW / "performance-independent-audit.json",
        "de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1"))
    require(performance["all_six_units_valid"] is True
            and performance["quality_decision"] == "not-measured",
            "historical runtime evidence scope drift")
    r12 = hashed(
        HERE / "HOTPATH_CACHE10R12_TERMINAL_AUDIT.md",
        "bfdf1bee864719a0bbc44f88aba58d0bcb7c330d2ae358ad5fcb3f9fec57e9d3").decode()
    require("52/57" in r12 and "No same-identity no-cache control" in r12,
            "r12 activation boundary drift")

    case = (HERE / "ASCEND_ARCHITECTURE_FIT_CASE_20261009.md").read_text()
    for phrase in ("Status: **partial-evidence**", "pre-implementation",
                   "C1 cached transition", "C2 relocated full-attention",
                   "C3 scatter/combine", "does-not-fit", "does not rerun"):
        require(phrase in case, f"case decision boundary absent: {phrase}")
    print(json.dumps({
        "schema": "ascend-architecture-fit-real-task-case/v1",
        "target_model_type": config["model_type"],
        "text_linear_layers": 48,
        "text_full_layers": 16,
        "c1_c2_single_instance_fit": True,
        "c3_current_service_fit": False,
        "historical_preimplementation_gate_met": False,
        "long_term_acceptance": "partial-evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
