#!/usr/bin/env python3
"""Export one frozen Qwen3.6 dense profile without weakening its evidence gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from torch_npu.profiler.profiler import analyse


REQUIRED = (
    "kernel_details.csv",
    "op_statistic.csv",
    "api_statistic.csv",
    "trace_view.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-dir", type=Path, required=True)
    args = parser.parse_args()
    directory = args.service_dir.resolve()
    manifest_path = directory / "service-manifest.json"
    client_path = directory / "profile-client.json"
    manifest = json.loads(manifest_path.read_text())
    client = json.loads(client_path.read_text())

    if manifest.get("schema") != "qwen36-dense-profile-service/v1":
        raise RuntimeError("unexpected service manifest schema")
    if client.get("schema") != "qwen36-dense-profile-client/v1":
        raise RuntimeError("unexpected profile client schema")
    if client.get("status") != "requests_complete":
        raise RuntimeError("profile client did not complete")
    if client.get("service_manifest_sha256") != digest(manifest_path):
        raise RuntimeError("profile client is not bound to this service manifest")
    if manifest.get("profiler_config", {}).get("max_iterations") != 30:
        raise RuntimeError("expected a frozen 30-iteration worker profile")
    if client.get("profile_steps") != 30:
        raise RuntimeError("client and worker profile limits differ")
    if manifest.get("physical_npu_contract") != [4, 5, 6, 7]:
        raise RuntimeError("physical NPU contract differs")

    traces: list[tuple[str, int, Path]] = []
    trace_root = (directory / "traces").resolve()
    for phase in ("prefill", "decode"):
        values = client["results"][phase]["trace_dirs"]
        if len(values) != 4:
            raise RuntimeError(f"exactly four trace directories required for {phase}")
        for value in values:
            path = (directory / value).resolve()
            if path.parent != trace_root:
                raise RuntimeError("trace escaped the service trace directory")
            match = re.fullmatch(r"rank([0-3])_\d+_\d+_ascend_pt", path.name)
            if not match:
                raise RuntimeError(f"unexpected trace directory name: {path.name}")
            if not path.is_dir():
                raise RuntimeError(f"missing trace directory: {path}")
            traces.append((phase, int(match[1]), path))

    if len({path for _, _, path in traces}) != 8:
        raise RuntimeError("prefill/decode trace directories overlap")
    for phase in ("prefill", "decode"):
        if {rank for item_phase, rank, _ in traces if item_phase == phase} != {0, 1, 2, 3}:
            raise RuntimeError(f"{phase} rank coverage differs")

    records = []
    for phase, rank, path in traces:
        output = path / "ASCEND_PROFILER_OUTPUT"
        already_complete = all((output / name).is_file() for name in REQUIRED)
        if not already_complete:
            analyse(str(path), max_process_number=1)
        missing = [name for name in REQUIRED if not (output / name).is_file()]
        if missing:
            raise RuntimeError(f"{path.name}: export missing {missing}")
        records.append(
            {
                "phase": phase,
                "rank": rank,
                "trace_dir": str(path.relative_to(directory)),
                "already_complete": already_complete,
                "sha256": {name: digest(output / name) for name in REQUIRED},
            }
        )

    receipt = directory / "profile-export.json"
    if receipt.exists():
        raise RuntimeError("preserve previous export receipt")
    receipt.write_text(
        json.dumps(
            {
                "schema": "qwen36-dense-profile-export/v1",
                "status": "eight_traces_exported",
                "service_manifest_sha256": digest(manifest_path),
                "profile_client_sha256": digest(client_path),
                "script_sha256": digest(Path(__file__)),
                "records": records,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"status": "eight_traces_exported", "records": len(records)}))


if __name__ == "__main__":
    main()
