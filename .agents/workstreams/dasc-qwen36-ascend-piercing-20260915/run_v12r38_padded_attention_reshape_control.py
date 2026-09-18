#!/usr/bin/env python3
"""Run the dense-padding discriminator with split Ascend K/V reshape support."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r37_trial",
    HERE / "run_v12r37_npu0_3_active_nontarget_guard.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r37 idle-lane controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "padded-attention-reshape-npu0-3-v12r38"
)
controller.CONTAINER = (
    "dasc_qwen36_padded_attention_reshape_npu0_3_v12r38_20260918"
)

EXPECTED_TP_WORKERS = 4
EXPECTED_ATTENTION_LAYERS = 16


def refresh_artifact_manifest() -> None:
    module = trial
    seen = set()
    for _ in range(32):
        if module is None or id(module) in seen:
            break
        seen.add(id(module))
        state_trial = getattr(module, "state_trial", None)
        if state_trial is not None:
            state_trial.refresh_artifact_manifest()
            return
        module = getattr(module, "trial", None)
    raise RuntimeError("cannot resolve DASC artifact manifest owner")


def padded_attention_reshape_verdict(rows: list[dict]) -> dict:
    prepared = [
        row
        for row in rows
        if row.get("event")
        == "ascend_split_padded_attention_reshape_prepared"
    ]
    adapted = [
        row
        for row in rows
        if row.get("event")
        == "ascend_split_padded_attention_reshape_adapted"
    ]
    prepared_by_key = {
        (row.get("pid"), row.get("layer")): row for row in prepared
    }
    adapted_by_key = {
        (row.get("pid"), row.get("layer")): row for row in adapted
    }
    keys = set(prepared_by_key)
    pids = sorted({pid for pid, _layer in keys})
    layers_by_pid = {
        pid: sorted(layer for row_pid, layer in keys if row_pid == pid)
        for pid in pids
    }
    expected_rows = EXPECTED_TP_WORKERS * EXPECTED_ATTENTION_LAYERS

    exact_rows = []
    for key in sorted(keys):
        before = prepared_by_key[key]
        after = adapted_by_key.get(key)
        padded = before.get("padded_page_bytes")
        real = before.get("real_page_bytes")
        blocks = before.get("num_blocks")
        allocated = before.get("allocated_split_bytes")
        logical = before.get("logical_split_bytes")
        slack = before.get("trailing_slack_bytes_per_split")
        if (
            after is not None
            and isinstance(padded, int)
            and isinstance(real, int)
            and isinstance(blocks, int)
            and isinstance(allocated, int)
            and isinstance(logical, int)
            and isinstance(slack, int)
            and padded > real > 0
            and padded % 2 == 0
            and real % 2 == 0
            and blocks > 0
            and before.get("manager_num_blocks", 0) > 0
            and blocks >= before["manager_num_blocks"]
            and allocated == blocks * (padded // 2)
            and logical == blocks * (real // 2)
            and slack == allocated - logical
            and slack == blocks * ((padded - real) // 2)
            and before.get("storage_pointer_preserved") is True
            and all(
                after.get(field) == before.get(field)
                for field in (
                    "num_blocks",
                    "manager_num_blocks",
                    "padded_page_bytes",
                    "real_page_bytes",
                    "allocated_split_bytes",
                    "logical_split_bytes",
                    "trailing_slack_bytes_per_split",
                    "storage_pointer_preserved",
                )
            )
        ):
            exact_rows.append(key)

    checks = {
        "four_tp_workers": len(pids) == EXPECTED_TP_WORKERS,
        "sixteen_attention_layers_per_worker": (
            len(layers_by_pid) == EXPECTED_TP_WORKERS
            and all(
                len(layer_names) == EXPECTED_ATTENTION_LAYERS
                for layer_names in layers_by_pid.values()
            )
        ),
        "exact_prepared_rows": (
            len(prepared) == len(prepared_by_key) == expected_rows
        ),
        "exact_adapted_rows": (
            len(adapted) == len(adapted_by_key) == expected_rows
        ),
        "prepared_and_adapted_keys_match": (
            set(prepared_by_key) == set(adapted_by_key)
        ),
        "every_row_has_exact_split_geometry": len(exact_rows) == expected_rows,
    }
    return {
        "schema": "mst.dasc.v12r38-padded-attention-reshape/v1",
        "expected_tp_workers": EXPECTED_TP_WORKERS,
        "expected_attention_layers": EXPECTED_ATTENTION_LAYERS,
        "expected_rows": expected_rows,
        "prepared_rows": len(prepared),
        "adapted_rows": len(adapted),
        "exact_rows": len(exact_rows),
        "worker_pids": pids,
        "layers_per_worker": {
            str(pid): len(layer_names)
            for pid, layer_names in layers_by_pid.items()
        },
        "checks": checks,
        "ok": all(checks.values()),
    }


def validate_padded_attention_reshape_evidence() -> dict:
    rows = [
        json.loads(line)
        for line in (controller.RESULT / "evidence.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    result = padded_attention_reshape_verdict(rows)
    controller.atomic_json(
        controller.RESULT / "padded-attention-reshape-verdict.json", result
    )
    refresh_artifact_manifest()
    if not result["ok"]:
        raise RuntimeError("v12r38 padded attention reshape evidence failed")
    return result


_validate_dense_padding_evidence = controller.validate_allocation_evidence


def validate_dense_padding_and_reshape_evidence() -> dict:
    _validate_dense_padding_evidence()
    return validate_padded_attention_reshape_evidence()


controller.validate_allocation_evidence = (
    validate_dense_padding_and_reshape_evidence
)


def preserve_reshape_verdict_after_failure() -> None:
    if not (controller.RESULT / "evidence.jsonl").is_file():
        return
    try:
        validate_padded_attention_reshape_evidence()
    except Exception as error:
        (
            controller.RESULT
            / "padded-attention-reshape-verdict-error.txt"
        ).write_text(repr(error) + "\n", encoding="utf-8")
        refresh_artifact_manifest()


def main() -> int:
    try:
        exit_code = trial.main()
    except BaseException:
        preserve_reshape_verdict_after_failure()
        raise
    if "--preflight-only" in sys.argv:
        return exit_code
    if (controller.RESULT / "evidence.jsonl").is_file():
        validate_padded_attention_reshape_evidence()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
