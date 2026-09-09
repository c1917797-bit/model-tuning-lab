#!/usr/bin/env python3
"""Bounded diagnostic capture on an already-ready service."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--cold-profile-index", type=int)
    ap.add_argument("--expected-replicas", type=int, default=2)
    a = ap.parse_args()
    if a.expected_replicas < 1:
        ap.error("expected replica count must be positive")
    root = Path(__file__).resolve().parent
    a.output.mkdir(parents=True, exist_ok=False)
    targets = json.loads(subprocess.check_output([sys.executable, str(root / "resolve_qwen35_dp_profile_workers.py"), "--container", a.container, "--expected-replicas", str(a.expected_replicas)], text=True, timeout=90))
    (a.output / "targets.json").write_text(json.dumps(targets, indent=2))
    cid = targets["container_id"]
    ready, go = a.output / "ready", a.output / "go"
    command = [sys.executable, str(root / "run_qwen35_profile_request.py"), "--base-url", "http://127.0.0.1:10010", "--model", "Qwen3-5/Qwen3.5-27B", "--dataset", "/cache/cch/query_rewrite.jsonl", "--dataset-sha256", "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d2674ca5a8704a056e"]
    # Keep the exact frozen workload identity; profile timings are diagnostic only.
    command[-1] = "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
    command += ["--run-id", a.output.name, "--control-mode", "external-msprof", "--external-ready-file", str(ready), "--external-go-file", str(go), "--output", str(a.output / "request.json")]
    if a.cold_profile_index is not None:
        command += ["--skip-warmup", "--profile-index", str(a.cold_profile_index)]
    request = subprocess.Popen(command, stdout=subprocess.DEVNULL)
    profilers = []
    def wait_for(predicate, seconds, process):
        deadline = time.monotonic() + seconds
        while not predicate():
            if process.poll() is not None:
                raise RuntimeError("child exited before expected readiness")
            if time.monotonic() > deadline:
                raise TimeoutError("capture stage timeout")
            time.sleep(0.5)
    try:
        wait_for(ready.exists, 600, request)
        for target in targets["targets"]:
            pid = target["container_pid"]
            out = a.output / str(pid)
            out.mkdir()
            log = a.output / f"msprof-{pid}.log"
            handle = log.open("w")
            proc = subprocess.Popen(["docker", "exec", "-i", cid, "/usr/local/Ascend/cann-9.1.0/bin/msprof", "--dynamic=on", f"--pid={pid}", f"--output={out}", "--ascendcl=on", "--runtime-api=on", "--task-time=l2", "--aic-metrics=PipeUtilization"], stdin=subprocess.PIPE, stdout=handle, stderr=subprocess.STDOUT, text=True)
            profilers.append((proc, handle, log, out))
            proc.stdin.write("start\n")
            proc.stdin.flush()
            wait_for(lambda: "start success" in log.read_text(), 180, proc)
        go.write_text("go\n")
        if request.wait(timeout=600):
            raise RuntimeError("profile request failed")
        for proc, handle, log, out in profilers:
            proc.stdin.write("stop\n")
            proc.stdin.flush()
            wait_for(lambda: "stop success" in log.read_text(), 180, proc)
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            proc.wait(timeout=120)
            handle.close()
            traces = list(out.glob("PROF_*"))
            if not traces:
                raise RuntimeError("missing PROF output")
            for trace in traces:
                with (out / "export.log").open("a") as export:
                    subprocess.run(["docker", "exec", cid, "/usr/local/Ascend/cann-9.1.0/bin/msprof", "--export=on", f"--output={trace}"], stdout=export, stderr=subprocess.STDOUT, check=True, timeout=300)
        print("CAPTURE_COMPLETE", a.output, flush=True)
    finally:
        if request.poll() is None:
            request.terminate()
        for proc, handle, log, out in profilers:
            if proc.poll() is None:
                try:
                    proc.stdin.write("stop\nquit\n")
                    proc.stdin.flush()
                    proc.wait(timeout=30)
                except (BrokenPipeError, subprocess.TimeoutExpired):
                    proc.terminate()
            handle.close()


if __name__ == "__main__":
    main()
