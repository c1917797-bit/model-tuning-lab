#!/usr/bin/env python3
"""Prepare a hashed local snapshot of MMLU, GSM8K and HumanEval.

Large benchmark data stays outside Git. This script records exact source bytes
and extracts only English MMLU dev/test CSVs needed by the evaluator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path


SOURCES = {
    "gsm8k_train.jsonl": "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/train.jsonl",
    "gsm8k_test.jsonl": "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl",
    "HumanEval.jsonl.gz": "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
    "mmlu_mirror.tar.gz": "https://codeload.github.com/google-research/crosslingual-knowledge-barriers/tar.gz/refs/heads/main",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dst: Path) -> None:
    if dst.is_file() and dst.stat().st_size:
        return
    tmp = dst.with_suffix(dst.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "model-tuning-lab/1"})
    with urllib.request.urlopen(req, timeout=60) as response, tmp.open("wb") as f:
        shutil.copyfileobj(response, f, length=1024 * 1024)
    tmp.replace(dst)


def extract_mmlu(src: Path, out: Path) -> dict[str, int]:
    for split in ("dev", "test"):
        (out / split).mkdir(parents=True, exist_ok=True)
    counts = {"dev": 0, "test": 0}
    with tarfile.open(src, "r:gz") as tf:
        for member in tf.getmembers():
            if not member.isfile() or not member.name.endswith(".csv") or "MMLU" not in member.name:
                continue
            parts = member.name.split("/")
            split = next((x for x in ("dev", "test") if x in parts), None)
            if split is None:
                continue
            source = tf.extractfile(member)
            if source is None:
                continue
            destination = out / split / Path(member.name).name
            with destination.open("wb") as f:
                shutil.copyfileobj(source, f)
            counts[split] += 1
    if counts["dev"] < 50 or counts["test"] < 50:
        raise RuntimeError(f"MMLU extraction incomplete: {counts}")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/cache/austinov/eval-data/general")
    args = parser.parse_args()
    root = Path(args.root)
    src = root / "src"
    prepared = root / "prepared"
    src.mkdir(parents=True, exist_ok=True)
    prepared.mkdir(parents=True, exist_ok=True)

    source_meta = {}
    for name, url in SOURCES.items():
        path = src / name
        download(url, path)
        source_meta[name] = {"url": url, "bytes": path.stat().st_size, "sha256": sha256(path)}

    for name in ("gsm8k_train.jsonl", "gsm8k_test.jsonl", "HumanEval.jsonl.gz"):
        shutil.copy2(src / name, prepared / name)
    mmlu_counts = extract_mmlu(src / "mmlu_mirror.tar.gz", prepared / "mmlu")

    prepared_hashes = {}
    for path in sorted(p for p in prepared.rglob("*") if p.is_file()):
        prepared_hashes[str(path.relative_to(prepared))] = sha256(path)
    manifest = {
        "schema": "model-tuning-general-eval-data/v1",
        "sources": source_meta,
        "mmlu_counts": mmlu_counts,
        "prepared_sha256": prepared_hashes,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
