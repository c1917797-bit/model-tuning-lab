"""Import helpers for scripts stored below a hyphenated directory."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_checker():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "check_qwen35_gdn_t12_activation.py"
    )
    spec = importlib.util.spec_from_file_location("qwen35_gdn_t12_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
