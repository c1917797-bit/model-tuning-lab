from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_v12r15_all_heads_bridge_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r15_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r15_has_distinct_immutable_identity_and_all_heads_gate():
    assert trial.controller.RESULT.name == "request-owned-all-heads-aligned-v12r15"
    assert trial.controller.CONTAINER == "dasc_qwen36_all_heads_aligned_v12r15_20260916"
    assert trial.controller.W_MAX == "1e-9"
    assert trial.controller.CANARY_EXTRA_ARGS == ("--allow-dense-pages",)


def test_v12r15_main_delegates_to_all_heads_controller(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 31)
    assert trial.main() == 31
