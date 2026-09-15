import pytest

from capture_prometheus_metrics import parse_metrics


def test_parse_metrics_keeps_labeled_series_and_ignores_unrelated_rows():
    result = parse_metrics(
        """
# HELP vllm:prefix_cache_hits_total hits
vllm:prefix_cache_hits_total{engine=\"0\"} 12
vllm:prefix_cache_hits_total{engine=\"1\"} 13
vllm:prefix_cache_queries_total{engine=\"0\"} 20
unrelated_metric 999
"""
    )
    assert result == {
        'vllm:prefix_cache_hits_total{engine="0"}': 12.0,
        'vllm:prefix_cache_hits_total{engine="1"}': 13.0,
        'vllm:prefix_cache_queries_total{engine="0"}': 20.0,
    }


def test_parse_metrics_fails_closed_without_hit_counter():
    with pytest.raises(ValueError, match="absent"):
        parse_metrics("vllm:request_success_total 1\n")


def test_parse_metrics_rejects_duplicate_series():
    with pytest.raises(ValueError, match="duplicate"):
        parse_metrics(
            "vllm:prefix_cache_hits_total 1\n"
            "vllm:prefix_cache_hits_total 2\n"
        )
