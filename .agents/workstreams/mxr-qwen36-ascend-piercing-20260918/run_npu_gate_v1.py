#!/usr/bin/env python3
"""Fail-closed one-shot MXR NPU4 gate controller.

All physical NPU4-7 must be process-free at admission. The probe maps only
physical NPU4 as logical device 0 and continuously rejects any foreign target
PID or any new process on physical NPU5-7. There is no retry loop.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PHYSICAL_NPUS = (4, 5, 6, 7)
MAPPED_NPU = 4
IMAGE = "quay.io/ascend/vllm-ascend:v0.23.0"
IMAGE_ID = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCE_ROOT = Path(
    "/cache/cch/paper-sources/mxr-tri-inverse-20260918/extracted/"
    "megagdn-pto-d357fd38608f99ddf9b9fb2d217b2e731ecd3a72"
)
PTO_LIB = Path(
    "/cache/cch/paper-sources/mxr-tri-inverse-20260918/"
    "pto-isa-01666f3b386f296c95e6e05825fe63b8e6bb4ef4"
)
PTO_COMMIT = "01666f3b386f296c95e6e05825fe63b8e6bb4ef4"
ARCHIVES = {
    Path("/cache/cch/paper-sources/mxr-tri-inverse-20260918/megagdn-pto-d357fd3.zip"):
        "4131a3b24e5b7d9a137574867b708c4ff03c547a956861637d508da958dad06d",
    Path("/cache/cch/paper-sources/mxr-tri-inverse-20260918/pto-kernels-282ed20.zip"):
        "8f57db5eb3f3c87608f54a957c7e6c8aa2374d92221efc61dd5a92648681b856",
}
RESULT = Path("/cache/cch/mxr-qwen36-ascend-20260918/npu-gate-v1")
LOCK = Path("/cache/cch/.locks/mxr-qwen36-npu4-7.lock")
CONTAINER = "mxr_qwen36_npu_gate_v1_20260918"
PROCESS_RE = re.compile(r"Process id:\s*(\d+)")


def run(args: list[str], *, check: bool = True, timeout: int = 30) -> str:
    result = subprocess.run(
        args,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout + result.stderr


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def device_pids(card: int) -> set[int]:
    text = run(
        ["/usr/local/bin/npu-smi", "info", "-t", "proc-mem", "-i", str(card), "-c", "0"]
    )
    return {int(value) for value in PROCESS_RE.findall(text)}


def target_snapshot() -> dict[int, set[int]]:
    return {card: device_pids(card) for card in PHYSICAL_NPUS}


def parse_top(text: str) -> set[int]:
    return {int(line.strip()) for line in text.splitlines() if line.strip().isdigit()}


def container_pids() -> set[int]:
    text = run(["/usr/bin/docker", "top", CONTAINER, "-eo", "pid"], check=False)
    return parse_top(text)


def ownership_verdict(snapshot: dict[int, set[int]], owned: set[int]) -> dict:
    mapped_foreign = sorted(snapshot.get(MAPPED_NPU, set()) - owned)
    unmapped = {
        str(card): sorted(snapshot.get(card, set()))
        for card in PHYSICAL_NPUS
        if card != MAPPED_NPU and snapshot.get(card)
    }
    return {
        "physical_npus": list(PHYSICAL_NPUS),
        "mapped_physical_npu": MAPPED_NPU,
        "observed": {str(card): sorted(snapshot.get(card, set())) for card in PHYSICAL_NPUS},
        "owned": sorted(owned),
        "mapped_foreign": mapped_foreign,
        "unmapped_processes": unmapped,
        "ok": not mapped_foreign and not unmapped,
    }


def source_manifest() -> dict:
    archive_rows = []
    for path, expected in ARCHIVES.items():
        actual = sha256(path)
        archive_rows.append(
            {"path": str(path), "expected_sha256": expected, "actual_sha256": actual, "ok": actual == expected}
        )
    pto_head = run(["/usr/bin/git", "-C", str(PTO_LIB), "rev-parse", "HEAD"]).strip()
    required = [
        SOURCE_ROOT / "megagdn_pto" / "compile.py",
        SOURCE_ROOT / "kernels" / "pto" / "tri_inverse.cpp",
        SOURCE_ROOT / "kernels" / "pto" / "mega_kernel.cpp",
        PTO_LIB / "include",
        HERE / "mxr_npu_probe.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    return {
        "archives": archive_rows,
        "pto_commit_expected": PTO_COMMIT,
        "pto_commit_actual": pto_head,
        "required_paths": [str(path) for path in required],
        "missing_paths": missing,
        "ok": all(row["ok"] for row in archive_rows) and pto_head == PTO_COMMIT and not missing,
    }


def docker_command() -> list[str]:
    args = [
        "/usr/bin/docker",
        "run",
        "--rm",
        "--name",
        CONTAINER,
        "--device",
        "/dev/davinci4:/dev/davinci0",
    ]
    for device in ("/dev/davinci_manager", "/dev/devmm_svm", "/dev/hisi_hdc"):
        args.extend(["--device", device])
    for source, destination, mode in (
        (SOURCE_ROOT, Path("/workspace/megagdn"), "ro"),
        (PTO_LIB, Path("/workspace/pto-isa"), "ro"),
        (REPO, Path("/workspace/model-tuning-lab"), "ro"),
        (RESULT, Path("/results"), "rw"),
        (Path("/usr/local/dcmi"), Path("/usr/local/dcmi"), "ro"),
        (Path("/usr/local/bin/npu-smi"), Path("/usr/local/bin/npu-smi"), "ro"),
        (Path("/usr/local/Ascend/driver/lib64"), Path("/usr/local/Ascend/driver/lib64"), "ro"),
        (Path("/usr/local/Ascend/driver/version.info"), Path("/usr/local/Ascend/driver/version.info"), "ro"),
        (Path("/etc/ascend_install.info"), Path("/etc/ascend_install.info"), "ro"),
    ):
        args.extend(["-v", f"{source}:{destination}:{mode}"])
    for key, value in (
        ("ASCEND_RT_VISIBLE_DEVICES", "0"),
        ("PTO_LIB_PATH", "/workspace/pto-isa"),
        ("GDN_COMPILED_DIR", "/results/compiled"),
        ("PTO_MEMORY_MODEL", "MEMORY_BASE"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
    ):
        args.extend(["-e", f"{key}={value}"])
    args.extend(
        [
            IMAGE,
            "/usr/local/python3.12.13/bin/python3",
            "/workspace/model-tuning-lab/.agents/workstreams/"
            "mxr-qwen36-ascend-piercing-20260918/mxr_npu_probe.py",
            "--source-root",
            "/workspace/megagdn",
            "--pto-lib",
            "/workspace/pto-isa",
            "--output-dir",
            "/results",
            "--phase",
            "all",
        ]
    )
    return args


def preflight() -> dict:
    if RESULT.exists():
        raise RuntimeError(f"refusing to overwrite immutable result root: {RESULT}")
    manifest = source_manifest()
    image_id = run(["/usr/bin/docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"]).strip()
    name_rows = run(
        ["/usr/bin/docker", "ps", "-a", "--filter", f"name=^{CONTAINER}$", "--format", "{{.ID}}"],
    ).strip()
    snapshot = target_snapshot()
    checks = {
        "source_manifest": manifest["ok"],
        "image_identity": image_id == IMAGE_ID,
        "container_name_absent": not name_rows,
        "all_target_cards_process_free": not any(snapshot.values()),
    }
    return {
        "schema": "mst.mxr.npu-preflight/v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": manifest,
        "image": IMAGE,
        "expected_image_id": IMAGE_ID,
        "actual_image_id": image_id,
        "container": CONTAINER,
        "target_processes": {str(card): sorted(pids) for card, pids in snapshot.items()},
        "checks": checks,
        "ok": all(checks.values()),
    }


def monitor(stop: threading.Event, violations: list[dict]) -> None:
    while not stop.wait(0.5):
        try:
            verdict = ownership_verdict(target_snapshot(), container_pids())
        except BaseException as error:
            verdict = {"ok": False, "error": repr(error), "error_type": type(error).__name__}
        if verdict["ok"]:
            continue
        violations.append(verdict)
        atomic_json(RESULT / "resource-race.json", verdict)
        run(["/usr/bin/docker", "stop", "--time", "1", CONTAINER], check=False, timeout=10)
        return


def artifact_manifest() -> dict:
    rows = []
    for path in sorted(RESULT.rglob("*")):
        if path.is_file() and not path.name.endswith(".tmp"):
            rows.append({"path": str(path.relative_to(RESULT)), "sha256": sha256(path), "size": path.stat().st_size})
    return {"schema": "mst.mxr.artifacts/v1", "files": rows}


def self_test() -> int:
    assert parse_top("PID\n123\nnot-a-pid\n456\n") == {123, 456}
    assert ownership_verdict({4: {10}, 5: set(), 6: set(), 7: set()}, {10})["ok"]
    assert not ownership_verdict({4: {10, 11}, 5: set(), 6: set(), 7: set()}, {10})["ok"]
    assert not ownership_verdict({4: {10}, 5: {12}, 6: set(), 7: set()}, {10})["ok"]
    command = docker_command()
    joined = " ".join(command)
    assert "/dev/davinci4:/dev/davinci0" in joined
    for forbidden in ("/dev/davinci5", "/dev/davinci6", "/dev/davinci7"):
        assert forbidden not in joined
    assert "--phase all" in joined
    print("PASS: MXR NPU gate controller self-test")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.preflight_only:
        gate = preflight()
        print(json.dumps(gate, indent=2, sort_keys=True))
        return 0 if gate["ok"] else 4

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        gate = preflight()
        if not gate["ok"]:
            print(json.dumps(gate, indent=2, sort_keys=True))
            return 4
        # Close the admission race immediately before creating the immutable root.
        second = preflight()
        if not second["ok"]:
            print(json.dumps(second, indent=2, sort_keys=True))
            return 4
        RESULT.mkdir(parents=True, exist_ok=False)
        atomic_json(RESULT / "preflight.json", second)
        (RESULT / "controller-command.json").write_text(
            json.dumps(docker_command(), indent=2) + "\n", encoding="utf-8"
        )

        violations: list[dict] = []
        stop = threading.Event()
        watcher = threading.Thread(target=monitor, args=(stop, violations), daemon=True)
        watcher.start()
        exit_code = 1
        output = ""
        try:
            process = subprocess.run(
                docker_command(),
                capture_output=True,
                text=True,
                timeout=3600,
            )
            exit_code = process.returncode
            output = process.stdout + process.stderr
        finally:
            stop.set()
            watcher.join(timeout=5)
            run(["/usr/bin/docker", "stop", "--time", "1", CONTAINER], check=False, timeout=10)
        (RESULT / "container.log").write_text(output, encoding="utf-8")
        final_snapshot = target_snapshot()
        final = {
            "schema": "mst.mxr.npu-controller-result/v1",
            "container_exit_code": exit_code,
            "monitor_violations": violations,
            "final_target_processes": {str(card): sorted(pids) for card, pids in final_snapshot.items()},
            "ok": exit_code == 0 and not violations and not any(final_snapshot.values()),
        }
        atomic_json(RESULT / "controller-result.json", final)
        atomic_json(RESULT / "artifacts.sha256.json", artifact_manifest())
        return 0 if final["ok"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
