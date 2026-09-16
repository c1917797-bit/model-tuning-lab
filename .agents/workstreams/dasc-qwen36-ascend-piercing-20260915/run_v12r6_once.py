#!/usr/bin/env python3
"""Run the graph-stable DASC v12r6 canary once, with fail-closed ownership."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request


REPO = Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT = REPO / "projects/dasc_vllm_ascend"
RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "physical-cache-graph-stable-v12r6"
)
PREVIOUS_CANARY = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "physical-cache-order-fix-v12r5/run_physical_canary.py"
)
LOCK = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/controllers/"
    "dasc-qwen36-npu4-7.lock"
)
CONTAINER = "dasc_qwen36_physical_graph_stable_v12r6_20260916"
IMAGE = "quay.io/ascend/vllm-ascend:v0.23.0"
IMAGE_ID = (
    "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
)
NPUS = (4, 5, 6, 7)
IDLE_HBM_LIMIT_MIB = 3932
PORT = 8030
BLOCK_ON_IDLE_CONTAINER_CLAIMS = True
ADDITIONAL_CONFIG: str | None = None
PLUGIN_MODE = "physical-cache-eager"
W_MAX = "64"
CANARY_EXTRA_ARGS: tuple[str, ...] = ()
SUPERSEDED_REASON = (
    "v12r6 is superseded: its per-forward compact restore would erase "
    "omitted-head updates after the first DASC-NR cache-load boundary"
)


def run(args: list[str], *, check: bool = True, timeout: int = 60) -> str:
    result = subprocess.run(
        args,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return result.stdout


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def npu_snapshot() -> tuple[str, dict[int, int], set[int]]:
    raw = run(["/usr/local/bin/npu-smi", "info"], timeout=30)
    hbm: dict[int, int] = {}
    current: int | None = None
    in_processes = False
    processes: set[int] = set()
    for line in raw.splitlines():
        if "Process id" in line:
            in_processes = True
            continue
        device = re.match(r"\|\s*([0-7])\s+910B", line)
        if device and not in_processes:
            current = int(device.group(1))
            continue
        if current is not None and not in_processes:
            pairs = re.findall(r"(\d+)\s*/\s*(\d+)", line)
            if pairs:
                hbm[current] = int(pairs[-1][0])
                current = None
        if in_processes:
            process = re.match(r"\|\s*([0-7])\s+\d+\s+\|\s*(\d+)", line)
            if process:
                processes.add(int(process.group(1)))
    return raw, hbm, processes


def container_claims_from_inspect(item: dict) -> list[int]:
    """Return physical target devices reserved by one running container.

    Explicit Docker device mappings are authoritative because PathOnHost names
    physical devices even when they are renumbered inside the container. Some
    Ascend development containers instead run privileged with no explicit
    device entries and select host devices only through
    ASCEND_RT_VISIBLE_DEVICES. In that case the environment values are
    host-physical reservation claims and must not be ignored.
    """
    host_config = item.get("HostConfig") or {}
    mapped = {
        int(match.group(1))
        for device in host_config.get("Devices") or []
        if (
            match := re.fullmatch(
                r"/dev/davinci([0-7])", device.get("PathOnHost", "")
            )
        )
    }
    if not host_config.get("Privileged"):
        return sorted(mapped.intersection(NPUS))
    visible_prefix = "ASCEND_RT_VISIBLE_DEVICES="
    visible = next(
        (
            value[len(visible_prefix) :]
            for value in (item.get("Config") or {}).get("Env") or []
            if value.startswith(visible_prefix)
        ),
        None,
    )
    if visible is None:
        return sorted(mapped.intersection(NPUS))
    declared = {
        int(value)
        for value in visible.split(",")
        if re.fullmatch(r"[0-7]", value.strip())
    }
    return sorted((mapped | declared).intersection(NPUS))


def docker_claims() -> dict[str, list[int]]:
    ids = run(
        ["/usr/bin/docker", "ps", "-q"], timeout=30
    ).split()
    claims: dict[str, list[int]] = {}
    for container_id in ids:
        item = json.loads(
            run(["/usr/bin/docker", "inspect", container_id], timeout=30)
        )[0]
        claimed = container_claims_from_inspect(item)
        if claimed:
            claims[item["Name"].lstrip("/")] = claimed
    return claims


def port_available() -> bool:
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", PORT))
        return True
    except OSError:
        return False
    finally:
        probe.close()


def runtime_resource_blockers(
    hbm: dict[int, int],
    processes: set[int],
    claims: dict[str, list[int]],
) -> list[str]:
    blockers: list[str] = []
    if set(hbm) != set(range(8)):
        blockers.append(f"could not parse all NPU HBM rows: {sorted(hbm)}")
    for device in NPUS:
        if device in processes:
            blockers.append(f"physical NPU{device} has an active NPU process")
        if hbm.get(device, IDLE_HBM_LIMIT_MIB + 1) > IDLE_HBM_LIMIT_MIB:
            blockers.append(
                f"physical NPU{device} HBM {hbm.get(device)} MiB exceeds "
                f"{IDLE_HBM_LIMIT_MIB} MiB"
            )
    if claims and BLOCK_ON_IDLE_CONTAINER_CLAIMS:
        blockers.append(f"running container device claims: {claims}")
    if not port_available():
        blockers.append(f"port {PORT} is unavailable")
    return blockers


def live_resource_state() -> tuple[dict, list[str]]:
    raw, hbm, processes = npu_snapshot()
    claims = docker_claims()
    state = {
        "hbm_mib": hbm,
        "npu_process_devices": sorted(processes),
        "container_claims": claims,
        "idle_container_claim_policy": (
            "block" if BLOCK_ON_IDLE_CONTAINER_CLAIMS else "record_only"
        ),
        "port": PORT,
        "npu_smi": raw,
    }
    return state, runtime_resource_blockers(hbm, processes, claims)


def preflight() -> tuple[dict, list[str]]:
    state, blockers = live_resource_state()
    if SUPERSEDED_REASON is not None:
        blockers.append(SUPERSEDED_REASON)
    if RESULT.exists():
        blockers.append(f"immutable result root already exists: {RESULT}")
    known = run(
        ["/usr/bin/docker", "ps", "-a", "--filter", f"name=^{CONTAINER}$", "-q"]
    ).strip()
    if known:
        blockers.append(f"owned container name already exists: {CONTAINER}")
    if not PROJECT.is_dir():
        blockers.append(f"plugin project is missing: {PROJECT}")
    if not PREVIOUS_CANARY.is_file():
        blockers.append(f"strict canary is missing: {PREVIOUS_CANARY}")
    status = run(
        ["/usr/bin/git", "status", "--porcelain"], timeout=30
    ).strip()
    if status:
        blockers.append("source repository is dirty")
    image_id = run(
        ["/usr/bin/docker", "image", "inspect", "--format", "{{.Id}}", IMAGE]
    ).strip()
    if image_id != IMAGE_ID:
        blockers.append(f"image identity mismatch: {image_id}")
    state.update({
        "git_head": run(
            ["/usr/bin/git", "rev-parse", "HEAD"], timeout=30
        ).strip(),
        "image": IMAGE,
        "image_id": image_id,
    })
    return state, blockers


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_plugin() -> None:
    snapshot = RESULT / "plugin-snapshot"
    shutil.copytree(
        PROJECT,
        snapshot / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    (snapshot / "site").mkdir()
    try:
        output = run(
            [
                "/usr/bin/docker",
                "run",
                "--rm",
                "--network",
                "none",
                "-e",
                "TORCH_DEVICE_BACKEND_AUTOLOAD=0",
                "-v",
                f"{snapshot / 'src'}:/build/src:ro",
                "-v",
                f"{snapshot / 'site'}:/target",
                IMAGE,
                "/bin/bash",
                "-lc",
                "cp -a /build/src /tmp/dasc-src && "
                "cd /tmp/dasc-src && "
                "/usr/local/python3.12.13/bin/python3 -m pip install "
                "--no-deps --no-build-isolation --target /target .",
            ],
            timeout=600,
        )
    except subprocess.CalledProcessError as error:
        (RESULT / "plugin-install.log").write_text(
            error.stdout or "", encoding="utf-8"
        )
        raise
    (RESULT / "plugin-install.log").write_text(output, encoding="utf-8")
    shutil.copy2(PREVIOUS_CANARY, RESULT / "run_physical_canary.py")


def launch() -> str:
    args = [
        "/usr/bin/docker",
        "run",
        "-d",
        "--name",
        CONTAINER,
        "--network",
        "host",
    ]
    for physical, logical in zip(NPUS, range(4)):
        args.extend(
            ["--device", f"/dev/davinci{physical}:/dev/davinci{logical}"]
        )
    for device in ("/dev/davinci_manager", "/dev/devmm_svm", "/dev/hisi_hdc"):
        args.extend(["--device", device])
    for source, destination, mode in (
        ("/usr/local/dcmi", "/usr/local/dcmi", "ro"),
        ("/cache/efim/Qwen3.6-27B", "/models/Qwen3.6-27B", "ro"),
        (str(RESULT / "plugin-snapshot/site"), "/workspace/dasc", "ro"),
        (str(RESULT), "/dasc-results", "rw"),
        ("/usr/local/bin/npu-smi", "/usr/local/bin/npu-smi", "ro"),
        ("/usr/local/Ascend/driver/lib64", "/usr/local/Ascend/driver/lib64", "ro"),
        (
            "/usr/local/Ascend/driver/version.info",
            "/usr/local/Ascend/driver/version.info",
            "ro",
        ),
        ("/etc/ascend_install.info", "/etc/ascend_install.info", "ro"),
    ):
        args.extend(["-v", f"{source}:{destination}:{mode}"])
    for key, value in {
        "MST_DASC_EVIDENCE_PATH": "/dasc-results/evidence.jsonl",
        "PYTHONPATH": "/workspace/dasc",
        "ASCEND_RT_VISIBLE_DEVICES": "0,1,2,3",
        "VLLM_PLUGINS": "ascend,dasc_vllm_ascend",
        "MST_DASC_ENABLE": "1",
        "MST_DASC_MODE": PLUGIN_MODE,
        "MST_DASC_W_MAX": W_MAX,
    }.items():
        args.extend(["-e", f"{key}={value}"])
    serve_args = [
            IMAGE,
            "vllm",
            "serve",
            "/models/Qwen3.6-27B",
            "--tensor-parallel-size",
            "4",
            "--mamba-cache-mode",
            "align",
            "--enable-prefix-caching",
            "--max-model-len",
            "4096",
            "--max-num-seqs",
            "16",
            "--kv-cache-memory",
            "9663676416",
            "--compilation-config",
            '{"cudagraph_capture_sizes":[1,2,4,8,16],"cudagraph_mode":"FULL_DECODE_ONLY"}',
    ]
    if ADDITIONAL_CONFIG is not None:
        serve_args.extend(["--additional-config", ADDITIONAL_CONFIG])
    serve_args.extend(["--port", str(PORT)])
    args.extend(serve_args)
    return run(args, timeout=60).strip()


def wait_ready() -> None:
    for attempt in range(1, 361):
        state = run(
            [
                "/usr/bin/docker",
                "inspect",
                "--format",
                "{{.State.Running}}",
                CONTAINER,
            ]
        ).strip()
        if state != "true":
            raise RuntimeError("service container exited before readiness")
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/v1/models", timeout=5
            ) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        recent_logs = run(
            ["/usr/bin/docker", "logs", "--tail", "200", CONTAINER],
            check=False,
            timeout=30,
        )
        if (
            "EngineCore failed" in recent_logs
            or "NPUModelRunner init failed" in recent_logs
        ):
            raise RuntimeError("service reported a fatal initialization failure")
        if attempt % 6 == 0:
            print(f"waiting for readiness attempt={attempt}/360", flush=True)
        time.sleep(10)
    raise TimeoutError("service did not become ready")


def preserve() -> None:
    if not RESULT.exists():
        return
    try:
        (RESULT / "service.log").write_text(
            run(
                ["/usr/bin/docker", "logs", CONTAINER],
                check=False,
                timeout=60,
            ),
            encoding="utf-8",
        )
        inspect = json.loads(
            run(["/usr/bin/docker", "inspect", CONTAINER], timeout=30)
        )
        atomic_json(RESULT / "container-inspect.json", inspect)
    except Exception as error:
        (RESULT / "preserve-error.txt").write_text(repr(error), encoding="utf-8")


def validate_allocation_evidence() -> None:
    rows = [
        json.loads(line)
        for line in (RESULT / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]
    initialized = {
        row.get("pid")
        for row in rows
        if row.get("event") == "request_active_state_initialized"
    }
    continued = {
        row.get("pid")
        for row in rows
        if row.get("event") == "request_active_state_continued"
    }
    physical_pids = {row.get("pid") for row in physical}
    checks = []
    for row in physical:
        actual_page = row.get("actual_page_bytes")
        compact_page = row.get("compact_page_bytes")
        persistent = row.get("persistent_bytes")
        num_blocks = row.get("num_blocks")
        checks.append(
            {
                "layer": row.get("layer"),
                "actual_page_bytes": actual_page,
                "compact_page_bytes": compact_page,
                "persistent_bytes": persistent,
                "num_blocks": num_blocks,
                "ok": (
                    row.get("allocation_matches_spec") is True
                    and isinstance(actual_page, int)
                    and actual_page == compact_page
                    and isinstance(num_blocks, int)
                    and persistent == actual_page * num_blocks
                ),
            }
        )
    result = {
        "schema": "mst.dasc.physical-allocation/v1",
        "binding_count": len(physical),
        "checks": checks,
        "request_state_initialized_pids": sorted(initialized),
        "request_state_continued_pids": sorted(continued),
        "physical_cache_pids": sorted(physical_pids),
        "lifecycle_cohort_aligned": (
            len(physical_pids) == 4
            and initialized == physical_pids
            and continued == physical_pids
        ),
        "ok": (
            bool(checks)
            and all(check["ok"] for check in checks)
            and len(physical_pids) == 4
            and initialized == physical_pids
            and continued == physical_pids
        ),
    }
    atomic_json(RESULT / "physical-allocation.json", result)
    if not result["ok"]:
        raise RuntimeError("physical allocation evidence gate failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    state, blockers = preflight()
    if blockers:
        print(json.dumps({"ok": False, "state": state, "blockers": blockers}, indent=2))
        return 2
    if args.preflight_only:
        print(json.dumps({"ok": True, "state": state}, indent=2))
        return 0

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("NPU4-7 lock is held", file=sys.stderr)
            return 2
        state, blockers = preflight()
        if blockers:
            print(json.dumps({"ok": False, "state": state, "blockers": blockers}, indent=2))
            return 2
        container_id = ""
        exit_code = 1
        RESULT.mkdir(parents=False)
        atomic_json(RESULT / "preflight.json", state)
        try:
            snapshot_plugin()
            prelaunch_state, prelaunch_blockers = live_resource_state()
            atomic_json(RESULT / "prelaunch-resource-check.json", prelaunch_state)
            if prelaunch_blockers:
                raise RuntimeError(
                    "prelaunch resource gate failed: "
                    + "; ".join(prelaunch_blockers)
                )
            container_id = launch()
            (RESULT / "container-id.txt").write_text(container_id + "\n")
            wait_ready()
            run(
                [
                    "/usr/bin/python3",
                    str(RESULT / "run_physical_canary.py"),
                    "--output-dir",
                    str(RESULT),
                    "--activation",
                    str(RESULT / "evidence.jsonl"),
                ] + list(CANARY_EXTRA_ARGS),
                timeout=1800,
            )
            validate_allocation_evidence()
            exit_code = 0
        except Exception as error:
            (RESULT / "controller-error.txt").write_text(
                repr(error) + "\n", encoding="utf-8"
            )
            raise
        finally:
            if container_id:
                preserve()
            if container_id:
                run(
                    ["/usr/bin/docker", "stop", "--time", "30", CONTAINER],
                    check=False,
                    timeout=60,
                )
            (RESULT / "npu-after.txt").write_text(
                run(["/usr/local/bin/npu-smi", "info"], timeout=30),
                encoding="utf-8",
            )
            (RESULT / "controller-exit-code.txt").write_text(
                str(exit_code) + "\n", encoding="utf-8"
            )
            files = {
                str(path.relative_to(RESULT)): sha256(path)
                for path in RESULT.rglob("*")
                if path.is_file()
            }
            atomic_json(RESULT / "artifacts.sha256.json", files)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
