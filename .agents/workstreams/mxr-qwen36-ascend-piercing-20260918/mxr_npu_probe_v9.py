#!/usr/bin/env python3
"""All-method numerical gate with the v0.23 BF16-state ABI adapter."""
from __future__ import annotations

from datetime import datetime, timezone
import os

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs explicit baseline context


BASE_LOAD_IMPLEMENTATIONS = probe.load_implementations


def load_abi_compatible_implementations():
    torch, RefGDN, tri_inverse, baseline_solve, methods = BASE_LOAD_IMPLEMENTATIONS()
    raw_v023 = methods["v023_triton"]

    def v023_bf16_state(q, k, v, g, beta, cu32, state):
        # The shipped AscendC binary selected by chunk.py's BF16 k/w/u path
        # requires FP32 g and BF16 initial_state. Keep the returned state BF16
        # across chained steps, matching the configured service cache dtype.
        return raw_v023(q, k, v, g, beta, cu32, state.to(torch.bfloat16))

    methods["v023_triton"] = v023_bf16_state
    return torch, RefGDN, tri_inverse, baseline_solve, methods


probe.load_implementations = load_abi_compatible_implementations


if __name__ == "__main__":
    output_dir = v3.output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")

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
    required_ops = ("chunk_gated_delta_rule_fwd_h", "chunk_fwd_o")
    registered = {name: hasattr(torch.ops._C_ascend, name) for name in required_ops}
    bootstrap = {
        "schema": "mst.mxr.v023-worker-bootstrap/v3",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "custom_opp_path": custom_opp_path,
        "custom_ops_enabled": custom_ops_enabled,
        "required_ops": registered,
        "baseline_state_dtype": "bfloat16",
        "ok": custom_ops_enabled and all(registered.values()),
    }
    probe.atomic_json(output_dir / "worker-bootstrap.json", bootstrap)
    if not bootstrap["ok"]:
        raise RuntimeError(f"v0.23 worker bootstrap incomplete: {bootstrap}")

    raise SystemExit(probe.main())
