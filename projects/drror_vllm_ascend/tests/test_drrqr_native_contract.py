"""Software-only contract checks for the plugin-owned native control op."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OP_ROOT = ROOT / "native" / "drrqr_recurrent_layout_control_v1"


def load_build_tool():
    path = ROOT / "tools" / "build_drrqr_native.py"
    spec = importlib.util.spec_from_file_location("build_drrqr_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_control_has_unique_public_names():
    source = "\n".join(
        path.read_text()
        for path in OP_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".cpp", ".h", ".txt"}
    )
    assert "DrrqrRecurrentLayoutControlV1" in source
    assert "aclnnDrrqrRecurrentLayoutControlV1GetWorkspaceSize" in source
    assert "aclnnDrrqrRecurrentLayoutControlV1(" in source
    assert "RecurrentGatedDeltaRule" not in source
    assert "recurrent_gated_delta_rule" not in source


def test_all_header_guards_are_isolated_from_upstream_name():
    headers = list(OP_ROOT.rglob("*.h"))
    guards = "\n".join(path.read_text() for path in headers)
    assert "RECURRENT_GATED_DELTA_RULE" not in guards
    assert "RECURRENT_GETED_DELTA_RULE" not in guards


def test_mutable_state_is_preserved_in_aclnn_and_torch_adapter():
    api = (
        OP_ROOT / "op_host/op_api/aclnn_drrqr_recurrent_layout_control_v1.h"
    ).read_text()
    adapter = (
        OP_ROOT / "drrqr_recurrent_layout_control_v1_torch_adpt.h"
    ).read_text()
    assert "aclTensor *stateRef" in api
    assert "at::Tensor& state" in adapter
    assert "EXEC_NPU_CMD(aclnnDrrqrRecurrentLayoutControlV1" in adapter


def test_provenance_and_builder_pin_same_frozen_commit():
    tool = load_build_tool()
    provenance = json.loads((OP_ROOT / "provenance.json").read_text())
    assert provenance["source_commit"] == tool.REFERENCE_COMMIT
    assert len(provenance["source_sha256"]) == 17
    assert all(len(value) == 64 for value in provenance["source_sha256"].values())


def test_results_path_translation_is_bounded():
    tool = load_build_tool()
    output = tool.HOST_RESULTS_ROOT / "native-control" / "build-v1"
    assert str(tool.result_path(output)) == "/drrqr-results/native-control/build-v1"
    try:
        tool.result_path(Path("/tmp/out"))
    except ValueError:
        pass
    else:
        raise AssertionError("unmounted output path was accepted")


def test_copy_filter_keeps_nested_output_source_directories(tmp_path):
    tool = load_build_tool()
    source = tmp_path / "csrc"
    source.mkdir()
    top_names = ["build", "build_out", "output", "__pycache__", "attention"]
    nested = source / "third_party/json/include/nlohmann/detail"
    nested.mkdir(parents=True)
    assert tool.copy_ignore(source)(str(source), top_names) == {
        "build", "build_out", "output", "__pycache__"
    }
    assert tool.copy_ignore(source)(str(nested), ["input", "output"]) == set()
