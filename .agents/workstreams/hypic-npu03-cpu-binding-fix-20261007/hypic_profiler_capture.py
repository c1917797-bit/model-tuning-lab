#!/usr/bin/env python3
"""Capture bounded HYPIC Prefill/Decode profiles on physical NPU0-3."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen


os.environ["HYPIC_QUALITY_ATTEMPT"] = "hotpath-cache10perf-hypic-only-repeat3-retry21"
os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = "/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008"
os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = "c12060cd47e7575ead059983d7a8bb4704165c98"

import binding_off_quality as quality  # noqa: E402


PINNED_BENCHMARK = Path("/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008/tools/benchmark_shared_prefix.py")
RAW_ROOT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profiler-hypic-hotcold-20261009-r6")
ARM = "hypic-only"
PORT = 8223
MODEL = "qwen36-hypic-e2e-2048"
SOURCE_COMMIT = "c12060cd47e7575ead059983d7a8bb4704165c98"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
MIN_DECODE_CHUNKS = 64
DECODE_OUTPUT_TOKENS = 512


def load_benchmark():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_hypic_profiler_benchmark", PINNED_BENCHMARK)
    if spec is None or spec.loader is None:
        raise RuntimeError("pinned benchmark import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def post(url: str, payload: object | None = None, timeout: int = 2400):
    data = b"" if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    return urlopen(request, timeout=timeout)


def phase_name(phase: str) -> str:
    return f"hypic_npu03_profiler_{phase}_{RAW_ROOT.name}"


def profiler_config(phase_dir: Path) -> dict:
    return {
        "profiler": "torch",
        "torch_profiler_dir": f"/results/{RAW_ROOT.name}/{phase_dir.name}/profiles",
        "torch_profiler_with_stack": False,
    }


def transformed_spec(phase: str) -> tuple[dict, list[str], list[str], str]:
    source, binds, env, command = quality.spec(ARM)
    old = f"/results/{quality.QROOT.name}/{ARM}"
    new = f"/results/{RAW_ROOT.name}/{phase}"
    if command.count(old) != 2:
        raise RuntimeError("retry21 command output seam drift")
    command = command.replace(old, new)
    old_evidence = f"VLLM_ASCEND_HYPIC_EVIDENCE_FILE={old}/hypic-evidence.jsonl"
    if env.count(old_evidence) != 1:
        raise RuntimeError("retry21 evidence environment seam drift")
    env = [f"VLLM_ASCEND_HYPIC_EVIDENCE_FILE={new}/hypic-evidence.jsonl"
           if item == old_evidence else item for item in env]
    env.append(f"ASCEND_PROFILER_OUTPUT={new}/profiles")
    config = json.dumps(profiler_config(Path(phase)), separators=(",", ":"))
    command += f" --profiler-config '{config}'"
    return source, binds, env, command


def inspect(name: str) -> dict | None:
    result = quality.run("docker", "inspect", name, check=False)
    if result.returncode:
        return None
    values = json.loads(result.stdout)
    return values[0] if len(values) == 1 else None


def create(phase: str) -> tuple[str, str, dict]:
    quality.assert_lane_available()
    name = phase_name(phase)
    if inspect(name) is not None:
        raise RuntimeError("exact profiler container already exists")
    source, binds, env, command = transformed_spec(phase)
    args = ["docker", "create", "--name", name,
            "--label", f"hypic.profiler={RAW_ROOT.name}", "--label", f"hypic.phase={phase}",
            "--network", "host", "--shm-size", str(source["HostConfig"]["ShmSize"]),
            "--cpuset-cpus", "112-191"]
    for item in source["HostConfig"]["Devices"]:
        args += ["--device", f"{item['PathOnHost']}:{item['PathInContainer']}:{item['CgroupPermissions']}"]
    for bind in binds:
        args += ["-v", bind]
    for item in env:
        args += ["-e", item]
    args += [IMAGE, "bash", "-lc", command]
    quality.run(*args)
    item = inspect(name)
    if item is None:
        raise RuntimeError("profiler container absent after create")
    mapped = [entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
              if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    if not (item["Id"] and item["Name"] == f"/{name}" and item["Image"] == IMAGE
            and mapped == [f"/dev/davinci{i}" for i in range(4)]
            and item["HostConfig"]["CpusetCpus"] == "112-191"
            and item["Config"]["Labels"].get("hypic.profiler") == RAW_ROOT.name
            and item["Config"]["Labels"].get("hypic.phase") == phase
            and item["Config"]["Cmd"] == ["bash", "-lc", command]):
        raise RuntimeError("exact profiler container identity mismatch")
    return name, item["Id"], {"command": command, "binds": binds, "env": env}


def worker_proof(name: str, out: Path) -> dict[str, int]:
    top = quality.run("docker", "top", name, "-eo", "pid,comm").stdout
    npu = quality.run("npu-smi", "info").stdout
    (out / "docker-top-at-health.txt").write_text(top)
    (out / "npu-smi-at-health.txt").write_text(npu)
    docker_pids = {int(parts[0]) for line in top.splitlines()[1:]
                   if (parts := line.split()) and parts[0].isdigit()}
    rows = quality.npu_processes(npu)
    mapping = {str(row["physical_npu"]): row["pid"] for row in rows
               if row["pid"] in docker_pids}
    if set(mapping) != {"0", "1", "2", "3"} or len(set(mapping.values())) != 4:
        raise RuntimeError(f"four-worker NPU mapping absent: {mapping}")
    return mapping


def wait_health(name: str, guard: object, out: Path) -> dict[str, int]:
    quality.run("docker", "start", name)
    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        guard.assert_clean()
        item = inspect(name)
        if item is None or item["State"]["Status"] != "running":
            raise RuntimeError("profiler service exited before health")
        try:
            with urlopen(f"http://127.0.0.1:{PORT}/health", timeout=5) as response:
                if response.status == 200:
                    mapping = worker_proof(name, out)
                    guard.set_expected_workers(mapping)
                    guard.assert_clean()
                    return mapping
        except Exception:
            pass
        time.sleep(10)
    raise RuntimeError("profiler service health timeout")


def build_prompts(module: object) -> list[list[int]]:
    args = SimpleNamespace(base_url=f"http://127.0.0.1:{PORT}", model=MODEL,
                           prefix_tokens=16384, input_tokens=32768,
                           requests=1, warmup_requests=2, timeout=2400)
    return module._build_prompts(args)


def completion_payload(prompt_tokens: list[int], max_tokens: int) -> dict:
    return {"model": MODEL, "prompt": prompt_tokens, "max_tokens": max_tokens,
            "temperature": 0, "seed": 0, "ignore_eos": max_tokens > 1,
            "stream": True, "stream_options": {"include_usage": True},
            "vllm_xargs": {"hypic_segment_ends": "16384,32768"}}


def consume(prompt_tokens: list[int], max_tokens: int) -> dict:
    chunks = 0
    output_tokens = None
    with post(f"http://127.0.0.1:{PORT}/v1/completions",
              completion_payload(prompt_tokens, max_tokens)) as response:
        for raw in response:
            body = raw.strip()
            if not body.startswith(b"data:"):
                continue
            body = body[5:].strip()
            if body == b"[DONE]":
                break
            data = json.loads(body)
            usage = data.get("usage") or {}
            if usage.get("completion_tokens") is not None:
                output_tokens = int(usage["completion_tokens"])
            for choice in data.get("choices") or []:
                if choice.get("text"):
                    chunks += 1
    if output_tokens != max_tokens:
        raise RuntimeError(f"fixed output mismatch: {output_tokens} != {max_tokens}")
    return {"chunks": chunks, "output_tokens": output_tokens}


def warmup(prompts: list[list[int]]) -> list[dict]:
    return [consume(prompts[index], 32) for index in range(2)]


def capture_prefill(prompt_tokens: list[int]) -> dict:
    with post(f"http://127.0.0.1:{PORT}/start_profile") as response:
        response.read()
    try:
        result = consume(prompt_tokens, 1)
    finally:
        with post(f"http://127.0.0.1:{PORT}/stop_profile") as response:
            response.read()
    return {"prefill_focused": True, "decode_tokens_in_window": 1, **result}


def capture_decode(prompt_tokens: list[int]) -> dict:
    first = threading.Event()
    profile_started = threading.Event()
    enough = threading.Event()
    profile_stopped = threading.Event()
    state: dict[str, object] = {"chunks_after_start": 0, "error": None,
                               "output_tokens": None, "profile_start_utc": None,
                               "profile_stop_utc": None}

    def stream() -> None:
        try:
            seen_first = False
            with post(f"http://127.0.0.1:{PORT}/v1/completions",
                      completion_payload(prompt_tokens, DECODE_OUTPUT_TOKENS)) as response:
                for raw in response:
                    body = raw.strip()
                    if not body.startswith(b"data:"):
                        continue
                    body = body[5:].strip()
                    if body == b"[DONE]":
                        break
                    data = json.loads(body)
                    usage = data.get("usage") or {}
                    if usage.get("completion_tokens") is not None:
                        state["output_tokens"] = int(usage["completion_tokens"])
                    nonempty = any(choice.get("text") for choice in data.get("choices") or [])
                    if not nonempty:
                        continue
                    if not seen_first:
                        seen_first = True
                        first.set()
                        if not profile_started.wait(60):
                            raise RuntimeError("profile start handshake timeout")
                        continue
                    if profile_started.is_set() and not profile_stopped.is_set():
                        state["chunks_after_start"] = int(state["chunks_after_start"]) + 1
                        if int(state["chunks_after_start"]) >= MIN_DECODE_CHUNKS:
                            enough.set()
                            if not profile_stopped.wait(300):
                                raise RuntimeError("profile stop handshake timeout")
        except Exception as exc:
            state["error"] = f"{type(exc).__name__}: {exc}"
            first.set()
            enough.set()

    thread = threading.Thread(target=stream)
    thread.start()
    if not first.wait(2400) or state["error"]:
        raise RuntimeError(str(state["error"] or "first Decode token timeout"))
    with post(f"http://127.0.0.1:{PORT}/start_profile") as response:
        response.read()
    state["profile_start_utc"] = datetime.now(timezone.utc).isoformat()
    profile_started.set()
    if not enough.wait(600) or state["error"]:
        profile_stopped.set()
        raise RuntimeError(str(state["error"] or "steady Decode window timeout"))
    with post(f"http://127.0.0.1:{PORT}/stop_profile") as response:
        response.read()
    state["profile_stop_utc"] = datetime.now(timezone.utc).isoformat()
    profile_stopped.set()
    thread.join(timeout=2400)
    if thread.is_alive() or state["error"] or state["output_tokens"] != DECODE_OUTPUT_TOKENS:
        raise RuntimeError(str(state["error"] or "Decode stream incomplete"))
    if int(state["chunks_after_start"]) < MIN_DECODE_CHUNKS:
        raise RuntimeError("fewer than 64 steady Decode chunks captured")
    return {"prefill_outside_window": True, **state}


def audit_artifacts(out: Path) -> dict:
    deadline = time.monotonic() + 600
    profile_root = out / "profiles"
    files: list[Path] = []
    while time.monotonic() < deadline:
        files = sorted(path for path in profile_root.rglob("*") if path.is_file() and path.stat().st_size)
        if files:
            break
        time.sleep(5)
    if not files:
        raise RuntimeError("profiler emitted no non-empty artifact")
    kernels = [path for path in files if path.name == "kernel_details.csv"]
    kernel_headers = {}
    for path in kernels:
        with path.open(newline="", errors="replace") as stream:
            width = len(next(csv.reader(stream)))
        kernel_headers[str(path.relative_to(out))] = width
        if width < 47:
            raise RuntimeError(f"kernel_details header too narrow: {width}")
    inventory = [{"path": str(path.relative_to(out)), "size": path.stat().st_size,
                  "sha256": digest(path)} for path in files]
    return {"nonempty_files": len(files), "kernel_details_files": len(kernels),
            "kernel_header_columns": kernel_headers, "inventory": inventory}


def cleanup(name: str, container_id: str, out: Path, worker_pids: dict[str, int]) -> dict:
    item = inspect(name)
    if item is None or item["Id"] != container_id or item["Config"]["Labels"].get("hypic.profiler") != RAW_ROOT.name:
        raise RuntimeError("exact profiler ownership changed; refusing cleanup")
    with (out / "service.log").open("w") as stream:
        subprocess.run(["docker", "logs", name], stdout=stream, stderr=subprocess.STDOUT,
                       text=True, timeout=300, check=False)
    if item["State"]["Status"] == "running":
        quality.run("docker", "stop", "--time", "60", container_id)
    quality.run("docker", "rm", container_id)
    if inspect(name) is not None:
        raise RuntimeError("exact profiler container remains after cleanup")
    snapshot = quality.run("npu-smi", "info").stdout
    observed = quality.npu_processes(snapshot)
    if any(row["pid"] in set(worker_pids.values()) for row in observed):
        raise RuntimeError("owned profiler worker remains on NPU")
    listeners = quality.run("ss", "-ltn", "sport", f":{PORT}").stdout
    if re.search(rf":{PORT}(?:\s|$)", listeners, re.M):
        raise RuntimeError("profiler port remains occupied")
    return {"container_removed": True, "owned_workers_released": True,
            "port_released": True, "at_utc": datetime.now(timezone.utc).isoformat()}


def run_phase(phase: str) -> int:
    out = RAW_ROOT / phase
    if out.exists():
        raise RuntimeError("phase root exists; never overwrite or resume")
    quality.preflight()
    quality.assert_lane_available()
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    out.mkdir()
    source, binds, env, command = transformed_spec(phase)
    contract = {"schema": "hypic-profiler-contract/v1", "phase": phase,
                "physical_npus": [0, 1, 2, 3], "port": PORT, "image": IMAGE,
                "source_commit": SOURCE_COMMIT, "model": MODEL,
                "profile_config": profiler_config(Path(phase)),
                "serving_command": command, "serving_binds": binds,
                "serving_env": env, "created_at_utc": datetime.now(timezone.utc).isoformat()}
    write_json(out / "contract.json", contract)
    name = ""
    container_id = ""
    guard = None
    workers: dict[str, int] = {}
    capture = None
    artifacts = None
    release = None
    errors: list[str] = []
    try:
        name, container_id, _ = create(phase)
        quality.QROOT = RAW_ROOT
        quality.ATTEMPT = RAW_ROOT.name
        guard = quality.ForeignProcessGuard(f"{ARM}-{phase}", {}, owned_container_id=container_id)
        guard.start()
        workers = wait_health(name, guard, out)
        prompts = build_prompts(load_benchmark())
        warmup_result = warmup(prompts)
        guard.assert_clean()
        capture_result = (capture_prefill(prompts[2]) if phase == "prefill"
                          else capture_decode(prompts[2]))
        guard.assert_clean()
        capture = {"warmups": warmup_result, "capture": capture_result,
                   "worker_pid_by_physical_npu": workers}
        write_json(out / "capture.json", capture)
        artifacts = audit_artifacts(out)
        write_json(out / "artifact-audit.json", artifacts)
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        if guard is not None:
            try:
                guard.close()
                guard_record = json.loads((RAW_ROOT / f"{ARM}-{phase}" / "lane-guard.json").read_text())
                if guard_record.get("foreign") or guard_record.get("probe_errors"):
                    errors.append("continuous lane guard recorded foreign activity or probe error")
            except Exception as exc:
                errors.append(f"guard close: {type(exc).__name__}: {exc}")
        if container_id:
            try:
                release = cleanup(name, container_id, out, workers)
                write_json(out / "release.json", release)
            except Exception as exc:
                errors.append(f"cleanup: {type(exc).__name__}: {exc}")
        result = {"schema": "hypic-profiler-result/v1", "phase": phase,
                  "valid": not errors, "errors": errors, "capture": capture,
                  "artifact_summary": None if artifacts is None else {
                      key: artifacts[key] for key in ("nonempty_files", "kernel_details_files", "kernel_header_columns")},
                  "release": release, "contract_sha256": digest(out / "contract.json"),
                  "at_utc": datetime.now(timezone.utc).isoformat()}
        write_json(out / "result.json", result)
        print(json.dumps(result, sort_keys=True), flush=True)
    if errors:
        raise RuntimeError("; ".join(errors))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prefill", "decode"), required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        _, binds, env, command = transformed_spec(args.phase)
        print(json.dumps({"phase": args.phase, "binds": binds, "env": env,
                          "command": command}, sort_keys=True))
        return 0
    return run_phase(args.phase)


if __name__ == "__main__":
    raise SystemExit(main())
