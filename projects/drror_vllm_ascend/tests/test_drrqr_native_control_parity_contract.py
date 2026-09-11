"""CPU-only source-contract tests; these are not NPU parity evidence."""

from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "tools/drrqr_native_control_parity.py"
)


def test_probe_compares_native_plugin_eager_and_plugin_graph():
    source = SCRIPT.read_text()
    assert "torch.ops._C_ascend.npu_recurrent_gated_delta_rule" in source
    assert "torch.ops.drrqr_ascend.recurrent_layout_control_v1" in source
    assert 'graph.replay()' in source
    assert '"eager_output_exact"' in source
    assert '"graph_output_exact"' in source


def test_probe_keeps_strict_state_storage_and_evidence_gates():
    source = SCRIPT.read_text()
    assert "view(torch.uint8)" in source
    assert '"eager_full_state_exact"' in source
    assert '"graph_full_state_exact"' in source
    assert '"guards_intact"' in source
    assert '"metadata_unchanged"' in source
    assert "reset_graph(graph, record, sys.exc_info()[1])" in source
    assert "no automatic retry" in source
    assert "not cache-manager integration" in source


def test_probe_is_bounded_to_audited_device_visibility():
    source = SCRIPT.read_text()
    assert 'ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3"' in source
    assert "logical npu:0; externally verified physical NPU4" in source
    assert '"batches": [1, 16]' in source
    assert "STEPS = 8" in source
