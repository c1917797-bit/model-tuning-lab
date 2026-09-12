#!/usr/bin/env python3
"""Build the isolated DRRQR PyTorch bridge in the dedicated Ascend container."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time

from build_drrqr_packed_native import (
    CONTAINER,
    CONTAINER_RESULTS_ROOT,
    HOST_RESULTS_ROOT,
    REFERENCE_COMMIT,
    git,
    result_path,
    sha256,
)


ADAPTER_FILES = (
    "op_api_common.h",
    "NPUBridge.h",
    "NPUBridge.cpp",
    "NPUStorageImpl.h",
    "NPUStorageImpl.cpp",
)


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--opapi-library", required=True, type=Path)
    parser.add_argument(
        "--reference-root",
        type=Path,
        default=Path("/cache/austinov/src/vllm-ascend"),
    )
    parser.add_argument("--container", default=CONTAINER)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 32:
        parser.error("--jobs must be in [1, 32]")

    output = args.output_dir.resolve()
    if output.exists():
        parser.error("output directory must not exist")
    opapi = args.opapi_library.resolve()
    if not opapi.is_file():
        parser.error("op-api library does not exist")
    container_output = result_path(output)
    container_opapi = result_path(opapi)
    reference = args.reference_root.resolve()
    if git(reference, "rev-parse", "HEAD") != REFERENCE_COMMIT:
        raise RuntimeError("reference commit changed; re-audit before build")
    if git(reference, "status", "--short"):
        raise RuntimeError("reference repository is dirty")

    project = Path(__file__).resolve().parents[1]
    bridge = (
        project / "native" / "drrqr_packed_recurrent_v1"
        / "torch_bridge.cpp"
    )
    output.mkdir(parents=True)
    adapter_out = output / "aclnn_torch_adapter"
    adapter_out.mkdir()
    adapter_source = reference / "csrc" / "aclnn_torch_adapter"
    adapter_hashes = {}
    for name in ADAPTER_FILES:
        source = adapter_source / name
        shutil.copy2(source, adapter_out / name)
        adapter_hashes[name] = sha256(source)
    shutil.copy2(bridge, output / bridge.name)

    build_script = output / "compile_bridge.py"
    build_script.write_text(
        """from pathlib import Path
import json
import torch
import torch_npu
from torch.utils.cpp_extension import load

root = Path(__file__).resolve().parent
module = load(
    name="drrqr_packed_recurrent_v1_bridge",
    sources=[
        str(root / "torch_bridge.cpp"),
        str(root / "aclnn_torch_adapter/NPUBridge.cpp"),
        str(root / "aclnn_torch_adapter/NPUStorageImpl.cpp"),
    ],
    extra_include_paths=[
        str(root),
        "/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/include",
        "/usr/local/Ascend/cann-9.1.0/include",
    ],
    extra_cflags=["-O2", "-std=c++17"],
    extra_ldflags=[
        "-L/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib",
        "-ltorch_npu",
        "-L/usr/local/Ascend/cann-9.1.0/lib64",
        "-lascendcl",
        "-lopapi",
        "-ldl",
        "-Wl,-rpath,/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib",
        "-Wl,-rpath,/usr/local/Ascend/cann-9.1.0/lib64",
    ],
    build_directory=str(root / "build"),
    verbose=True,
)
module.configure_exact_opapi(__OPAPI__)
receipt = {
    "module_file": str(Path(module.__file__).resolve()),
    "configured_opapi_path": module.configured_opapi_path(),
    "schema": str(torch.ops.drrqr_ascend.packed_recurrent_v1.default._schema),
}
(root / "bridge-runtime-smoke.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\\n"
)
print(json.dumps(receipt, sort_keys=True))
""".replace("__OPAPI__", repr(str(container_opapi)))
    )
    (output / "build").mkdir()

    manifest = {
        "schema": "drrqr-torch-bridge-build/v1",
        "status": "building",
        "created_unix_ns": time.time_ns(),
        "reference_commit": REFERENCE_COMMIT,
        "adapter_source_sha256": adapter_hashes,
        "bridge_source_sha256": sha256(bridge),
        "opapi_library": str(opapi),
        "opapi_sha256": sha256(opapi),
        "plugin_git_commit": git(project, "rev-parse", "HEAD"),
        "plugin_git_status": git(project, "status", "--short"),
        "limits": (
            "Build/load/schema evidence only; not NPU numerical, graph, "
            "endpoint performance, accuracy, or portability evidence."
        ),
    }
    manifest_path = output / "bridge-build-manifest.json"
    save(manifest_path, manifest)
    command = [
        "docker", "exec", "-e", f"MAX_JOBS={args.jobs}",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-w", str(container_output), args.container,
        "/usr/local/python3.12.13/bin/python3", "compile_bridge.py",
    ]
    manifest["command"] = command
    with (output / "bridge-build.log").open("w") as log:
        completed = subprocess.run(
            command, stdout=log, stderr=subprocess.STDOUT, text=True
        )
    manifest["returncode"] = completed.returncode
    manifest["completed_unix_ns"] = time.time_ns()
    artifacts = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != manifest_path:
            artifacts.append({
                "path": str(path.relative_to(output)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest["artifacts"] = artifacts
    manifest["status"] = "passed" if completed.returncode == 0 else "failed"
    save(manifest_path, manifest)
    if completed.returncode:
        raise SystemExit(completed.returncode)
    print(json.dumps({
        "status": "passed",
        "manifest": str(manifest_path),
        "artifact_count": len(artifacts),
    }))


if __name__ == "__main__":
    main()
