import importlib.util
from pathlib import Path


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
