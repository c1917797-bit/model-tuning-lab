import json

from verify_quality_pair import verify


def write_run(root, count=127):
    summary = root / "summary.json"
    details = root / "details.jsonl"
    rows = [
        {"index": index, "ok": True, "correct": index < 100}
        for index in range(count)
    ]
    details.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    summary.write_text(
        json.dumps(
            {
                "schema": "mst.dasc.cache-hit-quality/v1",
                "dataset": "longbenchv2",
                "requests": 127,
                "successful": 127,
                "failed": 0,
                "accuracy_pct": 100.0 * 100 / 127,
                "metrics_before": {"prefix_cache_hits_total": 2},
                "metrics_after": {"prefix_cache_hits_total": 5},
                "prefix_cache_hit_delta": 3,
                "adapter_require_cache_hit": True,
                "cache_hit_verified": True,
            }
        ),
        encoding="utf-8",
    )
    return summary, details


def test_accepts_complete_quality_pair(tmp_path):
    summary, details = write_run(tmp_path)
    result = verify("longbenchv2", summary, details)
    assert result["ok"] is True
    assert all(result["checks"].values())


def test_rejects_incomplete_details(tmp_path):
    summary, details = write_run(tmp_path, count=126)
    result = verify("longbenchv2", summary, details)
    assert result["ok"] is False
    assert result["checks"]["row_count"] is False
