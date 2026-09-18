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
    assert trial.controller.CONTAINER == "alltoall-dedup-ep4_nk"
    assert trial.REUSED_CONTAINER_ID.startswith("fd2be986b54d")
    assert (
        trial.controller.PLUGIN_MODE
        == "physical-cache-native-all-heads-state-index"
    )


def test_v12r24_keeps_v12r23_identity_capture():
    result = trial.trial.trial.trial.process_identity(999999999)
    assert result["pid"] == 999999999
    assert result["vanished_before_identity_capture"] is True


def test_reuse_identity_rejects_non_quiescent_process_tree(monkeypatch):
    item = {
        "Id": trial.REUSED_CONTAINER_ID,
        "Image": trial.controller.IMAGE_ID,
        "State": {"Running": True},
        "HostConfig": {"Privileged": True, "Devices": []},
        "Mounts": [
            {
                "Source": "/cache",
                "Destination": "/cache",
                "RW": True,
            }
        ],
    }

    def fake_run(args, **_kwargs):
        assert args[1:3] == ["top", trial.controller.CONTAINER]
        return "PID PPID CMD\n1 0 sleep infinity\n2 1 python foreign.py\n"

    monkeypatch.setattr(trial.controller, "run", fake_run)
    blockers = trial._reused_container_identity_blockers(item)
    assert any("not quiescent" in blocker for blocker in blockers)
