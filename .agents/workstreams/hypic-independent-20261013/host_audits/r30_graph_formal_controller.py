"""HOST-only formal graph first-pair driver; default is offline --check.

The genuine unchanged formal_r15_tp4 module owns device admission, workload,
journal, guard and cleanup. controller_sha256 retains that real base identity;
host_controller_sha256 separately identifies this launch adapter. No aliasing.
"""
import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
import formal_r15_tp4 as base
from host_audits import r27_graph_controller as graph
from host_audits import r30_graph_formal_audit as evidence

ENTRY = "host_audits/r30_graph_formal_controller.py"
HELPER = "host_audits/r27_graph_controller.py"
HELPER_SHA = "50a97e444fb14b3cd3a0b39833e861e3f9d0aba6f7d1682a1673858e7fec5342"
BASE = "formal_r15_tp4.py"
BASE_SHA = "bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
_LOCK = threading.Lock()


def check_contract(contract, *, source_root=WORKSTREAM, base_module=base):
    root = Path(source_root).resolve()
    sources = contract.get("host_controller_source_sha256")
    evidence.native._sources(root, sources)
    own = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (sources.get(ENTRY) != own
            or contract.get("host_controller_sha256") != own
            or sources.get(HELPER) != HELPER_SHA
            or sources.get(BASE) != BASE_SHA
            or contract.get("controller_sha256") != BASE_SHA
            or contract.get("base_controller_sha256") != BASE_SHA
            or Path(base_module.__file__).resolve() != root / BASE
            or hashlib.sha256(Path(base_module.__file__).read_bytes()).hexdigest() != BASE_SHA):
        raise ValueError("actual HOST adapter/helper/base identity required")
    evidence.host_binding(contract, root)
    cfg, manifest = evidence.components._manifest(contract, root)
    policy = evidence.validate_policy(contract, cfg)
    prior = evidence.prerequisite(contract, root)
    raw = Path(contract["raw_root"])
    if not raw.is_absolute() or raw.exists():
        raise ValueError("new immutable absolute raw root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(contract.get("absolute_stop_utc"))
    return dict(configuration_valid=True, device_run=False,
        device_admission_performed=False, controller_sha256=own,
        base_controller_sha256=BASE_SHA, graph_runtime=contract["graph_runtime"],
        policy=policy, active_manifest_sha256=manifest,
        source_bindings=len(contract.get("baseline_host_source_sha256")
            or contract["cache_diagnostic"]["source_sha256"]),
        prerequisite=prior)


def rewrite_launch(data, contract, checked):
    # The retained helper mutates the SAME argv list consumed by the base owner.
    graph._rewrite_launch(data, contract, checked)
    argv = data["argv"]
    if argv.count("VLLM_LOGGING_LEVEL=DEBUG") != 1:
        raise ValueError("one known common graph Canary logging override required")
    argv[argv.index("VLLM_LOGGING_LEVEL=DEBUG")] = "VLLM_LOGGING_LEVEL=INFO"
    data["graph_runtime"]["common_environment_added"] = ["VLLM_LOGGING_LEVEL=INFO"]
    data["graph_runtime"]["official_debug_logging"] = False
    data["graph_runtime"]["formal_logging"] = "INFO"
    return data


def run_contract(contract, *, source_root=WORKSTREAM, base_module=base):
    checked = check_contract(contract, source_root=source_root, base_module=base_module)
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("one owned formal graph driver per process")
    original = base_module.write
    raw = Path(contract["raw_root"])
    launches = 0
    def write(root, name, data):
        nonlocal launches
        if name == "launch.json":
            if Path(root) != raw or launches:
                raise ValueError("one exact formal raw launch required")
            launches += 1
            rewrite_launch(data, contract, checked)
        return original(root, name, data)
    base_module.write = write
    try:
        result = base_module.run_contract(contract)
        if launches != 1:
            raise ValueError("actual base launch absent")
        return result
    finally:
        if base_module.write is write:
            base_module.write = original
        _LOCK.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    c = json.loads(Path(args.contract).read_text())
    if args.run:
        run_contract(c)
    else:
        print(json.dumps(check_contract(c)))
