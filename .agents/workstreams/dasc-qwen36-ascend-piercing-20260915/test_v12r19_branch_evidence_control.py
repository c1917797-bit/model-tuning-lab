import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("run_v12r19_branch_evidence_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r19_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r19_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == "branch-evidence-all-heads-v12r19"
    assert trial.controller.CONTAINER == "dasc_qwen36_branch_evidence_v12r19_20260917"
    assert trial.controller.PLUGIN_MODE == "physical-cache-native-all-heads"


def test_v12r19_delegates_to_v12r18(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 29)
    assert trial.main() == 29


def complete_rows():
    rows = [
        {
            "event": "scheduler_mamba_lifecycle_initialized",
            "pid": 10,
            "has_mamba_layers": True,
            "need_mamba_block_aligned_split": True,
            "needs_kv_cache_zeroing": True,
            "block_size": 64,
        },
        {
            "event": "scheduler_mamba_aligned_split_executed",
            "pid": 10,
            "requested_tokens": 1938,
            "scheduled_tokens": 1920,
            "changed": True,
        },
        {
            "event": "scheduler_kv_zeroing_branch_executed",
            "pid": 10,
            "new_block_count": 31,
            "nonempty": True,
        },
    ]
    rows.extend(
        {
            "event": "heterogeneous_mamba_copy_branch_executed",
            "pid": pid,
            "mamba_layer_count": 48,
            "copy_entries_added": 96,
        }
        for pid in (21, 22, 23, 24)
    )
    return rows


def test_branch_verdict_separates_lifecycle_success_from_numerical_failure():
    result = trial.branch_evidence_verdict(complete_rows(), {"ok": False})
    assert result["branch_evidence_ok"] is True
    assert result["numerical_canary_ok"] is False
    assert result["overall_ok"] is False
    assert result["mamba_copy_worker_pids"] == [21, 22, 23, 24]
    assert "localize_physical_rows" in result["decision"]


def test_branch_verdict_rejects_incomplete_tp_copy_coverage():
    rows = [row for row in complete_rows() if row.get("pid") != 24]
    result = trial.branch_evidence_verdict(rows, {"ok": True})
    assert result["branch_evidence_ok"] is False
    assert result["overall_ok"] is False
    assert result["decision"] == (
        "mamba_copy_branch_missing_or_incomplete_tp_coverage"
    )


def test_numerical_failure_still_writes_branch_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(trial.controller, "RESULT", tmp_path)
    (tmp_path / "evidence.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in complete_rows()),
        encoding="utf-8",
    )
    (tmp_path / "physical-canary.json").write_text(
        json.dumps({"ok": False}), encoding="utf-8"
    )

    def fail():
        raise RuntimeError("strict numerical gate failed")

    monkeypatch.setattr(trial.trial, "main", fail)
    with pytest.raises(RuntimeError, match="strict numerical gate failed"):
        trial.main()

    result = json.loads(
        (tmp_path / "branch-evidence-verdict.json").read_text(encoding="utf-8")
    )
    assert result["branch_evidence_ok"] is True
    assert result["overall_ok"] is False
    assert not (tmp_path / "branch-evidence-verdict-error.txt").exists()
    manifest = json.loads(
        (tmp_path / "artifacts.sha256.json").read_text(encoding="utf-8")
    )
    assert "branch-evidence-verdict.json" in manifest
    assert "artifacts.sha256.json" not in manifest
