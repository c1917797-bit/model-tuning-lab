"""HOST-only graph Canary launcher around the unchanged, hash-bound TP4 owner.

Default CLI operation checks files/configuration only. --run alone delegates all
device admission, immutable-root creation, deadline/foreign guards and cleanup
to formal_r15_tp4.run_contract. No device framework is imported here.
Common DEBUG logging is for this bounded Canary, never a speed measurement.
"""
import argparse
import copy
import hashlib
import json
import sys
import threading
from pathlib import Path

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
import formal_r15_tp4 as base

ENTRY = "host_audits/r27_graph_controller.py"
BASE_ENTRY = "formal_r15_tp4.py"
BASE_SHA256 = "bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PROFILE = "selective-prefill-native-decode-v1"
BOOTSTRAP = "graph_candidate/bootstrap"
GRAPH_RUNTIME_SOURCES = (
    "graph_candidate/__init__.py", "graph_candidate/activation.py",
    "graph_candidate/source_contract.py", "graph_candidate/entry_router.py",
    "graph_candidate/prefill_bridge.py", "graph_candidate/worker_loader.py",
    "graph_candidate/bootstrap/sitecustomize.py")
# Actual pinned config/compilation.py, CompilationMode(enum.IntEnum), lines37-48:
# NONE=0, STOCK_TORCH_COMPILE=1, DYNAMO_TRACE_ONCE=2, VLLM_COMPILE=3.
ENUM_SOURCE_SHA256 = "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913"
CAPTURE_SIZES = [1, 4, 8, 16, 24, 32]
_OWNED_RUN = threading.Lock()


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sources(root, mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("explicit source map required")
    for name, digest in mapping.items():
        if not isinstance(name, str):
            raise ValueError("relative source name required")
        original = root / name
        resolved = original.resolve()
        if (original.is_symlink() or not resolved.is_relative_to(root)
                or not resolved.is_file() or _digest(resolved) != digest):
            raise ValueError("source drift: " + name)


def check_contract(contract, *, source_root=WORKSTREAM, base_module=base):
    """No docker, port binding, process probe, raw creation or activation."""
    root = Path(source_root).resolve()
    own_hash = _digest(__file__)
    host = contract.get("host_controller_source_sha256")
    _sources(root, host)
    if (contract.get("controller_sha256") != own_hash
            or host.get(ENTRY) != own_hash
            or host.get(BASE_ENTRY) != BASE_SHA256
            or contract.get("base_controller_sha256") != BASE_SHA256
            or Path(base_module.__file__).resolve() != root / BASE_ENTRY
            or _digest(base_module.__file__) != BASE_SHA256):
        raise ValueError("real entry/base controller identity required")
    if (contract.get("physical_npus") != [0, 1, 2, 3] or contract.get("tp") != 4
            or contract.get("enforce_eager") is not False
            or contract.get("image") != IMAGE):
        raise ValueError("pinned graph runtime requires physical0-3 TP4, eager=False")
    graph = contract.get("graph_runtime")
    if (not isinstance(graph, dict)
            or graph.get("profile") != PROFILE
            or type(graph.get("candidate_enabled")) is not bool
            or type(graph.get("compilation_mode")) is not int
            or graph.get("compilation_mode") != 3
            or graph.get("cudagraph_mode") != "FULL_DECODE_ONLY"
            or graph.get("capture_sizes") != CAPTURE_SIZES
            or graph.get("official_debug_logging") is not True
            or graph.get("official_compilation_source_sha256") != ENUM_SOURCE_SHA256):
        raise ValueError("explicit pinned VLLM_COMPILE/FULL_DECODE_ONLY profile required")
    enabled = graph["candidate_enabled"]
    expected_group = "G3" if enabled else "G1"
    group = contract.get("graph_canary_group", contract.get("performance_group"))
    if (group != expected_group
            or ("performance_group" in contract
                and contract["performance_group"] != expected_group)):
        raise ValueError("native G1/treatment G3 graph flag mismatch")
    diagnostic = contract.get("cache_diagnostic")
    if enabled:
        if not isinstance(diagnostic, dict) or not diagnostic.get("compact_manifest"):
            raise ValueError("graph treatment requires explicit source-bound manifest")
        runtime_sources = diagnostic.get("source_sha256")
        _sources(root, runtime_sources)
        name = diagnostic["compact_manifest"]
        if not isinstance(name, str) or name not in runtime_sources:
            raise ValueError("graph manifest must be in runtime source map")
        manifest = json.loads((root / name).read_text())
        if manifest.get("graph_profile") != PROFILE:
            raise ValueError("graph manifest profile mismatch")
        manifest_sources = manifest.get("source_sha256")
        _sources(root, manifest_sources)
        required = set(GRAPH_RUNTIME_SOURCES) | {manifest.get("config")}
        if (None in required or not required.issubset(manifest_sources)
                or any(runtime_sources.get(n) != h for n, h in manifest_sources.items())):
            raise ValueError("graph bootstrap/config/manifest closure mismatch")
    else:
        if diagnostic is not None:
            raise ValueError("native G1 must have no diagnostic treatment")
        runtime_sources = contract.get("baseline_host_source_sha256")
        _sources(root, runtime_sources)
    raw = Path(contract["raw_root"])
    if not raw.is_absolute() or raw.exists():
        raise ValueError("unused absolute immutable raw root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(contract.get("absolute_stop_utc"))
    return {"configuration_valid": True, "device_run": False,
            "device_admission_performed": False,
            "controller_sha256": own_hash, "base_controller_sha256": BASE_SHA256,
            "host_controller_source_bindings": len(host),
            "runtime_source_bindings": len(runtime_sources),
            "graph_runtime": copy.deepcopy(graph)}


def _rewrite_launch(data, contract, checked):
    """Mutate the SAME argv list consumed immediately by unchanged base.command."""
    argv = data.get("argv")
    if (not isinstance(argv, list) or data.get("controller_sha256") != BASE_SHA256
            or "--enforce-eager" in argv or argv.count("--compilation-config") != 1):
        raise ValueError("unexpected real base launch profile")
    if (argv.count(contract["image"]) != 1
            or any(value == "-e" and i + 1 < len(argv)
                   and argv[i + 1].startswith("VLLM_LOGGING_LEVEL=")
                   for i, value in enumerate(argv))):
        raise ValueError("ambiguous image or pre-existing logging override")
    index = argv.index("--compilation-config") + 1
    previous = {"cudagraph_mode": "FULL_DECODE_ONLY",
                "cudagraph_capture_sizes": CAPTURE_SIZES}
    if json.loads(argv[index]) != previous:
        raise ValueError("unexpected pinned base compilation argv")
    graph = checked["graph_runtime"]
    compiled = dict(previous, mode=3)
    removed, added = [], []
    pythonpath = None
    if graph["candidate_enabled"]:
        old_manifest = "INDEPENDENT_COMPACT_MANIFEST=/probe/" + contract["cache_diagnostic"]["compact_manifest"]
        replacements = {
            "INDEPENDENT_COMPACT_HYPIC=1": "INDEPENDENT_GRAPH_HYPIC=1",
            old_manifest: "INDEPENDENT_GRAPH_MANIFEST=/probe/" + contract["cache_diagnostic"]["compact_manifest"],
            "INDEPENDENT_COMPACT_RAW=/scratch/diagnostics": "INDEPENDENT_GRAPH_RAW=/scratch/diagnostics"}
        seen = set()
        replacement_argv = []
        cursor = 0
        while cursor < len(argv):
            item = argv[cursor]
            if item == "-e":
                if cursor + 1 >= len(argv):
                    raise ValueError("incomplete environment argv")
                value = argv[cursor + 1]
                if value.startswith("INDEPENDENT_GRAPH_"):
                    raise ValueError("graph environment already installed")
                if value.startswith("INDEPENDENT_COMPACT_"):
                    if value not in replacements or value in seen:
                        raise ValueError("ambiguous old compact environment")
                    seen.add(value)
                    replacement_argv.extend(["-e", replacements[value]])
                    removed.append(value)
                    added.append(replacements[value])
                elif value.startswith("PYTHONPATH="):
                    prefix = "PYTHONPATH=/probe/compact_bootstrap:/probe:"
                    if pythonpath is not None or not value.startswith(prefix):
                        raise ValueError("exact compact bootstrap path required")
                    updated = "PYTHONPATH=/probe/" + BOOTSTRAP + ":/probe:" + value[len(prefix):]
                    pythonpath = {"from": value, "to": updated}
                    replacement_argv.extend(["-e", updated])
                else:
                    replacement_argv.extend(["-e", value])
                cursor += 2
            else:
                replacement_argv.append(item)
                cursor += 1
        if seen != set(replacements) or pythonpath is None:
            raise ValueError("complete unambiguous compact-to-graph bootstrap required")
        argv[:] = replacement_argv
    else:
        for i, value in enumerate(argv):
            if (value == "-e" and i + 1 < len(argv)
                    and (argv[i + 1].startswith("INDEPENDENT_")
                         or argv[i + 1].startswith("PYTHONPATH="))):
                raise ValueError("native G1 cannot carry probe environment")
            if ":/probe" in value:
                raise ValueError("native G1 cannot mount probe package")
    argv[argv.index("--compilation-config") + 1] = json.dumps(compiled, separators=(",", ":"))
    argv[argv.index(contract["image"]):argv.index(contract["image"])] = [
        "-e", "VLLM_LOGGING_LEVEL=DEBUG"]
    data["base_controller_sha256"] = BASE_SHA256
    data["host_controller_sha256"] = checked["controller_sha256"]
    data["graph_runtime"] = dict(copy.deepcopy(graph), compilation_config=compiled,
        bootstrap=BOOTSTRAP if graph["candidate_enabled"] else None,
        environment_removed=removed, environment_added=added,
        common_environment_added=["VLLM_LOGGING_LEVEL=DEBUG"],
        pythonpath_change=pythonpath)
    return data


def run_contract(contract, *, source_root=WORKSTREAM, base_module=base):
    checked = check_contract(contract, source_root=source_root, base_module=base_module)
    if not _OWNED_RUN.acquire(blocking=False):
        raise RuntimeError("one owned graph controller per process")
    original_write = base_module.write
    launches = 0
    raw = Path(contract["raw_root"])
    def owned_write(root, name, data):
        nonlocal launches
        if name == "launch.json":
            if Path(root) != raw or launches:
                raise ValueError("one exact raw launch record required")
            launches += 1
            _rewrite_launch(data, contract, checked)
        return original_write(root, name, data)
    base_module.write = owned_write
    try:
        result = base_module.run_contract(contract)
        if launches != 1:
            raise ValueError("real base launch record missing")
        return result
    finally:
        # Never overwrite a replacement installed by someone else.
        if base_module.write is owned_write:
            base_module.write = original_write
        _OWNED_RUN.release()


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args(argv)
    contract = json.loads(args.contract.read_text())
    if args.run:
        return run_contract(contract)
    print(json.dumps(check_contract(contract)))


if __name__ == "__main__":
    main()
