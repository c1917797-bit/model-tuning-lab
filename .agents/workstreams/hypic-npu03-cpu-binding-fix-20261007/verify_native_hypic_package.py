#!/usr/bin/env python3
"""Read-only verification of the prospective native package; no device actions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = Path("/cache/cch/hypic_vllm_ascend-hotproof-20261008")
PACKAGE = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-delivery-package-20261012")
RAW = PACKAGE.parent / "native-delivery-package-evidence-20261012"
COMMIT = "4429e35177979c874bf053ab29789e4773f39b22"
MANIFEST_SHA = "dbac56e41b40214eff24ed305af77e18b50799a36b20e023f381a8dd3af05691"
RECEIPTS = {
    "image-source-assumption-failed.json": "1c48ebd7570684e67c64687e3feae38f29f345df91a5931285b66122277c8b0a",
    "image-source-spec.json": "00f43ef5e41d84c847b16ce7407b661c2f329a2732ea218b62ee2041189704cc",
    "assembly-static-check.json": "ae86147c4373d2ca0422a68b766e619c0065fe569fe1bbff5dff9378c9dc7646",
    "launcher-cpu.json": "ab57995e346d00d507479374d95d7d12f77cd94479425d872f7ca683d43e684f",
    "owned-release-check.json": "f7282ba492324174fa71ee4e1649b798a2eea36972738f933d03238808e6e2cb",
}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    records = {}
    for name, digest in RECEIPTS.items():
        p = RAW / name
        require(sha(p) == digest, "raw hash drift: " + name)
        record = json.loads(p.read_text())
        require(record["state"] == "completed" and not record["timedOut"]
                and not record["cancelled"], "nonterminal record")
        require(record["exitCode"] == (1 if "assumption-failed" in name else 0),
                "unexpected operation result")
        records[name] = record
    require("FileNotFoundError" in records["image-source-assumption-failed.json"]["stderr"],
            "original packaging-path failure missing")
    resolved = json.loads(records["image-source-spec.json"]["stdout"])
    require(resolved["sha256"] == "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
            and resolved["live_import_proven"] is False
            and resolved["object"] == "NPUModelRunner" and resolved["device_nodes"] == [],
            "image source scope mismatch")
    for name in ["image-source-spec.json", "launcher-cpu.json"]:
        args = records[name]["args"]
        require(records[name]["command"] == "docker" and args[0] == "run"
                and "--read-only" in args and "--rm" in args
                and args[args.index("--network") + 1] == "none"
                and not any(a == "--privileged" or a.startswith("--device") for a in args),
                "CPU isolation command mismatch")
    require(sha(PACKAGE / "MANIFEST.json") == MANIFEST_SHA, "manifest drift")
    assets = HERE / "hypic-native-delivery"
    for name in ["MANIFEST.json", "run_with_native_plugin.sh"]:
        require((PACKAGE / name).read_bytes() == (assets / name).read_bytes(),
                "tracked asset differs from tested bundle: " + name)
    spec = importlib.util.spec_from_file_location(
        "native_static_validator", REPO / "scripts/validate_monkeypatch_package.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    result = validator.validate(PACKAGE)
    require(result["source_files_verified"] == 32
            and result["not_runtime_activation_or_delivery_acceptance"] is True,
            "static validation boundary mismatch")
    listing = subprocess.check_output(
        ["git", "-C", str(SOURCE), "ls-tree", "-rz", COMMIT])
    archive_files = set()
    for row in listing.split(b"\0"):
        if not row:
            continue
        meta, path_bytes = row.split(b"\t", 1)
        mode, kind, oid = meta.split()
        name = path_bytes.decode()
        require(kind == b"blob" and mode in [b"100644", b"100755"],
                "nonregular archive entry needs review")
        p = PACKAGE / name
        require(p.is_file() and not p.is_symlink(), "archive entry missing")
        b = p.read_bytes()
        actual = hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()
        require(actual == oid.decode(), "HYPIC source archive changed: " + name)
        archive_files.add(name)
    actual_files = {p.relative_to(PACKAGE).as_posix()
                    for p in PACKAGE.rglob("*") if p.is_file()}
    require(actual_files == archive_files | {"MANIFEST.json", "run_with_native_plugin.sh"},
            "unexpected extra/missing bundle files")
    manifest = json.loads((PACKAGE / "MANIFEST.json").read_text())
    require(manifest["status"] == "draft" and manifest["evidence"]["commit"] == COMMIT
            and manifest["evidence"]["package_promotion_ready"] is False
            and manifest["source_contract"]["live_import_proven"] is False
            and manifest["rollback"]["device_executed"] is False,
            "draft was promoted without live evidence")
    previous = json.loads(records["assembly-static-check.json"]["stdout"])
    require(previous == result, "independent static replay differs")
    tested = json.loads(records["launcher-cpu.json"]["stdout"])
    require(tested["manifest_sha256"] == MANIFEST_SHA
            and tested["controls"] == [{"switch":None,"forwarded":"0"},
                                      {"switch":"0","forwarded":"0"},
                                      {"switch":"1","forwarded":"1"}]
            and tested["invalid_switch_exit"] == 78 and tested["no_command_exit"] == 64
            and tested["source_drift_rejected_before_dispatch"] is True
            and tested["uninstalled_package_rejected_before_dispatch"] is True,
            "launcher controls drift")
    require(tested["enabled_value_only_forwarded_to_harmless_command"] is True
            and all(tested[k] is False for k in
                    ["enabled_hook_tested", "real_request_tested", "npu_rollback_tested"])
            and tested["device_nodes"] == [], "CPU result overclaimed")
    require(sha(HERE / "probe_native_hypic_launcher.py") ==
            "182936f65ba19ff4432d0d809da9a39a461ddee67a26bac8ab9fba0fa9c54ddf",
            "executed launcher probe drift")
    require(records["owned-release-check.json"]["stdout"].strip() ==
            "182936f65ba19ff4432d0d809da9a39a461ddee67a26bac8ab9fba0fa9c54ddf  "
            ".agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/probe_native_hypic_launcher.py",
            "source clean/owned container absence receipt drift")
    print(json.dumps({"static_native_package_valid":True,
                      "unchanged_git_archive_files":len(archive_files),
                      "python_source_files":32,"launcher_cpu_checks":"PASS",
                      "package_promotion_ready":False,"npu_delivery_proven":False},
                     sort_keys=True))

if __name__ == "__main__":
    main()
