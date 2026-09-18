import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r31_dense_page_padding_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r31_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def physical_row(pid: int, layer: int) -> dict:
    payload_page = 801792
    reserved_page = 1588224
    num_blocks = 160
    return {
        "event": "physical_cache_bound",
        "pid": pid,
        "layer": f"language_model.model.layers.{layer}.linear_attn",
        "native_all_heads": True,
        "page_padding_preserved": True,
        "dense_page_bytes": reserved_page,
        "compact_page_bytes": reserved_page,
        "payload_page_bytes": payload_page,
        "reserved_page_bytes": reserved_page,
        "padding_bytes_per_page": reserved_page - payload_page,
        "payload_fits_reserved_page": True,
        "allocation_matches_spec": False,
        "num_blocks": num_blocks,
        "payload_bytes": payload_page * num_blocks,
        "reserved_bytes": reserved_page * num_blocks,
    }


def complete_rows() -> list[dict]:
    return [
        physical_row(pid, layer)
        for pid in (21, 22, 23, 24)
        for layer in range(48)
    ]


def test_v12r31_has_distinct_identity_and_one_variable_switch():
    assert trial.controller.RESULT.name == "dense-page-padding-identity-v12r31"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_page_padding_identity_v12r31_20260918"
    )
    assert trial.controller.ENFORCE_EAGER is True
    assert trial.controller.PLUGIN_EXTRA_ENV == {
        "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS": "1",
        "MST_DASC_PRESERVE_DENSE_PAGE_PADDING": "1",
    }
    assert trial.controller.CANARY_EXTRA_ARGS == ("--allow-dense-pages",)


def test_v12r31_launch_injects_padding_control(monkeypatch):
    captured = []

    def fake_run(args, **kwargs):
        captured.append(list(args))
        return "container-id\n"

    monkeypatch.setattr(trial.controller, "run", fake_run)
    assert trial.controller.launch() == "container-id"
    args = captured[-1]
    assert "MST_DASC_PRESERVE_DENSE_PAGE_PADDING=1" in args
    assert "MST_DASC_FULL_STATE_ROW_DIAGNOSTICS=1" in args
    assert "--enforce-eager" in args
    assert "--compilation-config" not in args


def test_dense_padding_verdict_accepts_exact_cartesian_rows():
    result = trial.dense_padding_verdict(complete_rows())
    assert result["physical_rows"] == 192
    assert result["exact_rows"] == 192
    assert result["ok"] is True


def test_dense_padding_verdict_rejects_one_unpadded_layer():
    rows = complete_rows()
    rows[37]["page_padding_preserved"] = False
    result = trial.dense_padding_verdict(rows)
    assert result["ok"] is False
    assert result["checks"]["every_row_preserves_dense_padding"] is False


def test_dense_padding_verdict_rejects_duplicate_key():
    rows = complete_rows()
    rows[-1] = dict(rows[0])
    result = trial.dense_padding_verdict(rows)
    assert result["ok"] is False
    assert result["checks"]["exact_pid_layer_cartesian_rows"] is False
