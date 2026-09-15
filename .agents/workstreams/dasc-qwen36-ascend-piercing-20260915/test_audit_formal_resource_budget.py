import json
from pathlib import Path

from audit_formal_resource_budget import audit


MODEL_CONFIG = Path("/cache/efim/Qwen3.6-27B/config.json")


def run_audit(**overrides):
    values = {
        "tensor_parallel_size": 4,
        "block_size": 128,
        "cache_bytes_per_rank": 9663676416,
        "cache_dtype_bytes": 2,
        "max_model_len": 44032,
        "max_num_seqs": 32,
        "performance_input_tokens": 32768,
        "performance_prefix_tokens": 16384,
        "performance_output_tokens": 1024,
        "performance_concurrency": 16,
    }
    values.update(overrides)
    return audit(json.loads(MODEL_CONFIG.read_text()), **values)


def test_frozen_dense_budget_has_expected_capacity():
    result = run_audit()
    assert result["ok"] is True
    assert result["dense_capacity"] == {
        "aggregate_page_bytes_per_rank": 21708800,
        "blocks_per_rank": 445,
        "token_capacity_per_rank": 56960,
        "longest_sequence_blocks": 344,
        "spare_blocks_after_longest_sequence": 101,
    }
    assert result["candidate_active_bridge"][
        "dense_temporal_workspace_bytes_per_rank_upper_bound"
    ] == 603979776


def test_budget_rejects_when_dense_cannot_fit_longest_request():
    result = run_audit(cache_bytes_per_rank=6 * 1024**3)
    assert result["ok"] is False
    assert result["checks"]["dense_single_max_sequence_fits"] is False
