#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("verify_physical_v12.py")
SPEC = importlib.util.spec_from_file_location("verify_physical_v12_under_test", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def evidence(pids: range = range(1, 5)) -> list[dict]:
    rows: list[dict] = [{"event": "heterogeneous_cache_grouped", "pid": 99}]
    for pid in pids:
        rows.extend(
            [
                {
                    "event": "physical_cache_bound",
                    "pid": pid,
                    "compact_page_bytes": 64,
                    "dense_page_bytes": 128,
                    "num_blocks": 1,
                },
                {"event": "tp_geometry_aligned", "pid": pid},
                {"event": "worker_dispatch_verified", "pid": pid},
            ]
        )
    return rows


def canary() -> dict:
    stopped = lambda content: {
        "content": content,
        "finish_reason": "stop",
        "reasoning_content": None,
    }
    return {
        "schema": "mst.dasc.physical-canary/v1",
        "short": stopped("OK"),
        "runs": [stopped("VERIFIED") for _ in range(3)],
        "variant": stopped("ASCEND"),
        "metrics_before": {"vllm:prefix_cache_hits_total": 0},
        "metrics_after": {"vllm:prefix_cache_hits_total": 3},
        "ok": True,
    }


class PhysicalV12VerifierTest(unittest.TestCase):
    def test_recomputes_positive_verdict(self) -> None:
        result = MODULE.canary_verdict(canary(), evidence())
        self.assertTrue(result["ok"])
        self.assertEqual(result["prefix_cache_hit_delta"], 3)

    def test_rejects_reported_success_with_bad_raw_evidence(self) -> None:
        rows = evidence()
        for row in rows:
            if row.get("event") == "worker_dispatch_verified":
                row["pid"] += 10
        result = MODULE.canary_verdict(canary(), rows)
        self.assertFalse(result["ok"])
        self.assertTrue(result["reported_ok"])

    def test_rejects_non_exact_output(self) -> None:
        value = canary()
        value["short"]["content"] = "OK\n"
        self.assertFalse(MODULE.canary_verdict(value, evidence())["ok"])

    def test_manifest_detects_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload.txt"
            payload.write_text("trusted\n", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = root / "manifest.sha256"
            manifest.write_text(f"{digest}  {payload}\n", encoding="utf-8")
            self.assertTrue(MODULE.verify_manifest(manifest, root)["ok"])
            payload.write_text("tampered\n", encoding="utf-8")
            self.assertFalse(MODULE.verify_manifest(manifest, root)["ok"])

    def test_container_identity_requires_exact_npu4_7_mapping(self) -> None:
        image = {"Id": "sha256:image"}
        devices = [
            {
                "PathOnHost": f"/dev/davinci{physical}",
                "PathInContainer": f"/dev/davinci{logical}",
            }
            for logical, physical in enumerate(range(4, 8))
        ]
        devices.extend(
            {"PathOnHost": value, "PathInContainer": value}
            for value in (
                "/dev/davinci_manager",
                "/dev/devmm_svm",
                "/dev/hisi_hdc",
            )
        )
        container = {
            "Name": MODULE.EXPECTED_CONTAINER,
            "Image": "sha256:image",
            "Config": {
                "Image": MODULE.EXPECTED_IMAGE,
                "Labels": {
                    "mst.owner": "c1917797-bit",
                    "mst.workstream": "dasc-qwen36-ascend-piercing-20260915",
                    "mst.experiment": "dasc-qwen36-physical-cache-v12",
                },
                "Env": [
                    "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
                    "VLLM_PLUGINS=ascend,dasc_vllm_ascend",
                    "MST_DASC_ENABLE=1",
                    "MST_DASC_MODE=physical-cache-eager",
                    "MST_DASC_W_MAX=64",
                ],
                "Cmd": [
                    "vllm",
                    "serve",
                    "/models/Qwen3.6-27B",
                    "--tensor-parallel-size",
                    "4",
                    "--mamba-cache-mode",
                    "align",
                    "--enable-prefix-caching",
                    "--port",
                    "8030",
                ],
            },
            "HostConfig": {"NetworkMode": "host", "Devices": devices},
            "Mounts": [
                {
                    "Source": "/cache/efim/Qwen3.6-27B",
                    "Destination": "/models/Qwen3.6-27B",
                    "RW": False,
                },
                {
                    "Source": str(MODULE.EXPECTED_RESULT_ROOT / "plugin-snapshot"),
                    "Destination": "/workspace/dasc",
                    "RW": False,
                },
                {
                    "Source": str(MODULE.EXPECTED_RESULT_ROOT),
                    "Destination": "/dasc-results",
                    "RW": True,
                },
            ],
            "State": {"Running": False},
        }
        self.assertTrue(MODULE.container_identity_verdict(container, image)["ok"])
        container["HostConfig"]["Devices"][0]["PathOnHost"] = "/dev/davinci0"
        self.assertFalse(MODULE.container_identity_verdict(container, image)["ok"])


if __name__ == "__main__":
    unittest.main()
