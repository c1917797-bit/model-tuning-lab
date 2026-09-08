#!/usr/bin/env python3
"""Device-free integrity and activation contract for the standalone patch."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8"


def main() -> int:
    patch = ROOT / "sitecustomize.py"
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256

    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["sitecustomize_sha256"] == digest
    assert manifest["status"] == "accepted_for_c1_ttft_40pct_only"
    assert any("32-sample" in item for item in manifest["limitations"])

    environment = os.environ.copy()
    environment.update(manifest["activation"])
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sitecustomize; "
                "assert sitecustomize.__file__.endswith('/sitecustomize.py'); "
                "print('activation_import_ok')"
            ),
        ],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == "activation_import_ok"
    assert "import hooks installed" in completed.stderr

    check = subprocess.run(
        [sys.executable, "-m", "qwen35_vllm_ascend_patch"],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    check_result = json.loads(check.stdout)
    assert check_result["sha256"] == EXPECTED_SHA256
    assert check_result["activation_requested"] is True
    print("PASS: standalone Qwen3.5 runtime patch contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
