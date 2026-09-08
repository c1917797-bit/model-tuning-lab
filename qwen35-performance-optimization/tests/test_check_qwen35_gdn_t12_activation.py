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
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        log = root / "service.log"
        inspect = root / "inspect.json"
        npu = root / "npu.txt"
        top = root / "top.txt"
        models = root / "models.json"

        rank_markers = "\n".join(checker.REQUIRED_MARKERS.values())
        log.write_text("\n".join([rank_markers] * 4) + "\n", encoding="utf-8")
        env = [f"{key}={value}" for key, value in checker.EXPECTED_ENV.items()]
        env.extend(
            [
                "QWEN35_ASCEND_MONKEYPATCH=1",
                "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1",
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
                            }
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
        control = json.loads(inspect.read_text(encoding="utf-8"))
        control_env = control[0]["Config"]["Env"]
        control[0]["Config"]["Labels"][
            "com.c1917797.qwen35-variant"
        ] = "control"
        control[0]["Config"]["Env"] = [
            "QWEN35_ASCEND_MONKEYPATCH=0"
            if value.startswith("QWEN35_ASCEND_MONKEYPATCH=")
            else "VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=0"
            if value.startswith("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=")
            else value
            for value in control_env
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
