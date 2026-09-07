#!/usr/bin/env python3
"""Device-free contract test for the deferred Ascend monkeypatch activation."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType


PATCH_PATH = Path(__file__).with_name("sitecustomize.py")
REGISTRY_NAME = "vllm.model_executor.models.registry"


class _LazyRegisteredModel:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def inspect_model_cls(self):
        if self.fail:
            raise RuntimeError("synthetic inspection failure")
        return "inspected"


def _load_patch_module():
    registry = ModuleType(REGISTRY_NAME)
    registry._LazyRegisteredModel = _LazyRegisteredModel
    sys.modules[REGISTRY_NAME] = registry
    os.environ["QWEN35_ASCEND_MONKEYPATCH"] = "1"
    spec = importlib.util.spec_from_file_location(
        "_qwen35_deferred_activation_probe", PATCH_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = _load_patch_module()
    assert module._ENABLED
    assert not module._RUNTIME_ACTIVE
    assert module._TARGETS == {REGISTRY_NAME}

    try:
        _LazyRegisteredModel(fail=True).inspect_model_cls()
    except RuntimeError as exc:
        assert str(exc) == "synthetic inspection failure"
    else:
        raise AssertionError("synthetic inspection failure was swallowed")
    assert not module._RUNTIME_ACTIVE
    assert module._TARGETS == {REGISTRY_NAME}

    assert _LazyRegisteredModel().inspect_model_cls() == "inspected"
    assert module._RUNTIME_ACTIVE
    assert module._RUNTIME_TARGETS <= module._TARGETS

    assert _LazyRegisteredModel().inspect_model_cls() == "inspected"
    assert module._RUNTIME_ACTIVE
    print("PASS: runtime hooks activate only after successful model inspection")


if __name__ == "__main__":
    main()
