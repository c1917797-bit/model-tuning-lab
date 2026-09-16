from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).with_name("run_v12r11_once.py")
SPEC = importlib.util.spec_from_file_location("run_v12r11_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r11_has_distinct_immutable_identity():
    assert trial.controller.RESULT.name == "request-owned-head256-prefill-v12r11"
    assert trial.controller.CONTAINER == "dasc_qwen36_head256_prefill_v12r11_20260916"
    assert trial.controller.ADDITIONAL_CONFIG == '{"pa_shape_list":[1,2,4,8,16]}'


def test_v12r11_main_delegates_to_inner_controller(monkeypatch):
    monkeypatch.setattr(trial.trial.trial, "main", lambda: 23)
    assert trial.main() == 23
