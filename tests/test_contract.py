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
EXPECTED_SHA256 = "aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b"


def main() -> int:
    patch = ROOT / "sitecustomize.py"
    digest = hashlib.sha256(patch.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256

    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["sitecustomize_sha256"] == digest
    assert manifest["status"] == "offline_contracts_passed_live_validation_pending"
    assert "bounded MMAR prefill decomposition" in manifest["excluded_historical_paths"]
    assert manifest["activation"]["VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS"] == "1"

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
                "from pathlib import Path; import sitecustomize; "
                "assert Path(sitecustomize.__file__).name == 'sitecustomize.py'; "
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
