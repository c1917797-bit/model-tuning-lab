#!/usr/bin/env python3
"""Freeze and verify the exact baseline environment before reusing its results."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={path}", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--quality", type=Path, required=True)
    parser.add_argument("--quality-max-out-len", type=int, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    model = Path("/cache/efim/Qwen3.6-27B")
    container = json.loads(
        subprocess.check_output(["docker", "inspect", args.container], text=True)
    )[0]
    device_paths = [
        entry["PathOnHost"] for entry in container["HostConfig"]["Devices"]
        if entry["PathOnHost"].startswith("/dev/davinci")
        and entry["PathOnHost"][len("/dev/davinci"):].isdigit()
    ]
    if device_paths != [f"/dev/davinci{i}" for i in range(4)]:
        raise SystemExit(f"baseline device mapping changed: {device_paths}")
    shards = sorted(model.glob("model-*.safetensors"))
    if len(shards) != 15:
        raise SystemExit(f"expected 15 weight shards, got {len(shards)}")

    fingerprint = {
        "image_digest": args.image,
        "container_image": container["Image"],
        "container_command": container["Config"]["Cmd"],
        "container_environment": sorted(container["Config"]["Env"]),
        "container_cpuset": container["HostConfig"]["CpusetCpus"],
        "physical_devices": device_paths,
        "source_commit": git_head(args.source),
        "model_index_sha256": sha256(model / "model.safetensors.index.json"),
        "model_shards": [
            {"name": shard.name, "size": shard.stat().st_size,
             "mtime_ns": shard.stat().st_mtime_ns}
            for shard in shards
        ],
        "benchmark_sha256": sha256(args.benchmark),
        "quality_evaluator_sha256": sha256(args.quality),
        "longbench_sha256": sha256(Path(
            "/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json"
        )),
        "gsm8k_sha256": sha256(Path(
            "/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl"
        )),
        "performance_protocol": {
            "input_tokens": 32768, "prefix_tokens": 16384,
            "output_tokens": 1024, "requests": 40, "concurrency": 16,
            "warmup_requests": 2, "repetitions": 3,
        },
        "quality_protocol": {
            "max_out_len": args.quality_max_out_len,
            "ignore_eos": False, "temperature": 0, "seed": 0,
            "thinking": False, "concurrency": 32, "repetitions": 3,
        },
    }
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))
    contract = {
        "schema": "hypic-baseline-contract/v1",
        "fingerprint_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "fingerprint": fingerprint,
    }
    path = root / "baseline-contract.json"
    if path.exists():
        previous = json.loads(path.read_text())
        if previous != contract:
            raise SystemExit(
                "baseline environment/protocol fingerprint changed; "
                "existing baseline cannot be reused"
            )
        print(f"baseline contract MATCH {contract['fingerprint_sha256']}")
        return 0
    if any((root / arm).exists() for arm in ("no-cache", "hypic-only")):
        # Empty precreated directories are fine; measured artifacts are not.
        if any((root / "no-cache").glob("performance.run*.json")) or any(
            (root / "quality/no-cache").glob("*.summary.json")
        ):
            raise SystemExit("baseline artifacts exist without provenance contract")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    print(f"baseline contract FROZEN {contract['fingerprint_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
