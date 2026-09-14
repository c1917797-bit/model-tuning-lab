#!/usr/bin/env bash
set -euo pipefail

WORKTREE=/opt/host/vnf/austinov/worktrees/sliminfer-qwen36-ascend-piercing
OUTPUT_ROOT=${SLIMINFER_SHADOW_OUTPUT_ROOT:-/cache/cch/sliminfer-qwen36-ascend-tp4-20260914/selection-shadow-v1}
MODEL_PATH=/cache/efim/Qwen3.6-27B
MODEL_NAME=qwen36-sliminfer-shadow
IMAGE=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
PORT=${SLIMINFER_SHADOW_PORT:-8235}
PORT_WAIT_SECONDS=${SLIMINFER_SHADOW_PORT_WAIT_SECONDS:-120}
CPUSET=${SLIMINFER_SHADOW_CPUSET:-112-191}
HOST_NPU_FIRST=4
HOST_NPU_LAST=7
VISIBLE_DEVICES=0,1,2,3
TP_SIZE=4
MAX_MODEL_LEN=16384
MAX_BATCHED_TOKENS=16384
PROMPT_TOKENS=13000
EXPERIMENT_ID=sliminfer-shadow-qwen36-tp4-20260914-v1
DISABLED_CONTAINER=sliminfer_qwen36_shadow_disabled_npu4_7_v1
ENABLED_CONTAINER=sliminfer_qwen36_shadow_enabled_npu4_7_v1
CURRENT_CONTAINER=
CURRENT_ARM=
MODE=${1:-run}

