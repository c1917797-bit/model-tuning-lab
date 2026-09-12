#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qwen35_performance_optimization_import import load_checker


def main() -> None:
    checker = load_checker()
    original_argv = sys.argv
    try:
        sys.argv = [
            "check_qwen35_gdn_t12_activation.py",
            "--log",
            "log",
            "--inspect",
            "inspect",
            "--npu",
            "npu",
            "--top",
            "top",
            "--models",
            "models",
            "--output",
            "output",
            "--variant",
            "candidate-super-kernel",
        ]
        assert checker.parse_args().variant == "candidate-super-kernel"
    finally:
        sys.argv = original_argv
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        log = root / "service.log"
        inspect = root / "inspect.json"
        npu = root / "npu.txt"
        top = root / "top.txt"
        models = root / "models.json"

        rank_markers = "\n".join(
            marker
            for name, marker in checker.REQUIRED_MARKERS.items()
            if name
            not in {
                "t21_dense_mlp",
                "mrv1_acl_graph",
                "mrv1_npugraph_options",
                "mrv1_optimized_graph",
            }
        )
        log.write_text("\n".join([rank_markers] * 4) + "\n", encoding="utf-8")
        env = [f"{key}={value}" for key, value in checker.EXPECTED_ENV.items()]
        env.extend(
            [
                "QWEN35_ASCEND_MONKEYPATCH=1",
                "QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH=1",
                "QWEN35_ASCEND_T21_DENSE_MLP=0",
                "QWEN35_ASCEND_SUPER_KERNEL=0",
                "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1",
                "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=0",
                "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=0",
                f"{checker.EXPECTED_OPERATOR_FEATURE_ENV}=1",
                f"ASCEND_CUSTOM_OPP_PATH={checker.EXPECTED_OPERATOR_VENDOR}",
                (
                    "LD_LIBRARY_PATH="
                    f"{checker.EXPECTED_OPERATOR_VENDOR}/op_api/lib:/image/lib"
                ),
                f"QWEN35_MMAR_OPERATOR_COMMIT={checker.EXPECTED_OPERATOR_COMMIT}",
                (
                    "QWEN35_MMAR_PACKAGE_SHA256="
                    f"{checker.EXPECTED_OPERATOR_PACKAGE_SHA256}"
                ),
            ]
        )
        env.append("PYTHONPATH=/opt/qwen35-t12-monkeypatch:/image/python:")
        inspect.write_text(
            json.dumps(
                [
                    {
                        "Name": "/qwen35_gdn_runtime_t12_npu03",
                        "Image": checker.EXPECTED_IMAGE_ID,
                        "State": {"Running": True},
                        "Config": {
                            "Env": env,
                            "Labels": {
                                "com.c1917797.qwen35-t12": "1",
                                "com.c1917797.qwen35-variant": "candidate",
                                "com.c1917797.qwen35-output-root": "/cache/test",
                            },
                        },
                        "HostConfig": {
                            "Privileged": False,
                            "ShmSize": 64 * 1024**3,
                            "Devices": [
                                {"PathOnHost": f"/dev/davinci{index}"}
                                for index in range(4)
                            ],
                        },
                        "Mounts": [
                            {
                                "Source": "/host/runtime-monkeypatch",
                                "Destination": "/opt/qwen35-t12-monkeypatch",
                                "RW": False,
                            },
                            {
                                "Source": "/host/aicpu-first-opp",
                                "Destination": checker.EXPECTED_OPERATOR_ROOT,
                                "RW": False,
                            },
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        npu.write_text(
            "\n".join(
                f"| {index}       0                 | {1000 + index}        | VLLMWorker_TP            | 28000                   |"
                for index in range(4)
            )
            + "\n",
            encoding="utf-8",
        )
        top.write_text(
            "PID PPID COMMAND\n"
            + "\n".join(f"{1000 + index} 1 worker" for index in range(4))
            + "\n",
            encoding="utf-8",
        )
        models.write_text(
            json.dumps({"data": [{"id": checker.EXPECTED_MODEL_ID}]}),
            encoding="utf-8",
        )

        result = checker.check(log, inspect, npu, top, models)
        assert result["passed"], result
        candidate = json.loads(inspect.read_text(encoding="utf-8"))
        candidate_prefill = json.loads(json.dumps(candidate))
        candidate_prefill_env = candidate_prefill[0]["Config"]["Env"]
        candidate_prefill[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "candidate-prefill"
        candidate_prefill[0]["Config"]["Env"] = [
            "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=512"
            if value.startswith("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=")
            else "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=16384"
            if value.startswith(
                "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS="
            )
            else value
            for value in candidate_prefill_env
            if not value.startswith(
                (
                    f"{checker.EXPECTED_OPERATOR_FEATURE_ENV}=",
                    "ASCEND_CUSTOM_OPP_PATH=",
                    "QWEN35_MMAR_OPERATOR_COMMIT=",
                    "QWEN35_MMAR_PACKAGE_SHA256=",
                )
            )
        ]
        candidate_prefill[0]["Config"]["Env"] = [
            value
            for value in candidate_prefill[0]["Config"]["Env"]
            if not (
                value.startswith("LD_LIBRARY_PATH=")
                and checker.EXPECTED_OPERATOR_ROOT in value
            )
        ]
        candidate_prefill[0]["Mounts"] = [
            mount
            for mount in candidate_prefill[0]["Mounts"]
            if mount["Destination"] != checker.EXPECTED_OPERATOR_ROOT
        ]
        inspect.write_text(json.dumps(candidate_prefill), encoding="utf-8")
        result = checker.check(
            log, inspect, npu, top, models, variant="candidate-prefill"
        )
        assert result["passed"], result

        candidate_prefill_t21 = json.loads(json.dumps(candidate_prefill))
        candidate_prefill_t21[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "candidate-prefill-t21"
        candidate_prefill_t21[0]["Config"]["Env"] = [
            "QWEN35_ASCEND_T21_DENSE_MLP=1"
            if value.startswith("QWEN35_ASCEND_T21_DENSE_MLP=")
            else (
                "PYTHONPATH=/opt/qwen35-t12-monkeypatch:"
                f"{checker.EXPECTED_T21_BRIDGE_ROOT}:/image/python:"
            )
            if value.startswith("PYTHONPATH=")
            else value
            for value in candidate_prefill_t21[0]["Config"]["Env"]
        ]
        candidate_prefill_t21[0]["Config"]["Env"].extend(
            [
                f"ASCEND_CUSTOM_OPP_PATH={checker.EXPECTED_T21_VENDOR}",
                (
                    "QWEN35_T21_OPAPI_LIBRARY="
                    f"{checker.EXPECTED_T21_VENDOR}/op_api/lib/libcust_opapi.so"
                ),
                (
                    "LD_LIBRARY_PATH="
                    f"{checker.EXPECTED_T21_VENDOR}/op_api/lib:/image/lib"
                ),
            ]
        )
        candidate_prefill_t21[0]["Mounts"].extend(
            [
                {
                    "Source": "/host/t21-opp",
                    "Destination": checker.EXPECTED_T21_OPP_ROOT,
                    "RW": False,
                },
                {
                    "Source": "/host/t21-bridge",
                    "Destination": checker.EXPECTED_T21_BRIDGE_ROOT,
                    "RW": False,
                },
            ]
        )
        inspect.write_text(json.dumps(candidate_prefill_t21), encoding="utf-8")
        t21_markers = rank_markers + "\n" + checker.REQUIRED_MARKERS[
            "t21_dense_mlp"
        ]
        log.write_text("\n".join([t21_markers] * 4) + "\n", encoding="utf-8")
        result = checker.check(
            log, inspect, npu, top, models, variant="candidate-prefill-t21"
        )
        assert result["passed"], result
        assert result["marker_counts"]["t21_dense_mlp"] == 4

        candidate_prefill_no_prefetch = json.loads(
            json.dumps(candidate_prefill)
        )
        candidate_prefill_no_prefetch[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "candidate-prefill-no-prefetch"
        candidate_prefill_no_prefetch[0]["Config"]["Env"] = [
            "QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH=0"
            if value.startswith("QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH=")
            else value
            for value in candidate_prefill_no_prefetch[0]["Config"]["Env"]
        ]
        inspect.write_text(
            json.dumps(candidate_prefill_no_prefetch), encoding="utf-8"
        )
        non_prefetch_markers = "\n".join(
            marker
            for name, marker in checker.REQUIRED_MARKERS.items()
            if name not in {
                "gate_up_prefetch",
                "rmsnorm_postprocess",
                "t21_dense_mlp",
            }
        )
        log.write_text(
            "\n".join([non_prefetch_markers] * 4) + "\n",
            encoding="utf-8",
        )
        result = checker.check(
            log,
            inspect,
            npu,
            top,
            models,
            variant="candidate-prefill-no-prefetch",
        )
        assert result["passed"], result
        assert result["marker_counts"]["gate_up_prefetch"] == 0
        assert result["marker_counts"]["rmsnorm_postprocess"] == 0

        candidate_super_kernel = json.loads(json.dumps(candidate_prefill_no_prefetch))
        candidate_super_kernel[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "candidate-super-kernel"
        candidate_super_kernel[0]["Config"]["Env"] = [
            "QWEN35_ASCEND_SUPER_KERNEL=1"
            if value.startswith("QWEN35_ASCEND_SUPER_KERNEL=")
            else "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=0"
            if value.startswith("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=")
            else "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=0"
            if value.startswith("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=")
            else "VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=0"
            if value.startswith("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=")
            else value
            for value in candidate_super_kernel[0]["Config"]["Env"]
        ]
        inspect.write_text(json.dumps(candidate_super_kernel), encoding="utf-8")
        super_kernel_markers = "\n".join(
            marker
            for name, marker in checker.REQUIRED_MARKERS.items()
            if name
            in {
                "multiprocessing_child",
                "mrv1_acl_graph",
                "mrv1_npugraph_options",
                "mrv1_optimized_graph",
            }
        )
        log.write_text(
            "\n".join([super_kernel_markers] * 4) + "\n",
            encoding="utf-8",
        )
        result = checker.check(
            log,
            inspect,
            npu,
            top,
            models,
            variant="candidate-super-kernel",
        )
        assert result["passed"], result
        assert result["marker_counts"]["mrv1_optimized_graph"] == 4

        control = json.loads(json.dumps(candidate))
        control_env = control[0]["Config"]["Env"]
        control[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "control"
        control[0]["Config"]["Env"] = [
            "QWEN35_ASCEND_MONKEYPATCH=0"
            if value.startswith("QWEN35_ASCEND_MONKEYPATCH=")
            else "QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH=0"
            if value.startswith("QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH=")
            else "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=0"
            if value.startswith("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=")
            else value
            for value in control_env
            if not value.startswith(
                (
                    f"{checker.EXPECTED_OPERATOR_FEATURE_ENV}=",
                    "ASCEND_CUSTOM_OPP_PATH=",
                    "QWEN35_MMAR_OPERATOR_COMMIT=",
                    "QWEN35_MMAR_PACKAGE_SHA256=",
                )
            )
        ]
        control[0]["Config"]["Env"] = [
            value
            for value in control[0]["Config"]["Env"]
            if not (
                value.startswith("LD_LIBRARY_PATH=")
                and checker.EXPECTED_OPERATOR_ROOT in value
            )
        ]
        control[0]["Mounts"] = [
            mount
            for mount in control[0]["Mounts"]
            if mount["Destination"] != checker.EXPECTED_OPERATOR_ROOT
        ]
        inspect.write_text(json.dumps(control), encoding="utf-8")
        log.write_text("unpatched control service\n", encoding="utf-8")
        result = checker.check(
            log, inspect, npu, top, models, variant="control"
        )
        assert result["passed"], result

        log.write_text("\n".join([rank_markers] * 4) + "\n", encoding="utf-8")
        broken = json.loads(inspect.read_text(encoding="utf-8"))
        broken[0]["Config"]["Env"] = env
        broken[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "candidate"
        broken[0]["Mounts"].append(
            {
                "Source": "/host/gdn.py",
                "Destination": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py",
                "RW": False,
            }
        )
        inspect.write_text(json.dumps(broken), encoding="utf-8")
        result = checker.check(log, inspect, npu, top, models)
        assert not result["passed"]
        assert not result["checks"]["mounts"]["no_vllm_source_overlays"]
    print("PASS: t12 activation checker")


if __name__ == "__main__":
    main()
