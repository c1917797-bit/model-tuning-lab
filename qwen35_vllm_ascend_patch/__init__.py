"""Installation and integrity helpers for the Qwen3.5 runtime patch."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path


__version__ = "0.2.0"
EXPECTED_SHA256 = "aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b"


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
