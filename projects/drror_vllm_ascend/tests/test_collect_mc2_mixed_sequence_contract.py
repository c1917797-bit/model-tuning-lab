"""Path and candidate contract tests for the mixed-sequence collector."""
import importlib.util
from pathlib import Path


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
