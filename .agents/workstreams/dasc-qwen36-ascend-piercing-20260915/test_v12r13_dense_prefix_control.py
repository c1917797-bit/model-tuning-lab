from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_v12r13_dense_prefix_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r13_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r13_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == "dense-exact-prefix-control-v12r13"
    assert trial.controller.CONTAINER == "dasc_qwen36_dense_exact_prefix_v12r13_20260916"
    assert trial.controller.PLUGIN_MODE == "compat-head256"
    assert trial.controller.PREVIOUS_CANARY.name == "run_dense_replay_probe.py"


def test_v12r13_main_delegates_to_dense_controller(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 29)
    assert trial.main() == 29
