"""Exact-image device-free API checks. Default OFF; no device initialization."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"

def ref(path):
    p = Path(path)
    assert p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in (p, *p.parents))
    b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def checked(r):
    assert set(r) == {"path", "bytes", "sha256"} and ref(r["path"]) == r
    return r

def main():
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--worker-ref", type=json.loads)
    p.add_argument("--controller-ref", type=json.loads)
    p.add_argument("--tests-ref", type=json.loads)
    a = p.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False, NPU=False)))
        return 0
    assert a.worker_ref and a.controller_ref and a.tests_ref
    pins = [checked(r) for r in [a.worker_ref, a.controller_ref, a.tests_ref]]
    assert os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0"
    assert "torch" not in sys.modules and "torch_npu" not in sys.modules
    worker_path = Path(a.worker_ref["path"])
    for f in [worker_path, Path(a.controller_ref["path"])]:
        r = subprocess.run([sys.executable, "-I", "-B", str(f)],
                           capture_output=True, text=True, timeout=10)
        assert r.returncode == 0 and json.loads(r.stdout)["enabled"] is False, r.stderr
    tests = subprocess.run([sys.executable, "-I", "-B", a.tests_ref["path"], "-v"],
                           capture_output=True, text=True, timeout=90)
    assert tests.returncode == 0, tests.stderr
    match = re.search(r"Ran (\d+) tests?", tests.stderr)
    assert match and int(match.group(1)) >= 15, tests.stderr
    spec = importlib.util.spec_from_file_location("_replay_cpu_api", worker_path)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    import torch
    import torch.distributed as dist
    assert "torch_npu" not in sys.modules
    raw = bytes.fromhex("00000080803f80bf01007f7f")
    tensor = torch.frombuffer(bytearray(raw), dtype=torch.bfloat16).reshape(2, 3).clone()
    assert worker.cpu_bytes(tensor, torch) == raw
    enabled = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    assert type(enabled) is bool and type(warn) is bool
    callable_identity = worker.callable_source(dist.all_reduce)
    assert callable_identity["transport_kernel_observed"] is False
    import torch.distributed.run as torchrun
    parsed = torchrun.parse_args(["--standalone", "--nnodes=1", "--nproc-per-node=4",
                                  "--local-addr=127.0.0.1", str(worker_path)])
    assert parsed.standalone and parsed.local_addr == "127.0.0.1" and parsed.nproc_per_node == "4"
    for r in pins:
        checked(r)
    result = dict(schema="bole.collective-replay-sameimage-software/v1",
        image=IMAGE, worker_ref=a.worker_ref, controller_ref=a.controller_ref,
        checks_source_ref=ref(__file__), tests_ref=a.tests_ref, passed=True,
        devices=[], NPU=False, backend_autoload="0", torch_npu_imported=False,
        torch_version=str(torch.__version__), python=sys.version.split()[0],
        actual_tests=int(match.group(1)), tests_stdout=tests.stdout, tests_stderr=tests.stderr,
        bf16_roundtrip=True, collective_callable=callable_identity,
        actual_torchrun_parser=True, torchrun_local_addr=parsed.local_addr,
        torch_deterministic_enabled=enabled, torch_deterministic_warn_only=warn,
        numerical_qualified=False, formal_performance=False)
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
