import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r25_ascend_block_scale_control.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r25_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r25_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == "ascend-block-scale-v12r25"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_ascend_block_scale_v12r25_20260918"
    )
    assert (
        trial.controller.PLUGIN_MODE
        == "physical-cache-native-all-heads-state-index"
    )
