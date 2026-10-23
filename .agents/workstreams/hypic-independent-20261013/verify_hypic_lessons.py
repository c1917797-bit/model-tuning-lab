"""Read-only historical lesson replay; never imports a runtime or allocates NPUs."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def load(name):
    return json.loads((HERE / name).read_text())

def verify(raw=False):
    pair = load("R21_FIRST_PAIR_DECISION_20261017.json")
    for field in ("weighted_tpot_ms", "ttft_p95_ms", "tpot_p95_ms"):
        baseline = pair["g1"]["report"]["timing"][field]
        candidate = pair["g3"]["timing"][field]
        delta = (candidate / baseline - 1) * 100
        assert abs(delta - pair["delta_percent_g3_vs_g1"][field]) < 1e-9
        assert delta > 0, "historical negative pair was relabelled"
    assert pair["full_goal_complete"] is False
    canary = load("R22_FIRSTBATCH_CANARY_R1_TERMINAL_20261017.json")["report"]
    assert canary["bounded_catalog_canary_valid"] is True
    assert canary["hot"]["denominator"] == canary["hot"]["covered_count"] == 17
    assert canary["cohort"]["private_responses"] == canary["cohort"]["unscored_producers"] == 17
    assert set(canary["physical"]["ranks"]) == {"0", "1", "2", "3"}
    assert canary["short_suffix"]["row_counts"] == [36]
    assert canary["c1_shadow"]["observed"] == 1728 and canary["c1_shadow"]["passed"]
    failure = load("R21_FULL_HYPIC_R1_FAILURE_20261017.json")
    assert failure["report"]["full_quality_valid"] is False
    assert failure["report"]["scored_responses"] == 0
    assert all(r["actual_slot_commit"] == "not_started" and not r["passed"]
               for r in failure["report"]["failed_receipts"])
    partial = load("R22_FULL_HYPIC_R1_DEADLINE_TERMINAL_20261017.json")
    assert partial["journal_scored_responses"] == 215
    assert partial["journal_request_success"] == 207
    assert partial["finish_reasons"] == {"stop": 121, "length": 86, "null": 8}
    assert partial["controller_result"]["responses"] == 0
    assert partial["controller_result"]["error"]["type"] == "TimeoutError"
    assert partial["full_quality_valid"] is False and partial["quality_acceptance"] == "INCOMPLETE"
    repair = load("R23_PARTIAL_RESPONSE_HOST_READINESS_20261017.json")
    assert repair["old_evidence_unchanged"] is True
    for name, expected in repair["hashes"].items():
        assert sha(HERE / name) == expected, name
    checked = 0
    if raw:
        inventories = [
            (Path(pair["g1"]["raw_root"]), pair["g1"]["report"]["raw_sha256"]),
            (Path(failure["raw_root"]), failure["report"]["raw_sha256"]),
            (Path("/cache/cch/hypic-independent-20261013/full-quality-r22-hypic-r1"),
             partial["raw_sha256"]),
        ]
        for root, inventory in inventories:
            assert root.is_dir() and not root.is_symlink()
            for relative, expected in inventory.items():
                path = root / relative
                assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
                assert path.is_file() and not path.is_symlink()
                assert path.resolve().is_relative_to(root.resolve())
                assert sha(path) == expected, str(path)
                checked += 1
        from independent_partial_quality_responses import recover_quality_responses
        recovered = recover_quality_responses(inventories[-1][0] / "events.jsonl")
        assert len(recovered) == 215 and sum(r["ok"] for r in recovered) == 207
    return {"historical_case_replay": "PASS", "raw_hashes_checked": checked,
            "device_run": False, "full_reproduction_accepted": False,
            "scope": "historical report arithmetic, immutable hashes and host repair only"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", action="store_true")
    print(json.dumps(verify(parser.parse_args().raw), sort_keys=True))
