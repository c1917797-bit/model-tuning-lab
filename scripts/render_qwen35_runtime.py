#!/usr/bin/env python3
"""Render the frozen Qwen3.5 runtime YAML into an auditable argv manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

SCHEMA = "qwen35-query-rewrite-runtime-manifest/v1"
EXPECTED_CONFIG_SCHEMA = "qwen35-query-rewrite-runtime/v1"


def compact(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def require(payload: dict, path: tuple[str, ...], expected) -> None:
    value = payload
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(f"missing config field: {'.'.join(path)}")
        value = value[key]
    if value != expected:
        raise ValueError(
            f"{'.'.join(path)} must be {expected!r}, got {value!r}"
        )


def render(config_path: Path) -> dict:
    raw = config_path.read_bytes()
    payload = yaml.safe_load(raw)
    if not isinstance(payload, dict):
        raise ValueError("runtime config must be a mapping")
    require(payload, ("schema",), EXPECTED_CONFIG_SCHEMA)
    require(payload, ("serve", "data_parallel_size"), 2)
    require(payload, ("serve", "tensor_parallel_size"), 4)
    require(payload, ("environment", "ASCEND_RT_VISIBLE_DEVICES"), "0,1,2,3,4,5,6,7")
    require(payload, ("benchmark", "concurrency"), [1, 5, 8, 16])
    require(payload, ("benchmark", "repetitions"), 3)
    require(payload, ("benchmark", "target_ttft_ratio"), 0.5)
    require(payload, ("benchmark", "target_tpot_ratio"), 0.5)
    require(payload, ("benchmark", "prompt_mode"), "raw_question")
    require(payload, ("benchmark", "generation"), "natural_eos")

    serve = payload["serve"]
    argv = [
        "vllm",
        "serve",
        str(payload["model"]),
        "--host",
        str(payload["host"]),
        "--port",
        str(payload["port"]),
        "--data-parallel-size",
        str(serve["data_parallel_size"]),
        "--tensor-parallel-size",
        str(serve["tensor_parallel_size"]),
        "--seed",
        str(serve["seed"]),
        "--served-model-name",
        str(payload["served_model_name"]),
        "--max-num-seqs",
        str(serve["max_num_seqs"]),
        "--max-model-len",
        str(serve["max_model_len"]),
        "--max-num-batched-tokens",
        str(serve["max_num_batched_tokens"]),
        "--gpu-memory-utilization",
        str(serve["gpu_memory_utilization"]),
        "--mamba-cache-mode",
        str(serve["mamba_cache_mode"]),
        "--mamba-cache-dtype",
        str(serve["mamba_cache_dtype"]),
        "--mamba-ssm-cache-dtype",
        str(serve["mamba_ssm_cache_dtype"]),
        "--compilation-config",
        compact(serve["compilation_config"]),
        "--additional-config",
        compact(serve["additional_config"]),
        "--default-chat-template-kwargs",
        compact(serve["default_chat_template_kwargs"]),
    ]
    for key, flag in (
        ("trust_remote_code", "--trust-remote-code"),
        ("enable_prefix_caching", "--enable-prefix-caching"),
        ("async_scheduling", "--async-scheduling"),
    ):
        if serve.get(key) is True:
            argv.append(flag)
        elif serve.get(key) is not False:
            raise ValueError(f"serve.{key} must be boolean")

    environment = {str(key): str(value) for key, value in payload["environment"].items()}
    canonical = {"argv": argv, "environment": environment}
    canonical_bytes = compact(canonical).encode()
    return {
        "schema": SCHEMA,
        "source": str(config_path.resolve()),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "runtime_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "argv": argv,
        "environment": environment,
        "benchmark": payload["benchmark"],
        "warnings": [
            "The VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE and VLLM_ASCEND_PTO_CHUNK_GDN environment variables are retained only for exact historical baseline fidelity; source inspection found no vLLM-Ascend reader for these environment names.",
            "This manifest renders configuration only. Device ownership, service health, correctness, and E2E performance require separate evidence.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = render(args.config)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to replace manifest: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
