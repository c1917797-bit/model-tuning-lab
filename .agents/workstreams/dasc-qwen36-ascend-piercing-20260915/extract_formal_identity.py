#!/usr/bin/env python3
"""Fail-closed extraction of a DASC v13 arm identity from Docker inspect."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


MODEL_CONTAINER = "/models/Qwen3.6-27B"
MODEL_HOST = "/cache/efim/Qwen3.6-27B"
PLUGIN_HOST = (
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "physical-cache-order-fix-v12/plugin-snapshot"
)
RESULT_HOST = "/cache/cch/dasc-qwen36-ascend-20260915/formal-ab-v13"
EXPECTED_DEVICES = {
    (f"/dev/davinci{physical}", f"/dev/davinci{logical}")
    for logical, physical in enumerate(range(4, 8))
}


def option(command: list[str], name: str) -> str | None:
    try:
        return command[command.index(name) + 1]
    except (ValueError, IndexError):
        return None


def extract(
    value: dict,
    arm: str,
    source_commit: str,
    model_config_sha256: str,
    plugin_manifest_sha256: str,
) -> dict:
    if arm not in ("dense", "candidate"):
        raise ValueError(f"unknown arm: {arm}")
    config = value.get("Config", {})
    host = value.get("HostConfig", {})
    env = dict(x.split("=", 1) for x in config.get("Env", []) if "=" in x)
    command = config.get("Cmd") or []
    mounts = {x.get("Destination"): x for x in value.get("Mounts", [])}
    devices = {
        (x.get("PathOnHost"), x.get("PathInContainer"))
        for x in host.get("Devices", [])
        if re.fullmatch(r"/dev/davinci\d+", str(x.get("PathOnHost", "")))
    }
    expected_name = f"/dasc_qwen36_formal_v13_{arm}_20260916"
    candidate = arm == "candidate"
    checks = {
        "name": value.get("Name") == expected_name,
        "image_id": isinstance(value.get("Image"), str) and value.get("Image").startswith("sha256:"),
        "network": host.get("NetworkMode") == "host",
        "devices": devices == EXPECTED_DEVICES,
        "visible": env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
        "owner": config.get("Labels", {}).get("mst.owner") == "c1917797-bit",
        "experiment": config.get("Labels", {}).get("mst.experiment")
        == "dasc-qwen36-formal-ab-v13",
        "arm": config.get("Labels", {}).get("mst.arm") == arm,
        "serve": command[:3] == ["vllm", "serve", MODEL_CONTAINER],
        "served_name": option(command, "--served-model-name") == "qwen36-dasc-formal-v13",
        "tp4": option(command, "--tensor-parallel-size") == "4",
        "mamba_align": option(command, "--mamba-cache-mode") == "align",
        "prefix_cache": "--enable-prefix-caching" in command,
        "max_model_len": option(command, "--max-model-len") == "44032",
        "max_num_seqs": option(command, "--max-num-seqs") == "32",
        "block_size": option(command, "--block-size") == "128",
        "kv_budget": option(command, "--kv-cache-memory") == "9663676416",
        "port": option(command, "--port") == "8031",
        "model_mount": mounts.get(MODEL_CONTAINER, {}).get("Source") == MODEL_HOST
        and mounts.get(MODEL_CONTAINER, {}).get("RW") is False,
        "plugin_mount": mounts.get("/workspace/dasc", {}).get("Source") == PLUGIN_HOST
        and mounts.get("/workspace/dasc", {}).get("RW") is False,
        "result_mount": mounts.get("/dasc-results", {}).get("Source") == RESULT_HOST
        and mounts.get("/dasc-results", {}).get("RW") is True,
        "plugins": env.get("VLLM_PLUGINS")
        == ("ascend,dasc_vllm_ascend" if candidate else "ascend"),
        "enable": env.get("MST_DASC_ENABLE") == ("1" if candidate else "0"),
        "mode": env.get("MST_DASC_MODE") == "physical-cache-eager"
        if candidate
        else "MST_DASC_MODE" not in env,
        "wmax": env.get("MST_DASC_W_MAX") == "64"
        if candidate
        else "MST_DASC_W_MAX" not in env,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"{arm} container identity mismatch: {failed}")
    return {
        "physical_npus": [4, 5, 6, 7],
        "host_to_container_devices": ["4:0", "5:1", "6:2", "7:3"],
        "tensor_parallel_size": 4,
        "communication": "HCCL",
        "max_model_len": 44032,
        "max_num_seqs": 32,
        "block_size": 128,
        "kv_cache_memory_bytes_per_rank": 9663676416,
        "image_digest": value["Image"],
        "model_config_sha256": model_config_sha256,
        "plugin_manifest_sha256": plugin_manifest_sha256,
        "source_commit": source_commit,
        "dasc_plugin": candidate,
        "mode": "physical-cache-eager" if candidate else None,
        "w_max": 64 if candidate else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--inspect", required=True, type=Path)
    parser.add_argument("--arm", required=True, choices=("dense", "candidate"))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--model-config-sha256", required=True)
    parser.add_argument("--plugin-manifest-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    values = json.loads(args.inspect.read_text(encoding="utf-8"))
    if not isinstance(values, list) or len(values) != 1:
        raise ValueError("Docker inspect artifact must contain exactly one container")
    identity = extract(
        values[0],
        args.arm,
        args.source_commit,
        args.model_config_sha256,
        args.plugin_manifest_sha256,
    )
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
