#!/usr/bin/env python3
"""Resolve all DP replicas' TP0 profiling targets; never choose just the first."""
import argparse
import json
import re
import subprocess


def parse_workers(output):
    targets = []
    for line in output.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) != 2 or not fields[0].isdigit():
            continue
        if re.search(r"\bWorker_TP0\b", fields[1]):
            targets.append(int(fields[0]))
    return sorted(set(targets))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--expected-replicas", type=int, default=2)
    args = parser.parse_args()
    if args.expected_replicas < 1 or args.container.startswith("-"):
        parser.error("invalid replica count or container name")
    def run(*command):
        return subprocess.check_output(command, text=True, timeout=30)
    identity = run("docker", "inspect", "--format", "{{.Id}}", args.container).strip()
    pids = parse_workers(run("docker", "exec", identity, "ps", "-e", "-o", "pid=,args="))
    if len(pids) != args.expected_replicas:
        raise RuntimeError(f"expected {args.expected_replicas} TP0 targets, found {len(pids)}; inspect process naming before proceeding")
    targets = []
    for pid in pids:
        socket = f"/root/dynamic_profiling_socket_{pid}"
        subprocess.run(["docker", "exec", identity, "test", "-S", socket], check=True, timeout=30)
        targets.append({"container_pid": pid, "socket": socket})
    print(json.dumps({"container_id": identity, "targets": targets,
                      "note": "Capture both targets. PID order is not a proven DP-rank or physical-NPU mapping."}, indent=2))


if __name__ == "__main__":
    main()
