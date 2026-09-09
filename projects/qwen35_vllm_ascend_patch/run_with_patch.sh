#!/usr/bin/env bash
set -euo pipefail

patch_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$patch_root/load_patch.sh"

if [[ "$#" -eq 0 ]]; then
  echo "usage: $0 vllm serve <model-path> [arguments...]" >&2
  exit 64
fi

exec "$@"
