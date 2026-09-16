#!/usr/bin/env python3
"""Independently recompute the DASC v12 mechanism verdict from raw artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess


SHA_LINE = re.compile(r"^([0-9a-f]{64}) [ *](.+)$")
EXPECTED_MODEL_CONFIG = Path("/cache/efim/Qwen3.6-27B/config.json")
EXPECTED_IMAGE = "quay.io/ascend/vllm-ascend:v0.23.0"
EXPECTED_CONTAINER = "/dasc_qwen36_physical_order_fix_v12_20260915"
EXPECTED_RESULT_ROOT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/physical-cache-order-fix-v12"
)
CONTROLLER_RELATIVE = (
    ".agents/workstreams/dasc-qwen36-ascend-piercing-20260915/"
    "run_physical_cache_v12.sh"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(path: Path) -> list[tuple[str, Path]]:
    records: list[tuple[str, Path]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = SHA_LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"{path}:{line_number}: invalid sha256sum record")
        records.append((match.group(1), Path(match.group(2))))
    if not records:
        raise ValueError(f"{path}: empty manifest")
    return records


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def verify_manifest(path: Path, allowed_root: Path) -> dict:
    failures: list[str] = []
    records = parse_manifest(path)
    for expected, target in records:
        if not target.is_absolute():
            target = path.parent / target
        if not is_within(target, allowed_root):
            failures.append(f"outside allowed root: {target}")
        elif not target.is_file():
            failures.append(f"missing: {target}")
        else:
            actual = sha256_file(target)
            if actual != expected:
                failures.append(f"sha256 mismatch: {target}")
    return {"records": len(records), "failures": failures, "ok": not failures}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected object")
        rows.append(value)
    return rows


def evidence_verdict(rows: list[dict]) -> dict:
    counts = Counter(row.get("event") for row in rows)

    def pids(event: str) -> list[int]:
        return sorted(
            {
                row["pid"]
                for row in rows
                if row.get("event") == event and isinstance(row.get("pid"), int)
            }
        )

    physical = [row for row in rows if row.get("event") == "physical_cache_bound"]
    physical_pids = pids("physical_cache_bound")
    geometry_pids = pids("tp_geometry_aligned")
    dispatch_pids = pids("worker_dispatch_verified")
    cohort_ok = (
        len(physical_pids) == 4
        and physical_pids == geometry_pids
        and physical_pids == dispatch_pids
    )
    compact_ok = bool(physical) and all(
        isinstance(row.get("compact_page_bytes"), int)
        and isinstance(row.get("dense_page_bytes"), int)
        and row["compact_page_bytes"] < row["dense_page_bytes"]
        for row in physical
    )
    blocks_ok = bool(physical) and all(
        isinstance(row.get("num_blocks"), int) and row["num_blocks"] > 0
        for row in physical
    )
    result = {
        "row_count": len(rows),
        "event_counts": dict(sorted(counts.items(), key=lambda item: str(item[0]))),
        "physical_cache_pids": physical_pids,
        "tp_geometry_pids": geometry_pids,
        "worker_dispatch_pids": dispatch_pids,
        "worker_cohort_aligned": cohort_ok,
        "compact_lt_dense": compact_ok,
        "positive_blocks": blocks_ok,
        "heterogeneous_cache_grouped": counts["heterogeneous_cache_grouped"] >= 1,
    }
    result["ok"] = all(
        result[key]
        for key in (
            "worker_cohort_aligned",
            "compact_lt_dense",
            "positive_blocks",
            "heterogeneous_cache_grouped",
        )
    )
    return result


def metric_sum(snapshot: dict[str, float], needle: str) -> float:
    return sum(float(value) for name, value in snapshot.items() if needle in name)


def exact_stopped(record: dict, expected: str) -> bool:
    return (
        record.get("content") == expected
        and record.get("finish_reason") == "stop"
        and not record.get("reasoning_content")
    )


def canary_verdict(canary: dict, evidence: list[dict]) -> dict:
    runs = canary.get("runs", [])
    hit_delta = metric_sum(
        canary.get("metrics_after", {}), "prefix_cache_hits_total"
    ) - metric_sum(canary.get("metrics_before", {}), "prefix_cache_hits_total")
    raw_evidence = evidence_verdict(evidence)
    checks = {
        "schema": canary.get("schema") == "mst.dasc.physical-canary/v1",
        "short_exact": exact_stopped(canary.get("short", {}), "OK"),
        "three_replays": len(runs) == 3,
        "replays_exact": len(runs) == 3
        and all(exact_stopped(run, "VERIFIED") for run in runs),
        "variant_exact": exact_stopped(canary.get("variant", {}), "ASCEND"),
        "cache_hit_positive": hit_delta > 0,
        "raw_activation": raw_evidence["ok"],
    }
    return {
        "checks": checks,
        "prefix_cache_hit_delta": hit_delta,
        "raw_activation": raw_evidence,
        "reported_ok": canary.get("ok"),
        "ok": all(checks.values()),
    }


def verify_source_commit(repo: Path, value: str) -> bool:
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        return False
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=repo,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def option_value(command: list[str], name: str) -> str | None:
    try:
        return command[command.index(name) + 1]
    except (ValueError, IndexError):
        return None


def container_identity_verdict(
    container: dict,
    image: dict,
    *,
    expected_container: str = EXPECTED_CONTAINER,
    expected_result_root: Path = EXPECTED_RESULT_ROOT,
    expected_experiment: str = "dasc-qwen36-physical-cache-v12",
) -> dict:
    config = container.get("Config", {})
    host_config = container.get("HostConfig", {})
    env = {
        item.split("=", 1)[0]: item.split("=", 1)[1]
        for item in config.get("Env", [])
        if "=" in item
    }
    devices = host_config.get("Devices", [])
    davinci = {
        (item.get("PathOnHost"), item.get("PathInContainer"))
        for item in devices
        if re.fullmatch(r"/dev/davinci\d+", str(item.get("PathOnHost")))
    }
    expected_davinci = {
        ("/dev/davinci4", "/dev/davinci0"),
        ("/dev/davinci5", "/dev/davinci1"),
        ("/dev/davinci6", "/dev/davinci2"),
        ("/dev/davinci7", "/dev/davinci3"),
    }
    auxiliary = {item.get("PathOnHost") for item in devices}
    mounts = {item.get("Destination"): item for item in container.get("Mounts", [])}
    command = config.get("Cmd", [])
    checks = {
        "container_name": container.get("Name") == expected_container,
        "image_tag": config.get("Image") == EXPECTED_IMAGE,
        "image_id": bool(image.get("Id")) and container.get("Image") == image.get("Id"),
        "owner_label": config.get("Labels", {}).get("mst.owner") == "c1917797-bit",
        "workstream_label": config.get("Labels", {}).get("mst.workstream")
        == "dasc-qwen36-ascend-piercing-20260915",
        "experiment_label": config.get("Labels", {}).get("mst.experiment")
        == expected_experiment,
        "network_host": host_config.get("NetworkMode") == "host",
        "physical_device_map": davinci == expected_davinci,
        "auxiliary_devices": {
            "/dev/davinci_manager",
            "/dev/devmm_svm",
            "/dev/hisi_hdc",
        }.issubset(auxiliary),
        "visible_devices": env.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
        "plugins": env.get("VLLM_PLUGINS") == "ascend,dasc_vllm_ascend",
        "dasc_enabled": env.get("MST_DASC_ENABLE") == "1",
        "dasc_mode": env.get("MST_DASC_MODE") == "physical-cache-eager",
        "dasc_wmax": env.get("MST_DASC_W_MAX") == "64",
        "serve_model": command[:3]
        == ["vllm", "serve", "/models/Qwen3.6-27B"],
        "tp4": option_value(command, "--tensor-parallel-size") == "4",
        "prefix_caching": "--enable-prefix-caching" in command,
        "mamba_align": option_value(command, "--mamba-cache-mode") == "align",
        "port": option_value(command, "--port") == "8030",
        "model_mount": mounts.get("/models/Qwen3.6-27B", {}).get("Source")
        == "/cache/efim/Qwen3.6-27B"
        and mounts.get("/models/Qwen3.6-27B", {}).get("RW") is False,
        "plugin_mount_read_only": mounts.get("/workspace/dasc", {}).get("Source")
        == str(expected_result_root / "plugin-snapshot")
        and mounts.get("/workspace/dasc", {}).get("RW") is False,
        "result_mount_writable": mounts.get("/dasc-results", {}).get("Source")
        == str(expected_result_root)
        and mounts.get("/dasc-results", {}).get("RW") is True,
        "terminal": container.get("State", {}).get("Running") is False,
    }
    return {"checks": checks, "ok": all(checks.values())}


def source_scope_verdict(repo: Path, commit: str) -> dict:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{CONTROLLER_RELATIVE}"],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        return {"loaded": False, "unscoped_npu_smi_lines": [], "ok": False}
    npu_lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if "npu-smi info" in line
    ]
    unscoped = [line for line in npu_lines if '-i "$device"' not in line]
    expected_maps = [
        f"--device /dev/davinci{physical}:/dev/davinci{logical}"
        for logical, physical in enumerate(range(4, 8))
    ]
    result = {
        "loaded": True,
        "npu_smi_lines": npu_lines,
        "unscoped_npu_smi_lines": unscoped,
        "device_maps_present": all(
            mapping in completed.stdout for mapping in expected_maps
        ),
    }
    result["ok"] = not unscoped and result["device_maps_present"]
    return result


def verify(
    root: Path,
    repo: Path,
    *,
    expected_container: str = EXPECTED_CONTAINER,
    expected_experiment: str = "dasc-qwen36-physical-cache-v12",
) -> dict:
    required = (
        "SUCCESS",
        "controller-exit-code.txt",
        "source-commit.txt",
        "source-status.txt",
        "model-config.sha256",
        "image-inspect.json",
        "container-inspect.json",
        "container-final-inspect.json",
        "npu-before.txt",
        "npu-smi-info.txt",
        "npu-after.txt",
        "plugin-files.sha256",
        "canary.sha256",
        "evidence.jsonl",
        "physical-canary.json",
        "service.log",
        "artifacts.sha256",
    )
    missing = [name for name in required if not (root / name).is_file()]
    result: dict = {"root": str(root), "missing": missing}
    if missing:
        result["ok"] = False
        return result

    result["artifacts_manifest"] = verify_manifest(root / "artifacts.sha256", root)
    result["plugin_manifest"] = verify_manifest(root / "plugin-files.sha256", root)
    result["canary_manifest"] = verify_manifest(root / "canary.sha256", root)

    model_records = parse_manifest(root / "model-config.sha256")
    model_ok = len(model_records) == 1
    if model_ok:
        expected, target = model_records[0]
        model_ok = (
            target.resolve() == EXPECTED_MODEL_CONFIG.resolve()
            and target.is_file()
            and sha256_file(target) == expected
        )
    result["model_config_ok"] = model_ok

    source_commit = (root / "source-commit.txt").read_text(encoding="utf-8").strip()
    source_lines = (root / "source-status.txt").read_text(encoding="utf-8").splitlines()
    result["source_commit"] = source_commit
    result["source_commit_exists"] = verify_source_commit(repo, source_commit)
    result["source_scope"] = source_scope_verdict(repo, source_commit)
    result["source_status_clean"] = bool(source_lines) and not any(
        line and not line.startswith("## ") for line in source_lines
    )
    result["controller_exit_zero"] = (
        root.joinpath("controller-exit-code.txt").read_text(encoding="utf-8").strip()
        == "0"
    )
    image_values = json.loads(root.joinpath("image-inspect.json").read_text(encoding="utf-8"))
    container_values = json.loads(
        root.joinpath("container-final-inspect.json").read_text(encoding="utf-8")
    )
    result["container_identity"] = (
        container_identity_verdict(
            container_values[0],
            image_values[0],
            expected_container=expected_container,
            expected_result_root=root,
            expected_experiment=expected_experiment,
        )
        if len(container_values) == 1 and len(image_values) == 1
        else {"checks": {}, "ok": False}
    )
    canary = json.loads(
        root.joinpath("physical-canary.json").read_text(encoding="utf-8")
    )
    result["canary"] = canary_verdict(canary, load_jsonl(root / "evidence.jsonl"))
    result["ok"] = (
        not missing
        and result["artifacts_manifest"]["ok"]
        and result["plugin_manifest"]["ok"]
        and result["canary_manifest"]["ok"]
        and result["model_config_ok"]
        and result["source_commit_exists"]
        and result["source_scope"]["ok"]
        and result["source_status_clean"]
        and result["controller_exit_zero"]
        and result["container_identity"]["ok"]
        and result["canary"]["ok"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--expected-container", default=EXPECTED_CONTAINER)
    parser.add_argument(
        "--expected-experiment", default="dasc-qwen36-physical-cache-v12"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(
        args.root.resolve(),
        args.repo.resolve(),
        expected_container=args.expected_container,
        expected_experiment=args.expected_experiment,
    )
    encoded = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
