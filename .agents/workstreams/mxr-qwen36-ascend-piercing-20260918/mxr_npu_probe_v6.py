#!/usr/bin/env python3
"""MXR gate with the complete v0.23 standalone worker bootstrap."""
from __future__ import annotations

from datetime import datetime, timezone

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs explicit baseline context


if __name__ == "__main__":
    output_dir = v3.output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")
    v3.run_canary(output_dir)

    import torch
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton
    from vllm_ascend.utils import enable_custom_op

    custom_ops_enabled = bool(enable_custom_op())
    init_device_properties_triton()
    required_ops = ("chunk_gated_delta_rule_fwd_h", "chunk_fwd_o")
    registered = {
        name: hasattr(torch.ops._C_ascend, name) for name in required_ops
    }
    bootstrap = {
        "schema": "mst.mxr.v023-worker-bootstrap/v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "custom_ops_enabled": custom_ops_enabled,
        "required_ops": registered,
        "ok": custom_ops_enabled and all(registered.values()),
    }
    probe.atomic_json(output_dir / "worker-bootstrap.json", bootstrap)
    if not bootstrap["ok"]:
        raise RuntimeError(f"v0.23 worker bootstrap incomplete: {bootstrap}")

    raise SystemExit(probe.main())
