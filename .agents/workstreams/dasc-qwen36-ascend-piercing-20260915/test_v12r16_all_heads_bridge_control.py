from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_v12r16_all_heads_bridge_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r16_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r16_pins_current_canary_and_new_identity():
    assert trial.controller.RESULT.name == "request-owned-all-heads-current-canary-v12r16"
    assert trial.controller.CONTAINER == "dasc_qwen36_all_heads_current_v12r16_20260916"
    assert trial.controller.PREVIOUS_CANARY == MODULE_PATH.with_name(
        "run_physical_canary.py"
    )
    assert trial.controller.CANARY_EXTRA_ARGS == ("--allow-dense-pages",)


def test_v12r16_main_delegates(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 37)
    assert trial.main() == 37
