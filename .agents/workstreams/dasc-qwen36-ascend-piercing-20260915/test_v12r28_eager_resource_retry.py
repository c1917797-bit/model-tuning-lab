import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "run_v12r28_eager_resource_retry.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_v12r28_under_test", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
trial = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trial)


def test_v12r28_changes_only_immutable_run_identity():
    assert trial.controller.RESULT.name == "state-index-eager-boundary-v12r28"
    assert trial.controller.CONTAINER == (
        "dasc_qwen36_state_index_eager_boundary_v12r28_20260918"
    )
    assert trial.controller.ENFORCE_EAGER is True
    assert (
        trial.controller.PLUGIN_MODE
        == "physical-cache-native-all-heads-state-index"
    )


def test_v12r28_still_omits_graph_compilation(monkeypatch):
    captured = []

    def fake_run(args, **kwargs):
        captured.append(list(args))
        return "container-id\n"

    monkeypatch.setattr(trial.controller, "run", fake_run)
    assert trial.controller.launch() == "container-id"
    args = captured[-1]
    assert "--enforce-eager" in args
    assert "--compilation-config" not in args
