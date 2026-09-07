#!/usr/bin/env python3
"""Resumable one-arm runner for the formal Qwen3.6 DRRQR Ascend experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


WORKTREE = Path("/cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend")
RECORDS = WORKTREE / ".agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend"
ROOT = Path("/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906")
EXPERIMENT_ID = "state-reduction-qwen36-formal-npu4-7-tp4-20260906"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PORT = 8225
CPUSET = "0-95"
HOST_NPUS = [4, 5, 6, 7]
HCCL_RANGE = "26910-27010"
BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py")
QUALITY = RECORDS / "hypic_quality_eval.py"
LONGBENCH = Path("/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json")
GSM8K = Path("/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl")
EXPECTED = {
    str(BENCHMARK): "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822",
    str(QUALITY): "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0",
    str(LONGBENCH): "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a",
    str(GSM8K): "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
    "/cache/efim/Qwen3.6-27B/config.json": "69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c",
    "/cache/efim/Qwen3.6-27B/model.safetensors.index.json": "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b",
    "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk64/drrqr_manifest.json": "2eaa9a14fffe3dc0cd37906e08bee857be7c9ce2ed761f693a99a0ef02d90c0d",
    "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk96/drrqr_manifest.json": "a8f8f162f15fb6e4717ed509927d93c549a2ef01eca4c88e45e75cdf900b16fc",
}
ARMS = {
    "baseline": {
        "model": "/cache/efim/Qwen3.6-27B",
        "served": "qwen36-state-reduction-baseline",
        "container": "qwen36_state_reduction_baseline_npu4_7_tp4",
        "head_k_dim": 128,
    },
    "drrqr-dk64": {
        "model": "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk64",
        "served": "qwen36-state-reduction-drrqr-dk64",
        "container": "qwen36_state_reduction_drrqr_dk64_npu4_7_tp4",
        "head_k_dim": 64,
    },
    "drrqr-dk96": {
        "model": "/cache/cch/Qwen3.6-27B-gdn-drrqr-dk96",
        "served": "qwen36-state-reduction-drrqr-dk96",
        "container": "qwen36_state_reduction_drrqr_dk96_npu4_7_tp4",
        "head_k_dim": 96,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, text=True, **kwargs)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def write_status(arm: str, phase: str, detail: str) -> None:
    atomic_json(
        ROOT / "controller-status.json",
        {
            "schema": "state-reduction-controller-status/v1",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "arm": arm,
            "phase": phase,
            "detail": detail,
        },
    )


def preflight() -> None:
    for name, expected in EXPECTED.items():
        observed = sha256(Path(name))
        if observed != expected:
            raise RuntimeError(f"hash drift: {name}: {observed} != {expected}")
    run(["docker", "image", "inspect", IMAGE], stdout=subprocess.DEVNULL)
    run([sys.executable, "-m", "py_compile", str(BENCHMARK), str(QUALITY), __file__])
    for arm, spec in ARMS.items():
        if arm == "baseline":
            continue
        expected_dim = spec["head_k_dim"]
        config = json.loads(Path(ARMS[arm]["model"], "config.json").read_text())
        if config["text_config"]["linear_key_head_dim"] != expected_dim:
            raise RuntimeError(
                f"{arm} config does not declare head_k_dim={expected_dim}"
            )


def container_state(name: str) -> str:
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", name],
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "absent"


def port_is_free() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", PORT)) != 0


def lane_is_empty() -> bool:
    for device in HOST_NPUS:
        output = run(
            ["npu-smi", "info", "-t", "proc-mem", "-i", str(device)],
            capture_output=True,
        ).stdout
        if "No process in device" not in output:
            return False
    return True


def wait_lane_empty(timeout_s: int = 180) -> None:
    deadline = time.monotonic() + timeout_s
    while not lane_is_empty():
        if time.monotonic() >= deadline:
            raise RuntimeError("NPU4-7 remained occupied; no process was changed")
        time.sleep(10)


def inspect_container(name: str) -> dict:
    return json.loads(run(["docker", "inspect", name], capture_output=True).stdout)[0]


def verify_container(arm: str, expected_state: str | None = None) -> None:
    spec = ARMS[arm]
    item = inspect_container(spec["container"])
    if expected_state and item["State"]["Status"] != expected_state:
        raise RuntimeError(f"{spec['container']}: unexpected state")
    if item["Image"] != IMAGE or item["HostConfig"]["CpusetCpus"] != CPUSET:
        raise RuntimeError(f"{spec['container']}: image or CPU-set drift")
    device_pairs = [
        (entry["PathOnHost"], entry["PathInContainer"])
        for entry in item["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    expected_pairs = [(f"/dev/davinci{i}", f"/dev/davinci{i - 4}") for i in HOST_NPUS]
    if device_pairs != expected_pairs:
        raise RuntimeError(f"{spec['container']}: device mapping drift {device_pairs}")
    command = " ".join(item["Config"].get("Cmd") or [])
    required = [
        spec["model"],
        "--tensor-parallel-size 4",
        "--max-model-len 40960",
        "--max-num-batched-tokens 16384",
        "--max-num-seqs 16",
        "--no-enable-prefix-caching",
        "--async-scheduling",
    ]
    missing = [value for value in required if value not in command]
    if missing:
        raise RuntimeError(f"{spec['container']}: command drift {missing}")


def create_container(arm: str) -> None:
    spec = ARMS[arm]
    state = container_state(spec["container"])
    if state != "absent":
        verify_container(arm)
        return
    args = [
        "docker", "create",
        "--name", spec["container"],
        "--label", f"paper.experiment={EXPERIMENT_ID}",
        "--label", f"paper.arm={arm}",
        "--network", "host",
        "--shm-size", "800g",
        "--cpuset-cpus", CPUSET,
        "--memory", "48g",
        "--memory-swap", "48g",
    ]
    for host_device in HOST_NPUS:
        args += ["--device", f"/dev/davinci{host_device}:/dev/davinci{host_device - 4}"]
    args += [
        "--device", "/dev/davinci_manager:/dev/davinci_manager",
        "--device", "/dev/devmm_svm:/dev/devmm_svm",
        "--device", "/dev/hisi_hdc:/dev/hisi_hdc",
        "-v", "/usr/local/dcmi:/usr/local/dcmi",
        "-v", "/usr/local/bin/npu-smi:/usr/local/bin/npu-smi",
        "-v", "/usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info",
        "-v", "/usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool",
        "-v", "/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64",
        "-v", "/etc/ascend_install.info:/etc/ascend_install.info",
        "-v", "/cache/efim:/cache/efim:ro",
        "-v", "/cache/cch:/cache/cch:ro",
        "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
        "-e", "HCCL_OP_EXPANSION_MODE=AIV",
        "-e", f"HCCL_NPU_SOCKET_PORT_RANGE={HCCL_RANGE}",
        "-e", "PYTORCH_NPU_ALLOC_CONF=expandable_segments:True",
        "-e", "TASK_QUEUE_ENABLE=1",
        "-e", "OMP_NUM_THREADS=1",
        IMAGE,
        "vllm", "serve", spec["model"],
        "--served-model-name", spec["served"],
        "--host", "127.0.0.1",
        "--port", str(PORT),
        "--data-parallel-size", "1",
        "--tensor-parallel-size", "4",
        "--max-model-len", "40960",
        "--max-num-batched-tokens", "16384",
        "--max-num-seqs", "16",
        "--gpu-memory-utilization", "0.9",
        "--no-enable-prefix-caching",
        "--compilation-config",
        '{"cudagraph_capture_sizes":[1,4,8,12,16,24,32,48,56,64,72,84,96,108,112,128,160,172,196,200,212,232,272,288,312,328,344,360,384,400,416,432,448,480,512],"cudagraph_mode":"FULL_DECODE_ONLY"}',
        "--trust-remote-code",
        "--async-scheduling",
    ]
    run(args, stdout=subprocess.DEVNULL)
    verify_container(arm, "created")


def assert_lane_owned(arm: str) -> None:
    spec = ARMS[arm]
    top = run(
        ["docker", "top", spec["container"], "-eo", "pid"],
        capture_output=True,
    ).stdout.splitlines()[1:]
    container_pids = {int(item.strip()) for item in top if item.strip().isdigit()}
    for device in HOST_NPUS:
        output = run(
            ["npu-smi", "info", "-t", "proc-mem", "-i", str(device)],
            capture_output=True,
        ).stdout
        observed = {int(value) for value in re.findall(r"Process id:(\d+)", output)}
        if not observed or not observed.issubset(container_pids):
            raise RuntimeError(f"NPU{device}: ownership mismatch {observed}")


def start_service(arm: str) -> None:
    spec = ARMS[arm]
    running_others = [
        other
        for other in ARMS
        if other != arm and container_state(ARMS[other]["container"]) == "running"
    ]
    if running_others:
        raise RuntimeError(f"other experiment arm already running: {running_others}")
    if container_state(spec["container"]) == "running":
        verify_container(arm, "running")
    else:
        wait_lane_empty()
        if not port_is_free():
            raise RuntimeError(f"port {PORT} is in use")
        run(["docker", "start", spec["container"]], stdout=subprocess.DEVNULL)
        verify_container(arm, "running")
    write_status(arm, "service-starting", spec["container"])
    deadline = time.monotonic() + 900
    while True:
        healthy = subprocess.run(
            ["curl", "-fsS", f"http://127.0.0.1:{PORT}/health"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0
        if healthy:
            break
        if container_state(spec["container"]) != "running":
            raise RuntimeError(f"{spec['container']} exited before readiness")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{spec['container']} health timeout")
        time.sleep(10)
    assert_lane_owned(arm)
    write_status(arm, "service-ready", spec["container"])


def stop_service(arm: str, phase: str) -> None:
    spec = ARMS[arm]
    if container_state(spec["container"]) == "running":
        verify_container(arm, "running")
        run(["docker", "stop", "--time", "60", spec["container"]], stdout=subprocess.DEVNULL)
    verify_container(arm, "exited")
    wait_lane_empty()
    arm_dir = ROOT / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    with (arm_dir / f"service.{phase}.log").open("w") as stream:
        subprocess.run(["docker", "logs", "--timestamps", spec["container"]], text=True, stdout=stream, stderr=subprocess.STDOUT)
    write_status(arm, f"{phase}-stopped", spec["container"])


def valid_performance(path: Path) -> bool:
    try:
        data = json.loads(path.read_text())
        config = data["config"]
        expected = {
            "input_tokens": 32768,
            "prefix_tokens": 16384,
            "output_tokens": 1024,
            "requests": 40,
            "concurrency": 16,
            "warmup_requests": 2,
            "ignore_eos": True,
            "segment_ends": [16384, 32768],
        }
        summary = data["summary"]
        return (
            all(config.get(key) == value for key, value in expected.items())
            and summary.get("requests") == 40
            and summary.get("successful") == 40
            and summary.get("failed") == 0
            and summary.get("fixed_output_verified") is True
        )
    except Exception:
        return False


def archive_invalid(path: Path) -> None:
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        os.replace(path, path.with_name(path.name + f".invalid.{stamp}"))


def run_performance(arm: str) -> None:
    spec = ARMS[arm]
    arm_dir = ROOT / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    for index in range(1, 4):
        output = arm_dir / f"performance.run{index}.json"
        if valid_performance(output):
            continue
        archive_invalid(output)
        write_status(arm, f"performance-run{index}", str(output))
        command = [
            sys.executable, str(BENCHMARK),
            "--base-url", f"http://127.0.0.1:{PORT}",
            "--model", spec["served"],
            "--input-tokens", "32768",
            "--prefix-tokens", "16384",
            "--output-tokens", "1024",
            "--requests", "40",
            "--concurrency", "16",
            "--warmup-requests", "2",
            "--warmup-evidence-timeout", "300",
            "--timeout", "2400",
            "--json-output", str(output),
        ]
        with (arm_dir / f"performance.run{index}.log").open("w") as log:
            run(command, stdout=log, stderr=subprocess.STDOUT)
        if not valid_performance(output):
            raise RuntimeError(f"invalid performance artifact: {output}")


def run_smoke(arm: str) -> None:
    spec = ARMS[arm]
    arm_dir = ROOT / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    output = arm_dir / "smoke-completion.json"
    payload = json.dumps(
        {
            "model": spec["served"],
            "messages": [
                {
                    "role": "user",
                    "content": "Return exactly: ASCEND_DRRQR_OK",
                }
            ],
            "temperature": 0,
            "seed": 0,
            "max_tokens": 32,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    )
    response = run(
        [
            "curl",
            "-fsS",
            f"http://127.0.0.1:{PORT}/v1/chat/completions",
            "-H",
            "Content-Type: application/json",
            "-d",
            payload,
        ],
        capture_output=True,
    )
    output.write_text(response.stdout)
    body = json.loads(response.stdout)
    observed = body["choices"][0]["message"]["content"].strip()
    if observed != "ASCEND_DRRQR_OK":
        raise RuntimeError(f"unexpected smoke response: {observed!r}")
    write_status(arm, "smoke-complete", str(output))


def valid_quality(summary_path: Path, rows: int) -> bool:
    try:
        data = json.loads(summary_path.read_text())
        return (
            data.get("requests") == rows
            and data.get("successful") == rows
            and data.get("failed") == 0
            and isinstance(data.get("accuracy_pct"), (int, float))
        )
    except Exception:
        return False


def run_quality(arm: str) -> None:
    spec = ARMS[arm]
    quality_dir = ROOT / arm / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    datasets = [
        ("longbenchv2", LONGBENCH, 127),
        ("gsm8k", GSM8K, 1319),
    ]
    for dataset, data_path, rows in datasets:
        for index in range(1, 4):
            summary = quality_dir / f"{dataset}.run{index}.summary.json"
            if valid_quality(summary, rows):
                continue
            write_status(arm, f"quality-{dataset}-run{index}", str(summary))
            command = [
                sys.executable, str(QUALITY),
                "--dataset", dataset,
                "--data", str(data_path),
                "--base-url", f"http://127.0.0.1:{PORT}",
                "--model", spec["served"],
                "--output-dir", str(quality_dir),
                "--run-id", f"run{index}",
                "--concurrency", "32",
                "--max-out-len", "1024",
                "--seed", "0",
                "--timeout", "2400",
                "--retries", "2",
            ]
            with (quality_dir / f"{dataset}.run{index}.log").open("a") as log:
                run(command, stdout=log, stderr=subprocess.STDOUT)
            if not valid_quality(summary, rows):
                raise RuntimeError(f"invalid quality artifact: {summary}")


def snapshot(arm: str, phase: str) -> None:
    spec = ARMS[arm]
    payload = {
        "schema": "state-reduction-runtime-snapshot/v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "arm": arm,
        "phase": phase,
        "model": spec["model"],
        "served_model": spec["served"],
        "head_k_dim": spec["head_k_dim"],
        "image": IMAGE,
        "container": inspect_container(spec["container"]),
        "runner_sha256": sha256(Path(__file__)),
        "benchmark_sha256": sha256(BENCHMARK),
        "quality_evaluator_sha256": sha256(QUALITY),
    }
    atomic_json(ROOT / arm / f"runtime-snapshot.{phase}.json", payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument(
        "--phase", choices=("smoke", "performance", "quality"), required=True
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    preflight()
    if args.self_test:
        print("state-reduction formal runner self-test passed")
        return 0
    ROOT.mkdir(parents=True, exist_ok=True)
    create_container(args.arm)
    current = False
    try:
        start_service(args.arm)
        current = True
        snapshot(args.arm, args.phase)
        if args.phase == "smoke":
            run_smoke(args.arm)
        elif args.phase == "performance":
            run_performance(args.arm)
        else:
            run_quality(args.arm)
        write_status(args.arm, f"{args.phase}-complete", "all three repetitions accepted")
    finally:
        if current or container_state(ARMS[args.arm]["container"]) == "running":
            stop_service(args.arm, args.phase)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
