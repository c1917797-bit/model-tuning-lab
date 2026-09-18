import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_dense_eager_replay_probe.py")
SPEC = importlib.util.spec_from_file_location("dense_eager_probe_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def test_exact_verified_requires_exact_stop_without_reasoning():
    good = {
        "content": "VERIFIED",
        "finish_reason": "stop",
        "reasoning_content": None,
    }
    assert probe.exact_verified(good)
    assert not probe.exact_verified({**good, "content": "VERIFIED."})
    assert not probe.exact_verified({**good, "finish_reason": "length"})
    assert not probe.exact_verified({**good, "reasoning_content": "hidden"})
