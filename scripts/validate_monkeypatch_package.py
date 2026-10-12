#!/usr/bin/env python3
"""Validate a runtime-monkeypatch package's static, hash-bound identity.

This deliberately does not claim live import, activation, quality, or rollback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
STATUSES = {"draft", "accepted", "partial-component", "rejected", "failed",
            "inconclusive"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def mapping(value: object, label: str) -> dict:
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def nonplaceholder(value: object, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip()),
            f"{label} must be a nonempty string")
    text = value.strip()
    require(not text.startswith("replace-")
            and "replace.with." not in text
            and not text.startswith("example-"),
            f"{label} still has a template placeholder")
    return text


def digest(value: object, label: str, *, length: int = 64) -> str:
    pattern = HEX64 if length == 64 else HEX40
    require(isinstance(value, str) and pattern.fullmatch(value) is not None
            and set(value) != {"0"},
            f"{label} must be a nonzero lowercase {length}-hex digest")
    return value


def file_inside(root: Path, relative: object, label: str) -> Path:
    name = nonplaceholder(relative, label)
    candidate = Path(name)
    require(not candidate.is_absolute()
            and all(part not in ("", ".", "..") for part in candidate.parts)
            and "\\" not in name,
            f"{label} must be a safe relative path")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes package root") from exc
    require(resolved.is_file(), f"{label} does not exist: {name}")
    return resolved


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashed_file(root: Path, section: dict, path_key: str,
                      hash_key: str) -> tuple[str, str]:
    path = file_inside(root, section.get(path_key), path_key)
    expected = digest(section.get(hash_key), hash_key)
    actual = file_hash(path)
    require(actual == expected, f"{path_key} SHA256 mismatch")
    return str(path.relative_to(root)), actual


def native_plugin_identity(root: Path, manifest: dict, treatment: dict,
                           module: str, entrypoint: str) -> int:
    """Validate declaration and complete package Python inventory, never import."""
    require(treatment.get("entry_point_group") == "vllm.general_plugins",
            "entry_point_group must be vllm.general_plugins")
    name = nonplaceholder(treatment.get("entry_point_name"), "entry_point_name")
    require(IDENT.fullmatch(name) is not None, "entry_point_name invalid")
    try:
        import tomllib
    except ImportError as exc:
        raise ValueError("native-plugin validation requires Python 3.11; "
                         "use the configured host-test Python environment") from exc
    config = tomllib.loads((root / treatment["loader_file"]).read_text(encoding="utf-8"))
    project = mapping(config.get("project", {}), "project")
    groups = mapping(project.get("entry-points", {}), "project.entry-points")
    entries = mapping(groups.get("vllm.general_plugins", {}), "vllm.general_plugins")
    require(entries.get(name) == entrypoint, "native entrypoint declaration mismatch")
    package = root / module.split(".")[0]
    require(package.is_dir() and not package.is_symlink(),
            "native plugin root must be a nonsymlink package directory")
    require(not any(path.is_symlink() for path in package.rglob("*")),
            "native source symlink needs review")
    actual = {path.relative_to(root).as_posix()
              for path in package.rglob("*.py") if path.is_file()}
    files = manifest.get("source_files")
    require(isinstance(files, list) and bool(files), "native source_files missing")
    declared = set()
    for index, item in enumerate(files):
        item = mapping(item, f"source_files[{index}]")
        relative, _ = check_hashed_file(root, item, "path", "sha256")
        require(relative not in declared, "duplicate native source file")
        declared.add(relative)
    require(actual == declared, "native source file inventory mismatch")
    return len(declared)


def validate(package_dir: Path) -> dict:
    root = package_dir.resolve()
    require(root.is_dir(), "package directory does not exist")
    manifest_path = file_inside(root, "MANIFEST.json", "manifest")
    manifest = mapping(json.loads(manifest_path.read_text(encoding="utf-8")),
                       "MANIFEST.json")
    require(manifest.get("schema") == "runtime-monkeypatch-delivery/v1",
            "manifest schema mismatch")
    name = nonplaceholder(manifest.get("name"), "name")
    require(name != "runtime-monkeypatch-template",
            "template package has not been customized")
    require(manifest.get("status") in STATUSES, "terminal state invalid")

    source = mapping(manifest.get("source_contract"), "source_contract")
    image = nonplaceholder(source.get("image_digest"), "image_digest")
    require(image.startswith("sha256:")
            and HEX64.fullmatch(image[7:]) is not None
            and set(image[7:]) != {"0"},
            "image_digest must pin an image SHA256")
    nonplaceholder(source.get("framework_version"), "framework_version")
    nonplaceholder(source.get("cann_version"), "cann_version")
    module = nonplaceholder(source.get("live_module"), "live_module")
    require(all(IDENT.fullmatch(part) for part in module.split(".")),
            "live_module must be a Python module path")
    live_object = nonplaceholder(source.get("live_object"), "live_object")
    require(IDENT.fullmatch(live_object) is not None,
            "live_object must be a Python identifier")
    digest(source.get("source_sha256"), "source_sha256")

    treatment = mapping(manifest.get("treatment"), "treatment")
    loader_kind = treatment.get("loader_kind", "sitecustomize")
    require(loader_kind in {"sitecustomize", "vllm.general_plugins"},
            "unknown loader_kind")
    switch = nonplaceholder(treatment.get("switch"), "switch")
    require(ENV_NAME.fullmatch(switch) is not None,
            "switch must be an environment variable name")
    nonplaceholder(treatment.get("enabled_value"), "enabled_value")
    require(treatment.get("single_primary_variable") is True,
            "single_primary_variable must be true")
    patch_file, patch_sha = check_hashed_file(
        root, treatment, "patch_file", "patch_sha256")
    loader_file, loader_sha = check_hashed_file(
        root, treatment, "loader_file", "loader_sha256")
    launcher_file, launcher_sha = check_hashed_file(
        root, treatment, "launcher_file", "launcher_sha256")
    if loader_kind == "sitecustomize":
        require(loader_file == "sitecustomize.py",
                "loader_file must be sitecustomize.py for this package schema")
        require(launcher_file == "run_with_patch.sh",
                "launcher_file must be run_with_patch.sh for this package schema")
    else:
        require(loader_file == "pyproject.toml",
                "native loader_file must be pyproject.toml")
    entrypoint = nonplaceholder(treatment.get("entrypoint"), "entrypoint")
    parts = entrypoint.split(":")
    require(len(parts) == 2 and bool(parts[0]) and bool(parts[1])
            and all(IDENT.fullmatch(part) for part in parts[0].split("."))
            and IDENT.fullmatch(parts[1]) is not None,
            "entrypoint must be module:callable")
    module_path = parts[0].replace(".", "/")
    entrypoint_files = {module_path + ".py"}
    if loader_kind == "vllm.general_plugins":
        entrypoint_files.add(module_path + "/__init__.py")
    require(patch_file in entrypoint_files,
            "entrypoint module does not match patch_file")
    source_files_verified = 0
    if loader_kind == "vllm.general_plugins":
        source_files_verified = native_plugin_identity(
            root, manifest, treatment, parts[0], entrypoint)
    require(b"Implement the one declared treatment" not in
            (root / patch_file).read_bytes(),
            "template patch has not been implemented")

    activation = mapping(manifest.get("activation"), "activation")
    nonplaceholder(activation.get("marker_prefix"), "marker_prefix")
    roles = activation.get("required_roles")
    require(isinstance(roles, list) and bool(roles)
            and all(isinstance(role, str) and role.strip() for role in roles)
            and len(roles) == len(set(roles)),
            "required_roles must be a nonempty unique list")
    require(activation.get("disabled_control_required") is True,
            "disabled_control_required must be true")

    rollback = mapping(manifest.get("rollback"), "rollback")
    nonplaceholder(rollback.get("disable_command"), "disable_command")
    nonplaceholder(rollback.get("uninstall_command"), "uninstall_command")
    evidence = mapping(manifest.get("evidence"), "evidence")
    nonplaceholder(evidence.get("experiment_id"), "experiment_id")
    branch = nonplaceholder(evidence.get("branch"), "branch")
    require(branch.startswith("work/"), "evidence branch must be work/*")
    digest(evidence.get("commit"), "commit", length=40)

    libraries = manifest.get("native_libraries", [])
    require(isinstance(libraries, list), "native_libraries must be a list")
    for index, library in enumerate(libraries):
        item = mapping(library, f"native_libraries[{index}]")
        check_hashed_file(root, item, "path", "sha256")
        nonplaceholder(item.get("abi"), f"native_libraries[{index}].abi")

    return {
        "schema": "runtime-monkeypatch-package-static-check/v1",
        "static_identity_valid": True,
        "loader_kind": loader_kind,
        "source_files_verified": source_files_verified,
        "not_runtime_activation_or_delivery_acceptance": True,
        "name": name,
        "manifest_sha256": file_hash(manifest_path),
        "patch_sha256": patch_sha,
        "loader_sha256": loader_sha,
        "launcher_sha256": launcher_sha,
        "required_roles": roles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_dir", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.package_dir)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"static_identity_valid": False,
                          "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
