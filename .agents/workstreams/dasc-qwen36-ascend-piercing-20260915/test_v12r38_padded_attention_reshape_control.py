import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r38_padded_attention_reshape_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r38_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def _row(event: str, pid: int, layer: int) -> dict:
    blocks = 95
    padded = 1_588_224
    real = 1_572_864
    return {
        "event": event,
        "pid": pid,
        "layer": f"language_model.model.layers.{layer}.self_attn",
        "num_blocks": blocks,
        "manager_num_blocks": 84,
        "padded_page_bytes": padded,
        "real_page_bytes": real,
        "allocated_split_bytes": blocks * (padded // 2),
        "logical_split_bytes": blocks * (real // 2),
        "trailing_slack_bytes_per_split": blocks * ((padded - real) // 2),
        "storage_pointer_preserved": True,
    }


def _valid_rows() -> list[dict]:
    rows = []
    attention_layers = tuple(range(3, 64, 4))
    assert len(attention_layers) == 16
    for pid in (101, 102, 103, 104):
        for layer in attention_layers:
            rows.append(_row(
                "ascend_split_padded_attention_reshape_prepared", pid, layer
            ))
            rows.append(_row(
                "ascend_split_padded_attention_reshape_adapted", pid, layer
            ))
    return rows


def test_v12r38_targets_idle_npu_lane_with_immutable_result_identity():
    assert trial.controller.NPUS == (0, 1, 2, 3)
    assert trial.controller.RESULT.name == (
        "padded-attention-reshape-npu0-3-v12r38"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_padded_attention_reshape_npu0_3_v12r38_20260918"
    )


def test_v12r38_accepts_exact_four_by_sixteen_reshape_evidence():
    verdict = trial.padded_attention_reshape_verdict(_valid_rows())
    assert verdict["ok"] is True
    assert verdict["prepared_rows"] == 64
    assert verdict["adapted_rows"] == 64
    assert verdict["exact_rows"] == 64
    assert verdict["layers_per_worker"] == {
        "101": 16,
        "102": 16,
        "103": 16,
        "104": 16,
    }


def test_v12r38_rejects_missing_adapted_row_and_bad_split_geometry():
    rows = _valid_rows()
    rows.pop()
    rows[0]["logical_split_bytes"] += 1
    verdict = trial.padded_attention_reshape_verdict(rows)
    assert verdict["ok"] is False
    assert verdict["checks"]["exact_adapted_rows"] is False
    assert verdict["checks"]["prepared_and_adapted_keys_match"] is False
    assert verdict["checks"]["every_row_has_exact_split_geometry"] is False
