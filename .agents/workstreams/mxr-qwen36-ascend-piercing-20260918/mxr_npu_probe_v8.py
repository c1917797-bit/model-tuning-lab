#!/usr/bin/env python3
"""Candidate-only MXR numerical gate after v0.23 baseline ABI isolation."""
from __future__ import annotations

from datetime import datetime, timezone
import os

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs explicit baseline context


BASE_LOAD_IMPLEMENTATIONS = probe.load_implementations
CANDIDATES = ("pto_staged", "pto_mega")


def load_candidate_implementations():
    torch, RefGDN, tri_inverse, baseline_solve, methods = BASE_LOAD_IMPLEMENTATIONS()
    selected = {name: methods[name] for name in CANDIDATES}
    return torch, RefGDN, tri_inverse, baseline_solve, selected


probe.load_implementations = load_candidate_implementations


if __name__ == "__main__":
    output_dir = v3.output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")

    # Match the v0.23 worker bootstrap order even though this phase only runs
    # the official PTO candidates. This keeps the runtime evidence comparable.
    from vllm_ascend.utils import bootstrap_custom_op_env, enable_custom_op

    bootstrap_custom_op_env()
    custom_opp_path = os.environ.get("ASCEND_CUSTOM_OPP_PATH", "")
    if not custom_opp_path:
        raise RuntimeError("ASCEND_CUSTOM_OPP_PATH was not established before device initialization")

    v3.run_canary(output_dir)

    import torch
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton

    custom_ops_enabled = bool(enable_custom_op())
    init_device_properties_triton()
    bootstrap = {
        "schema": "mst.mxr.candidate-bootstrap/v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "custom_opp_path": custom_opp_path,
        "custom_ops_enabled": custom_ops_enabled,
        "candidates": list(CANDIDATES),
        "ok": custom_ops_enabled,
    }
    probe.atomic_json(output_dir / "worker-bootstrap.json", bootstrap)
    if not bootstrap["ok"]:
        raise RuntimeError(f"v0.23 worker bootstrap incomplete: {bootstrap}")

    raise SystemExit(probe.main())
