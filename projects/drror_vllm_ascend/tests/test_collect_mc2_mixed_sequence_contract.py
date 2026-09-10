"""Path and candidate contract tests for the mixed-sequence collector."""
import importlib.util
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch


def load_collector():
    script = Path(__file__).resolve().parents[1] / "tools/collect_mc2_mixed_sequence.py"
    spec = importlib.util.spec_from_file_location("mixed_sequence_contract_collector", script)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    return collector


def test_dk80_endpoint_screen_is_an_explicit_supported_experiment():
    collector = load_collector()
    assert "dk80" in collector.VARIANTS
    assert collector.service_directory_allowed(
        Path("/drrqr-results/dk80-endpoint-screen-v1/service-dk80-packed-mixed-v4")
    )
    assert collector.service_directory_allowed(
        Path(
            "/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/"
            "dk64-energy/preflight/dk80-endpoint-screen-v1/"
            "service-dk80-packed-mixed-v4"
        )
    )


def test_unrelated_result_tree_is_rejected():
    collector = load_collector()
    assert not collector.service_directory_allowed(
        Path("/drrqr-results/unrelated/service-dk80-packed-mixed-v4")
    )


def test_mixed_cache_state_isolation_is_an_explicit_supported_experiment():
    collector = load_collector()
    assert collector.service_directory_allowed(
        Path(
            "/drrqr-results/dk80-mixed-cache-state-isolation-v1/"
            "service-dk80-packed-mixed-v1"
        )
    )


def test_http_error_preserves_prompt_identity_and_failure_body():
    collector = load_collector()
    error = HTTPError(
        "http://127.0.0.1:6666/v1/completions",
        400,
        "Bad Request",
        {},
        BytesIO(b'{"error":"non-finite response"}'),
    )
    with patch.object(collector, "urlopen", side_effect=error):
        result = collector.request(
            "http://127.0.0.1:6666",
            "frozen prompt",
            7,
            None,
            input_tokens=8,
            output_tokens=1,
        )
    assert result["ok"] is False
    assert result["index"] == 7
    assert len(result["prompt_sha256"]) == 64
    assert result["http_status"] == 400
    assert "non-finite response" in result["response_body"]
