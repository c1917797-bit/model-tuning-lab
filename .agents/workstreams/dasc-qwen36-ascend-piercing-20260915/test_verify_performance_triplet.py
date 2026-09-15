import json

from verify_performance_triplet import verify


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def valid_report():
    return {
        "config": {
            "input_tokens": 32768,
            "prefix_tokens": 16384,
            "output_tokens": 1024,
            "requests": 40,
            "concurrency": 16,
            "warmup_requests": 2,
            "warmup_mode": "concurrent_materialization_gate",
            "ignore_eos": True,
            "segment_boundary_transport": "vllm_xargs.hypic_segment_ends",
            "segment_ends": [16384, 32768],
        },
        "summary": {
            "successful": 40,
            "failed": 0,
            "fixed_output_verified": True,
            "ttft_mean_ms": 1.0,
            "ttft_p95_ms": 1.0,
            "tpot_mean_ms": 1.0,
            "tpot_p95_ms": 1.0,
            "benchmark_duration_s": 1.0,
        },
        "results": [
            {
                "index": index,
                "ok": True,
                "output_tokens": 1024,
                "requested_output_tokens": 1024,
            }
            for index in range(40)
        ],
    }


def test_accepts_complete_triplet(tmp_path):
    report = tmp_path / "report.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    write(report, valid_report())
    write(before, {"vllm:prefix_cache_hits_total": 5})
    write(after, {"vllm:prefix_cache_hits_total": 6})
    result = verify(report, before, after)
    assert result["ok"] is True
    assert all(result["checks"].values())


def test_rejects_nonpositive_cache_hit_delta(tmp_path):
    report = tmp_path / "report.json"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    write(report, valid_report())
    write(before, {"vllm:prefix_cache_hits_total": 5})
    write(after, {"vllm:prefix_cache_hits_total": 5})
    result = verify(report, before, after)
    assert result["ok"] is False
    assert result["checks"]["positive_cache_hit_delta"] is False
