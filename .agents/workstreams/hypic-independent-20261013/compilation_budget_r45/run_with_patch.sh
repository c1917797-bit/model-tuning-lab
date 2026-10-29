#!/bin/sh
set -eu
pkg=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
base=$(dirname -- "$pkg")
export INDEPENDENT_COMPILATION_BUDGET="${INDEPENDENT_COMPILATION_BUDGET:-0}"
export PYTHONPATH="$pkg:$base${PYTHONPATH:+:$PYTHONPATH}"
exec "$@"
