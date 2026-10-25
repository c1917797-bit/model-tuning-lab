#!/bin/sh
set -eu
case "${INDEPENDENT_EVIDENCE_IO_BUDGET:-0}" in 0) ;; *) exit 78 ;; esac
case "${INDEPENDENT_EVIDENCE_STEP_DURABILITY:-0}" in 0|1) ;; *) exit 78 ;; esac
case "${INDEPENDENT_PREFIX_TERMINAL_ONLY:-0}" in 0) ;; *) exit 78 ;; esac
if [ "${INDEPENDENT_GRAPH_HYPIC:-0}" = "1" ]; then
  package_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  package_root=$(dirname -- "$package_dir")
  export PYTHONPATH="$package_dir:$package_root${PYTHONPATH:+:$PYTHONPATH}"
fi
exec "$@"
