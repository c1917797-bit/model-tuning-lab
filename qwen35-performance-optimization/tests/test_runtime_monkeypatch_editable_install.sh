#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
patch_root="$root/qwen35-performance-optimization/runtime-monkeypatch"

python3 -m py_compile "$patch_root/setup.py"
bash -n "$patch_root/install_editable.sh"
bash -n "$patch_root/load_patch.sh"
bash -n "$patch_root/run_with_patch.sh"
grep -Fq 'py_modules=["sitecustomize"]' "$patch_root/setup.py"
grep -Fq -- '--no-index' "$patch_root/install_editable.sh"
grep -Fq -- '--no-build-isolation' "$patch_root/install_editable.sh"
grep -Fq 'VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1' "$patch_root/load_patch.sh"
! grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_' "$patch_root/load_patch.sh"
grep -Fq 'aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b' "$patch_root/load_patch.sh"

echo 'PASS: t12 editable-install contract'
