"""Fail-closed native/paper canary pairing; no timing or task-accuracy claim."""
import argparse
import hashlib
import json
from pathlib import Path


def compare(native, paper):
    identities = [json.loads((root / "identity.json").read_text()) for root in (native, paper)]
    a, b = identities
    assert a["cache_mode"] == "native" and b["cache_mode"] == "paper"
    stimulus = a.get("stimulus", "repeat-v1")
    assert stimulus == b.get("stimulus", "repeat-v1")
    assert stimulus in ("repeat-v1", "divergent-prefix-v1", "prefix-lookup-v1")
    count = 2 if stimulus == "repeat-v1" else 4
    if count == 4:
        assert a["seed_overlap_tokens"] == b["seed_overlap_tokens"]
        assert all(1536 <= n < 3072 for n in a["seed_overlap_tokens"])
    for key in ("model_path", "config_sha256", "packages", "context_repeats",
                "max_model_len", "prompt_sha256"):
        assert a[key] == b[key], "identity mismatch: " + key
    assert a["context_repeats"] == 640 and a["max_model_len"] == 4096
    for key in ("block_size", "mamba_cache_mode", "enable_prefix_caching", "prompt_token_counts"):
        assert a["resolved_runtime"][key] == b["resolved_runtime"][key], key
    assert a["resolved_runtime"]["block_size"] == 1536
    assert all(n > 3072 for n in a["resolved_runtime"]["prompt_token_counts"])
    image_ids = [json.loads((root / "image.json").read_text())[0]["Id"] for root in (native, paper)]
    assert image_ids == ["sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"] * 2
    expected = {(r, p) for r in range(3) for p in range(count)}
    arms = []
    for root in (native, paper):
        rows = json.loads((root / "smoke.json").read_text())
        indexed = {(row["repeat"], row["prompt_index"]): row for row in rows}
        assert len(rows) == count * 3 and set(indexed) == expected
        assert all(row["finish_reason"] == "stop" and row["text"].strip()
                   and row["token_ids"] for row in rows)
        if stimulus == "prefix-lookup-v1":
            assert a["expected_answers"] == b["expected_answers"]
            assert len(set(a["expected_answers"])) == 4
            assert all(row["text"].strip() == a["expected_answers"][row["prompt_index"]]
                       for row in rows)
        arms.append(indexed)
    for index in expected:
        assert arms[0][index]["token_ids"] == arms[1][index]["token_ids"], index
        if index[0] > 0:
            assert arms[0][index]["num_cached_tokens"] == 3072
            assert arms[1][index]["num_cached_tokens"] == 1536
        if count == 4 and index[0] == 0 and index[1] > 0:
            assert arms[0][index]["num_cached_tokens"] == 0
            assert arms[1][index]["num_cached_tokens"] == 1536
    events = [json.loads(line) for line in (paper / "sparse-events.jsonl").read_text().splitlines()]
    for kind in ("engine_constructed", "checkpoint_split", "checkpoint_published"):
        assert any(e["kind"] == kind for e in events), kind
    assert all(e["position"] == 1536 for e in events if e["kind"] == "checkpoint_published")
    assert not (native / "sparse-events.jsonl").exists(), "control patch unexpectedly active"
    hashes = {str(root / name): hashlib.sha256((root / name).read_bytes()).hexdigest()
              for root in (native, paper) for name in ("identity.json", "smoke.json", "run.log", "image.json")}
    # Disabled control does not execute the candidate files. Preserve both
    # manifests, rather than requiring inactive code to equal the corrected arm.
    assert a["patch_sha256"] and b["patch_sha256"]
    return {"paired_requests": count * 3, "exact_token_match": True, "hashes": hashes,
            "patch_manifests": {"native_inactive": a["patch_sha256"],
                                "paper_active": b["patch_sha256"]},
            "scope": str(count) + " synthetic prompts repeated three times only: " + stimulus,
            "worker_copy_instrumented": False, "performance_tested": False,
            "task_accuracy_tested": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("native", type=Path)
    parser.add_argument("paper", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.native, args.paper), indent=2))
