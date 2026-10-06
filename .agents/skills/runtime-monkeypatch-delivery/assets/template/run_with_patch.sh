#!/usr/bin/env bash
set -euo pipefail

package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -eq 0 ]; then
  echo "usage: $0 <service-command> [args...]" >&2
  exit 2
fi

export MODEL_TUNING_RUNTIME_PATCH_ENABLE=1
export MODEL_TUNING_RUNTIME_PATCH_ENTRYPOINT="${MODEL_TUNING_RUNTIME_PATCH_ENTRYPOINT:-patch:activate}"
export PYTHONPATH="${package_dir}${PYTHONPATH:+:${PYTHONPATH}}"

# Python reports sitecustomize failures without necessarily failing startup.
# Import once explicitly so a broken or unfinished treatment fails closed before
# the long-lived service is started. Worker processes still load sitecustomize
# in their own interpreters and must emit their own activation evidence.
python3 -c 'import sitecustomize'
exec "$@"
