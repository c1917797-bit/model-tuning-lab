#!/usr/bin/env bash
set -euo pipefail
package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
runtime_dir=$(dirname -- "$package_dir")
if [ "$#" -eq 0 ]; then
  echo "usage: $0 <service-command> [args...]" >&2
  exit 2
fi
export INDEPENDENT_COMPACT_HYPIC="${INDEPENDENT_COMPACT_HYPIC:-0}"
export INDEPENDENT_COMPACT_MANIFEST="${INDEPENDENT_COMPACT_MANIFEST:-${runtime_dir}/LIFECYCLE_COMPACT_MANIFEST_R16.json}"
export PYTHONPATH="${package_dir}:${runtime_dir}${PYTHONPATH:+:${PYTHONPATH}}"
python3 -c 'import sitecustomize'
exec "$@"
