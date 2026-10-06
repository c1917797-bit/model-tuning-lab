#!/usr/bin/env python3
"""Exercise the post-treatment disabled control and release owned NPU0-3."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


BASELINE = "qwen36_hypic2048_baseline_npu0_3_v1"
TREATMENT = "qwen36_hypic2048_treatment_npu0_3_v1"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
EXPERIMENT = "hypic-qwen36-e2e-2048-20261006"
PORT = 8223


def command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(name: str) -> dict:
    data = json.loads(command("docker", "inspect", name).stdout)
    if len(data) != 1:
        raise RuntimeError(f"unexpected docker inspect result for {name}")
    return data[0]


def verify_identity(name: str, arm: str, enable: str) -> dict:
    item = inspect(name)
    env = dict(
        entry.split("=", 1)
        for entry in item["Config"]["Env"]
        if "=" in entry
    )
    devices = [
        entry["PathOnHost"]
        for entry in item["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    if not (
        item["Image"] == IMAGE
        and item["Config"]["Labels"].get("hypic.experiment") == EXPERIMENT
        and item["Config"]["Labels"].get("hypic.arm") == arm
        and env.get("VLLM_ASCEND_HYPIC_ENABLE") == enable
        and env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3"
        and devices == [f"/dev/davinci{i}" for i in range(4)]
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and "--no-enable-prefix-caching" in " ".join(item["Config"]["Cmd"])
        and "--tensor-parallel-size 4" in " ".join(item["Config"]["Cmd"])
        and "--max-num-seqs 16" in " ".join(item["Config"]["Cmd"])
    ):
        raise RuntimeError(f"{name}: identity or device mapping mismatch")
    return item


def verify_one_switch_pair(base: dict, treatment: dict) -> None:
    def normalized_command(item: dict) -> list[str]:
        return [
            part.replace("/results/no-cache", "/results/<arm>")
                .replace("/results/hypic-only", "/results/<arm>")
            for part in item["Config"]["Cmd"]
        ]
    if normalized_command(base) != normalized_command(treatment):
        raise RuntimeError("baseline and treatment serving commands differ")
    excluded = {
        "VLLM_ASCEND_HYPIC_ENABLE",
        "VLLM_ASCEND_HYPIC_EVIDENCE_FILE",
    }
    def stable_env(item: dict) -> dict[str, str]:
        return {
            key: value
            for key, value in (
                entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry
            )
            if key not in excluded
        }
    if stable_env(base) != stable_env(treatment):
        raise RuntimeError("baseline and treatment differ beyond declared switch")


def npu_snapshot() -> str:
    return command("npu-smi", "info").stdout


def lane_empty(snapshot: str) -> bool:
    return all(
        f"No running processes found in NPU {index}" in snapshot
        for index in range(4)
    )


def port_snapshot() -> str:
    return command("ss", "-ltn", "sport", f":{PORT}").stdout


def port_free(snapshot: str) -> bool:
    return not re.search(rf":{PORT}(?:\s|$)", snapshot, re.M)


def wait_health(name: str, seconds: int = 2400) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if inspect(name)["State"]["Status"] != "running":
            raise RuntimeError(f"{name}: exited before health")
        try:
            with urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError(f"{name}: health timeout")


def wait_released(seconds: int = 180) -> tuple[str, str]:
    deadline = time.monotonic() + seconds
    last_npu = ""
    last_port = ""
    while time.monotonic() < deadline:
        last_npu = npu_snapshot()
        last_port = port_snapshot()
        if lane_empty(last_npu) and port_free(last_port):
            return last_npu, last_port
        time.sleep(5)
    return last_npu, last_port


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--canary-script", required=True, type=Path)
    parser.add_argument("--remove-owned-containers", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    rollback = root / "rollback"
    rollback.mkdir(parents=True, exist_ok=True)
    receipt_path = root / "rollback-evidence.json"
    lock_path = root / "controller.lock"
    lock = lock_path.open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("controller still owns the experiment; rollback refused")

    def interrupted(_signum: int, _frame: object) -> None:
        raise RuntimeError("rollback interrupted")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    started = datetime.now(timezone.utc)
    error = None
    started_container = False
    disabled_request_passed = False
    treatment_marker_absent = False
    owned_npus_released = False
    port_released = False
    removed = False
    baseline_id = None
    treatment_id = None
    try:
        base = verify_identity(BASELINE, "no-cache", "0")
        treatment = verify_identity(TREATMENT, "hypic-only", "1")
        verify_one_switch_pair(base, treatment)
        baseline_id, treatment_id = base["Id"], treatment["Id"]
        if base["State"]["Status"] != "exited":
            raise RuntimeError("baseline must be exited before rollback test")
        if treatment["State"]["Status"] != "exited":
            raise RuntimeError("treatment must be exited before rollback test")
        if not lane_empty(npu_snapshot()) or not port_free(port_snapshot()):
            raise RuntimeError("NPU0-3 or service port occupied before rollback test")

        command("docker", "start", BASELINE)
        started_container = True
        wait_health(BASELINE)
        canary_path = rollback / "disabled-canary.json"
        command(
            sys.executable,
            str(args.canary_script),
            "--base-url", f"http://127.0.0.1:{PORT}",
            "--model", "qwen36-hypic-e2e-2048",
            "--phase", "rollback-no-cache",
            "--output", str(canary_path),
            "--timeout", "2400",
        )
        canary = json.loads(canary_path.read_text())
        disabled_request_passed = (
            canary.get("schema") == "hypic-active-semantic-canary/v1"
            and canary.get("answer_contains_key") is True
            and canary.get("input_tokens") == 32768
        )
        if not disabled_request_passed:
            raise RuntimeError("post-treatment disabled control failed")
        source_events = root / "no-cache/hypic-evidence.jsonl"
        target_events = rollback / "disabled-evidence.jsonl"
        shutil.copyfile(source_events, target_events)
        treatment_marker_absent = target_events.stat().st_size == 0
        if not treatment_marker_absent:
            raise RuntimeError("disabled control emitted HYPIC treatment evidence")
    except Exception as exc:
        error = str(exc)
    finally:
        try:
            if started_container and inspect(BASELINE)["State"]["Status"] == "running":
                stopped = command("docker", "stop", "--time", "60", BASELINE, check=False)
                if stopped.returncode != 0:
                    raise RuntimeError("baseline docker stop failed")
        except Exception as exc:
            error = (error + "; " if error else "") + str(exc)
        try:
            npu_after, port_after = wait_released()
        except Exception as exc:
            npu_after, port_after = "", ""
            error = (error + "; " if error else "") + str(exc)
        (rollback / "npu-smi-after.txt").write_text(npu_after)
        (rollback / "port-after.txt").write_text(port_after)
        owned_npus_released = lane_empty(npu_after)
        port_released = port_free(port_after)
        if args.remove_owned_containers and error is None and (
            disabled_request_passed and treatment_marker_absent
            and owned_npus_released and port_released
        ):
            try:
                for name, arm, enable, expected_id in (
                    (BASELINE, "no-cache", "0", baseline_id),
                    (TREATMENT, "hypic-only", "1", treatment_id),
                ):
                    item = verify_identity(name, arm, enable)
                    if item["Id"] != expected_id or item["State"]["Status"] != "exited":
                        raise RuntimeError(f"{name}: changed before owned-container removal")
                    command("docker", "rm", name)
                removed = True
            except Exception as exc:
                error = (error + "; " if error else "") + str(exc)
        raw_paths = [
            "rollback/disabled-canary.json",
            "rollback/disabled-evidence.jsonl",
            "rollback/npu-smi-after.txt",
            "rollback/port-after.txt",
        ]
        receipt = {
            "schema": "hypic-e2e-rollback/v1",
            "started_at": started.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "baseline_container_id": baseline_id,
            "treatment_container_id": treatment_id,
            "disabled_request_passed": disabled_request_passed,
            "treatment_marker_absent": treatment_marker_absent,
            "owned_npus_released": owned_npus_released,
            "port_released": port_released,
            "owned_containers_removed": removed,
            "error": error,
            "raw_sha256": {
                rel: sha256(root / rel) for rel in raw_paths if (root / rel).is_file()
            },
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, sort_keys=True))
    return 0 if error is None and disabled_request_passed and treatment_marker_absent and owned_npus_released and port_released else 2


if __name__ == "__main__":
    raise SystemExit(main())
