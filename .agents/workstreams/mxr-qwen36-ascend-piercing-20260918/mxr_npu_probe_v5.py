#!/usr/bin/env python3
"""MXR gate with all v0.23 standalone worker prerequisites initialized."""
from __future__ import annotations

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3
import mxr_npu_probe_v4 as v4  # noqa: F401 - installs the explicit baseline context


if __name__ == "__main__":
    output_dir = v3.output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")
    v3.run_canary(output_dir)

    # The normal vLLM-Ascend worker performs this before any Triton operator.
    # Standalone operator tests in the upstream tree do the same.
    from vllm_ascend.ops.triton.triton_utils import init_device_properties_triton

    init_device_properties_triton()
    raise SystemExit(probe.main())
