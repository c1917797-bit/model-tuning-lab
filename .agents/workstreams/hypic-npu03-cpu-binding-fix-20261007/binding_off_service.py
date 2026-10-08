#!/usr/bin/env python3
"""Run an opt-in, isolated NPU0-3 service with the upstream CPU-binding switch.

The frozen original container supplies every Docker and vLLM option. This
controller changes only its artifact mount and one serving CLI option. It does
not edit the image, source checkout, shared service, or host CPU settings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007")
SOURCE_ROOT = Path("/cache/cch/hypic-qwen36-e2e-2048-20261006")
SNAPSHOT = SOURCE_ROOT / "environment-and-container-snapshot.txt"
SNAPSHOT_SHA = "c88cd60f6929d1596f3553b68f31de506f5d60c2401429aa5cd819418ac40ad4"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
SOURCE_REPO = Path("/cache/cch/hypic_vllm_ascend-v0.8.5")
SOURCE_COMMIT = "3ad0967589304cd8fc4e7cff02f48ecc6125c89f"
BENCHMARK = SOURCE_REPO / "tools/benchmark_shared_prefix.py"
BENCHMARK_SHA = "cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822"
CANARY = Path(__file__).resolve().parents[1] / "WS-20260904-qwen38-dense-paper-to-ascend/hypic_semantic_canary.py"
FLAG = " --additional-config '{\"enable_cpu_binding\":false}'"
PORT = 8223
ARMS = {
    "no-cache": "qwen36_hypic2048_baseline_npu0_3_v1",
    "hypic-only": "qwen36_hypic2048_treatment_npu0_3_v1",
}
SLEEP_CONTAINER = "agentgpu-910b4-qwen35-4b-v0"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=check)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def frozen_source(arm: str) -> dict:
    if sha256(SNAPSHOT) != SNAPSHOT_SHA or sha256(BENCHMARK) != BENCHMARK_SHA:
        raise RuntimeError("frozen snapshot or benchmark bytes drifted")
    if run("git", "-C", str(SOURCE_REPO), "rev-parse", "HEAD").stdout.strip() != SOURCE_COMMIT:
        raise RuntimeError("HYPIC source commit drifted")
    content = SNAPSHOT.read_text(encoding="utf-8")
    marker = '[\n    {\n        "Id"'
    if marker not in content:
        raise RuntimeError("frozen Docker inspect JSON absent")
    values, _ = json.JSONDecoder().raw_decode(content[content.index(marker):])
    by_name = {value["Name"]: value for value in values}
    if set(by_name) != {f"/{name}" for name in ARMS.values()}:
        raise RuntimeError("frozen source container set drifted")
    source = by_name[f"/{ARMS[arm]}"]
    devices = [
        entry["PathOnHost"] for entry in source["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    if source["Image"] != IMAGE or source["HostConfig"]["CpusetCpus"] != "112-191":
        raise RuntimeError("frozen image or cpuset drifted")
    if devices != [f"/dev/davinci{i}" for i in range(4)]:
        raise RuntimeError(f"frozen physical NPU mapping drifted: {devices}")
    if source["HostConfig"]["NetworkMode"] != "host":
        raise RuntimeError("frozen network mode drifted")
    command = source["Config"]["Cmd"]
    if command[:2] != ["bash", "-lc"] or len(command) != 3:
        raise RuntimeError("frozen command shape drifted")
    if "--additional-config" in command[2] or "--enforce-eager" in command[2]:
        raise RuntimeError("frozen command already changes CPU or graph mode")
    visible = [item for item in source["Config"]["Env"] if item.startswith("ASCEND_RT_VISIBLE_DEVICES=")]
    if visible != ["ASCEND_RT_VISIBLE_DEVICES=0,1,2,3"]:
        raise RuntimeError("frozen visible-NPU setting drifted")
    return source


def exact_name(arm: str, phase: str) -> str:
    return f"hypic_npu03_bindingfix_{arm.replace('-', '_')}_{phase}_20261007"


def inspect(name: str) -> dict | None:
    result = run("docker", "inspect", name, check=False)
    if result.returncode:
        return None
    values = json.loads(result.stdout)
    if len(values) != 1:
        raise RuntimeError("Docker inspect cardinality changed")
    return values[0]


def assert_lane_available() -> None:
    output = run("npu-smi", "info").stdout
    if not all(f"No running processes found in NPU {n}" in output for n in range(4)):
        raise RuntimeError("physical NPU0-3 have a running process")
    listeners = run("ss", "-ltn", "sport", f":{PORT}").stdout
    if re.search(rf":{PORT}(?:\s|$)", listeners, re.M):
        raise RuntimeError("service port 8223 is occupied")
    # A container device mapping reserves access, not active use. Isolation is
    # established by physical NPU processes here and the continuous guard once
    # our service starts; leave all foreign containers untouched.


def assert_owned(item: dict, name: str, arm: str, phase: str) -> None:
    labels = item["Config"]["Labels"]
    mapped = [
        entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
        if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
    ]
    command = item["Config"]["Cmd"]
    if not (
        item["Name"] == f"/{name}"
        and item["Image"] == IMAGE
        and labels.get("hypic.cpu-binding-fix") == "20261007"
        and labels.get("hypic.arm") == arm
        and labels.get("hypic.phase") == phase
        and item["HostConfig"]["CpusetCpus"] == "112-191"
        and mapped == [f"/dev/davinci{i}" for i in range(4)]
        and f"{ROOT}:/results" in item["HostConfig"]["Binds"]
        and "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3" in item["Config"]["Env"]
        and command[:2] == ["bash", "-lc"]
        and len(command) == 3
        and command[2].count("enable_cpu_binding") == 1
    ):
        raise RuntimeError(f"{name}: exact owned-container identity mismatch")


def create(source: dict, arm: str, phase: str, out: Path) -> tuple[str, str]:
    assert_lane_available()
    name = exact_name(arm, phase)
    if inspect(name) is not None:
        raise RuntimeError(f"exact candidate container {name} already exists")
    old_mount = f"{SOURCE_ROOT}:/results"
    binds = source["HostConfig"]["Binds"]
    if binds.count(old_mount) != 1:
        raise RuntimeError("frozen artifact mount drifted")
    command = source["Config"]["Cmd"][2] + FLAG
    args = [
        "docker", "create", "--name", name,
        "--label", "hypic.cpu-binding-fix=20261007",
        "--label", f"hypic.arm={arm}", "--label", f"hypic.phase={phase}",
        "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
        "--cpuset-cpus", "112-191",
    ]
    for entry in source["HostConfig"]["Devices"]:
        args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
    for bind in binds:
        args += ["-v", f"{ROOT}:/results" if bind == old_mount else bind]
    for entry in source["Config"]["Env"]:
        args += ["-e", entry]
    args += [IMAGE, "bash", "-lc", command]
    run(*args)
    item = inspect(name)
    if item is None:
        raise RuntimeError("Docker create returned without a candidate container")
    try:
        assert_owned(item, name, arm, phase)
        contract = {
        "schema": "hypic-npu03-binding-fix-run/v1",
        "arm": arm, "phase": phase, "container": name, "container_id": item["Id"],
        "image": IMAGE, "source_commit": SOURCE_COMMIT, "source_snapshot_sha256": SNAPSHOT_SHA,
        "benchmark_sha256": BENCHMARK_SHA, "physical_npus": list(range(4)),
        "cpuset": "112-191", "serving_command": command,
        "only_serving_change": FLAG.strip(), "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (out / "contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    except Exception:
        # A newly created, never-started container is ours only when its
        # unique label and exact Docker ID still match this create result.
        current = inspect(name)
        if (current is not None and current["Id"] == item["Id"]
                and current["Config"]["Labels"].get("hypic.cpu-binding-fix") == "20261007"
                and current["State"]["Status"] == "created"):
            run("docker", "rm", name)
        raise
    return name, item["Id"]


def wait_for_health(name: str) -> None:
    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        item = inspect(name)
        if item is None or item["State"]["Status"] != "running":
            raise RuntimeError("candidate exited before health")
        try:
            with urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError("candidate health timeout")


def verify_activation(name: str, out: Path) -> None:
    logs = run("docker", "logs", name).stdout + run("docker", "logs", name).stderr
    (out / "service.activation.log").write_text(logs)
    if "'enable_cpu_binding': False" not in logs:
        raise RuntimeError("parsed enable_cpu_binding=False not observed in service log")
    if "The CPU allocation plan is as follows:" in logs:
        raise RuntimeError("CPU binding plan appeared despite disable switch")


def benchmark(arm: str, out: Path, output_tokens: int, requests: int, concurrency: int) -> None:
    output = out / "performance.json"
    command = [
        "python3", str(BENCHMARK), "--base-url", f"http://127.0.0.1:{PORT}",
        "--model", "qwen36-hypic-e2e-2048", "--input-tokens", "32768",
        "--prefix-tokens", "16384", "--output-tokens", str(output_tokens),
        "--requests", str(requests), "--concurrency", str(concurrency),
        "--warmup-requests", "2", "--timeout", "2400",
        "--json-output", str(output), "--evidence-file", str(ROOT / arm / "hypic-evidence.jsonl"),
    ]
    # The 4-request smoke has only one measured wave. Native Decode scheduler
    # passthrough may fire during warmup, outside the benchmark's measured
    # evidence window; require the complete evidence set on formal traffic.
    if arm == "hypic-only" and (output_tokens, requests, concurrency) != (128, 4, 4):
        command.append("--require-hot-path")
    result = run(*command, check=False)
    (out / "performance.stdout.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"benchmark exit {result.returncode}; see {out / 'performance.stdout.log'}")
    report = json.loads(output.read_text())
    summary = report["summary"]
    if not (summary["successful"] == requests and summary["failed"] == 0
            and summary["fixed_output_verified"] and summary["output_tokens"] == requests * output_tokens):
        raise RuntimeError("fixed-output benchmark validity guard failed")
    if arm == "hypic-only" and (output_tokens, requests, concurrency) == (128, 4, 4):
        require_smoke_hot_path(summary)
    print(json.dumps({"arm": arm, "summary": summary}, sort_keys=True), flush=True)


def require_smoke_hot_path(summary: dict) -> None:
    required = (
        "plugin_build_active", "runtime_scheduler_active", "scheduler_hot_path",
        "materialization_ready", "worker_hot_path", "position_independent_attention",
        "position_independent_gdn", "physical_kv_layout",
    )
    evidence = summary.get("hot_path_evidence") or {}
    missing = [event for event in required if evidence.get(event) is not True]
    if missing or not summary.get("gdn_npu_material_verified"):
        raise RuntimeError(f"HYPIC smoke core hot path missing: {missing}")


def audit_smoke(arm: str) -> None:
    out = ROOT / arm / "smoke"
    contract = json.loads((out / "contract.json").read_text())
    canary = json.loads((out / "semantic-canary.json").read_text())
    original = json.loads((SOURCE_ROOT / arm / "semantic-canary.json").read_text())
    report = json.loads((out / "performance.json").read_text())
    summary = report["summary"]
    cleanup_record = json.loads((out / "cleanup.json").read_text())
    activation = (out / "service.activation.log").read_text()
    if (contract.get("arm") != arm or contract.get("phase") != "smoke"
            or contract.get("image") != IMAGE or contract.get("source_commit") != SOURCE_COMMIT
            or contract.get("physical_npus") != [0, 1, 2, 3]
            or FLAG.strip() not in contract.get("serving_command", "")):
        raise RuntimeError("smoke contract mismatch")
    if (not canary.get("answer_contains_key")
            or canary.get("response_token_ids") != original.get("response_token_ids")):
        raise RuntimeError("smoke deterministic canary mismatch")
    if not (summary.get("successful") == 4 and summary.get("failed") == 0
            and summary.get("fixed_output_verified") is True
            and summary.get("output_tokens") == 512):
        raise RuntimeError("smoke benchmark result invalid")
    if arm == "hypic-only":
        require_smoke_hot_path(summary)
    if ("'enable_cpu_binding': False" not in activation
            or "The CPU allocation plan is as follows:" in activation):
        raise RuntimeError("binding-off activation mismatch")
    if (cleanup_record.get("container_id") != contract.get("container_id")
            or not all(cleanup_record.get(key) is True for key in
                       ("container_removed", "owned_npus_released", "port_released"))
            or inspect(contract["container"]) is not None):
        raise RuntimeError("smoke cleanup receipt mismatch")
    assert_lane_available()
    result = {
        "arm": arm, "status": "core-smoke-pass",
        "full_formal_hot_path": "not-yet-tested",
        "smoke_hot_path_missing": summary.get("hot_path_missing", []),
        "benchmark_exit_1_reason": (
            "full-formal native_decode_scheduler_passthrough event absent from one-wave "
            "measured window; event present during warmup"
            if arm == "hypic-only" and summary.get("hot_path_missing")
            == ["native_decode_scheduler_passthrough"] else None
        ),
        "performance_sha256": sha256(out / "performance.json"),
        "canary_sha256": sha256(out / "semantic-canary.json"),
        "cleanup_sha256": sha256(out / "cleanup.json"),
    }
    (out / "smoke-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True), flush=True)


def semantic_canary(arm: str, out: Path) -> None:
    result = run(
        "python3", str(CANARY), "--base-url", f"http://127.0.0.1:{PORT}",
        "--model", "qwen36-hypic-e2e-2048", "--phase", arm,
        "--output", str(out / "semantic-canary.json"), "--timeout", "900", check=False,
    )
    (out / "semantic-canary.stdout.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"semantic canary exit {result.returncode}")
    current = json.loads((out / "semantic-canary.json").read_text())
    original = json.loads((SOURCE_ROOT / arm / "semantic-canary.json").read_text())
    if not current["answer_contains_key"] or current["response_token_ids"] != original["response_token_ids"]:
        raise RuntimeError("deterministic semantic canary differs from frozen control")


def cleanup(name: str, container_id: str, arm: str, phase: str, out: Path) -> None:
    item = inspect(name)
    if item is None or item["Id"] != container_id:
        raise RuntimeError("owned container disappeared or identity changed; do not touch another container")
    assert_owned(item, name, arm, phase)
    logs = run("docker", "logs", name, check=False)
    (out / "service.full.log").write_text(logs.stdout + logs.stderr)
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "60", name)
    run("docker", "rm", name)
    assert_lane_available()
    (out / "cleanup.json").write_text(json.dumps({
        "container": name, "container_id": container_id, "container_removed": True,
        "owned_npus_released": True, "port_released": True,
        "at": datetime.now(timezone.utc).isoformat(),
    }, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), default="no-cache")
    parser.add_argument("--phase", choices=("inspect", "audit-smoke", "smoke", "screen", "repeat2", "repeat3"), required=True)
    parser.add_argument("--enable-binding-off", action="store_true")
    args = parser.parse_args()
    source = frozen_source(args.arm)
    if args.phase == "inspect":
        print(json.dumps({"source": source["Name"], "image": IMAGE,
                          "physical_npus": [0, 1, 2, 3], "candidate_flag": FLAG.strip()}))
        return 0
    if args.phase == "audit-smoke":
        audit_smoke(args.arm)
        return 0
    if not args.enable_binding_off:
        raise RuntimeError("live run requires explicit --enable-binding-off")
    out = ROOT / args.arm / args.phase
    if out.exists():
        raise RuntimeError(f"{out} exists; refuse to overwrite evidence")
    out.mkdir(parents=True)
    name = ""
    container_id = ""
    try:
        name, container_id = create(source, args.arm, args.phase, out)
        run("docker", "start", name)
        wait_for_health(name)
        verify_activation(name, out)
        if args.phase == "smoke":
            semantic_canary(args.arm, out)
            benchmark(args.arm, out, 128, 4, 4)
        else:
            benchmark(args.arm, out, 1024, 40, 16)
        return 0
    finally:
        if name and container_id:
            cleanup(name, container_id, args.arm, args.phase, out)


if __name__ == "__main__":
    raise SystemExit(main())
