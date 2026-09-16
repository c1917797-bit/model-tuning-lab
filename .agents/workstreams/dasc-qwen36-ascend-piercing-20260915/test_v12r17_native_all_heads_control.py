from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name(
    "run_v12r17_native_all_heads_control.py"
)
SPEC = importlib.util.spec_from_file_location("run_v12r17_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r17_uses_native_all_heads_mode_and_new_identity():
    assert trial.controller.RESULT.name == "native-all-heads-control-v12r17"
    assert trial.controller.CONTAINER == "dasc_qwen36_native_all_heads_v12r17_20260916"
    assert trial.controller.PLUGIN_MODE == "physical-cache-native-all-heads"
    assert trial.controller.W_MAX == "1e-9"
    assert trial.controller.PREVIOUS_CANARY == MODULE_PATH.with_name(
        "run_physical_canary.py"
    )


def test_v12r17_main_delegates(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 41)
    assert trial.main() == 41
