from __future__ import annotations

import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_qwen35_mmar_async_finalize.py"
)
SPEC = importlib.util.spec_from_file_location("qwen35_mmar_benchmark", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@contextmanager
def candidate_environment(enabled: tuple[str, ...]):
    previous = {name: os.environ.get(name) for name in MODULE.CANDIDATE_FEATURE_ENVS}
    try:
        for name in MODULE.CANDIDATE_FEATURE_ENVS:
            os.environ.pop(name, None)
        for name in enabled:
            os.environ[name] = "1"
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def assert_exactly_one_error() -> None:
    try:
        MODULE.require_single_candidate_feature()
    except RuntimeError as error:
        assert "exactly one" in str(error)
    else:
        raise AssertionError("missing exactly-one feature error")


def test_accepts_each_supported_candidate_feature() -> None:
    for feature in MODULE.CANDIDATE_FEATURE_ENVS:
        with candidate_environment((feature,)):
            assert MODULE.require_single_candidate_feature() == feature


def test_rejects_missing_candidate_feature() -> None:
    with candidate_environment(()):
        assert_exactly_one_error()


def test_rejects_multiple_candidate_features() -> None:
    with candidate_environment(tuple(MODULE.CANDIDATE_FEATURE_ENVS)):
        assert_exactly_one_error()


if __name__ == "__main__":
    test_accepts_each_supported_candidate_feature()
    test_rejects_missing_candidate_feature()
    test_rejects_multiple_candidate_features()
    print("PASS: MMAR candidate feature gate without pytest")
