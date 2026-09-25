"""Opt-in Ada-KV Ascend adaptation; no runtime patch is installed by import."""

import os


def register() -> None:
    if os.environ.get("QWEN36_ADAKV_NATIVE_ORACLE_ENABLE") == "1":
        if (os.environ.get("QWEN36_ADAKV_CANDIDATE_ENABLE") == "1"
                or os.environ.get("QWEN36_ADAKV_PROBE_ENABLE") == "1"):
            raise RuntimeError("Ada-KV native oracle, candidate and selector probe are mutually exclusive")
        from .native_oracle_probe import register as register_native_oracle

        register_native_oracle()
        return
    if os.environ.get("QWEN36_ADAKV_CANDIDATE_ENABLE") == "1":
        if os.environ.get("QWEN36_ADAKV_PROBE_ENABLE") == "1":
            raise RuntimeError("Ada-KV candidate and read-only probe are mutually exclusive")
        from .single_request_candidate import register as register_candidate

        register_candidate()
    else:
        from .live_probe import register as register_probe

        register_probe()

__all__ = ["register"]
