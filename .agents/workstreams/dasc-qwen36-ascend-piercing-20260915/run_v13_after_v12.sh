#!/usr/bin/env bash
set -euo pipefail

REPO=/opt/host/vnf/austinov/model-tuning-lab
WS=.agents/workstreams/dasc-qwen36-ascend-piercing-20260915
BASE=/cache/cch/dasc-qwen36-ascend-20260915
V12=$BASE/physical-cache-order-fix-v12
VERIFY=$REPO/$WS/verify_physical_v12.py
RUN_V13=$REPO/$WS/run_formal_ab_v13.sh
SUPERVISOR_LOCK=$BASE/controllers/dasc-qwen36-v13-after-v12.lock
VERDICT=$BASE/controllers/dasc-qwen36-v12-verification.json

mkdir -p "$BASE/controllers"
exec 7>"$SUPERVISOR_LOCK"
flock -n 7 || { echo "another v13-after-v12 supervisor owns the lock"; exit 75; }

while [[ ! -f "$V12/SUCCESS" ]]; do
  echo "$(date -u +%FT%T%:z) waiting for independently verifiable v12 success"
  sleep 60
done

python3 "$VERIFY" --root "$V12" --repo "$REPO" --output "$VERDICT"

while true; do
  set +e
  bash "$RUN_V13"
  rc=$?
  set -e
  case "$rc" in
    0)
      echo "$(date -u +%FT%T%:z) v13 completed successfully"
      exit 0
      ;;
    75)
      echo "$(date -u +%FT%T%:z) NPU4-7 handoff not ready; retrying"
      sleep 60
      ;;
    *)
      echo "$(date -u +%FT%T%:z) v13 failed closed with rc=$rc"
      exit "$rc"
      ;;
  esac
done
