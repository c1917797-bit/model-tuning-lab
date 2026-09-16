#!/usr/bin/env python3
"""Run the request-owned DASC v12r7 canary through the audited controller."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ENGINE = HERE / "run_v12r6_once.py"
REQUIRED_CORE_COMMIT = "e064564"

spec = importlib.util.spec_from_file_location("dasc_v12_controller", ENGINE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load controller engine: {ENGINE}")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)

controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "request-owned-active-state-v12r7"
)
controller.CONTAINER = "dasc_qwen36_request_owned_v12r7_20260916"
controller.SUPERSEDED_REASON = None


def main() -> int:
    subprocess.run(
        [
            "/usr/bin/git",
            "merge-base",
            "--is-ancestor",
            REQUIRED_CORE_COMMIT,
            "HEAD",
        ],
        cwd=controller.REPO,
        check=True,
    )
    return controller.main()


if __name__ == "__main__":
    raise SystemExit(main())
