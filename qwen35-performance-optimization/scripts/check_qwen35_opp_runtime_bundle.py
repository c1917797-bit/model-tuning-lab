#!/usr/bin/env python3
"""Reject build stubs / shadowed CANN runtime libraries in a custom OPP bundle.

This is a packaging guard, not ELF/linkage, numerical, or performance validation.
Run ldd -r in the pinned image and the physical-device gates separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORBIDDEN_RUNTIME_NAMES = (
    "libopapi_math.so", "libopapi.so", "libnnopbase.so", "libascendcl.so",
)
KNOWN_BUILD_STUB_SHA256 = "dbcf3ec4a5dc360d520f74556d0c591fce0183ad7c29fee5dc95cd3db366e937"


def inspect_bundle(root: Path) -> dict:
    root = root.resolve()
    result = {"schema":"qwen35-opp-runtime-bundle-guard/v1", "root":str(root),
              "scope":"packaging-stub-shadow-guard-only", "errors":[],
              "custom_opapi_count":0, "full_validation_passed":False}
    errors = result["errors"]
    if not root.is_dir():
        errors.append("Bundle root does not exist or is not a directory")
        result["passed"] = False
        return result
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if any(path.name == name or path.name.startswith(name + ".")
               for name in FORBIDDEN_RUNTIME_NAMES):
            errors.append("CANN runtime must resolve from the pinned image, not the bundle: " + relative)
        if path.name == "libcust_opapi.so" and path.is_file():
            result["custom_opapi_count"] += 1
        if ".so" in path.name and (path.is_file() or path.is_symlink()):
            if path.is_symlink():
                try:
                    path.resolve(strict=True).relative_to(root)
                except (OSError, ValueError):
                    errors.append("Shared-library symlink escapes bundle or is dangling: " + relative)
                    continue
            try:
                h = hashlib.sha256()
                with path.open("rb") as f:
                    for block in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(block)
                if h.hexdigest() == KNOWN_BUILD_STUB_SHA256:
                    errors.append("Known build-only opapi_math stub is not deployable: " + relative)
            except OSError as exc:
                errors.append("Cannot inspect shared library " + relative + ": " + str(exc))
    if result["custom_opapi_count"] != 1:
        errors.append("Require exactly one libcust_opapi.so")
    result["passed"] = not errors
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opp-root", required=True, type=Path)
    args = parser.parse_args()
    result = inspect_bundle(args.opp_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
