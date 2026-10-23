"""Checked caller for the existing DeltaLog software owner; no new controller."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import types

BASE = Path("/opt/host/vnf/austinov")

def need(value, message):
    if not value:
        raise ValueError(message)

def checked_json(reference):
    need(type(reference) is dict and set(reference) == {"path", "bytes", "sha256"}, "complete Ref3")
    path = Path(reference["path"])
    need(path.is_absolute() and path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), "ordinary exact input file")
    raw = path.read_bytes()
    need(type(reference["bytes"]) is int and len(raw) == reference["bytes"] and hashlib.sha256(raw).hexdigest() == reference["sha256"], "exact input identity")
    return json.loads(raw)

def checked_source(reference):
    path = Path(reference["path"])
    need(path.is_absolute() and path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), "ordinary source")
    raw = path.read_bytes()
    need(len(raw) == reference["bytes"] and hashlib.sha256(raw).hexdigest() == reference["sha256"], "exact source identity")
    return raw

def plan(binding_ref, host_cpu, guest_cpu):
    binding = checked_json(binding_ref)
    need(binding["schema"] == "deltalog.current-three-tree-bound-controls/v1", "actual bound controls")
    early_ref = binding["early_source"]
    early = checked_json(early_ref)
    need(early["prepared_only"] is False and early["prepared_template"] == binding["early_template"], "bound early source, not a template")
    guard_ref = early["files"]["current_source_window.py"]
    guard = types.ModuleType("_actual_checked_early_guard")
    guard.__file__ = guard_ref["path"]
    exec(compile(checked_source(guard_ref), guard.__file__, "exec"), guard.__dict__)
    authority = guard.require(early, "early-cpu")
    need(early["current_source_authority_ref"] == binding["authority_ref"] and authority["MAIN_review_ref"] == binding["MAIN_review_ref"], "same independently reviewed current authority")
    model = checked_json(binding["model_template"])
    need(model["root"] == early["current_guard_contract"]["role_roots"]["model"], "same actual model role")
    output_root = Path(early["output_root"])
    need(str(output_root) == early["current_guard_contract"]["outputs"]["early"], "exact registered output policy")
    allowed = os.sched_getaffinity(0)
    need(type(host_cpu) is int and type(guest_cpu) is int and host_cpu != guest_cpu and {host_cpu, guest_cpu} <= allowed, "actual disjoint inherited CPU affinity")
    owner_ref = early["files"]["owner.py"]
    checked_source(owner_ref)
    leaf = output_root / "consumer"
    return {
        "binding": binding_ref, "early_source": early_ref,
        "model_template": binding["model_template"], "owner": owner_ref,
        "output_root": output_root, "output": leaf,
        "host_cpu": host_cpu, "guest_cpu": guest_cpu,
    }

def initialize(output_root, leaf, allowed_base=BASE):
    output_root, leaf, allowed_base = Path(output_root), Path(leaf), Path(allowed_base)
    need(allowed_base.is_absolute() and ".." not in output_root.parts and ".." not in leaf.parts, "no unresolved output traversal")
    need(output_root.is_absolute() and allowed_base in output_root.parents and leaf == output_root / "consumer", "bounded exact output parent and new leaf")
    need(not any(p.is_symlink() for p in (leaf, *leaf.parents)), "no output symlink components")
    need(not leaf.exists(), "no retry over a prior experiment leaf")
    need(not output_root.exists() or output_root.is_dir(), "output parent is a directory")
    missing = [str(p) for p in (output_root.parent, output_root) if not p.exists()]
    output_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    need(output_root.is_dir() and not leaf.exists() and not any(p.is_symlink() for p in (leaf, *leaf.parents)), "initialized lock parent only; experiment leaf remains fresh")
    return missing

def argv(value):
    return ["/usr/bin/python3", "-I", "-B", value["owner"]["path"],
        "--execute", "--source-ref", json.dumps(value["early_source"], separators=(",", ":")),
        "--model-template-ref", json.dumps(value["model_template"], separators=(",", ":")),
        "--host-cpu", str(value["host_cpu"]), "--guest-cpu", str(value["guest_cpu"]),
        "--output", str(value["output"])]

def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--binding-ref")
    parser.add_argument("--host-cpu", type=int)
    parser.add_argument("--guest-cpu", type=int)
    args = parser.parse_args()
    if not (args.check or args.execute):
        need(args.binding_ref is None and args.host_cpu is None and args.guest_cpu is None, "explicit mode for all operands")
        print('{"enabled":false,"container_started":false,"NPU":false}')
        return
    need(args.binding_ref is not None and args.host_cpu is not None and args.guest_cpu is not None, "complete explicit caller operands")
    value = plan(json.loads(args.binding_ref), args.host_cpu, args.guest_cpu)
    need(not value["output"].exists(), "fresh experiment leaf before any caller mutation")
    command = argv(value)
    if args.check:
        print(json.dumps({"actual_registered_argv": command, "lock_parent_present": value["output_root"].is_dir(), "container_started": False, "NPU": False}))
        return
    created = initialize(value["output_root"], value["output"])
    print(json.dumps({"initialized_lock_parents": created, "actual_registered_argv": command, "caller_only": True, "NPU": False}), flush=True)
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    os.execve(command[0], command, environment)

if __name__ == "__main__":
    main()
