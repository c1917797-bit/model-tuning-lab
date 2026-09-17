import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r19_npu0_3_branch_evidence_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r19_npu0_3_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r19_npu0_3_has_distinct_lane_identity():
    assert trial.controller.NPUS == (0, 1, 2, 3)
    assert trial.controller.RESULT.name == (
        "branch-evidence-all-heads-v12r19-npu0-3"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_branch_evidence_v12r19_npu0_3_20260917"
    )


def test_v12r19_npu0_3_delegates_to_unchanged_candidate(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 31)
    assert trial.main() == 31
