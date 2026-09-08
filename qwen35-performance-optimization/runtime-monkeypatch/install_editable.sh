#!/usr/bin/env bash
set -euo pipefail

patch_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# pip 26 uses PEP 517 for editable installs and otherwise creates an isolated
# build environment that may try to contact PyPI.  Reuse the setuptools already
# present in the pinned vLLM-Ascend image and prohibit index access.
PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install \
  --no-deps \
  --no-index \
  --no-build-isolation \
  -e "$patch_root"

installed_path="$(
  QWEN35_ASCEND_MONKEYPATCH=0 python3 -c \
    'import pathlib, sitecustomize; print(pathlib.Path(sitecustomize.__file__).resolve())'
)"
expected_path="$(realpath "$patch_root/sitecustomize.py")"
if [[ "$installed_path" != "$expected_path" ]]; then
  echo "editable install resolved to an unexpected patch: $installed_path" >&2
  exit 66
fi

echo "Qwen3.5 patch installed in editable mode from $patch_root" >&2
