"""Start one output-preserving FFD mechanism probe on physical NPU4-7.

This creates and retains an owned container. It does not benchmark a candidate.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time


ROOT = Path("/opt/host/vnf/austinov/model-tuning-lab")
WORKSPACE = ROOT / "projects/qwen36-paper-portfolio"
RESULTS = Path("/cache/cch/ffd-qwen36-realprobe-v2-20260928")
LOCK = Path("/cache/cch/ffd-qwen36-realprobe-v2-20260928.admission.lock")
MODEL = Path("/cache/efim/Qwen3.6-27B")
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAME = "qwen36_ffd_realprobe_v2_20260928"
PORT = 8235
OFFICIAL_COMMIT = "ca09458ab1536328e5f46502b27891412733cd6d"


def capture(args: list[str], timeout: int = 30, cwd: Path | None = None) -> str:
    result = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=timeout, check=True, cwd=cwd,
    )
    return result.stdout


def check_npus() -> str:
    raw = capture(["npu-smi", "info"])
    lines = raw.splitlines()
    for physical in range(4, 8):
        if f"No running processes found in NPU {physical}" not in raw:
            raise RuntimeError(f"physical NPU{physical} has a process or unknown state")
        i = next(
            (index for index, line in enumerate(lines)
             if re.match(rf"\|\s*{physical}\s+910B4\s*\|", line)),
            None,
        )
        if i is None or i + 1 >= len(lines):
            raise RuntimeError(f"cannot parse NPU{physical} telemetry")
        fields = lines[i + 1].split("|")
        if len(fields) < 5:
            raise RuntimeError(f"cannot parse NPU{physical} HBM/AICore")
        detail = fields[3]
        if not detail.split() or detail.split()[0] != "0":
            raise RuntimeError(f"NPU{physical} AICore is active")
        hbm = re.search(r"(\d+)\s*/\s*32768", detail)
        if hbm is None or int(hbm.group(1)) > 3200:
            raise RuntimeError(f"NPU{physical} HBM is above idle baseline")
    return raw


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    patch = WORKSPACE / "plugin/qwen36_ffd_probe/patch.py"
    if not patch.is_file() or not MODEL.is_dir():
        raise RuntimeError("probe plugin or model path is missing")
    for physical in range(4, 8):
        if not Path(f"/dev/davinci{physical}").exists():
            raise RuntimeError(f"missing physical NPU{physical} device node")
    with LOCK.open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if RESULTS.exists():
            raise FileExistsError(f"immutable result root exists: {RESULTS}")
        snapshot = check_npus()
        all_names = capture(["docker", "ps", "-a", "--format", "{{.Names}}"]).splitlines()
        if NAME in all_names:
            raise RuntimeError(f"owned container name already exists: {NAME}")
        running = capture(["docker", "ps", "--format", "{{.Names}}"]).splitlines()
        inspected_image = capture(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE]).strip()
        if inspected_image != IMAGE:
            raise RuntimeError(f"image identity mismatch: {inspected_image}")
        with socket.socket() as test:
            test.bind(("127.0.0.1", PORT))
        if RESULTS.exists():
            raise FileExistsError(f"result root raced into existence: {RESULTS}")
        RESULTS.mkdir(parents=False, exist_ok=False)
        admission = {
            "schema": "ffd-realprobe-admission/v1",
            "time_ns": time.time_ns(),
            "status": "admitted_not_started",
            "git_head": capture(["git", "rev-parse", "HEAD"], cwd=ROOT).strip(),
            "plugin_sha256": sha256(patch),
            "official_commit": OFFICIAL_COMMIT,
            "image": IMAGE,
            "model": str(MODEL),
            "physical_npus": [4, 5, 6, 7],
            "container_logical_npus": [0, 1, 2, 3],
            "container_name": NAME,
            "port": PORT,
            "other_running_containers": running,
            "npu_smi_prelaunch": snapshot,
            "claim_scope": "output_preserving_selector_diagnostic_only",
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
            "-v", f"{MODEL}:/models/Qwen3.6-27B:ro",
            "-e", f"PYTHONPATH={pythonpath}",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "QWEN36_FFD_PROBE_ENABLE=1",
            "-e", "QWEN36_FFD_PROBE_AUDIT=/results/audit.jsonl",
            "-e", "HCCL_OP_EXPANSION_MODE=AIV",
            "-e", "HCCL_NPU_SOCKET_PORT_RANGE=26730-26830",
            "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
            "--entrypoint", "/usr/local/python3.12.13/bin/python3",
            IMAGE,
            "-m", "vllm.entrypoints.openai.api_server",
            "--model", "/models/Qwen3.6-27B",
            "--served-model-name", "qwen36-ffd-realprobe-v2",
            "--host", "127.0.0.1", "--port", str(PORT),
            "--data-parallel-size", "1", "--tensor-parallel-size", "4",
            "--max-model-len", "40960",
            "--max-num-batched-tokens", "40960", "--max-num-seqs", "16",
            "--gpu-memory-utilization", "0.9",
            "--no-enable-prefix-caching", "--enforce-eager",
            "--trust-remote-code",
        ]
        container_id = capture(command, timeout=120).strip()
        if not container_id:
            raise RuntimeError("docker did not return an owned container id")
        inspected = json.loads(capture(["docker", "inspect", container_id]))[0]
        actual = {
            item["PathInContainer"]: item["PathOnHost"]
            for item in inspected["HostConfig"]["Devices"]
        }
        for logical, physical in enumerate(range(4, 8)):
            if actual.get(f"/dev/davinci{logical}") != f"/dev/davinci{physical}":
                capture(["docker", "stop", container_id], timeout=60)
                raise RuntimeError("post-launch device map mismatched; owned service stopped")
        admission.update(status="started", container_id=container_id, device_map=actual)
        (RESULTS / "admission.json").write_text(
            json.dumps(admission, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps({"container_id": container_id, "results": str(RESULTS)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FFD admission failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
