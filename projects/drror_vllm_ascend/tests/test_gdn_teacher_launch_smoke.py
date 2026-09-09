"""Five bounded software checks; distributed/NPU calls are mocked, never executed."""
import ast
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def harness(tmp_path, monkeypatch):
    smoke = import_file("isolated_teacher_smoke", ROOT / "tools/gdn_teacher_launch_smoke.py")
    launcher = import_file("isolated_smoke_teacher_launcher", ROOT / "tools/run_gdn_teacher_capture.py")
    monkeypatch.setitem(sys.modules, "run_gdn_teacher_capture", launcher)
    # Redirect only the hard-coded results root, keeping all artifact paths and
    # exclusive filesystem operations real within pytest's temporary directory.
    monkeypatch.setattr(smoke, "Path", lambda value: tmp_path if str(value) == "/drrqr-results" else Path(value))
    monkeypatch.setenv("ASCEND_RT_VISIBLE_DEVICES", "0,1,2,3")
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.delenv("DRRQR_DIAGNOSTIC_DETERMINISM", raising=False)
    manifest = tmp_path / "capture.json"
    manifest.write_text('{"schema":"mock-control-only"}')
    calls = []
    lifecycle_source = inspect.getsource(launcher.shared.run_service)

    def run(command, env, output, budget, grace):
        calls.append((command, env, output, budget, grace))
        for rank in range(4):
            smoke.write_json(output / f"rank{rank}.json", {
                "status": "passed", "rank": rank, "reduction": [10.0] * 16,
            })
        return 0

    monkeypatch.setattr(launcher.shared, "run_service", run)
    args = [
        "--output-dir", str(tmp_path / "smoke"), "--service-output-dir", str(tmp_path / "service"),
        "--capture-manifest", str(manifest), "--capture-manifest-sha256", smoke.digest(manifest),
        "--launcher-sha256", smoke.digest(ROOT / "tools/run_gdn_teacher_capture.py"),
    ]
    return SimpleNamespace(smoke=smoke, launcher=launcher, root=tmp_path, calls=calls,
                           args=args, lifecycle_source=lifecycle_source)


def test_shared_environment_removes_native_overrides_and_controller_rejects_leak(harness, monkeypatch):
    h = harness
    monkeypatch.setenv("HCCL_DETERMINISTIC", "0")
    monkeypatch.setenv("LCCL_DETERMINISTIC", "1")
    assert h.smoke.main(h.args) == 0
    env = h.calls[0][1]
    assert "HCCL_DETERMINISTIC" not in env and "LCCL_DETERMINISTIC" not in env
    doc = json.loads((h.root / "smoke/manifest.json").read_text())
    assert doc["inherited_runtime_environment"]["HCCL_DETERMINISTIC"] == "0"
    original = h.launcher.service_environment
    def leaking(*args, **kwargs):
        env, disabled, observer, inherited = original(*args, **kwargs)
        env["LCCL_DETERMINISTIC"] = "0"
        return env, disabled, observer, inherited
    monkeypatch.setattr(h.launcher, "service_environment", leaking)
    args = list(h.args)
    args[1] = str(h.root / "smoke-leak")
    with pytest.raises(ValueError, match="remove invalid native overrides"):
        h.smoke.main(args)
    assert len(h.calls) == 1 and not (h.root / "smoke-leak").exists()


def test_controller_reuses_single_bounded_independent_session_lifecycle(harness):
    h = harness
    assert h.smoke.main(h.args) == 0
    assert len(h.calls) == 1
    command, _, output, budget, grace = h.calls[0]
    assert (budget, grace) == (120, 10)
    assert command[:3] == [sys.executable, "-m", "torch.distributed.run"]
    assert "--standalone" in command and "--nnodes=1" in command and "--nproc-per-node=4" in command
    assert command[-3:] == ["--worker", "--output-dir", str(output)]
    # Verify the reused implementation retains its independent-session launch;
    # no subprocess is started by this software test.
    tree = ast.parse(h.lifecycle_source)
    popen = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "Popen"]
    assert len(popen) == 1
    assert any(k.arg == "start_new_session" and isinstance(k.value, ast.Constant)
               and k.value.value is True for k in popen[0].keywords)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "passed" and [x["rank"] for x in report["ranks"]] == list(range(4))


