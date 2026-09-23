"""One-shot fail-closed Qwen3.6 Kascade mechanism diagnostic on NPU4-7.

The owned container is stopped after evidence collection but not deleted.
This controller does not benchmark performance or change model outputs.
"""

from __future__ import annotations

import fcntl
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time


ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
WORKSPACE = ROOT / "projects/qwen36-paper-portfolio"
RESULTS = Path("/cache/cch/kascade-qwen36-crosslayer-v2")
LOCK = Path("/cache/cch/kascade-qwen36-crosslayer-v2.admission.lock")
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAME = "qwen36_kascade_crosslayer_v2_20260923"
PORT = 8237


def capture(args: list[str], timeout: int = 30) -> str:
    result = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=True,
    )
    return result.stdout


def check_npus() -> str:
    raw = capture(["npu-smi", "info"])
    lines = raw.splitlines()
    for physical in range(4, 8):
        if f"No running processes found in NPU {physical}" not in raw:
            raise RuntimeError(f"physical NPU{physical} has a process or unknown state")
        match_at = next(
            (i for i, line in enumerate(lines)
             if re.match(rf"\|\s*{physical}\s+910B4\s*\|", line)), None,
        )
        if match_at is None or match_at + 1 >= len(lines):
            raise RuntimeError(f"cannot parse physical NPU{physical} telemetry")
        detail = lines[match_at + 1].split("|")
        if len(detail) < 5:
            raise RuntimeError(f"cannot parse physical NPU{physical} detail")
        fields = detail[3].split()
        hbm = re.search(r"(\d+)\s*/\s*32768", detail[3])
        if not fields or fields[0] != "0" or hbm is None or int(hbm.group(1)) > 3200:
            raise RuntimeError(f"physical NPU{physical} is not at idle baseline")
    return raw


def main() -> int:
    if not WORKSPACE.is_dir() or not (WORKSPACE / "plugin/qwen36_kascade_probe").is_dir():
        raise RuntimeError("pinned Kascade workspace is absent")
    if RESULTS.exists():
        raise FileExistsError(f"immutable result root exists: {RESULTS}")
    for physical in range(4, 8):
        if not Path(f"/dev/davinci{physical}").exists():
            raise RuntimeError(f"missing physical NPU device {physical}")
    with LOCK.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        snapshot = check_npus()
        running = capture(["docker", "ps", "--format", "{{.Names}}"])
        existing = capture(["docker", "ps", "-a", "--format", "{{.Names}}"])
        if NAME in existing.splitlines():
            raise RuntimeError(f"owned container name already exists: {NAME}")
        capture(["docker", "image", "inspect", IMAGE])
        with socket.socket() as test:
            test.bind(("127.0.0.1", PORT))
        if RESULTS.exists():
            raise FileExistsError(f"result root raced into existence: {RESULTS}")
        RESULTS.mkdir(parents=False, exist_ok=False)
        admission = {
            "schema": "kascade-crosslayer-admission/v2", "time_ns": time.time_ns(),
            "physical_npus": [4, 5, 6, 7], "container_logical_npus": [0, 1, 2, 3],
            "npu_smi_prelaunch": snapshot,
            "other_running_containers": running.splitlines(),
            "image": IMAGE, "container_name": NAME, "port": PORT,
            "status": "admitted_not_started",
        }
        (RESULTS / "admission.json").write_text(
            json.dumps(admission, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        pythonpath = (
            "/workspace/plugin:/workspace/tools:"
            "/usr/local/Ascend/ascend-toolkit/latest/python/site-packages:"
            "/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:"
            "/usr/local/Ascend/cann-9.1.0/python/site-packages:"
            "/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:"
        )
        command = [
            "docker", "run", "-d", "--name", NAME, "--network", "host",
            "--security-opt", "no-new-privileges:true",
            "--device", "/dev/davinci4:/dev/davinci0",
            "--device", "/dev/davinci5:/dev/davinci1",
            "--device", "/dev/davinci6:/dev/davinci2",
            "--device", "/dev/davinci7:/dev/davinci3",
            "--device", "/dev/davinci_manager:/dev/davinci_manager",
            "--device", "/dev/devmm_svm:/dev/devmm_svm",
            "--device", "/dev/hisi_hdc:/dev/hisi_hdc",
            "-v", f"{WORKSPACE}:/workspace:ro",
            "-v", f"{RESULTS}:/results:rw",
            "-v", "/usr/local/Ascend/driver:/usr/local/Ascend/driver:ro",
            "-v", "/cache/efim/Qwen3.6-27B:/models/Qwen3.6-27B:ro",
            "-e", f"PYTHONPATH={pythonpath}",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "QWEN36_KASCADE_PROBE_ENABLE=1",
            "-e", "QWEN36_KASCADE_PROBE_AUDIT=/results/audit.jsonl",
            "-e", "HCCL_OP_EXPANSION_MODE=AIV",
            "-e", "HCCL_NPU_SOCKET_PORT_RANGE=26620-26720",
            "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
            "--entrypoint", "/usr/local/python3.12.13/bin/python3", IMAGE,
            "-m", "vllm.entrypoints.openai.api_server",
            "--model", "/models/Qwen3.6-27B",
            "--served-model-name", "qwen36-kascade-crosslayer-v2",
            "--host", "127.0.0.1", "--port", str(PORT),
            "--data-parallel-size", "1", "--tensor-parallel-size", "4",
            "--max-model-len", "40960", "--max-num-batched-tokens", "40960",
            "--max-num-seqs", "16", "--gpu-memory-utilization", "0.9",
            "--no-enable-prefix-caching", "--enforce-eager", "--trust-remote-code",
        ]
        container_id = capture(command, timeout=120).strip()
        if not container_id:
            raise RuntimeError("docker did not return an owned container id")
        inspected = json.loads(capture(["docker", "inspect", container_id]))[0]
        actual = {item["PathInContainer"]: item["PathOnHost"]
                  for item in inspected["HostConfig"]["Devices"]}
        for logical, physical in enumerate(range(4, 8)):
            if actual.get(f"/dev/davinci{logical}") != f"/dev/davinci{physical}":
                capture(["docker", "stop", container_id], timeout=60)
                raise RuntimeError("device map mismatch; owned service stopped")
        admission["status"] = "started"
        admission["container_id"] = container_id
        admission["device_map"] = actual
        (RESULTS / "admission.json").write_text(
            json.dumps(admission, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({"container_id": container_id, "results": str(RESULTS)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Kascade admission failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
