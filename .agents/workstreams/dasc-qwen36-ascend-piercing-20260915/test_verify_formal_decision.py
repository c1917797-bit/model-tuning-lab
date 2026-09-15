from verify_formal_decision import FIXED_IDENTITY, evaluate


def metrics(hits):
    return {'vllm:prefix_cache_hits_total{engine="0"}': hits}


def performance(run_id, ttft, duration):
    rows = [
        {
            "index": index,
            "ok": True,
            "output_tokens": 1024,
            "requested_output_tokens": 1024,
        }
        for index in range(40)
    ]
    return {
        "run_id": run_id,
        "metrics_before": metrics(10),
        "metrics_after": metrics(20),
        "report": {
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
                "ttft_mean_ms": ttft,
                "ttft_p95_ms": ttft * 1.1,
                "tpot_mean_ms": 10,
                "tpot_p95_ms": 11,
                "benchmark_duration_s": duration,
            },
            "results": rows,
        },
    }


def quality(dataset, run_id, correct):
    count = 127 if dataset == "longbenchv2" else 1319
    rows = [
        {"index": index, "ok": True, "correct": index < correct}
        for index in range(count)
    ]
    accuracy = 100.0 * correct / count
    return {
        "run_id": run_id,
        "summary": {
            "schema": "mst.dasc.cache-hit-quality/v1",
            "dataset": dataset,
            "requests": count,
            "successful": count,
            "failed": 0,
            "accuracy_pct": accuracy,
            "metrics_before": metrics(3),
            "metrics_after": metrics(5),
            "prefix_cache_hit_delta": 2,
            "adapter_require_cache_hit": True,
            "cache_hit_verified": True,
        },
        "details": rows,
    }


def identity(candidate):
    return {
        **FIXED_IDENTITY,
        "model_config_sha256": "same",
        "image_digest": "same",
        "source_commit": "same",
        "dasc_plugin": candidate,
        "mode": "physical-cache-eager" if candidate else None,
        "w_max": 64 if candidate else None,
    }


def payload(candidate_quality_drop=0):
    run_ids = ["r1", "r2", "r3"]
    dense_quality = {"longbenchv2": 90, "gsm8k": 1200}
    arms = {}
    for arm, candidate in (("dense", False), ("candidate", True)):
        arms[arm] = {
            "identity": identity(candidate),
            "performance": [
                performance(
                    run_id,
                    80 if candidate else 100,
                    8 if candidate else 10,
                )
                for run_id in run_ids
            ],
            "quality": {
                dataset: [
                    quality(
                        dataset,
                        run_id,
                        correct - (candidate_quality_drop if candidate else 0),
                    )
                    for run_id in run_ids
                ]
                for dataset, correct in dense_quality.items()
            },
        }
    return {
        "schema": "dasc-formal-v13-normalized/v1",
        "candidate_activation": {
            "ok": True,
            "physical_cache_pids": [101, 102, 103, 104],
            "tp_geometry_pids": [101, 102, 103, 104],
            "worker_dispatch_pids": [101, 102, 103, 104],
            "compact_lt_dense": True,
            "positive_blocks": True,
            "heterogeneous_cache_grouped": True,
        },
        "cache_capacity": {
            "ok": True,
            "checks": {
                "dense_matches_static_budget": True,
                "candidate_admits_more_blocks": True,
                "candidate_log_matches_evidence": True,
                "same_cache_group_multiplier": True,
                "total_token_capacity_grows": True,
                "four_candidate_workers": True,
            },
        },
        "arms": arms,
    }


def test_accepts_complete_paired_positive_evidence():
    result = evaluate(payload())
    assert result["ok"] is True
    assert result["decision"] == "accept"


def test_rejects_performance_gain_with_quality_regression():
    result = evaluate(payload(candidate_quality_drop=20))
    assert result["ok"] is False
    assert result["decision"] == "reject"
    assert result["checks"]["quality"] is False


def test_rejects_zero_cache_hit_even_when_metrics_improve():
    value = payload()
    value["arms"]["candidate"]["performance"][0]["metrics_after"] = metrics(10)
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["all_raw_runs_valid"] is False


def test_rejects_missing_four_worker_candidate_activation():
    value = payload()
    value["candidate_activation"]["physical_cache_pids"] = [101, 102, 103]
    value["candidate_activation"]["tp_geometry_pids"] = [101, 102, 103]
    value["candidate_activation"]["worker_dispatch_pids"] = [101, 102, 103]
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["candidate_activation"] is False
