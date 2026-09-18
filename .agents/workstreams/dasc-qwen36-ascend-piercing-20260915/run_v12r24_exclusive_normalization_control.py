#!/usr/bin/env python3
"""Run the v12r23 gate in a pinned existing container when Docker cannot mount."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import time
import urllib.request


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r23_trial",
    HERE / "run_v12r23_race_identity_control.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r23 race-identity controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "kernel-block-normalization-exclusive-v12r24"
)
controller.CONTAINER = "alltoall-dedup-ep4_nk"

REUSED_CONTAINER_ID = (
    "fd2be986b54d2ac96d30b5c3fbc5785ba7c1f9703d812275d0fa0d48204622b5"
)
SERVICE_LOG = controller.RESULT / "service.live.log"
_base_preflight = controller.preflight


def _reused_container_inspect() -> dict:
    return json.loads(
        controller.run(
            ["/usr/bin/docker", "inspect", controller.CONTAINER], timeout=30
        )
    )[0]


def _reused_container_identity_blockers(item: dict) -> list[str]:
    blockers: list[str] = []
    if item.get("Id") != REUSED_CONTAINER_ID:
        blockers.append(
            "reused container identity mismatch: "
            f"{item.get('Id')} != {REUSED_CONTAINER_ID}"
        )
    if item.get("Image") != controller.IMAGE_ID:
        blockers.append(
            "reused container image mismatch: "
            f"{item.get('Image')} != {controller.IMAGE_ID}"
        )
    if (item.get("State") or {}).get("Running") is not True:
        blockers.append("reused container is not running")
    if (item.get("HostConfig") or {}).get("Privileged") is not True:
        blockers.append("reused container is not privileged")
    devices = (item.get("HostConfig") or {}).get("Devices") or []
    if devices:
        blockers.append(f"reused container has unexpected device mappings: {devices}")
    cache_mounts = [
        mount
        for mount in item.get("Mounts") or []
        if mount.get("Source") == "/cache"
        and mount.get("Destination") == "/cache"
        and mount.get("RW") is True
    ]
    if len(cache_mounts) != 1:
        blockers.append("reused container lacks the exact writable /cache bind")
    top = controller.run(
        [
            "/usr/bin/docker",
            "top",
            controller.CONTAINER,
            "-eo",
            "pid,ppid,cmd",
        ],
        timeout=30,
    )
    process_rows = [
        line.split(None, 2)[-1].strip()
        for line in top.splitlines()[1:]
        if line.strip()
    ]
    if process_rows != ["sleep infinity"]:
        blockers.append(
            "reused container is not quiescent: " + repr(process_rows)
        )
    return blockers


def preflight() -> tuple[dict, list[str]]:
    state, blockers = _base_preflight()
    existing_name = (
        f"owned container name already exists: {controller.CONTAINER}"
    )
    blockers = [blocker for blocker in blockers if blocker != existing_name]
    item = _reused_container_inspect()
    blockers.extend(_reused_container_identity_blockers(item))
    state["existing_container_reuse"] = {
        "container": controller.CONTAINER,
        "container_id": item.get("Id"),
        "image_id": item.get("Image"),
        "policy": (
            "exact-id exact-image quiescent-process-tree controlled takeover; "
            "physical devices selected only by per-exec ASCEND_RT_VISIBLE_DEVICES"
        ),
    }
    return state, blockers


def snapshot_plugin() -> None:
    snapshot = controller.RESULT / "plugin-snapshot"
    shutil.copytree(
        controller.PROJECT,
        snapshot / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    (snapshot / "site").mkdir()
    source = snapshot / "src"
    target = snapshot / "site"
    build_script = (
        "set -e\n"
        "build_dir=$(mktemp -d /tmp/dasc-v12r24-build.XXXXXX)\n"
        f"cp -a {shlex.quote(str(source))}/. \"$build_dir/\"\n"
        "cd \"$build_dir\"\n"
        "/usr/local/python3.12.13/bin/python3 -m pip install "
        "--no-deps --no-build-isolation "
        f"--target {shlex.quote(str(target))} ."
    )
    output = controller.run(
        [
            "/usr/bin/docker",
            "exec",
            controller.CONTAINER,
            "/bin/bash",
            "-lc",
            build_script,
        ],
        timeout=600,
    )
    (controller.RESULT / "plugin-install.log").write_text(
        output, encoding="utf-8"
    )
    shutil.copy2(
        controller.PREVIOUS_CANARY,
        controller.RESULT / "run_physical_canary.py",
    )


def launch() -> str:
    env = {
        "MST_DASC_EVIDENCE_PATH": str(
            controller.RESULT / "evidence.jsonl"
        ),
        "PYTHONPATH": str(controller.RESULT / "plugin-snapshot/site"),
        "ASCEND_RT_VISIBLE_DEVICES": "4,5,6,7",
        "VLLM_PLUGINS": "ascend,dasc_vllm_ascend",
        "MST_DASC_ENABLE": "1",
        "MST_DASC_MODE": controller.PLUGIN_MODE,
        "MST_DASC_W_MAX": controller.W_MAX,
    }
    command = [
        "vllm",
        "serve",
        "/cache/efim/Qwen3.6-27B",
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
    if controller.ADDITIONAL_CONFIG is not None:
        command.extend(
            ["--additional-config", controller.ADDITIONAL_CONFIG]
        )
    command.extend(["--port", str(controller.PORT)])
    shell = (
        "source /usr/local/Ascend/ascend-toolkit/set_env.sh\n"
        "source "
        "/usr/local/Ascend/cann-9.1.0/share/info/ascendnpu-ir/bin/set_env.sh\n"
        "source /usr/local/Ascend/nnal/atb/set_env.sh "
        "--cxx_abi=${ATB_CXX_ABI:-1}\n"
        f"exec {shlex.join(command)} >> {shlex.quote(str(SERVICE_LOG))} 2>&1"
    )
    args = ["/usr/bin/docker", "exec", "-d"]
    for key, value in env.items():
        args.extend(["-e", f"{key}={value}"])
    args.extend([controller.CONTAINER, "/bin/bash", "-lc", shell])
    controller.run(args, timeout=60)
    (controller.RESULT / "service-launch.json").write_text(
        json.dumps(
            {
                "container": controller.CONTAINER,
                "container_id": REUSED_CONTAINER_ID,
                "physical_npus": list(controller.NPUS),
                "visible_devices": env["ASCEND_RT_VISIBLE_DEVICES"],
                "command": command,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return REUSED_CONTAINER_ID


def wait_ready() -> None:
    for attempt in range(1, 361):
        state = controller.run(
            [
                "/usr/bin/docker",
                "inspect",
                "--format",
                "{{.State.Running}}",
                controller.CONTAINER,
            ]
        ).strip()
        if state != "true":
            raise RuntimeError("reused service container exited before readiness")
        trial.validate_startup_ownership()
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{controller.PORT}/v1/models", timeout=5
            ) as response:
                if response.status == 200:
                    trial.validate_startup_ownership()
                    return
        except Exception:
            pass
        recent_logs = (
            SERVICE_LOG.read_text(encoding="utf-8", errors="replace")[-50000:]
            if SERVICE_LOG.is_file()
            else ""
        )
        if (
            "EngineCore failed" in recent_logs
            or "NPUModelRunner init failed" in recent_logs
        ):
            trial.validate_startup_ownership()
            raise RuntimeError("service reported a fatal initialization failure")
        if attempt % 6 == 0:
            print(f"waiting for readiness attempt={attempt}/360", flush=True)
        time.sleep(10)
    raise TimeoutError("service did not become ready")


def preserve() -> None:
    try:
        item = _reused_container_inspect()
        controller.atomic_json(
            controller.RESULT / "container-inspect.json", [item]
        )
        if SERVICE_LOG.is_file():
            shutil.copy2(SERVICE_LOG, controller.RESULT / "service.log")
    except Exception as error:
        (controller.RESULT / "preserve-error.txt").write_text(
            repr(error), encoding="utf-8"
        )


controller.preflight = preflight
controller.snapshot_plugin = snapshot_plugin
controller.launch = launch
controller.wait_ready = wait_ready
controller.preserve = preserve


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
