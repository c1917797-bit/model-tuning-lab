#!/usr/bin/env python3
"""Read-only replay of the cache10r9 old-baseline non-comparability decision."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-cache10r9-full-baseline"

from binding_off_quality import ROOT, frozen_source, spec  # noqa: E402


OLD = ROOT / "quality-context-41984-hotpath-full-baseline"
NEW = ROOT / "quality-context-41984-hotpath-cache10r9-full-hypic"
EXPECTED_HASHES = {
    OLD / "contract.json": "73e2f5ae76e5fcaf7b623791e68d5b0e62030ac6fa828534b72ae227bc542336",
    OLD / "arm-result.json": "856b33bf897187bdc5351d63b165cb7067fca794b65eea99bf501c6411f9c898",
    OLD / "no-cache/service-start.json": "9e9d2c8f676b0a8fbce3f256078ba9aae381f87ca9f7cea6b9ffe480bc1ac601",
    OLD / "no-cache/lane-guard.json": "a523cc0f1ad1a89604c75a4e561429d8ddcc931419e8e74b5b1ebffef5d7c432",
    OLD / "no-cache/service-stop.json": "b4c7e0582db71a62d6f9e1e25df2cbaca7a4b26e259bfa5daeae687ff93ab540",
    NEW / "contract.json": "89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48",
}
SAMPLE_MANIFEST_SHA = "d289db3f3e9ceb627d48ad2b01925d37a41954f915bdcdf6b7aaf8589fe29a6f"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        checked(digest(path) == expected, f"raw artifact drift: {path}")

    old = json.loads((OLD / "contract.json").read_text())
    new = json.loads((NEW / "contract.json").read_text())
    checked(old["arm"] == "no-cache" and new["arm"] == "hypic-only", "arm identity drift")
    # The newer controller records these inactive split-only fields as null;
    # the old controller did not serialize them at all.
    excluded = {"arm", "fingerprint", "split_shard", "clean_set_receipt_sha256"}
    checked(new.get("split_shard") is None and new.get("clean_set_receipt_sha256") is None,
            "split-only fields unexpectedly active")
    checked({k: v for k, v in old.items() if k not in excluded} ==
            {k: v for k, v in new.items() if k not in excluded},
            "workload or sample identity drift")
    differences = {key: (old["fingerprint"].get(key), new["fingerprint"].get(key))
                   for key in set(old["fingerprint"]) | set(new["fingerprint"])
                   if old["fingerprint"].get(key) != new["fingerprint"].get(key)}
    checked(differences == {
        "gpu_memory_utilization": (None, 0.85),
        "material_cache_max_mb": (None, 3584),
        "max_materialized_segments": (None, 10),
    }, f"unexpected fingerprint differences: {differences}")

    result = json.loads((OLD / "arm-result.json").read_text())
    guard = json.loads((OLD / "no-cache/lane-guard.json").read_text())
    stop = json.loads((OLD / "no-cache/service-stop.json").read_text())
    files = sorted((OLD / "samples").glob("*.json"))
    rows = [json.loads(path.read_text()) for path in files]
    checked(result["error"] is None and result["completed_samples"] == 127
            and result["scored_rows"] == 381, "old control was not complete")
    checked(len(files) == 127 and sorted(row["index"] for row in rows) == list(range(127))
            and all(len(row["scores"]) == 3 for row in rows), "old sample set incomplete")
    manifest = "".join(f"{digest(path)}  samples/{path.name}\n" for path in files)
    checked(hashlib.sha256(manifest.encode()).hexdigest() == SAMPLE_MANIFEST_SHA,
            "old sample manifest drift")
    checked(guard["samples"] > 0 and not guard["foreign"] and not guard["probe_errors"],
            "old control isolation invalid")
    checked(all(stop[key] is True for key in
                ("container_removed", "owned_npus_released", "port_released", "lane_available")),
            "old control release invalid")

    old_command = frozen_source("no-cache")["Config"]["Cmd"][2]
    new_control_command = spec("no-cache")[3]
    new_candidate_command = spec("hypic-only")[3]
    util = lambda command: re.findall(r"--gpu-memory-utilization\s+(\S+)", command)
    checked(util(old_command) == ["0.9"] and util(new_control_command) == ["0.85"]
            and util(new_candidate_command) == ["0.85"], "common GPU budget proof failed")

    print(json.dumps({"old_control_complete": True, "old_control_reusable": False,
                      "reason": "common gpu-memory-utilization 0.9 versus 0.85",
                      "matched_new_control": str(ROOT / "quality-context-41984-hotpath-cache10r9-full-baseline")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
