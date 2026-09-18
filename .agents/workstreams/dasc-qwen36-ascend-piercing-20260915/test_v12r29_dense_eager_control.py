import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_v12r29_dense_eager_control.py")
SPEC = importlib.util.spec_from_file_location("run_v12r29_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r29_is_a_dense_eager_one_variable_control():
    assert trial.controller.RESULT.name == "dense-eager-exact-prefix-control-v12r29"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_dense_eager_exact_v12r29_20260918"
    )
    assert trial.controller.PLUGIN_MODE == "compat-head256"
    assert trial.controller.PREVIOUS_CANARY.name == (
        "run_dense_eager_replay_probe.py"
    )
    assert trial.controller.CANARY_EXTRA_ARGS == ()
    assert trial.controller.ENFORCE_EAGER is True
    assert set(trial.DISABLED_TREATMENT_VERDICTS) == {
        "validate_all_heads_evidence",
        "validate_branch_evidence",
        "validate_state_index_evidence",
    }


def test_v12r29_keeps_eager_launch_and_disables_dasc_treatment(monkeypatch):
    captured = []

    def fake_run(args, **kwargs):
        captured.append(list(args))
        return "container-id\n"

    monkeypatch.setattr(trial.controller, "run", fake_run)
    assert trial.controller.launch() == "container-id"
    args = captured[-1]
    assert "--enforce-eager" in args
    assert "--compilation-config" not in args
    assert "MST_DASC_MODE=compat-head256" in args


def test_v12r29_main_delegates_to_guarded_controller(monkeypatch):
    monkeypatch.setattr(trial.trial, "main", lambda: 41)
    assert trial.main() == 41
