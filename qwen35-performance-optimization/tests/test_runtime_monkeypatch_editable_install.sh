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
grep -Fq 'VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=0' "$patch_root/load_patch.sh"
grep -Fq '8d2d403f17843ed2e40d2e768b61bc1faa55fa9fce9d1fcd58af810567aa89e1' "$patch_root/load_patch.sh"

echo 'PASS: t12 editable-install contract'
