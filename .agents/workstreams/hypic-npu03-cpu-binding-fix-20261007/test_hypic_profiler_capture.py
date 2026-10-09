#!/usr/bin/env python3
"""Offline contract checks for the bounded profiler controller."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module():
    path = HERE / "hypic_profiler_capture.py"
    spec = importlib.util.spec_from_file_location("hypic_profiler_capture", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_transformed_spec_is_profiler_only_delta() -> None:
    module = load_module()
    _, binds, env, command = module.transformed_spec("decode")
    assert module.MIN_DECODE_CHUNKS >= 10
    assert command.count("--profiler-config") == 1
    assert '"profiler":"torch"' in command
    assert '"torch_profiler_with_stack":false' in command
    assert "/profiler-hypic-hotcold-20261009-r5/decode/profiles" in command
    assert "--additional-config '{\"enable_cpu_binding\":false}'" in command
    assert "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3" in env
    assert any(item.startswith("ASCEND_PROFILER_OUTPUT=") for item in env)
    assert "/cache/cch/hypic-npu03-cpu-binding-fix-20261007:/results" in binds


def test_preregistered_phase_names_are_disjoint() -> None:
    module = load_module()
    assert module.phase_name("prefill") != module.phase_name("decode")
    assert module.profiler_config(Path("prefill"))["torch_profiler_dir"] != module.profiler_config(Path("decode"))["torch_profiler_dir"]
