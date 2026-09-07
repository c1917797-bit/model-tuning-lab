#!/usr/bin/env python3
"""Fresh quality-first Dk112 continuation using the audited formal runner."""

from pathlib import Path

import state_reduction_formal_runner as runner


runner.EXPERIMENT_ID = "state-reduction-qwen36-dk112-quality-first-20260907"
runner.ROOT = Path("/cache/cch/state-reduction-qwen36-dk112-quality-first-20260907")
runner.PORT = 8226
runner.HCCL_RANGE = "27020-27120"
runner.EXPECTED = {
    str(runner.BENCHMARK): (
        "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"
    ),
    str(runner.QUALITY): (
        "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
    ),
    str(runner.LONGBENCH): (
        "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a"
    ),
    str(runner.GSM8K): (
        "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"
    ),
    "/cache/efim/Qwen3.6-27B/config.json": (
        "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c"
    ),
    "/cache/efim/Qwen3.6-27B/model.safetensors.index.json": (
        "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b"
    ),
    "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk112/drrqr_manifest.json": (
        "033eac4d29e12e9f219b213f12a15ebd3217e183f353c43c2200bb47f149243a"
    ),
}
runner.ARMS = {
    "baseline": {
        "model": "/cache/efim/Qwen3.6-27B",
        "served": "qwen36-dk112-quality-first-baseline",
        "container": "qwen36_dk112_qf_baseline_npu4_7_tp4",
        "head_k_dim": 128,
    },
    "drrqr-dk112": {
        "model": "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk112",
        "served": "qwen36-dk112-quality-first-treatment",
        "container": "qwen36_dk112_qf_treatment_npu4_7_tp4",
        "head_k_dim": 112,
    },
}


if __name__ == "__main__":
    raise SystemExit(runner.main())
