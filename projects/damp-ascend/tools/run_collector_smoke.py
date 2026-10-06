"""Parent-owned, one-shot DAMP collector smoke; never a performance test."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

REPO = Path("/opt/host/vnf/austinov/model-tuning-lab")
RESULT = Path("/cache/cch/qwen36-damp-20261006")
MODEL = "/cache/efim/Qwen3.6-27B"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
NAME = "qwen36_damp_collector_tp4_20261006_v1"
AUDIT = RESULT / "smoke-hook-v1-launch"
MANIFEST = RESULT / "calibration-inputs/smoke-hook-v1.json"
SOURCE = "/cache/cch/qwen36-awq-w4a8-20260923/calibration_text_v1.jsonl"
EXPECTED_SOURCE = "2ad23073422f443ac35a90af82812f236ceea2da998a5fe8cb7c65b83a0b0ec3"
PYTHON = "/usr/local/python3.12.13/bin/python3"

def require(value, message):
    if not value:
        raise RuntimeError(message)

def output(argv, timeout=30):
    result = subprocess.run(argv, check=True, text=True, capture_output=True, timeout=timeout)
    return result.stdout

def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")

def idle_snapshot():
    raw = output(["npu-smi", "info"])
    telemetry, current = {}, None
    for line in raw.splitlines():
        head = re.match(r"^\|\s*(\d+)\s+910B4\s*\|", line)
        if head:
            current = int(head.group(1))
            continue
        fields = line.split("|")
        row = (re.fullmatch(r"\s*(\d+)\s+\d+\s*/\s*\d+\s+(\d+)\s*/\s*(\d+)\s*", fields[3])
               if len(fields) == 5 and re.fullmatch(r"\s*[0-9A-Fa-f:.]+\s*", fields[2]) else None)
        if row and current is not None:
            telemetry[current] = dict(aicore=int(row[1]), hbm_mib=int(row[2]), capacity_mib=int(row[3]))
    for npu in range(4, 8):
        require("No running processes found in NPU " + str(npu) in raw, "target has real compute process")
        require(npu in telemetry and telemetry[npu]["aicore"] == 0, "unknown/busy target telemetry")
        require(telemetry[npu]["hbm_mib"] <= 3165, "target HBM outside idle envelope")
    return dict(npu_smi=raw, telemetry=telemetry,
                docker_ps=output(["docker", "ps", "--no-trunc"]),
                uda_namespace=Path("/proc/uda/namespace_node").read_text(),
                meminfo=Path("/proc/meminfo").read_text())

def python_in_container(*args):
    # Append to the original CANN path; never replace acl discovery paths.
    shell = 'set -e; export PYTHONPATH="' + str(REPO) + '/projects/damp-ascend/collector:${PYTHONPATH:-}"; exec ' + PYTHON + ' -B "$@"'
    return ["docker", "exec", NAME, "/bin/bash", "-c", shell, "damp-python", *args]

def logged(label, argv, timeout):
    print("START " + label, flush=True)
    started = time.monotonic()
    with (AUDIT / (label + ".log")).open("x", encoding="utf-8") as stream:
        result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    write_new(AUDIT / (label + ".receipt.json"),
              dict(argv=argv, exit_code=result.returncode, seconds=time.monotonic()-started))
    require(result.returncode == 0, label + " failed; preserve log and do not rerun")
    print("PASS " + label, flush=True)

def main():
    require(Path.cwd().resolve() == REPO and REPO.is_dir(), "canonical cwd required")
    require(not AUDIT.exists() and not MANIFEST.exists()
            and all(not (RESULT / ("smoke-hook-v1-" + arm)).exists() for arm in ("off", "on")),
            "v1 output already exists; never overwrite")
    require(hashlib.sha256(Path(SOURCE).read_bytes()).hexdigest() == EXPECTED_SOURCE,
            "smoke source changed")
    collision = subprocess.run(["docker", "container", "inspect", NAME], capture_output=True)
    require(collision.returncode != 0, "owned container name already exists")
    image = json.loads(output(["docker", "image", "inspect", IMAGE]))[0]
    require(image["Id"] == IMAGE and image["Architecture"] == "arm64", "image identity mismatch")
    snapshot = idle_snapshot()
    available = int(re.search(r"^MemAvailable:\s*(\d+)", snapshot["meminfo"], re.M)[1])
    require(available >= 64 * 1024 * 1024, "insufficient ordinary host memory; do not release HugeTLB")
    AUDIT.mkdir(parents=True, exist_ok=False)
    write_new(AUDIT / "prelaunch.json", snapshot)
    hashes = {}
    for path in sorted((REPO / "projects/damp-ascend/collector").rglob("*")):
        if path.is_file():
            require("__pycache__" not in path.parts, "unexpected generated collector code")
            hashes[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_new(AUDIT / "source.json", dict(commit=output(["git", "rev-parse", "HEAD"]).strip(),
                                         dirty=output(["git", "status", "--short"]), files=hashes))
    create = ["docker", "create", "--name", NAME, "--network", "host", "--shm-size", "8g",
              "-e", "ASCEND_RT_VISIBLE_DEVICES=0,1,2,3", "-e", "PYTHONDONTWRITEBYTECODE=1",
              "-e", "VLLM_USE_V1=1", "-e", "VLLM_WORKER_MULTIPROC_METHOD=spawn",
              "-e", "OMP_NUM_THREADS=1", "-e", "TOKENIZERS_PARALLELISM=false",
              "-v", "/usr/local/Ascend/driver:/usr/local/Ascend/driver:ro",
              "-v", str(REPO) + ":" + str(REPO) + ":ro",
              "-v", MODEL + ":" + MODEL + ":ro",
              "-v", str(RESULT) + ":" + str(RESULT) + ":rw",
              "-v", SOURCE + ":" + SOURCE + ":ro"]
    for physical in range(4, 8):
        create += ["--device", "/dev/davinci" + str(physical) + ":/dev/davinci" + str(physical-4)]
    for common in ("/dev/davinci_manager", "/dev/devmm_svm", "/dev/hisi_hdc"):
        create += ["--device", common]
    create += [IMAGE, "sleep", "infinity"]
    created = False
    try:
        container_id = output(create).strip()
        created = True
        inspect = json.loads(output(["docker", "inspect", NAME]))[0]
        require(inspect["Id"] == container_id and inspect["Image"] == IMAGE, "container identity mismatch")
        require(inspect["HostConfig"]["Privileged"] is False, "privileged container forbidden")
        mapping = {d["PathOnHost"]: d["PathInContainer"] for d in inspect["HostConfig"]["Devices"]}
        require(mapping == {**{"/dev/davinci"+str(p):"/dev/davinci"+str(p-4) for p in range(4,8)},
                            **{p:p for p in ("/dev/davinci_manager", "/dev/devmm_svm", "/dev/hisi_hdc")}},
                "unexpected physical mapping")
        mounts = {m["Destination"]: m for m in inspect["Mounts"]}
        require(mounts[str(REPO)]["RW"] is False and mounts[MODEL]["RW"] is False
                and mounts[str(RESULT)]["RW"] is True, "mount mutability mismatch")
        write_new(AUDIT / "container.json", dict(id=container_id, image=inspect["Image"],
                  devices=inspect["HostConfig"]["Devices"], mounts=inspect["Mounts"],
                  privileged=False, network=inspect["HostConfig"]["NetworkMode"]))
        output(["docker", "start", NAME])
        # Import/schema inspection is no-device; a separate canary initializes only mapped cards.
        logged("import", python_in_container("-c",
              "import acl, torch, torch_npu, importlib.metadata as m; "
              "import vllm_ascend.ops; import vllm_ascend.ops.gdn as g; "
              "import vllm_ascend.worker.model_runner_v1 as r; import damp_capture.patch as p; "
              "from vllm_ascend.utils import enable_custom_op; assert enable_custom_op(); "
              "from damp_capture.contract import file_digest,GDN_SHA,RUNNER_SHA; "
              "assert file_digest(g.__file__)==GDN_SHA and file_digest(r.__file__)==RUNNER_SHA; "
              "assert len([e for e in m.entry_points(group='vllm.general_plugins') if e.name=='damp_capture'])==1; "
              "print(g.__file__,r.__file__,p.__file__,torch.__version__,torch_npu.__version__); "
              "print(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)"), 90)
        logged("prepare", python_in_container("-m", "damp_capture.prepare", "--mode", "smoke",
              "--limit", "2", "--input", SOURCE, "--output", str(MANIFEST)), 90)
        logged("canary", python_in_container("-c",
              "import torch,torch_npu; assert torch.npu.device_count()==4; "
              "[(torch.npu.set_device(i), print('logical',i,'sum',torch.ones(16,device='npu').sum().cpu().item())) for i in range(4)]; "
              "torch.npu.synchronize()"), 90)
        for arm in ("off", "on"):
            # Require no orphaned workers between separate paired processes.
            top = output(["docker", "top", NAME, "-eo", "pid,args"])
            require("python" not in top, "unexpected model process before paired arm")
            idle_snapshot()
            logged(arm, python_in_container("-m", "damp_capture.run", "--manifest", str(MANIFEST),
                   "--output-dir", str(RESULT / ("smoke-hook-v1-" + arm)), "--capture", arm,
                   "--batch-size", "2", "--memory-utilization", "0.80"), 900)
        logged("validate", python_in_container("-m", "damp_capture.validate", "--manifest", str(MANIFEST),
              "--output-dir", str(RESULT / "smoke-hook-v1-on"),
              "--dense-output-dir", str(RESULT / "smoke-hook-v1-off")), 90)
        write_new(AUDIT / "RESULT.json", dict(status="pass", scope="collector-smoke-only",
                  not_proven=["full calibration", "compressed recurrence", "graph", "E2E throughput", "task accuracy"]))
    except Exception as error:
        write_new(AUDIT / "FAILURE.json", dict(error_type=type(error).__name__, error=str(error)))
        raise
    finally:
        if created:
            # Only this fresh owned container; retain all logs and container for recovery.
            stopped = subprocess.run(["docker", "stop", "--time", "30", NAME], capture_output=True, text=True, timeout=45)
            write_new(AUDIT / "stop.json", dict(exit_code=stopped.returncode, stdout=stopped.stdout,
                                               stderr=stopped.stderr))
            print("STOPPED AND RETAINED " + NAME, flush=True)

if __name__ == "__main__":
    main()
