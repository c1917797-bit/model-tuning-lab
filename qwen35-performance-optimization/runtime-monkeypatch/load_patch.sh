#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "source this file before starting vLLM: source $0" >&2
  exit 64
fi

patch_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
patch_file="$patch_root/sitecustomize.py"
expected_sha=aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b
actual_sha="$(sha256sum "$patch_file" | awk '{print $1}')"

if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "Qwen3.5 patch SHA256 mismatch: $actual_sha" >&2
  return 65
fi

installed_path="$(
  QWEN35_ASCEND_MONKEYPATCH=0 python3 -c \
    'import pathlib, sitecustomize; print(pathlib.Path(sitecustomize.__file__).resolve())'
)"
if [[ "$installed_path" != "$(realpath "$patch_file")" ]]; then
  echo "editable patch is not installed from $patch_root: $installed_path" >&2
  return 66
fi

export QWEN35_ASCEND_MONKEYPATCH=1
export VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1

echo "Qwen3.5 t12 candidate patch loaded: $expected_sha" >&2
