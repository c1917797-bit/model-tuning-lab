#!/usr/bin/env python3
"""Replay the immutable retry5 environmental failure without touching NPU."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r5")
EXPECTED = {
    "decode/result.json": "b10005d2848cf4070761a38ebb9edf2b698fc8d1b2ab1fe1cd539f45d9fcc807",
    "hypic-only-decode/lane-guard.json": "c70898e22e29eaf0e77c4a69a9a9ee74c02670738c1422c6d4bb3be3e05bfdf1",
    "decode/release.json": "60794eb7dc56140ac48c28a18379d3aa2c81357b84e0f9c6634a56d61c68482e",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> int:
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        require(path.is_file(), f"missing immutable receipt: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                f"receipt drift: {relative}")
    result = json.loads((ROOT / "decode/result.json").read_text())
    guard = json.loads((ROOT / "hypic-only-decode/lane-guard.json").read_text())
    release = json.loads((ROOT / "decode/release.json").read_text())
    require(result["phase"] == "decode" and result["valid"] is False,
            "retry5 incorrectly accepted")
    require(result["capture"] is None and result["artifact_summary"] is None,
            "retry5 produced a claimed profile")
    require(guard["attempt"] == "profiler-hypic-hotcold-20261009-r4",
            "known stale internal attempt label changed")
    require(guard["samples"] == 4 and guard["probe_errors"] == [],
            "guard sample/probe record drift")
    foreign = guard["foreign"]
    require(len(foreign) == 1 and len(foreign[0]["processes"]) == 1,
            "foreign process cardinality drift")
    process = foreign[0]["processes"][0]
    require(process["physical_npu"] == 0 and process["pid"] == 3750311,
            "foreign process identity drift")
    require(process["container_id"] ==
            "87ab8b2137c62e965c4ed88ce241b306794316cc04625770648a1d1c3bd1caaa",
            "foreign container identity drift")
    require(all(release[k] for k in
                ("container_removed", "owned_workers_released", "port_released")),
            "exact owned-resource release incomplete")
    require(result["release"] == release, "release receipt mismatch")
    print(json.dumps({"retry": "r5", "valid_decode": False,
                      "classification": "environmental pre-capture isolation failure",
                      "foreign_npu": 0, "foreign_pid": 3750311,
                      "owned_resources_released": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
