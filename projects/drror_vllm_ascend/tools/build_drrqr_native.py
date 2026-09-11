#!/usr/bin/env python3
"""Build one plugin-owned DRRQR Ascend operator from a frozen source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time


REFERENCE_COMMIT = "5cb98caaadeff42b5b62b996e34bb2aaa29d20fd"
OP_SNAKE = "drrqr_recurrent_layout_control_v1"
OP_TYPE = "DrrqrRecurrentLayoutControlV1"
VENDOR = "drrqr_research"
CONTAINER = "drrqr_qwen38_energy_preflight_20260908"
HOST_RESULTS_ROOT = Path(
    "/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/"
    "dk64-energy/preflight"
)
CONTAINER_RESULTS_ROOT = PurePosixPath("/drrqr-results")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


def result_path(output: Path) -> PurePosixPath:
    try:
        relative = output.relative_to(HOST_RESULTS_ROOT)
    except ValueError as error:
        raise ValueError(f"output must be below {HOST_RESULTS_ROOT}") from error
    return CONTAINER_RESULTS_ROOT.joinpath(*relative.parts)


def verify_source(reference: Path, plugin_op: Path) -> dict:
    provenance = json.loads((plugin_op / "provenance.json").read_text())
    if git(reference, "rev-parse", "HEAD") != REFERENCE_COMMIT:
        raise RuntimeError("reference commit changed; re-audit before build")
    if git(reference, "status", "--short"):
        raise RuntimeError("reference repository is dirty")
    if provenance["source_commit"] != REFERENCE_COMMIT:
        raise RuntimeError("provenance commit does not match build contract")
    source_root = reference / provenance["source_subtree"]
    mismatches = {}
    for relative, expected in provenance["source_sha256"].items():
        actual = sha256(source_root / relative)
        if actual != expected:
            mismatches[relative] = {"expected": expected, "actual": actual}
    if mismatches:
        raise RuntimeError(f"frozen source hashes changed: {mismatches}")
    forbidden = ("RecurrentGatedDeltaRule", "recurrent_gated_delta_rule")
    for path in plugin_op.rglob("*"):
        if path.is_file() and path.suffix in {".cpp", ".h", ".txt"}:
            content = path.read_text(errors="strict")
            if any(token in content for token in forbidden):
                raise RuntimeError(f"upstream identifier remains in {path}")
    return provenance


def artifact_receipt(root: Path) -> list[dict]:
    suffixes = {".json", ".run", ".so"}
    files = [
        path for path in root.rglob("*")
        if path.is_file() and path.suffix in suffixes
    ]
    return [
        {
            "path": str(path.relative_to(root)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(files)
    ]


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("/cache/austinov/src/vllm-ascend"),
    )
    parser.add_argument("--container", default=CONTAINER)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 32:
        parser.error("--jobs must be in [1, 32]")

    output = args.output_dir.resolve()
    container_output = result_path(output)
    if output.exists():
        parser.error("output directory must not exist")

    project = Path(__file__).resolve().parents[1]
    plugin_op = project / "native" / OP_SNAKE
    provenance = verify_source(args.reference_root.resolve(), plugin_op)
    output.mkdir(parents=True)
    receipt = {
        "schema": "drrqr-native-build/v1",
        "status": "preparing",
        "created_unix_ns": time.time_ns(),
        "operator": OP_TYPE,
        "operator_snake": OP_SNAKE,
        "vendor": VENDOR,
        "soc": "ascend910b",
        "container": args.container,
        "reference_root": str(args.reference_root.resolve()),
        "reference_commit": REFERENCE_COMMIT,
        "plugin_git_commit": git(project, "rev-parse", "HEAD"),
        "plugin_git_status": git(project, "status", "--short"),
        "provenance": provenance,
        "limits": (
            "Build receipt only; not NPU numerical, graph, endpoint "
            "performance, accuracy, or portability evidence."
        ),
    }
    manifest = output / "build-manifest.json"
    save(manifest, receipt)

    csrc = output / "csrc"
    ignore = shutil.ignore_patterns(
        "build", "build_out", "output", "__pycache__", "*.pyc"
    )
    shutil.copytree(args.reference_root.resolve() / "csrc", csrc, ignore=ignore)
    destination = csrc / "attention" / OP_SNAKE
    shutil.copytree(plugin_op, destination)

    command = [
        "docker", "exec",
        "-w", str(container_output / "csrc"),
        args.container,
        "bash", "build.sh",
        "--pkg",
        "--soc=ascend910b",
        f"--vendor_name={VENDOR}",
        f"--ops={OP_SNAKE}",
        f"-j{args.jobs}",
        "-O3",
    ]
    receipt["command"] = command
    receipt["status"] = "building"
    save(manifest, receipt)
    with (output / "build.log").open("w") as log:
        completed = subprocess.run(
            command, stdout=log, stderr=subprocess.STDOUT, text=True
        )
    receipt["returncode"] = completed.returncode
    receipt["completed_unix_ns"] = time.time_ns()
    receipt["artifacts"] = artifact_receipt(csrc)
    receipt["status"] = "passed" if completed.returncode == 0 else "failed"
    save(manifest, receipt)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print(json.dumps({
        "status": receipt["status"],
        "manifest": str(manifest),
        "artifact_count": len(receipt["artifacts"]),
    }))


if __name__ == "__main__":
    main()
