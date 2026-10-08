#!/usr/bin/env python3
"""Run one matched, resumable 2048-token quality arm on physical NPU0-3."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from binding_off_service import (
    FLAG, IMAGE, PORT, ROOT, SOURCE_COMMIT, SOURCE_ROOT, ARMS,
    assert_lane_available, frozen_source, inspect, run, sha256,
)

ATTEMPT = os.environ.get("HYPIC_QUALITY_ATTEMPT", "original")
PERFORMANCE_ATTEMPTS = {
    f"hotpath-cache10perf-{arm}-{phase}":
        f"performance-context-41984-hotpath-cache10perf-{arm}-{phase}"
    for arm in ("no-cache", "hypic-only")
    for phase in ("screen", "repeat2", "repeat3")
}
ATTEMPT_ROOTS = {
    "original": "quality-context-41984",
    "clean2": "quality-context-41984-clean2",
    "hotpath-canary": "quality-context-41984-hotpath-canary",
    "hotpath-baseline": "quality-context-41984-hotpath-baseline",
    "hotpath-pilot-hypic": "quality-context-41984-hotpath-pilot-hypic",
    "hotpath-pilot2-hypic": "quality-context-41984-hotpath-pilot2-hypic",
    "hotpath-full-baseline": "quality-context-41984-hotpath-full-baseline",
    "hotpath-full-hypic": "quality-context-41984-hotpath-full-hypic",
    "hotpath-reserve-stress-hypic": "quality-context-41984-hotpath-reserve-stress-hypic",
    "hotpath-reserve-stress2-hypic": "quality-context-41984-hotpath-reserve-stress2-hypic",
    "hotpath-reserve-full-baseline": "quality-context-41984-hotpath-reserve-full-baseline",
    "hotpath-reserve-full-hypic": "quality-context-41984-hotpath-reserve-full-hypic",
    "hotpath-cache10-stress-hypic": "quality-context-41984-hotpath-cache10-stress-hypic",
    "hotpath-cache10-full-baseline": "quality-context-41984-hotpath-cache10-full-baseline",
    "hotpath-cache10-full-hypic": "quality-context-41984-hotpath-cache10-full-hypic",
    "hotpath-cache10r1-full-baseline": "quality-context-41984-hotpath-cache10r1-full-baseline",
    "hotpath-cache10r1-full-hypic": "quality-context-41984-hotpath-cache10r1-full-hypic",
    "hotpath-cache10r2-full-baseline": "quality-context-41984-hotpath-cache10r2-full-baseline",
    "hotpath-cache10r2-full-hypic": "quality-context-41984-hotpath-cache10r2-full-hypic",
    "hotpath-cache10r3-full-baseline": "quality-context-41984-hotpath-cache10r3-full-baseline",
    "hotpath-cache10r3-full-hypic": "quality-context-41984-hotpath-cache10r3-full-hypic",
    "hotpath-cache10r4-full-baseline": "quality-context-41984-hotpath-cache10r4-full-baseline",
    "hotpath-cache10r4-full-hypic": "quality-context-41984-hotpath-cache10r4-full-hypic",
    "hotpath-cache10r5-full-baseline": "quality-context-41984-hotpath-cache10r5-full-baseline",
    "hotpath-cache10r5-full-hypic": "quality-context-41984-hotpath-cache10r5-full-hypic",
    "hotpath-cache10r6-full-baseline": "quality-context-41984-hotpath-cache10r6-full-baseline",
    "hotpath-cache10r6-full-hypic": "quality-context-41984-hotpath-cache10r6-full-hypic",
    "hotpath-cache10r7-full-baseline": "quality-context-41984-hotpath-cache10r7-full-baseline",
    "hotpath-cache10r7-full-hypic": "quality-context-41984-hotpath-cache10r7-full-hypic",
    "hotpath-cache10r8-full-baseline": "quality-context-41984-hotpath-cache10r8-full-baseline",
    "hotpath-cache10r8-full-hypic": "quality-context-41984-hotpath-cache10r8-full-hypic",
    "hotpath-cache10r9-full-baseline": "quality-context-41984-hotpath-cache10r9-full-baseline",
    "hotpath-cache10r9-full-hypic": "quality-context-41984-hotpath-cache10r9-full-hypic",
    "hotpath-cache10split-baseline-shard0": "quality-context-41984-hotpath-cache10split-baseline-shard0",
    "hotpath-cache10split-baseline-shard1": "quality-context-41984-hotpath-cache10split-baseline-shard1",
    "hotpath-cache10split-hypic-shard1": "quality-context-41984-hotpath-cache10split-hypic-shard1",
    **PERFORMANCE_ATTEMPTS,
}
if ATTEMPT not in ATTEMPT_ROOTS:
    raise RuntimeError(f"unrecognized HYPIC quality attempt: {ATTEMPT}")
RESERVE_ATTEMPTS = frozenset({
    "hotpath-reserve-stress-hypic",
    "hotpath-reserve-stress2-hypic",
    "hotpath-reserve-full-baseline",
    "hotpath-reserve-full-hypic",
    "hotpath-cache10-stress-hypic",
    "hotpath-cache10-full-baseline",
    "hotpath-cache10-full-hypic",
    "hotpath-cache10r1-full-baseline",
    "hotpath-cache10r1-full-hypic",
    "hotpath-cache10r2-full-baseline",
    "hotpath-cache10r2-full-hypic",
    "hotpath-cache10r3-full-baseline",
    "hotpath-cache10r3-full-hypic",
    "hotpath-cache10r4-full-baseline",
    "hotpath-cache10r4-full-hypic",
    "hotpath-cache10r5-full-baseline",
    "hotpath-cache10r5-full-hypic",
    "hotpath-cache10r6-full-baseline",
    "hotpath-cache10r6-full-hypic",
    "hotpath-cache10r7-full-baseline",
    "hotpath-cache10r7-full-hypic",
    "hotpath-cache10r8-full-baseline",
    "hotpath-cache10r8-full-hypic",
    "hotpath-cache10r9-full-baseline",
    "hotpath-cache10r9-full-hypic",
    "hotpath-cache10split-baseline-shard0",
    "hotpath-cache10split-baseline-shard1",
    "hotpath-cache10split-hypic-shard1",
} | set(PERFORMANCE_ATTEMPTS))
QROOT = ROOT / ATTEMPT_ROOTS[ATTEMPT]
CONTEXT = 41984
EVALUATOR = Path(__file__).resolve().parents[1] / "WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py"
DATASETS = {
    "longbenchv2": (Path("/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json"), 127, "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a"),
    "gsm8k": (Path("/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl"), 1319, "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"),
}
EVALUATOR_SHA = "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
MODEL_INDEX_SHA = "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b"
MODEL_NAME = "qwen36-hypic-e2e-2048"
MODEL_DIR = Path("/cache/efim/Qwen3.6-27B")
BASE_URL = f"http://127.0.0.1:{PORT}"
PROC_ROOT = Path("/proc")
EXPERIMENT = f"hypic-npu03-bindingoff-quality41984-20261007-{ATTEMPT}"
UNIT_ORDER = (("longbenchv2", 1), ("gsm8k", 1), ("longbenchv2", 2),
              ("gsm8k", 2), ("longbenchv2", 3), ("gsm8k", 3))


def name_for(arm: str) -> str:
    suffix = "" if ATTEMPT == "original" else f"_{ATTEMPT}"
    return f"hypic_npu03_bindingfix_quality_{arm.replace('-', '_')}_20261007{suffix}"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def status(arm: str, stage: str, **details: object) -> None:
    value = {"schema": "hypic-bindingoff-quality-status/v1", "arm": arm,
             "stage": stage, "at_utc": datetime.now(timezone.utc).isoformat(), **details}
    write_json(QROOT / arm / "status.json", value)
    print(json.dumps(value, sort_keys=True), flush=True)


def npu_processes(snapshot: str) -> list[dict[str, int]]:
    """Return host PIDs actually using physical NPU0-3, not Docker claims."""
    return [{"physical_npu": int(card), "pid": int(pid)} for card, pid in
            re.findall(r"^\|\s*([0-3])\s+0\s*\|\s*(\d+)\s*\|", snapshot, re.M)]


def foreign_container_id(pid: int) -> str | None:
    """Capture transient Docker ownership during the same NPU observation."""
    try:
        cgroup = (PROC_ROOT / str(pid) / "cgroup").read_text(errors="replace")
    except OSError:
        return None
    match = re.search(r"(?:/docker/|docker-)([a-f0-9]{64})", cgroup)
    return match.group(1) if match else None


class ForeignProcessGuard:
    """Record any competing 0-3 NPU process throughout a quality service."""

    def __init__(self, arm: str, worker_pids: dict[str, int],
                 owned_container_id: str | None = None) -> None:
        self.arm = arm
        self.expected = set(worker_pids.values())
        self.owned_container_id = owned_container_id
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.samples = 0
        self.foreign: list[dict] = []
        self.errors: list[dict] = []
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.started = False

    def _record(self, foreign: list[dict[str, int]], error: str | None) -> None:
        with self.lock:
            self.samples += 1
            event = {"at_utc": datetime.now(timezone.utc).isoformat()}
            if foreign:
                self.foreign.append({**event, "processes": foreign})
            if error:
                self.errors.append({**event, "error": error})
            if foreign or error:
                self._write()

    def _write(self) -> None:
        write_json(QROOT / self.arm / "lane-guard.json", {
            "schema": "hypic-bindingoff-quality-lane-guard/v1", "arm": self.arm,
            "attempt": ATTEMPT, "expected_worker_pids": sorted(self.expected),
            "owned_container_id": self.owned_container_id,
            "samples": self.samples, "foreign": self.foreign, "probe_errors": self.errors})

    def sample(self) -> None:
        try:
            result = subprocess.run(["npu-smi", "info"], text=True,
                                    capture_output=True, timeout=30, check=False)
            if result.returncode:
                raise RuntimeError(f"npu-smi exited {result.returncode}")
            observed = npu_processes(result.stdout)
            if not all((f"No running processes found in NPU {card}" in result.stdout
                        or any(item["physical_npu"] == card for item in observed))
                       for card in range(4)):
                raise RuntimeError("npu-smi process section incomplete")
            foreign = []
            for item in observed:
                if item["pid"] in self.expected:
                    continue
                container_id = foreign_container_id(item["pid"])
                if container_id and container_id == self.owned_container_id:
                    continue
                foreign.append({**item, **({"container_id": container_id}
                                         if container_id else {})})
            self._record(foreign, None)
        except Exception as exc:
            self._record([], f"{type(exc).__name__}: {exc}")

    def assert_clean(self) -> None:
        self.sample()
        with self.lock:
            if self.foreign or self.errors:
                raise RuntimeError("quality lane guard detected foreign NPU0-3 process or probe error")

    def _loop(self) -> None:
        while not self.stop_event.wait(10):
            self.sample()

    def start(self) -> None:
        self.assert_clean()
        self.thread.start()
        self.started = True

    def set_expected_workers(self, worker_pids: dict[str, int]) -> None:
        with self.lock:
            self.expected = set(worker_pids.values())

    def close(self) -> None:
        self.stop_event.set()
        if self.started:
            self.thread.join(timeout=35)
        with self.lock:
            if self.started and self.thread.is_alive():
                self.errors.append({"at_utc": datetime.now(timezone.utc).isoformat(),
                                    "error": "lane guard did not stop cleanly"})
            self._write()


def preflight() -> dict:
    parent = json.loads((SOURCE_ROOT / "baseline-contract.json").read_text())
    fp = parent["fingerprint"]
    for arm in ARMS:
        frozen_source(arm)
    if sha256(EVALUATOR) != EVALUATOR_SHA:
        raise RuntimeError("quality evaluator source hash drift")
    if sha256(MODEL_DIR / "model.safetensors.index.json") != MODEL_INDEX_SHA:
        raise RuntimeError("model index hash drift")
    for shard in fp["model_shards"]:
        info = (MODEL_DIR / shard["name"]).stat()
        if info.st_size != shard["size"] or info.st_mtime_ns != shard["mtime_ns"]:
            raise RuntimeError(f"model shard metadata drift: {shard['name']}")
    for dataset, (path, expected, digest) in DATASETS.items():
        if sha256(path) != digest:
            raise RuntimeError(f"{dataset} dataset hash drift")
        if dataset == "longbenchv2" and expected != 127:
            raise RuntimeError("LongBench expected count drift")
    if 39642 + 2048 > CONTEXT:
        raise RuntimeError("longest prompt exceeds quality context")
    fingerprint = {"image": IMAGE, "source_commit": SOURCE_COMMIT, "model_index_sha256": MODEL_INDEX_SHA,
            "evaluator_sha256": EVALUATOR_SHA, "datasets": {key: {"count": value[1],
            "sha256": value[2]} for key, value in DATASETS.items()},
            "max_model_len": CONTEXT, "max_output_tokens": 2048,
            "physical_npus": [0, 1, 2, 3], "cpuset": "112-191",
            "common_serving_change": FLAG.strip(), "unit_order": list(UNIT_ORDER)}
    if ATTEMPT in RESERVE_ATTEMPTS:
        fingerprint["gpu_memory_utilization"] = 0.85
    if ATTEMPT.startswith("hotpath-cache10"):
        fingerprint["material_cache_max_mb"] = 3584
        fingerprint["max_materialized_segments"] = 10
    return fingerprint


def spec(arm: str) -> tuple[dict, list[str], list[str], str]:
    source = frozen_source(arm)
    old_path = f"/results/{arm}"
    new_path = f"/results/{QROOT.name}/{arm}"
    command = source["Config"]["Cmd"][2]
    if (command.count(old_path) != 2 or command.count("--max-model-len 40960") != 1
            or command.count("--max-num-batched-tokens 40960") != 1):
        raise RuntimeError("frozen quality command seam drift")
    command = command.replace(old_path, new_path)
    command = command.replace("--max-model-len 40960", f"--max-model-len {CONTEXT}")
    command = command.replace("--max-num-batched-tokens 40960", f"--max-num-batched-tokens {CONTEXT}")
    if ATTEMPT in RESERVE_ATTEMPTS:
        old_util = "--gpu-memory-utilization 0.9"
        if command.count(old_util) != 1:
            raise RuntimeError("frozen GPU memory utilization seam drift")
        command = command.replace(old_util, "--gpu-memory-utilization 0.85")
    command += FLAG
    old_mount = f"{SOURCE_ROOT}:/results"
    binds = source["HostConfig"]["Binds"]
    if binds.count(old_mount) != 1:
        raise RuntimeError("frozen artifact mount seam drift")
    binds = [f"{ROOT}:/results" if value == old_mount else value for value in binds]
    old_env = f"VLLM_ASCEND_HYPIC_EVIDENCE_FILE={old_path}/hypic-evidence.jsonl"
    env = source["Config"]["Env"]
    if env.count(old_env) != 1:
        raise RuntimeError("frozen HYPIC evidence env seam drift")
    env = [f"VLLM_ASCEND_HYPIC_EVIDENCE_FILE={new_path}/hypic-evidence.jsonl"
           if value == old_env else value for value in env]
    if ATTEMPT.startswith("hotpath-cache10"):
        for key, old_value, new_value in (
            ("VLLM_ASCEND_HYPIC_MATERIAL_CACHE_MAX_MB", "1536", "3584"),
            ("VLLM_ASCEND_HYPIC_MAX_MATERIALIZED_SEGMENTS", "4", "10"),
        ):
            old_entry = f"{key}={old_value}"
            if env.count(old_entry) != 1:
                raise RuntimeError(f"frozen HYPIC material cache environment seam drift: {key}")
            env = [f"{key}={new_value}" if entry == old_entry else entry
                   for entry in env]
    return source, binds, env, command


def owned(item: dict, arm: str, container_id: str) -> None:
    source, binds, env, command = spec(arm)
    mapped = [entry["PathOnHost"] for entry in item["HostConfig"]["Devices"]
              if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])]
    labels = item["Config"]["Labels"]
    if not (item["Id"] == container_id and item["Name"] == f"/{name_for(arm)}"
            and item["Image"] == IMAGE and item["HostConfig"]["CpusetCpus"] == "112-191"
            and item["HostConfig"]["NetworkMode"] == "host"
            and mapped == [f"/dev/davinci{i}" for i in range(4)]
            and sorted(item["HostConfig"]["Binds"]) == sorted(binds)
            and sorted(item["Config"]["Env"]) == sorted(env)
            and item["Config"]["Cmd"] == ["bash", "-lc", command]
            and labels.get("hypic.experiment") == EXPERIMENT
            and labels.get("hypic.arm") == arm):
        raise RuntimeError("exact quality container identity mismatch")


def create(arm: str) -> str:
    assert_lane_available()
    name = name_for(arm)
    if inspect(name) is not None:
        raise RuntimeError(f"{name} already exists; inspect before any resume")
    source, binds, env, command = spec(arm)
    args = ["docker", "create", "--name", name, "--label", f"hypic.experiment={EXPERIMENT}",
            "--label", f"hypic.arm={arm}", "--network", "host",
            "--shm-size", str(source["HostConfig"]["ShmSize"]), "--cpuset-cpus", "112-191"]
    for entry in source["HostConfig"]["Devices"]:
        args += ["--device", f"{entry['PathOnHost']}:{entry['PathInContainer']}:{entry['CgroupPermissions']}"]
    for bind in binds:
        args += ["-v", bind]
    for entry in env:
        args += ["-e", entry]
    args += [IMAGE, "bash", "-lc", command]
    run(*args)
    item = inspect(name)
    if item is None:
        raise RuntimeError("quality container absent after create")
    try:
        owned(item, arm, item["Id"])
    except Exception:
        current = inspect(name)
        if current and current["Id"] == item["Id"] and current["State"]["Status"] == "created":
            run("docker", "rm", name)
        raise
    return item["Id"]


def worker_proof(name: str, arm: str) -> dict:
    directory = QROOT / arm
    npu_path = directory / "npu-smi-at-health.txt"
    top_path = directory / "docker-top-at-health.txt"
    npu_path.write_text(run("npu-smi", "info").stdout)
    top_path.write_text(run("docker", "top", name, "-eo", "pid,comm").stdout)
    docker_pids = {int(parts[0]) for line in top_path.read_text().splitlines()[1:]
                   if (parts := line.split()) and parts[0].isdigit()}
    workers = {match.group(1): int(match.group(2)) for match in re.finditer(
        r"^\|\s*([0-3])\s+0\s*\|\s*(\d+)\s*\|\s*VLLMWorker_TP\b",
        npu_path.read_text(), re.M)}
    if (set(workers) != {"0", "1", "2", "3"} or len(set(workers.values())) != 4
            or not set(workers.values()).issubset(docker_pids)):
        raise RuntimeError("quality workers not proven on physical NPU0-3 in exact container")
    return {"worker_pid_by_physical_npu": workers, "npu_smi_sha256": sha256(npu_path),
            "docker_top_sha256": sha256(top_path)}


def start(arm: str, container_id: str, fingerprint: dict,
          guard: ForeignProcessGuard | None = None) -> None:
    name = name_for(arm)
    run("docker", "start", name)
    deadline = time.monotonic() + 2400
    while time.monotonic() < deadline:
        if guard is not None:
            guard.assert_clean()
        item = inspect(name)
        if item is None or item["State"]["Status"] != "running":
            raise RuntimeError("quality container exited before health")
        try:
            with urlopen(f"{BASE_URL}/health", timeout=5) as response:
                healthy = response.status == 200
        except Exception:
            healthy = False
        if healthy:
            if guard is not None:
                guard.assert_clean()
            proof = worker_proof(name, arm)
            logs = run("docker", "logs", name)
            if ("'enable_cpu_binding': False" not in logs.stdout + logs.stderr
                    or "The CPU allocation plan is as follows:" in logs.stdout + logs.stderr):
                raise RuntimeError("quality service binding-off activation missing")
            receipt = {"schema": "hypic-bindingoff-quality-service/v1", "arm": arm,
                       "container": name, "container_id": container_id,
                       "at_utc": datetime.now(timezone.utc).isoformat(),
                       "fingerprint": fingerprint, **proof}
            write_json(QROOT / arm / f"service-start.{container_id[:12]}.json", receipt)
            write_json(QROOT / arm / "service-start.json", receipt)
            status(arm, "service-ready", container_id=container_id)
            return
        time.sleep(10)
    raise RuntimeError("quality service health timeout")


def validate_unit(arm: str, dataset: str, index: int) -> dict:
    path, expected, digest = DATASETS[dataset]
    directory = QROOT / "quality" / arm
    stem = f"{dataset}.run{index}"
    summary_path = directory / f"{stem}.summary.json"
    details_path = directory / f"{stem}.jsonl"
    summary = json.loads(summary_path.read_text())
    scorer = ("supplied_ais_bench_first_option_postprocess" if dataset == "longbenchv2"
              else "supplied_ais_bench_gsm8k_numeric_postprocess")
    fields = {"schema": "hypic-quality-eval/v1", "dataset": dataset,
              "run_id": f"run{index}", "data_sha256": digest,
              "evaluator_script_sha256": EVALUATOR_SHA, "scorer": scorer,
              "model": MODEL_NAME, "base_url": BASE_URL, "concurrency": 32,
              "max_out_len": 2048, "temperature": 0, "seed": 0,
              "ignore_eos": False, "enable_thinking": False, "requests": expected,
              "successful": expected, "failed": 0}
    if any(summary.get(key) != value for key, value in fields.items()):
        raise RuntimeError(f"{stem}: evaluator summary contract drift")
    if (Path(summary.get("details_path", "")).resolve() != details_path.resolve()
            or summary.get("details_sha256") != sha256(details_path)):
        raise RuntimeError(f"{stem}: raw/detail hash mismatch")
    rows = [json.loads(line) for line in details_path.read_text().splitlines() if line]
    if len(rows) != expected or sorted(row.get("index") for row in rows) != list(range(expected)):
        raise RuntimeError(f"{stem}: missing/duplicate sample indexes")
    for row in rows:
        response = row.get("response_text")
        usage = row.get("usage") or {}
        if (row.get("ok") is not True or row.get("error") is not None
                or not isinstance(response, str)
                or row.get("response_sha256") != hashlib.sha256(response.encode()).hexdigest()
                or not isinstance(usage.get("prompt_tokens"), int)
                or usage["prompt_tokens"] <= 0
                or not isinstance(usage.get("completion_tokens"), int)
                or not 0 <= usage["completion_tokens"] <= 2048):
            raise RuntimeError(f"{stem}: invalid row {row.get('index')}")
    correct = sum(row.get("correct") is True for row in rows)
    completion = sum(row["usage"]["completion_tokens"] for row in rows)
    if (summary.get("correct") != correct or summary.get("completion_tokens") != completion
            or not math.isclose(summary.get("accuracy_pct", -1), 100 * correct / expected,
                                abs_tol=1e-9, rel_tol=1e-9)
            or sum(summary.get("finish_reasons", {}).values()) != expected):
        raise RuntimeError(f"{stem}: summary arithmetic mismatch")
    return summary


def check_partial(arm: str, dataset: str, index: int) -> None:
    details = QROOT / "quality" / arm / f"{dataset}.run{index}.jsonl"
    if not details.exists():
        return
    expected = DATASETS[dataset][1]
    rows = [json.loads(line) for line in details.read_text().splitlines() if line]
    indexes = [row.get("index") for row in rows]
    if len(indexes) != len(set(indexes)) or any(not isinstance(i, int) or i < 0 or i >= expected for i in indexes):
        raise RuntimeError("partial quality rows have invalid indexes")
    for row in rows:
        response = row.get("response_text")
        if (row.get("ok") is not True or not isinstance(response, str)
                or row.get("response_sha256") != hashlib.sha256(response.encode()).hexdigest()):
            raise RuntimeError("partial quality row hash/state invalid")


def run_unit(arm: str, dataset: str, index: int, container_id: str,
             guard: ForeignProcessGuard) -> None:
    guard.assert_clean()
    directory = QROOT / "quality" / arm
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{dataset}.run{index}"
    summary_path = directory / f"{stem}.summary.json"
    if summary_path.exists():
        validate_unit(arm, dataset, index)
        receipt_path = directory / f"{stem}.receipt.json"
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("summary_sha256") != sha256(summary_path)
                or receipt.get("details_sha256") != sha256(directory / f"{stem}.jsonl")):
            raise RuntimeError(f"{stem}: previous unit receipt drift")
        status(arm, "unit-reused", dataset=dataset, run=index)
        return
    check_partial(arm, dataset, index)
    status(arm, "unit-running", dataset=dataset, run=index)
    command = ["python3", str(EVALUATOR), "--dataset", dataset, "--data", str(DATASETS[dataset][0]),
               "--base-url", BASE_URL, "--model", MODEL_NAME, "--output-dir", str(directory),
               "--run-id", f"run{index}", "--concurrency", "32", "--max-out-len", "2048",
               "--seed", "0", "--timeout", "2400", "--retries", "2"]
    started = time.monotonic()
    with (directory / f"{stem}.log").open("a", encoding="utf-8") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                timeout=21600, check=False)
    if result.returncode:
        raise RuntimeError(f"{stem}: evaluator exit {result.returncode}")
    guard.assert_clean()
    summary = validate_unit(arm, dataset, index)
    write_json(directory / f"{stem}.receipt.json", {
        "schema": "hypic-bindingoff-quality-unit/v1", "arm": arm, "dataset": dataset,
        "run": index, "container_id": container_id, "duration_s": time.monotonic() - started,
        "summary_sha256": sha256(summary_path),
        "details_sha256": sha256(directory / f"{stem}.jsonl"),
        "correct": summary["correct"], "requests": summary["requests"]})
    status(arm, "unit-verified", dataset=dataset, run=index,
           accuracy_pct=summary["accuracy_pct"])


def cleanup(arm: str, container_id: str) -> None:
    name = name_for(arm)
    item = inspect(name)
    if item is None or item["Id"] != container_id:
        raise RuntimeError("owned quality container disappeared or changed identity")
    owned(item, arm, container_id)
    start_path = QROOT / arm / "service-start.json"
    reached_health = start_path.exists()
    prehealth_pids: set[int] = set()
    top_error = None
    if not reached_health and item["State"]["Status"] == "running":
        top = run("docker", "top", name, "-eo", "pid,comm", check=False)
        if top.returncode:
            top_error = f"pre-health docker top exited {top.returncode}"
        else:
            prehealth_pids = {int(parts[0]) for line in top.stdout.splitlines()[1:]
                              if (parts := line.split()) and parts[0].isdigit()}
            if not prehealth_pids:
                top_error = "pre-health docker top returned no host PIDs"
    log_path = QROOT / arm / f"service.full.{container_id[:12]}.log"
    log_error = None
    try:
        # A full 12-unit quality campaign can produce a very large service log.
        # Stream it to disk instead of retaining it in controller RAM.
        with log_path.open("wb") as log:
            capture = subprocess.run(["docker", "logs", name], stdout=log,
                                     stderr=subprocess.STDOUT, timeout=300, check=False)
        if capture.returncode:
            log_error = f"docker logs exited {capture.returncode}"
    except Exception as exc:
        log_error = f"{type(exc).__name__}: {exc}"
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "60", name)
    run("docker", "rm", name)
    start_receipt = json.loads(start_path.read_text()) if reached_health else None
    if (start_receipt is not None and start_receipt.get("container_id") != container_id
            or inspect(name) is not None):
        raise RuntimeError("owned quality service removal cannot be proven")
    snapshot = run("npu-smi", "info").stdout
    observed = npu_processes(snapshot)
    old_worker_pids = (set(start_receipt["worker_pid_by_physical_npu"].values())
                       if start_receipt is not None else prehealth_pids)
    if any(entry["pid"] in old_worker_pids for entry in observed):
        raise RuntimeError("owned quality worker remains on NPU after container removal")
    listeners = run("ss", "-ltn", "sport", f":{PORT}").stdout
    if re.search(rf":{PORT}(?:\s|$)", listeners, re.M):
        raise RuntimeError("quality service port remains occupied after container removal")
    lane_error = None
    try:
        assert_lane_available()
    except RuntimeError as exc:
        lane_error = str(exc)
    receipt = {
        "schema": "hypic-bindingoff-quality-service-stop/v1", "arm": arm,
        "container": name, "container_id": container_id,
        "container_removed": True, "owned_npus_released": top_error is None,
        "port_released": True, "service_reached_health": reached_health,
        "prehealth_top_error": top_error,
        "lane_available": lane_error is None, "lane_error": lane_error,
        "foreign_npu_processes": [entry for entry in observed
                                  if entry["pid"] not in old_worker_pids],
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "service_log_sha256": sha256(log_path) if log_path.exists() else None,
        "service_log_error": log_error}
    write_json(QROOT / arm / f"service-stop.{container_id[:12]}.json", receipt)
    write_json(QROOT / arm / "service-stop.json", receipt)
    status(arm, "service-released" if lane_error is None else "release-with-lane-conflict",
           container_id=container_id)
    if log_error:
        raise RuntimeError(f"service released, but log capture failed: {log_error}")
    if top_error:
        raise RuntimeError(f"service released, but pre-health process proof failed: {top_error}")
    if lane_error:
        raise RuntimeError(f"owned service released, but shared lane unavailable: {lane_error}")


def stop_owned_for_abort(arm: str, container_id: str) -> None:
    """Break in-flight requests after an invalid arm; final cleanup keeps the receipt."""
    name = name_for(arm)
    item = inspect(name)
    if item is None:
        raise RuntimeError("owned quality container absent during abort")
    owned(item, arm, container_id)
    if item["State"]["Status"] == "running":
        run("docker", "stop", "--time", "30", container_id)


def interrupt(_number: int, _frame: object) -> None:
    raise RuntimeError("quality controller interrupted; cleaning exact owned container")


def main() -> int:
    if ATTEMPT.startswith("hotpath-"):
        raise RuntimeError("hotpath quality is separate from the frozen 12-unit campaign")
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    fingerprint = preflight()
    if not args.run:
        print(json.dumps(fingerprint, sort_keys=True))
        return 0
    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    QROOT.mkdir(parents=True, exist_ok=True)
    with (QROOT / "controller.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        completed = [QROOT / "quality" / args.arm / f"{dataset}.run{index}.summary.json"
                     for dataset, index in UNIT_ORDER]
        if all(path.exists() for path in completed):
            if inspect(name_for(args.arm)) is not None:
                raise RuntimeError("all quality summaries exist but exact service still exists; audit ownership before completion")
            for dataset, index in UNIT_ORDER:
                validate_unit(args.arm, dataset, index)
            stop_path = QROOT / args.arm / "service-stop.json"
            if not stop_path.exists() or json.loads(stop_path.read_text()).get("lane_available") is not True:
                raise RuntimeError("all quality summaries exist without service release receipt")
            print(json.dumps({"arm": args.arm, "status": "already-complete-and-verified"}))
            return 0
        status(args.arm, "preflight-passed", fingerprint=fingerprint)
        container_id = ""
        error = None
        guard = None
        try:
            container_id = create(args.arm)
            start(args.arm, container_id, fingerprint)
            start_receipt = json.loads((QROOT / args.arm / "service-start.json").read_text())
            guard = ForeignProcessGuard(args.arm, start_receipt["worker_pid_by_physical_npu"])
            guard.start()
            for dataset, index in UNIT_ORDER:
                run_unit(args.arm, dataset, index, container_id, guard)
            guard.assert_clean()
            status(args.arm, "all-units-verified")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            status(args.arm, "failed-or-incomplete", error=error)
            raise
        finally:
            try:
                if guard is not None:
                    guard.close()
            finally:
                if container_id:
                    cleanup(args.arm, container_id)
                    status(args.arm, "incomplete-released" if error else "arm-complete-and-released",
                           container_id=container_id, prior_error=error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
