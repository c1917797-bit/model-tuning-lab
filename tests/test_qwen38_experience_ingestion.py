#!/usr/bin/env python3
"""Static maintainer-knowledge regression; performs no model or NPU work."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

orientation = (ROOT / ".agents/skills/ascend-npu-environment-orientation/SKILL.md").read_text()
benchmark = (ROOT / ".agents/skills/ascend-benchmark-evidence/SKILL.md").read_text()
tuning = (ROOT / ".agents/skills/ascend-inference-tuning-loop/SKILL.md").read_text()
lessons = (ROOT / "docs/LESSONS_LEARNED.md").read_text()

checks = {
    "identity_ladder": "## Model identity proof ladder" in orientation,
    "alias_not_identity": all(
        token in orientation
        for token in ("API alias", "checkpoint version", "architecture class")
    ),
    "no_hash_during_latency": "Do not compute multi-gigabyte model hashes inside an active latency benchmark" in orientation,
    "interference_section": "## Measurement hygiene and long-matrix integrity" in benchmark,
    "preserve_contaminated": "preserve the original artifact" in benchmark and "Never overwrite" in benchmark,
    "single_controller": "one controller owns the matrix" in benchmark,
    "summary_recomputed": "final summaries are recomputed" in benchmark,
    "config_candidate": "Configuration tuning is a valid optimization" in tuning,
    "denominator_not_mutated": "Do not edit the baseline in place" in tuning,
    "partial_quality_not_final": all(
        token in benchmark
        for token in ("suite as incomplete", "operational", "model-quality regression")
    ),
    "qwen38_lessons": "## 9. Qwen3.8 TP8 baseline and identity lessons" in lessons,
}

failed = [name for name, passed in checks.items() if not passed]
assert not failed, "missing Qwen3.8 experience guards: " + ", ".join(failed)
print(f"PASS: {len(checks)} Qwen3.8 experience-ingestion guards; zero NPU work launched")
