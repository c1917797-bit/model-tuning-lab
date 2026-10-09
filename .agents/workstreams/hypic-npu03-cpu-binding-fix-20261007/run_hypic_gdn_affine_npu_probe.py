"""Own, guard, and release one pinned-image physical-NPU0 GDN diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


WORKTREE = Path("/cache/cch/model-tuning-lab-hypic-e2e-20261006")
PLUGIN = Path("/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008")
RAW = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/gdn-affine-20261009-r4")
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCE = "c12060cd47e7575ead059983d7a8bb4704165c98"
NAME = "hypic_gdn_affine_npu03_20261009_r4"
LABEL = "hypic.gdn.affine=gdn-affine-20261009-r4"
NUMBERED_DEVICES = tuple(f"/dev/davinci{i}" for i in range(4))
DRIVER_BINDS = (
    "/usr/local/Ascend/driver/tools/hccn_tool",
    "/etc/ascend_install.info",
    "/usr/local/dcmi",
    "/usr/local/bin/npu-smi",
    "/usr/local/Ascend/driver/version.info",
    "/usr/local/Ascend/driver/lib64",
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(*argv: str, timeout: int = 30, check: bool = True):
    completed = subprocess.run(
        argv, text=True, capture_output=True, timeout=timeout, check=False
    )
    if check and completed.returncode:
        raise RuntimeError(
            f"{argv[0]} exited {completed.returncode}: {completed.stderr[:1200]}"
        )
    return completed


def inspect(identity: str) -> dict | None:
    result = run("docker", "inspect", identity, check=False)
    if result.returncode:
        return None
    objects = json.loads(result.stdout)
    return objects[0] if len(objects) == 1 else None


def npu_processes(snapshot: str) -> list[dict[str, int]]:
    rows = [
        {"physical_npu": int(card), "pid": int(pid)}
        for card, pid in re.findall(
            r"^\|\s*([0-3])\s+0\s*\|\s*(\d+)\s*\|", snapshot, re.M
        )
    ]
    for card in range(4):
        if (
            f"No running processes found in NPU {card}" not in snapshot
            and not any(row["physical_npu"] == card for row in rows)
        ):
            raise RuntimeError(f"physical NPU{card} process section incomplete")
    return rows


def save_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if RAW.exists():
        raise RuntimeError(f"immutable diagnostic root already exists: {RAW}")
    if inspect(NAME) is not None:
        raise RuntimeError(f"exact diagnostic container name already exists: {NAME}")
    if run("git", "-C", str(PLUGIN), "rev-parse", "HEAD").stdout.strip() != SOURCE:
        raise RuntimeError("plugin source commit drifted")
    if run("git", "-C", str(PLUGIN), "status", "--porcelain").stdout.strip():
        raise RuntimeError("plugin source is dirty")
    if run("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}").stdout.strip() != IMAGE:
        raise RuntimeError("pinned image digest unavailable")
    for bind in DRIVER_BINDS:
        if not Path(bind).exists():
            raise RuntimeError(f"frozen driver source missing: {bind}")
    before = run("npu-smi", "info").stdout
    if npu_processes(before):
        raise RuntimeError("physical NPU0-3 not actually idle")
    listeners = run("ss", "-lntp").stdout
    if re.search(r":8223\s", listeners):
        raise RuntimeError("HYPIC service port 8223 is occupied")
    if args.preflight:
        print(json.dumps({
            "preflight": "passed",
            "physical_npus_0_3": "no running processes",
            "port_8223": "not listening",
            "pinned_image": IMAGE,
            "source_commit": SOURCE,
            "new_root": str(RAW),
            "container_name": NAME,
        }, sort_keys=True))
        return

    RAW.mkdir(parents=True)
    (RAW / "npu-before.txt").write_text(before, encoding="utf-8")
    (RAW / "docker-before.txt").write_text(
        run("docker", "ps", "--no-trunc").stdout, encoding="utf-8"
    )
    owned_id: str | None = None
    events: list[dict] = []
    failures: list[dict] = []
    saw_owned_npu0 = False
    exit_code: int | None = None
    released = False
    try:
        argv = [
            "docker", "create", "--name", NAME, "--label", LABEL,
            "--network", "none", "--shm-size", "1073741824",
            "--cpuset-cpus", "112-191",
            "--device", "/dev/davinci_manager:/dev/davinci_manager:rwm",
            "--device", "/dev/devmm_svm:/dev/devmm_svm:rwm",
            "--device", "/dev/hisi_hdc:/dev/hisi_hdc:rwm",
        ]
        for device in NUMBERED_DEVICES:
            argv += ["--device", f"{device}:{device}:rwm"]
        for bind in DRIVER_BINDS:
            argv += ["-v", f"{bind}:{bind}:ro"]
        argv += [
            "-v", f"{WORKTREE}:/study:ro",
            "-v", f"{PLUGIN}:/plugin:ro",
            "-v", f"{RAW}:/results:rw",
            "-e", "PYTHONPATH=/plugin",
            "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3",
            IMAGE, "python3", "-B",
            "/study/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/"
            "hypic_gdn_affine_device_probe.py",
            "--output", "/results",
        ]
        owned_id = run(*argv, timeout=60).stdout.strip()
        item = inspect(owned_id)
        if item is None:
            raise RuntimeError("created container cannot be inspected")
        numbered = [
            entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
            if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
        ]
        if not (
            item["Id"] == owned_id
            and item["Image"] == IMAGE
            and item["Name"] == f"/{NAME}"
            and item["Config"]["Labels"].get("hypic.gdn.affine")
            == "gdn-affine-20261009-r4"
            and numbered == list(NUMBERED_DEVICES)
            and all(bind + ":" + bind + ":ro" in item["HostConfig"]["Binds"]
                    for bind in DRIVER_BINDS)
            and item["HostConfig"]["NetworkMode"] == "none"
            and "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3" in item["Config"]["Env"]
        ):
            raise RuntimeError("exact owned container or physical NPU mapping drift")
        save_json(RAW / "container-inspect.json", {
            "id": owned_id, "image": item["Image"], "name": item["Name"],
            "devices": item["HostConfig"]["Devices"],
            "binds": item["HostConfig"]["Binds"],
            "env": item["Config"]["Env"],
            "labels": item["Config"]["Labels"],
            "network_mode": item["HostConfig"]["NetworkMode"],
        })
        run("docker", "start", owned_id)
        deadline = time.monotonic() + 240
        while time.monotonic() < deadline:
            snapshot = run("npu-smi", "info", timeout=20).stdout
            rows = npu_processes(snapshot)
            top = run("docker", "top", owned_id, "-eo", "pid,comm", check=False)
            owned_pids = {
                int(parts[0]) for line in top.stdout.splitlines()[1:]
                if (parts := line.split()) and parts[0].isdigit()
            }
            classified = []
            for row in rows:
                pid = row["pid"]
                try:
                    cgroup = (Path("/proc") / str(pid) / "cgroup").read_text(
                        errors="replace"
                    )
                except OSError:
                    cgroup = ""
                is_owned = pid in owned_pids or owned_id in cgroup
                if is_owned and row["physical_npu"] == 0:
                    saw_owned_npu0 = True
                classified.append({
                    **row, "owned": is_owned,
                    "cgroup": cgroup[:1000] if not is_owned else "",
                })
            events.append({"at_utc": utc(), "processes": classified})
            foreign = [row for row in classified if not row["owned"]]
            unexpected_owned = [row for row in classified
                                if row["owned"] and row["physical_npu"] != 0]
            if foreign:
                failures.append({"at_utc": utc(), "foreign_processes": foreign})
                break
            if unexpected_owned:
                failures.append({"at_utc": utc(), "unexpected_owned_processes": unexpected_owned})
                break
            item = inspect(owned_id)
            if item is None:
                failures.append({"at_utc": utc(), "error": "owned container disappeared"})
                break
            if item["State"]["Status"] == "exited":
                exit_code = int(item["State"]["ExitCode"])
                break
            time.sleep(1)
        else:
            failures.append({"at_utc": utc(), "error": "240-second probe deadline"})
    except Exception as exc:
        failures.append({"at_utc": utc(), "error": f"{type(exc).__name__}: {exc}"})
    finally:
        if owned_id is not None:
            item = inspect(owned_id)
            if item is not None and item["Id"] == owned_id and item["Name"] == f"/{NAME}":
                if item["State"]["Status"] == "running":
                    run("docker", "stop", "--time", "10", owned_id, timeout=30, check=False)
                logs = run("docker", "logs", owned_id, timeout=30, check=False)
                (RAW / "container.log").write_text(
                    logs.stdout + logs.stderr, encoding="utf-8"
                )
                run("docker", "rm", owned_id, timeout=30, check=False)
                released = inspect(owned_id) is None
        save_json(RAW / "lane-guard.json", {
            "schema": "hypic-gdn-affine-lane-guard/v1",
            "owned_container_id": owned_id,
            "samples": events,
            "failures": failures,
            "saw_owned_physical_npu0_process": saw_owned_npu0,
        })
        after = run("npu-smi", "info", timeout=20, check=False)
        (RAW / "npu-after.txt").write_text(after.stdout, encoding="utf-8")
        output = RAW / "result.json"
        tensors = RAW / "tensors.pt"
        valid = bool(
            not failures and exit_code == 0 and saw_owned_npu0 and released
            and output.is_file() and tensors.is_file() and after.returncode == 0
        )
        terminal = {
            "schema": "hypic-gdn-affine-terminal/v1",
            "at_utc": utc(),
            "valid": valid,
            "container_exit_code": exit_code,
            "owned_container_id": owned_id,
            "owned_resource_released": released,
            "guard_sample_count": len(events),
            "guard_failures": failures,
            "saw_owned_physical_npu0_process": saw_owned_npu0,
            "result_sha256": sha(output) if output.is_file() else None,
            "tensors_sha256": sha(tensors) if tensors.is_file() else None,
        }
        save_json(RAW / "terminal.json", terminal)
        print(json.dumps(terminal, sort_keys=True), flush=True)
        if not valid:
            sys.exit(1)


if __name__ == "__main__":
    main()
