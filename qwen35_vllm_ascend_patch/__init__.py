"""Installation and integrity helpers for the Qwen3.5 runtime patch."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path


__version__ = "0.1.0"
EXPECTED_SHA256 = "9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8"


def main() -> int:
    spec = importlib.util.find_spec("sitecustomize")
    if spec is None or spec.origin is None:
        raise SystemExit("sitecustomize module is not installed")
    path = Path(spec.origin).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"unexpected sitecustomize module at {path}: SHA256 {digest}"
        )
    print(
        json.dumps(
            {
                "package": "qwen35-vllm-ascend-patch",
                "version": __version__,
                "sitecustomize": str(path),
                "sha256": digest,
                "activation_requested": (
                    os.getenv("QWEN35_ASCEND_MONKEYPATCH", "0") == "1"
                ),
            },
            sort_keys=True,
        )
    )
    return 0
