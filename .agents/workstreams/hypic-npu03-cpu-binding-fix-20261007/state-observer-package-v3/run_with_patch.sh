#!/usr/bin/env bash
set -euo pipefail
package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -eq 0 ]; then
  echo "usage: $0 <service-command> [args...]" >&2
  exit 2
fi
export HYPIC_STATE_OBSERVER_ENABLE="${HYPIC_STATE_OBSERVER_ENABLE:-0}"
export PYTHONPATH="${package_dir}${PYTHONPATH:+:${PYTHONPATH}}"
python3 -B -c 'import sitecustomize'
exec "$@"
