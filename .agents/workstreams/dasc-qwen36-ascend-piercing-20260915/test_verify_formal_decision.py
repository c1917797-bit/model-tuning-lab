import hashlib

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
    rows = []
    for index in range(count):
        is_correct = index < correct
        response = f"{dataset}-response-{index}"
        rows.append(
            {
                "index": index,
                "ok": True,
                "correct": is_correct,
                "prediction": "A" if is_correct else "B",
                "reference": "A",
                "response_text": response,
                "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
            }
        )
    accuracy = 100.0 * correct / count
    prompt_sha = "1" * 64
    prefix_sha = "2" * 64
    effective_sha = hashlib.sha256(
        f"{prompt_sha}:{prefix_sha}".encode("ascii")
    ).hexdigest()
    details_sha = "3" * 64
    return {
        "run_id": run_id,
        "details_sha256": details_sha,
        "summary": {
            "schema": "mst.dasc.cache-hit-quality/v1",
            "dataset": dataset,
            "requests": count,
            "successful": count,
            "failed": 0,
            "run_id": run_id,
            "correct": correct,
            "accuracy_pct": accuracy,
            "concurrency": 32,
            "max_out_len": 1024,
            "temperature": 0,
            "seed": 0,
            "ignore_eos": False,
            "enable_thinking": False,
            "data_sha256": "4" * 64 if dataset == "longbenchv2" else "5" * 64,
            "prompt_template_sha256": prompt_sha,
            "shared_prefix_sha256": prefix_sha,
            "effective_prompt_contract_sha256": effective_sha,
            "shared_prefix_lines": 96,
            "shared_prefix_bytes": 1024,
            "base_evaluator_sha256": "6" * 64,
            "evaluator_script_sha256": "6" * 64,
            "adapter_sha256": "7" * 64,
            "details_sha256": details_sha,
            "unique_response_sha256": count,
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
        "runtime_manifest_sha256": "manifest",
        "image_digest": "same",
        "source_commit": "same",
        "dasc_plugin": candidate,
        "mode": "physical-cache-eager" if candidate else None,
        "w_max": 64 if candidate else None,
    }


def ownership(arm):
    return [
        {
            "container": f"dasc_qwen36_formal_v13_{arm}_20260916",
            "physical_npus": [4, 5, 6, 7],
            "observed_at_utc": "2026-09-16T12:00:00+00:00",
            "owned_pids": [101, 102, 103, 104],
            "observed_device_pids": [101, 102, 103, 104],
            "foreign_pids": [],
            "ok": True,
        }
    ]


def payload(candidate_quality_drop=0):
    run_ids = ["r1", "r2", "r3"]
    dense_quality = {"longbenchv2": 90, "gsm8k": 1200}
    arms = {}
    for arm, candidate in (("dense", False), ("candidate", True)):
        arms[arm] = {
            "identity": identity(candidate),
            "runtime_manifest": {
                "schema": "dasc-formal-runtime-manifest/v1",
                "files": {
                    "model_index": {"sha256": "same"},
                    "longbenchv2": {"sha256": "4" * 64},
                    "gsm8k": {"sha256": "5" * 64},
                    "quality_evaluator": {"sha256": "6" * 64},
                    "quality_adapter": {"sha256": "7" * 64},
                },
            },
            "runtime_manifest_sha256": "manifest",
            "device_ownership_history": ownership(arm),
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


def test_rejects_runtime_manifest_drift():
    value = payload()
    value["arms"]["candidate"]["runtime_manifest"]["files"]["model_index"][
        "sha256"
    ] = "changed"
    result = evaluate(value)
    assert result["ok"] is False
    assert result["identity_checks"]["runtime_manifests_equal"] is False


def test_rejects_unbound_runtime_manifest_hash():
    value = payload()
    value["arms"]["candidate"]["runtime_manifest_sha256"] = "different"
    result = evaluate(value)
    assert result["ok"] is False
    assert result["identity_checks"]["runtime_manifest_hash_bound"] is False


def test_rejects_quality_response_hash_mismatch():
    value = payload()
    value["arms"]["candidate"]["quality"]["gsm8k"][0]["details"][0][
        "response_sha256"
    ] = "0" * 64
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["all_raw_runs_valid"] is False


def test_rejects_quality_dataset_hash_drift():
    value = payload()
    value["arms"]["dense"]["quality"]["longbenchv2"][0]["summary"][
        "data_sha256"
    ] = "8" * 64
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["all_raw_runs_valid"] is False


def test_rejects_missing_device_ownership_history():
    value = payload()
    value["arms"]["candidate"]["device_ownership_history"] = []
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["device_ownership"] is False


def test_rejects_foreign_device_process_in_history():
    value = payload()
    sample = value["arms"]["dense"]["device_ownership_history"][0]
    sample["observed_device_pids"].append(999)
    sample["foreign_pids"] = [999]
    sample["ok"] = False
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["device_ownership"] is False


def test_rejects_malformed_device_ownership_history_without_crashing():
    value = payload()
    value["arms"]["dense"]["device_ownership_history"] = ["not-an-object"]
    result = evaluate(value)
    assert result["ok"] is False
    assert result["checks"]["device_ownership"] is False
