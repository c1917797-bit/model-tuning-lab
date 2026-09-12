#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repo_root/scripts/build_qwen35_t21_public_acl_bridge.sh"

bash -n "$script"
grep -F -- '--network none' "$script" >/dev/null
grep -F 'device_mapping=none' "$script" >/dev/null
grep -F 'NPUBridge|NPUStorageImpl' "$script" >/dev/null
grep -F 'refusing to reuse output root' "$script" >/dev/null
echo "PASS: T21 bridge build runner contract"