def test_existing_output_or_service_directory_cannot_be_overwritten(harness):
    h = harness
    output = h.root / "smoke"
    output.mkdir()
    marker = output / "prior-evidence"
    marker.write_text("preserve")
    with pytest.raises(ValueError, match="fresh absolute smoke output"):
        h.smoke.main(h.args)
    assert not h.calls and marker.read_text() == "preserve"
    args = list(h.args)
    args[1] = str(h.root / "fresh-smoke")
    (h.root / "service").mkdir()
    with pytest.raises(ValueError, match="fresh distinct intended service"):
        h.smoke.main(args)
    assert not h.calls and not (h.root / "fresh-smoke").exists()


def install_fake_npu(monkeypatch, *, reduction=10.0):
    calls = []
    torch = ModuleType("torch")
    torch.__path__ = []
    torch.__version__ = "mock"
    torch.float32 = "torch.float32"
    torch.npu = SimpleNamespace(set_device=lambda rank: calls.append(("device", rank)),
                                synchronize=lambda: calls.append(("synchronize",)))
    class Values:
        def __init__(self, shape, fill, dtype, device):
            self.shape, self.values, self.dtype, self.device = shape, [float(fill)] * shape[0], dtype, device
        def cpu(self):
            return self
        def tolist(self):
            return self.values
    def full(shape, fill, dtype, device):
        calls.append(("full", shape, fill, dtype, device))
        return Values(shape, fill, dtype, device)
    torch.full = full
    dist = ModuleType("torch.distributed")
    def init(backend, timeout):
        calls.append(("init", backend, timeout.total_seconds()))
    def all_reduce(values):
        calls.append(("reduce",))
        values.values[:] = [reduction] * 16
    dist.init_process_group = init
    dist.all_reduce = all_reduce
    dist.destroy_process_group = lambda: calls.append(("destroy",))
    torch.distributed = dist
    npu = ModuleType("torch_npu")
    npu.__version__, npu.__file__ = "mock", str(Path(__file__))
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch.distributed", dist)
    monkeypatch.setitem(sys.modules, "torch_npu", npu)
    return calls


def test_four_rank_fixed_fp32_reduction_and_worker_override_rejection(harness, monkeypatch):
    h = harness
    calls = install_fake_npu(monkeypatch)
    monkeypatch.setenv("WORLD_SIZE", "4")
    for name in ("HCCL_DETERMINISTIC", "LCCL_DETERMINISTIC"):
        monkeypatch.delenv(name, raising=False)
    for rank in range(4):
        monkeypatch.setenv("RANK", str(rank))
        monkeypatch.setenv("LOCAL_RANK", str(rank))
        h.smoke.communication_worker(h.root)
        report = json.loads((h.root / f"rank{rank}.json").read_text())
        assert report["status"] == "passed" and report["reduction"] == [10.0] * 16
        assert report["world_size"] == 4 and report["rank"] == report["local_rank"] == rank
    assert [c for c in calls if c[0] == "full"] == [
        ("full", (16,), rank + 1, "torch.float32", f"npu:{rank}") for rank in range(4)]
    assert [c for c in calls if c[0] == "init"] == [("init", "hccl", 45.0)] * 4
    assert len([c for c in calls if c[0] == "destroy"]) == 4
    previous = list(calls)
    monkeypatch.setenv("HCCL_DETERMINISTIC", "false")
    with pytest.raises(ValueError, match="overrides must be absent"):
        h.smoke.communication_worker(h.root)
    assert calls == previous


def test_failure_is_recorded_and_never_retried(harness, monkeypatch):
    h = harness
    starts = []
    def failed(*args):
        starts.append(args)
        return 7
    monkeypatch.setattr(h.launcher.shared, "run_service", failed)
    assert h.smoke.main(h.args) == 7
    assert len(starts) == 1
    report = json.loads((h.root / "smoke/report.json").read_text())
    assert report["status"] == "failed" and report["process_exit_code"] == 7
    assert report["ranks"] == []

    calls = install_fake_npu(monkeypatch, reduction=9.0)
    monkeypatch.setenv("RANK", "0")
    monkeypatch.setenv("LOCAL_RANK", "0")
    monkeypatch.setenv("WORLD_SIZE", "4")
    monkeypatch.delenv("HCCL_DETERMINISTIC", raising=False)
    monkeypatch.delenv("LCCL_DETERMINISTIC", raising=False)
    with pytest.raises(RuntimeError, match="all_reduce output mismatch"):
        h.smoke.communication_worker(h.root)
    assert len([c for c in calls if c[0] == "init"]) == 1
    assert len([c for c in calls if c[0] == "reduce"]) == 1
    assert len([c for c in calls if c[0] == "destroy"]) == 1
    worker_report = json.loads((h.root / "rank0.json").read_text())
    assert worker_report["status"] == "failed" and "all_reduce output mismatch" in worker_report["error"]

