import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r24_exclusive_normalization_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r24_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r24_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == (
        "kernel-block-normalization-exclusive-v12r24"
    )
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_kernel_normalization_v12r24_20260918"
    )
    assert (
        trial.controller.PLUGIN_MODE
        == "physical-cache-native-all-heads-state-index"
    )


def test_v12r24_keeps_v12r23_identity_capture():
    result = trial.trial.trial.trial.process_identity(999999999)
    assert result["pid"] == 999999999
    assert result["vanished_before_identity_capture"] is True
