import json

from verify_cache_capacity import verify


def write_fixture(tmp_path, dense_blocks=445, candidate_blocks=600, groups=12):
    dense = tmp_path / "dense.log"
    candidate = tmp_path / "candidate.log"
    evidence = tmp_path / "evidence.jsonl"
    dense.write_text(f"GPU KV cache size: {dense_blocks * groups * 128:,} tokens\n")
    candidate.write_text(f"GPU KV cache size: {candidate_blocks * groups * 128:,} tokens\n")
    rows = []
    for pid in range(4):
        rows.append({"event": "physical_cache_bound", "pid": pid + 10, "num_blocks": candidate_blocks})
    evidence.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return dense, candidate, evidence


def test_accepts_live_capacity_growth(tmp_path):
    result = verify(*write_fixture(tmp_path))
    assert result["ok"] is True
    assert result["candidate_blocks_per_group"] == 600
    assert result["candidate_cache_groups"] == 12


def test_rejects_no_admission_growth(tmp_path):
    result = verify(*write_fixture(tmp_path, candidate_blocks=445))
    assert result["ok"] is False
    assert result["checks"]["candidate_admits_more_blocks"] is False


def test_rejects_log_evidence_disagreement(tmp_path):
    dense, candidate, evidence = write_fixture(tmp_path)
    rows = [json.loads(line) for line in evidence.read_text().splitlines()]
    for row in rows:
        row["num_blocks"] = 599
    evidence.write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = verify(dense, candidate, evidence)
    assert result["ok"] is False
    assert result["checks"]["candidate_log_matches_evidence"] is False
