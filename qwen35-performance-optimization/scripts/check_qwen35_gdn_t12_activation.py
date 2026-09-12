#!/usr/bin/env python3
"""Fail closed unless the live t12 runtime-only service is fully activated."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


EXPECTED_IMAGE_ID = (
    "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
)
EXPECTED_MODEL_ID = "Qwen3-5/Qwen3.5-27B"
EXPECTED_OPERATOR_FEATURE_ENV = "ASCEND_MATMUL_ALLREDUCE_M1_AICPU_FIRST"
EXPECTED_OPERATOR_COMMIT = "41515133cadc7e2de54bb6f2297887bfefc7e4ad"
EXPECTED_OPERATOR_PACKAGE_SHA256 = (
    "8e22ab5d7b0c5b7eb88a393bc452a60fc377df434e1b8f70986a48723b67c84a"
)
EXPECTED_OPERATOR_ROOT = "/opt/qwen35-mmar-aicpu-first-opp"
EXPECTED_OPERATOR_VENDOR = (
    f"{EXPECTED_OPERATOR_ROOT}/vendors/"
    "qwen35_mmar_aicpu_first_transformer_transformer"
)
EXPECTED_T21_OPP_ROOT = "/opt/qwen35-t21-opp"
EXPECTED_T21_VENDOR = f"{EXPECTED_T21_OPP_ROOT}/vendors/qwen35_t21_v910_transformer"
EXPECTED_T21_BRIDGE_ROOT = "/opt/qwen35-t21-bridge"
EXPECTED_ENV = {
    "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE": "1",
    "VLLM_ASCEND_ENABLE_FLASHCOMM1": "0",
    "VLLM_ASCEND_ENABLE_NZ": "1",
}
REQUIRED_MARKERS = {
    "multiprocessing_child": "runtime hooks enabled for multiprocessing child",
    "gdn_construction": "patched Qwen3.5 GDN fused projection construction",
    "weight_mapping": "patched Qwen3.5 six-way fused projection weight mapping",
    "ascend_forward": "patched Ascend GDN fused projection forward path",
    "gate_up_prefetch": "patched linear-attention gate/up prefetch",
    "rmsnorm_postprocess": "patched Gemma RMSNorm prefetch postprocess",
    "t21_dense_mlp": "patched Qwen2MoeMLP with opt-in T21 dense path",
    "mrv1_acl_graph": "backported upstream MRV1 ACL Graph super-kernel",
    "mrv1_npugraph_options": "backported upstream MRV1 npugraph-ex options",
    "mrv1_optimized_graph": "MRV1 super-kernel optimized ACL graph",
}
NPU_PROCESS_RE = re.compile(
    r"^\|\s*([0-7])\s+\d+\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_inspect(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1:
            raise ValueError("container inspect must contain exactly one object")
        value = value[0]
    if not isinstance(value, dict):
        raise ValueError("container inspect must be a JSON object")
    return value


def _environment(inspect: dict) -> dict[str, str]:
    result = {}
    for item in inspect.get("Config", {}).get("Env") or []:
        key, separator, value = item.partition("=")
        if separator:
            result[key] = value
    return result


def _top_pids(text: str) -> set[int]:
    result = set()
    for line in text.splitlines():
        first = line.strip().split(maxsplit=1)[0] if line.strip() else ""
        if first.isdigit():
            result.add(int(first))
    return result


def check(
    log_path: Path,
    inspect_path: Path,
    npu_path: Path,
    top_path: Path,
    models_path: Path,
    expected_ranks: int = 4,
    variant: str = "candidate",
) -> dict:
    variants = {
        "candidate",
        "candidate-prefill",
        "candidate-prefill-t21",
        "candidate-prefill-no-prefetch",
        "candidate-super-kernel",
        "control",
    }
    if variant not in variants:
        raise ValueError(f"variant must be one of {sorted(variants)}")
    patch_enabled = variant != "control"
    operator_enabled = variant == "candidate"
    t21_enabled = variant == "candidate-prefill-t21"
    super_kernel_enabled = variant == "candidate-super-kernel"
    gdn_fusion_enabled = patch_enabled and not super_kernel_enabled
    prefill_enabled = variant in {
        "candidate-prefill",
        "candidate-prefill-t21",
        "candidate-prefill-no-prefetch",
    }
    prefetch_patch_enabled = variant in {
        "candidate",
        "candidate-prefill",
        "candidate-prefill-t21",
    }
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    inspect = _load_inspect(inspect_path)
    npu_text = npu_path.read_text(encoding="utf-8", errors="replace")
    top_text = top_path.read_text(encoding="utf-8", errors="replace")
    models = json.loads(models_path.read_text(encoding="utf-8"))

    marker_counts = {
        name: log_text.count(marker) for name, marker in REQUIRED_MARKERS.items()
    }
    marker_checks = {}
    for name, count in marker_counts.items():
        expected = patch_enabled
        if name in {"gdn_construction", "weight_mapping", "ascend_forward"}:
            expected = gdn_fusion_enabled
        if name in {"gate_up_prefetch", "rmsnorm_postprocess"}:
            expected = prefetch_patch_enabled
        if name == "t21_dense_mlp":
            expected = t21_enabled
        if name in {
            "mrv1_acl_graph",
            "mrv1_npugraph_options",
            "mrv1_optimized_graph",
        }:
            expected = super_kernel_enabled
        marker_checks[name] = count >= expected_ranks if expected else count == 0

    env = _environment(inspect)
    expected_env = {
        **EXPECTED_ENV,
        "QWEN35_ASCEND_MONKEYPATCH": "1" if patch_enabled else "0",
        "QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH": (
            "1" if prefetch_patch_enabled else "0"
        ),
        "QWEN35_ASCEND_T21_DENSE_MLP": "1" if t21_enabled else "0",
        "QWEN35_ASCEND_SUPER_KERNEL": "1" if super_kernel_enabled else "0",
        "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS": (
            "1" if gdn_fusion_enabled else "0"
        ),
        "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD": (
            "512" if prefill_enabled else "0"
        ),
        "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS": (
            "16384" if prefill_enabled else "0"
        ),
    }
    env_checks = {
        key: env.get(key) == expected for key, expected in expected_env.items()
    }
    python_path = env.get("PYTHONPATH", "")
    env_checks["patch_first_on_pythonpath"] = python_path.startswith(
        "/opt/qwen35-t12-monkeypatch:"
    )
    if operator_enabled:
        env_checks.update(
            {
                "operator_feature_enabled": (
                    env.get(EXPECTED_OPERATOR_FEATURE_ENV) == "1"
                ),
                "operator_commit": (
                    env.get("QWEN35_MMAR_OPERATOR_COMMIT")
                    == EXPECTED_OPERATOR_COMMIT
                ),
                "operator_package_sha256": (
                    env.get("QWEN35_MMAR_PACKAGE_SHA256")
                    == EXPECTED_OPERATOR_PACKAGE_SHA256
                ),
                "operator_opp_path": (
                    env.get("ASCEND_CUSTOM_OPP_PATH")
                    == EXPECTED_OPERATOR_VENDOR
                ),
                "operator_library_first": env.get(
                    "LD_LIBRARY_PATH", ""
                ).startswith(f"{EXPECTED_OPERATOR_VENDOR}/op_api/lib:"),
            }
        )
    else:
        env_checks.update(
            {
                "operator_feature_absent": (
                    EXPECTED_OPERATOR_FEATURE_ENV not in env
                ),
                "operator_opp_absent": (
                    EXPECTED_OPERATOR_ROOT
                    not in env.get("ASCEND_CUSTOM_OPP_PATH", "")
                ),
            }
        )
    if t21_enabled:
        env_checks.update(
            {
                "t21_opp_path": (
                    env.get("ASCEND_CUSTOM_OPP_PATH") == EXPECTED_T21_VENDOR
                ),
                "t21_operator_library": (
                    env.get("QWEN35_T21_OPAPI_LIBRARY")
                    == f"{EXPECTED_T21_VENDOR}/op_api/lib/libcust_opapi.so"
                ),
                "t21_library_first": env.get("LD_LIBRARY_PATH", "").startswith(
                    f"{EXPECTED_T21_VENDOR}/op_api/lib:"
                ),
                "t21_bridge_on_pythonpath": (
                    EXPECTED_T21_BRIDGE_ROOT in python_path.split(":")
                ),
            }
        )
    else:
        env_checks["t21_operator_library_absent"] = (
            "QWEN35_T21_OPAPI_LIBRARY" not in env
        )

    host_devices = {
        item.get("PathOnHost")
        for item in inspect.get("HostConfig", {}).get("Devices") or []
    }
    compute_devices = {f"/dev/davinci{index}" for index in range(4)}
    protected_devices = {f"/dev/davinci{index}" for index in range(4, 8)}
    device_checks = {
        "physical_0_3_present": compute_devices.issubset(host_devices),
        "physical_4_7_absent": host_devices.isdisjoint(protected_devices),
        "not_privileged": not inspect.get("HostConfig", {}).get("Privileged", False),
        "shm_at_least_64g": int(
            inspect.get("HostConfig", {}).get("ShmSize", 0)
        )
        >= 64 * 1024**3,
    }

    mounts = inspect.get("Mounts") or []
    patch_mounts = [
        item
        for item in mounts
        if item.get("Destination") == "/opt/qwen35-t12-monkeypatch"
    ]
    operator_mounts = [
        item
        for item in mounts
        if item.get("Destination") == EXPECTED_OPERATOR_ROOT
    ]
    t21_opp_mounts = [
        item for item in mounts
        if item.get("Destination") == EXPECTED_T21_OPP_ROOT
    ]
    t21_bridge_mounts = [
        item for item in mounts
        if item.get("Destination") == EXPECTED_T21_BRIDGE_ROOT
    ]
    forbidden_mounts = [
        item
        for item in mounts
        if str(item.get("Destination", "")).startswith(
            ("/vllm-workspace/vllm/", "/vllm-workspace/vllm-ascend/")
        )
    ]
    mount_checks = {
        "one_patch_mount": len(patch_mounts) == 1,
        "patch_mount_read_only": len(patch_mounts) == 1
        and not patch_mounts[0].get("RW", True),
        "no_vllm_source_overlays": not forbidden_mounts,
        "operator_mount": (
            len(operator_mounts) == 1
            and not operator_mounts[0].get("RW", True)
            if operator_enabled
            else not operator_mounts
        ),
        "t21_opp_mount": (
            len(t21_opp_mounts) == 1 and not t21_opp_mounts[0].get("RW", True)
            if t21_enabled else not t21_opp_mounts
        ),
        "t21_bridge_mount": (
            len(t21_bridge_mounts) == 1
            and not t21_bridge_mounts[0].get("RW", True)
            if t21_enabled else not t21_bridge_mounts
        ),
    }

    top_pids = _top_pids(top_text)
    npu_processes: dict[int, list[dict]] = {index: [] for index in range(8)}
    for match in NPU_PROCESS_RE.finditer(npu_text):
        device = int(match.group(1))
        npu_processes[device].append(
            {"pid": int(match.group(2)), "name": match.group(3).strip()}
        )
    binding_checks = {}
    for device in range(4):
        processes = npu_processes[device]
        binding_checks[f"npu{device}_one_worker"] = (
            len(processes) == 1
            and processes[0]["name"] == "VLLMWorker_TP"
            and processes[0]["pid"] in top_pids
        )

    model_ids = {
        item.get("id") for item in models.get("data", []) if isinstance(item, dict)
    }
    identity_checks = {
        "container_running": inspect.get("State", {}).get("Running") is True,
        "image_id": inspect.get("Image") == EXPECTED_IMAGE_ID,
        "model_ready": EXPECTED_MODEL_ID in model_ids,
        "t12_label": (
            inspect.get("Config", {}).get("Labels", {}).get(
                "com.c1917797.qwen35-t12"
            )
            == "1"
        ),
        "variant_label": (
            inspect.get("Config", {}).get("Labels", {}).get(
                "com.c1917797.qwen35-variant"
            )
            == variant
        ),
    }

    all_groups = [
        marker_checks,
        env_checks,
        device_checks,
        mount_checks,
        binding_checks,
        identity_checks,
    ]
    passed = all(all(group.values()) for group in all_groups)
    return {
        "schema": "qwen35-gdn-runtime-t12-activation/v1",
        "variant": variant,
        "passed": passed,
        "expected_ranks": expected_ranks,
        "marker_counts": marker_counts,
        "checks": {
            "markers": marker_checks,
            "environment": env_checks,
            "devices": device_checks,
            "mounts": mount_checks,
            "bindings": binding_checks,
            "identity": identity_checks,
        },
        "observed": {
            "container_name": inspect.get("Name"),
            "image_id": inspect.get("Image"),
            "host_devices": sorted(value for value in host_devices if value),
            "patch_mounts": patch_mounts,
            "operator_mounts": operator_mounts,
            "t21_opp_mounts": t21_opp_mounts,
            "t21_bridge_mounts": t21_bridge_mounts,
            "forbidden_mounts": forbidden_mounts,
            "npu_processes": npu_processes,
            "container_pids": sorted(top_pids),
            "model_ids": sorted(value for value in model_ids if value),
        },
        "inputs": {
            "log": {"path": str(log_path), "sha256": _sha256(log_path)},
            "inspect": {"path": str(inspect_path), "sha256": _sha256(inspect_path)},
            "npu": {"path": str(npu_path), "sha256": _sha256(npu_path)},
            "top": {"path": str(top_path), "sha256": _sha256(top_path)},
            "models": {"path": str(models_path), "sha256": _sha256(models_path)},
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--inspect", type=Path, required=True)
    parser.add_argument("--npu", type=Path, required=True)
    parser.add_argument("--top", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-ranks", type=int, default=4)
    parser.add_argument(
        "--variant",
        choices=(
            "candidate",
            "candidate-prefill",
            "candidate-prefill-t21",
            "candidate-prefill-no-prefetch",
            "candidate-super-kernel",
            "control",
        ),
        default="candidate",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check(
        args.log,
        args.inspect,
        args.npu,
        args.top,
        args.models,
        args.expected_ranks,
        args.variant,
    )
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
