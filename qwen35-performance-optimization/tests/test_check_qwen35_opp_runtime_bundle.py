#!/usr/bin/env python3
"""Device-free positive and fail-closed packaging-guard checks."""
import importlib.util
from pathlib import Path
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_qwen35_opp_runtime_bundle.py"
SPEC = importlib.util.spec_from_file_location("opp_runtime_bundle_guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def make_bundle(root: Path) -> Path:
    lib = root / "vendors/test/op_api/lib"
    lib.mkdir(parents=True)
    (lib / "libcust_opapi.so").write_bytes(b"packaging-fixture-not-real-ELF")
    return lib


def run_checks() -> None:
    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        make_bundle(root)
        result = GUARD.inspect_bundle(root)
        assert result["passed"]
        assert not result["full_validation_passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        lib = make_bundle(root)
        (lib / "libopapi_math.so").write_bytes(b"stub")
        assert not GUARD.inspect_bundle(root)["passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        lib = make_bundle(root)
        (lib / "libnnopbase.so.0").write_bytes(b"shadow")
        assert not GUARD.inspect_bundle(root)["passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        lib = make_bundle(root)
        data = b"simulated-known-build-stub"
        (lib / "librenamed.so").write_bytes(data)
        original = GUARD.KNOWN_BUILD_STUB_SHA256
        try:
            GUARD.KNOWN_BUILD_STUB_SHA256 = GUARD.hashlib.sha256(data).hexdigest()
            assert not GUARD.inspect_bundle(root)["passed"]
        finally:
            GUARD.KNOWN_BUILD_STUB_SHA256 = original

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        lib = make_bundle(root)
        (lib / "liboutside.so").symlink_to("/does-not-exist-outside-bundle")
        assert not GUARD.inspect_bundle(root)["passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        lib = make_bundle(root)
        (lib / "libcust_opapi.so").unlink()
        assert not GUARD.inspect_bundle(root)["passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        make_bundle(root)
        other = root / "other"
        other.mkdir()
        (other / "libcust_opapi.so").write_bytes(b"duplicate")
        assert not GUARD.inspect_bundle(root)["passed"]

    with tempfile.TemporaryDirectory() as value:
        root = Path(value)
        assert not GUARD.inspect_bundle(root / "missing")["passed"]


if __name__ == "__main__":
    run_checks()
    print("PASS: OPP runtime bundle guard")
