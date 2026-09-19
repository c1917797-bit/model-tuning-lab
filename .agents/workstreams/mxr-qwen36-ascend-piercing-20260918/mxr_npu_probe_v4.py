#!/usr/bin/env python3
"""MXR gate with the v0.23 standalone baseline context made explicit."""
from __future__ import annotations

from types import SimpleNamespace

import mxr_npu_probe as probe
import mxr_npu_probe_v3 as v3


BASE_LOAD_IMPLEMENTATIONS = probe.load_implementations


def load_implementations():
    result = BASE_LOAD_IMPLEMENTATIONS()
    # v0.23's chunk kernel reads two service-owned globals even for a local
    # world-size-one operator call. Mirror the upstream operator unit-test
    # harness without placing mocks inside the timed callable.
    from vllm_ascend.ops.triton.fla import chunk as chunk_module

    forward_context = SimpleNamespace(attn_metadata=None)
    pcp_group = SimpleNamespace(world_size=1, rank_in_group=0)
    chunk_module.get_forward_context = lambda: forward_context
    chunk_module.get_pcp_group = lambda: pcp_group
    return result


probe.load_implementations = load_implementations


if __name__ == "__main__":
    output_dir = v3.output_dir_from_argv()
    if not output_dir.is_dir():
        raise RuntimeError("output directory must already exist")
    v3.run_canary(output_dir)
    raise SystemExit(probe.main())
