from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name(
    "run_v12r18_mixed_lifecycle_fix_control.py"
)
SPEC = importlib.util.spec_from_file_location("run_v12r18_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r18_keeps_native_all_heads_and_uses_new_identity():
    assert trial.controller.RESULT.name == "mixed-lifecycle-fix-all-heads-v12r18"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_mixed_lifecycle_v12r18_20260916"
    )
    assert trial.controller.PLUGIN_MODE == "physical-cache-native-all-heads"
    assert trial.controller.W_MAX == "1e-9"
    assert trial.controller.PREVIOUS_CANARY == MODULE_PATH.with_name(
        "run_physical_canary.py"
    )


def test_v12r18_main_delegates(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 43)
    assert trial.main() == 43
