import json
import hashlib

from verify_quality_pair import verify


def write_run(root, count=127):
    summary = root / "summary.json"
    details = root / "details.jsonl"
    rows = []
    for index in range(count):
        response = f"response-{index}"
        rows.append(
            {
                "index": index,
                "ok": True,
                "correct": index < 100,
                "prediction": "A" if index < 100 else "B",
                "reference": "A",
                "response_text": response,
                "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
            }
        )
    details.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    details_sha = hashlib.sha256(details.read_bytes()).hexdigest()
    prompt_sha = "1" * 64
    prefix_sha = "2" * 64
    summary.write_text(
        json.dumps(
            {
                "schema": "mst.dasc.cache-hit-quality/v1",
                "dataset": "longbenchv2",
                "run_id": "run1",
                "requests": 127,
                "successful": 127,
                "failed": 0,
                "correct": 100,
                "accuracy_pct": 100.0 * 100 / 127,
                "concurrency": 32,
                "max_out_len": 1024,
                "temperature": 0,
                "seed": 0,
                "ignore_eos": False,
                "enable_thinking": False,
                "data_sha256": "3" * 64,
                "prompt_template_sha256": prompt_sha,
                "shared_prefix_sha256": prefix_sha,
                "effective_prompt_contract_sha256": hashlib.sha256(
                    f"{prompt_sha}:{prefix_sha}".encode("ascii")
                ).hexdigest(),
                "shared_prefix_lines": 96,
                "shared_prefix_bytes": 1024,
                "base_evaluator_sha256": "4" * 64,
                "evaluator_script_sha256": "4" * 64,
                "adapter_sha256": "5" * 64,
                "details_sha256": details_sha,
                "unique_response_sha256": count,
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
