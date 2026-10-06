#!/usr/bin/env python3
"""Validate a runtime-monkeypatch package contract without importing it."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ALLOWED_STATES = {
    "draft",
    "pending",
    "accepted",
    "partial-component",
    "rejected",
    "failed",
    "inconclusive",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def fail(message: str) -> None:
    raise ValueError(message)


def get_string(data: dict, path: str) -> str:
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            fail(f"missing required field: {path}")
        value = value[part]
    if not isinstance(value, str) or not value.strip():
        fail(f"required field must be a non-empty string: {path}")
    return value


def validate(package: Path) -> None:
    manifest_path = package / "MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema") != "runtime-monkeypatch-delivery/v1":
        fail("unsupported manifest schema")
    if data.get("status") not in ALLOWED_STATES:
        fail("invalid status")

    for field in (
        "name",
        "source_contract.image_digest",
        "source_contract.framework_version",
        "source_contract.live_module",
        "source_contract.live_object",
        "source_contract.source_sha256",
        "treatment.switch",
        "treatment.enabled_value",
        "treatment.patch_file",
        "treatment.entrypoint",
        "treatment.patch_sha256",
        "activation.marker_prefix",
        "rollback.disable_command",
        "rollback.uninstall_command",
        "evidence.experiment_id",
        "evidence.branch",
        "evidence.commit",
    ):
        get_string(data, field)

    switch = get_string(data, "treatment.switch")
    if not ENV_RE.fullmatch(switch):
        fail("treatment.switch must be an uppercase environment variable")
    if data["treatment"].get("single_primary_variable") is not True:
        fail("single_primary_variable must be true")
    if data["activation"].get("disabled_control_required") is not True:
        fail("disabled_control_required must be true")
    roles = data["activation"].get("required_roles")
    if not isinstance(roles, list) or not roles or not all(
        isinstance(role, str) and role for role in roles
    ):
        fail("required_roles must be a non-empty string list")

    for field in ("source_contract.source_sha256", "treatment.patch_sha256"):
        if not SHA256_RE.fullmatch(get_string(data, field)):
            fail(f"{field} must be lowercase SHA256")

    patch_rel = Path(get_string(data, "treatment.patch_file"))
    if patch_rel.is_absolute() or ".." in patch_rel.parts:
        fail("patch_file must stay inside the package")
    patch_path = package / patch_rel
    actual = hashlib.sha256(patch_path.read_bytes()).hexdigest()
    expected = get_string(data, "treatment.patch_sha256")
    if actual != expected:
        fail(f"patch hash mismatch: expected {expected}, got {actual}")

    for required in ("sitecustomize.py", "run_with_patch.sh"):
        if not (package / required).is_file():
            fail(f"missing required file: {required}")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <package-dir>", file=sys.stderr)
        return 2
    try:
        validate(Path(sys.argv[1]).resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid runtime monkeypatch package: {exc}", file=sys.stderr)
        return 1
    print("runtime monkeypatch package contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