if [[ "$MODE" != run && "$MODE" != --preflight-only ]] || [[ $# -gt 1 ]]; then
  printf 'usage: %s [--preflight-only]\n' "$0" >&2
  exit 2
fi

cd "$WORKTREE"

fail() {
  printf 'FAILED: %s\n' "$*" >&2
  return 1
}

container_state() {
  local state
  if state=$(docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null); then
    printf '%s\n' "$state"
  else
    printf 'absent\n'
  fi
}

lane_pids() {
  local device output
  for ((device = HOST_NPU_FIRST; device <= HOST_NPU_LAST; device++)); do
    output=$(npu-smi info -t proc-mem -i "$device")
    sed -n 's/.*Process id:\([0-9][0-9]*\).*/\1/p' <<<"$output"
  done | sort -nu
}

assert_lane_empty() {
  local pids
  pids=$(lane_pids)
  [[ -z "$pids" ]] || fail "NPU4-7 occupied by pid(s): ${pids//$'\n'/,}"
}

port_is_free() {
  python3 - "$PORT" <<'PY'
import socket
import sys

port = int(sys.argv[1])
with socket.socket() as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        raise SystemExit(1)
PY
}

wait_for_port_free() {
  local waited
  for ((waited = 0; waited <= PORT_WAIT_SECONDS; waited++)); do
    if port_is_free; then
      return 0
    fi
    if (( waited < PORT_WAIT_SECONDS )); then
      sleep 1
    fi
  done
  fail "port $PORT did not become reusable within ${PORT_WAIT_SECONDS}s"
}

verify_static_inputs() {
  [[ -s "$MODEL_PATH/config.json" ]] || fail "model config is missing"
  [[ -s "$MODEL_PATH/model.safetensors.index.json" ]] || fail "model index is missing"
  [[ $(git rev-parse --show-toplevel) == "$WORKTREE" ]] || fail "wrong worktree"
  [[ -z $(git status --porcelain) ]] || fail "worktree is not clean"
  [[ $(docker image inspect -f '{{.Id}}' "$IMAGE") == "$IMAGE" ]] ||
    fail "pinned image identity differs"
  [[ ! -e "$OUTPUT_ROOT" ]] || fail "output root already exists: $OUTPUT_ROOT"
  [[ $(container_state "$DISABLED_CONTAINER") == absent ]] ||
    fail "container already exists: $DISABLED_CONTAINER"
  [[ $(container_state "$ENABLED_CONTAINER") == absent ]] ||
    fail "container already exists: $ENABLED_CONTAINER"
  wait_for_port_free
  assert_lane_empty
}

assert_container_owns_lane() {
  local name=$1 container_pids device output pid observed=0
  container_pids=$(docker top "$name" -eo pid | sed -n '2,$p')
  for ((device = HOST_NPU_FIRST; device <= HOST_NPU_LAST; device++)); do
    output=$(npu-smi info -t proc-mem -i "$device")
    pid=$(sed -n 's/.*Process id:\([0-9][0-9]*\).*/\1/p' <<<"$output")
    [[ -n "$pid" ]] || fail "container has no process on NPU$device"
    grep -qx "$pid" <<<"$container_pids" ||
      fail "NPU$device pid $pid is not owned by $name"
    observed=$((observed + 1))
  done
  [[ $observed -eq 4 ]] || fail "container does not own all four devices"
}

create_container() {
  local arm=$1 name=$2 enabled=$3 serve_command
  mkdir -p "$OUTPUT_ROOT/$arm"
  serve_command="set -euo pipefail; cp -a /source-sliminfer /opt/sliminfer; "
  serve_command+="python3 -m pip install --no-build-isolation --no-deps -e /opt/sliminfer; "
  if [[ "$enabled" == 1 ]]; then
    serve_command+=": > /results/$arm/runtime.jsonl; "
  fi
  serve_command+="exec vllm serve $MODEL_PATH --served-model-name $MODEL_NAME "
  serve_command+="--host 127.0.0.1 --port $PORT --data-parallel-size 1 "
  serve_command+="--tensor-parallel-size $TP_SIZE --max-model-len $MAX_MODEL_LEN "
  serve_command+="--max-num-batched-tokens $MAX_BATCHED_TOKENS --max-num-seqs 4 "
  serve_command+="--gpu-memory-utilization 0.9 --no-enable-prefix-caching "
  serve_command+="--trust-remote-code --enforce-eager"

  docker create \
    --name "$name" \
    --label sliminfer.experiment="$EXPERIMENT_ID" \
    --label sliminfer.arm="$arm" \
    --network host \
    --shm-size 8g \
    --cpuset-cpus "$CPUSET" \
    --device /dev/davinci4:/dev/davinci0 \
    --device /dev/davinci5:/dev/davinci1 \
    --device /dev/davinci6:/dev/davinci2 \
    --device /dev/davinci7:/dev/davinci3 \
    --device /dev/davinci_manager:/dev/davinci_manager \
    --device /dev/devmm_svm:/dev/devmm_svm \
    --device /dev/hisi_hdc:/dev/hisi_hdc \
    -v /usr/local/dcmi:/usr/local/dcmi:ro \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
    -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
    -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool:ro \
    -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
    -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
    -v /cache/efim:/cache/efim:ro \
    -v "$WORKTREE:/source-sliminfer:ro" \
    -v "$OUTPUT_ROOT:/results" \
    -e ASCEND_RT_VISIBLE_DEVICES="$VISIBLE_DEVICES" \
    -e VLLM_PLUGINS=ascend,sliminfer_ascend \
    -e MST_SLIMINFER_ENABLE="$enabled" \
    -e MST_SLIMINFER_MODE=selection-shadow \
    -e MST_SLIMINFER_REQUIRE_RUNTIME_HOOKS=1 \
    -e MST_SLIMINFER_EVIDENCE_FILE="/results/$arm/runtime.jsonl" \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e OMP_NUM_THREADS=1 \
    -e TASK_QUEUE_ENABLE=1 \
    -e HCCL_OP_EXPANSION_MODE=AIV \
    -e HCCL_NPU_SOCKET_PORT_RANGE=26700-26800 \
    -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True \
    "$IMAGE" bash -lc "$serve_command" >/dev/null
  docker inspect "$name" >"$OUTPUT_ROOT/$arm/container.created.json"
}

wait_for_health() {
  local name=$1 attempt
  for attempt in $(seq 1 240); do
    if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
      assert_container_owns_lane "$name"
      return 0
    fi
    if [[ $(container_state "$name") != running ]]; then
      docker logs "$name" >"$OUTPUT_ROOT/current-failed.log" 2>&1 || true
      fail "$name exited before becoming healthy"
    fi
    sleep 5
  done
  fail "$name did not become healthy within 20 minutes"
}

start_arm() {
  local arm=$1 name=$2 enabled=$3
  assert_lane_empty
  wait_for_port_free
  create_container "$arm" "$name" "$enabled"
  CURRENT_CONTAINER=$name
  CURRENT_ARM=$arm
  docker start "$name" >/dev/null
  wait_for_health "$name"
  docker inspect "$name" >"$OUTPUT_ROOT/$arm/container.running.json"
  npu-smi info >"$OUTPUT_ROOT/$arm/npu.running.txt"
}

stop_arm() {
  local arm=$1 name=$2 label
  label=$(docker inspect -f '{{index .Config.Labels "sliminfer.experiment"}}' "$name")
  [[ "$label" == "$EXPERIMENT_ID" ]] || fail "refusing to stop unowned container $name"
  docker stop --time 60 "$name" >/dev/null
  docker inspect "$name" >"$OUTPUT_ROOT/$arm/container.exited.json"
  docker logs "$name" >"$OUTPUT_ROOT/$arm/service.log" 2>&1
  CURRENT_CONTAINER=
  CURRENT_ARM=
  assert_lane_empty
}

cleanup() {
  local status=$?
  if [[ -n "$CURRENT_CONTAINER" ]] && [[ $(container_state "$CURRENT_CONTAINER") != absent ]]; then
    local label
    label=$(docker inspect -f '{{index .Config.Labels "sliminfer.experiment"}}' \
      "$CURRENT_CONTAINER" 2>/dev/null || true)
    if [[ "$label" == "$EXPERIMENT_ID" ]]; then
      if [[ $(container_state "$CURRENT_CONTAINER") == running ]]; then
        docker stop --time 60 "$CURRENT_CONTAINER" >/dev/null || true
      fi
      mkdir -p "$OUTPUT_ROOT/$CURRENT_ARM"
      docker inspect "$CURRENT_CONTAINER" \
        >"$OUTPUT_ROOT/$CURRENT_ARM/container.failure.json" 2>/dev/null || true
      docker logs "$CURRENT_CONTAINER" \
        >"$OUTPUT_ROOT/$CURRENT_ARM/service.failure.log" 2>&1 || true
    fi
  fi
  exit "$status"
}

verify_static_inputs
if [[ "$MODE" == --preflight-only ]]; then
  printf 'SlimInfer TP4 shadow preflight passed; no state was changed.\n'
  exit 0
fi

trap cleanup EXIT
mkdir -p "$OUTPUT_ROOT"
git rev-parse HEAD >"$OUTPUT_ROOT/source-commit.txt"
git status --short --branch >"$OUTPUT_ROOT/source-status.txt"
docker image inspect "$IMAGE" >"$OUTPUT_ROOT/image.json"
npu-smi info >"$OUTPUT_ROOT/npu.before.txt"

start_arm disabled "$DISABLED_CONTAINER" 0
python3 tools/run_sliminfer_shadow_request.py \
  --endpoint "http://127.0.0.1:$PORT/v1/completions" \
  --model "$MODEL_NAME" \
  --prompt-tokens "$PROMPT_TOKENS" \
  --output "$OUTPUT_ROOT/disabled/request.json"
stop_arm disabled "$DISABLED_CONTAINER"

start_arm enabled "$ENABLED_CONTAINER" 1
python3 tools/run_sliminfer_shadow_request.py \
  --endpoint "http://127.0.0.1:$PORT/v1/completions" \
  --model "$MODEL_NAME" \
  --prompt-tokens "$PROMPT_TOKENS" \
  --output "$OUTPUT_ROOT/enabled/request.json"
stop_arm enabled "$ENABLED_CONTAINER"

python3 tools/summarize_sliminfer_shadow.py \
  "$OUTPUT_ROOT/enabled/runtime.jsonl" \
  --expected-ranks 0,1,2,3 \
  --min-request-tokens "$PROMPT_TOKENS" \
  --output "$OUTPUT_ROOT/enabled/audit.json"
python3 tools/compare_sliminfer_shadow_outputs.py \
  "$OUTPUT_ROOT/disabled/request.json" \
  "$OUTPUT_ROOT/enabled/request.json" \
  --output "$OUTPUT_ROOT/output-parity.json"
npu-smi info >"$OUTPUT_ROOT/npu.after.txt"
find "$OUTPUT_ROOT" -type f ! -name SHA256SUMS -print0 |
  sort -z | xargs -0 sha256sum >"$OUTPUT_ROOT/SHA256SUMS"
printf 'SlimInfer TP4 selection-shadow canary passed: %s\n' "$OUTPUT_ROOT"
