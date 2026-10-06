#!/usr/bin/env bash
set -euo pipefail

WORKTREE=${HYPIC_WORKTREE:-/cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend}
RECORDS=$WORKTREE/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend
OUTPUT_ROOT=${HYPIC_OUTPUT_ROOT:-/cache/cch/hypic-qwen36-historical-reproduction-20260905}
MODEL_PATH=/cache/efim/Qwen3.6-27B
MODEL_NAME=${HYPIC_MODEL_NAME:-qwen36-historical-ruler}
SOURCE_HYPIC=/cache/cch/hypic_vllm_ascend-v0.8.5
IMAGE=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
PORT=${HYPIC_PORT:-8223}
CPUSET=${HYPIC_CPUSET:-112-191}
BASELINE_CONTAINER=${HYPIC_BASELINE_CONTAINER:-qwen36_hypic_nocache_baseline_npu0_3}
TREATMENT_CONTAINER=${HYPIC_TREATMENT_CONTAINER:-qwen36_hypic_only_npu0_3}
EXPERIMENT_ID=${HYPIC_EXPERIMENT_ID:-hypic-qwen36-historical-ruler-20260905}
HOST_NPU_FIRST=${HYPIC_HOST_NPU_FIRST:-0}
HOST_NPU_LAST=${HYPIC_HOST_NPU_LAST:-3}
VISIBLE_DEVICES=${HYPIC_VISIBLE_DEVICES:-0,1,2,3}
CONTAINER_DEVICE_FIRST=${HYPIC_CONTAINER_DEVICE_FIRST:-0}
TP_SIZE=${HYPIC_TP_SIZE:-4}
HCCL_PORT_RANGE=${HYPIC_HCCL_PORT_RANGE:-26400-26500}
MAX_NUM_BATCHED_TOKENS=${HYPIC_MAX_NUM_BATCHED_TOKENS:-40960}
QUALITY_MAX_OUT_LEN=${HYPIC_QUALITY_MAX_OUT_LEN:-1024}
MEMORY_LIMIT=${HYPIC_MEMORY_LIMIT:-}
REFERENCE_SHA256=${HYPIC_REFERENCE_SHA256:-204b01d76eff8a0fd69a4a048de44da8385c6bfdc250c1efb8af542b63fb438c}
OWNED_LANE=NPU${HOST_NPU_FIRST}-${HOST_NPU_LAST}
BENCHMARK=$SOURCE_HYPIC/tools/benchmark_shared_prefix.py
QUALITY=$RECORDS/hypic_quality_eval.py
ANALYZER=$RECORDS/summarize_hypic_historical_reproduction.py
CANARY=$RECORDS/hypic_semantic_canary.py
E2E_RECORDS=$WORKTREE/.agents/workstreams/hypic-qwen36-e2e-2048-20261006
E2E_GATES=0
if [[ -v HYPIC_E2E_GATES ]]; then
  E2E_GATES=$HYPIC_E2E_GATES
fi
REFERENCE=$RECORDS/hypic-previous-practice-reference.json
STATUS_FILE=$OUTPUT_ROOT/controller-status.json
CURRENT_CONTAINER=
SELF_TEST=0

if [[ ${1:-} == --self-test ]]; then
  SELF_TEST=1
fi

cd "$WORKTREE"

verify_static_inputs() {
  [[ $(git -c safe.directory="$SOURCE_HYPIC" -C "$SOURCE_HYPIC" rev-parse HEAD) == 3ad0967589304cd8fc4e7cff02f48ecc6125c89f ]]
  git -c safe.directory="$SOURCE_HYPIC" -C "$SOURCE_HYPIC" diff --quiet -- hypic_vllm_ascend
  printf '%s  %s\n' cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822 "$BENCHMARK" | sha256sum -c -
  printf '%s  %s\n' 9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0 "$QUALITY" | sha256sum -c -
  [[ $(sha256sum "$REFERENCE" | awk '{print $1}') == "$REFERENCE_SHA256" ]]
  [[ -s "$MODEL_PATH/config.json" ]]
  [[ -s "$MODEL_PATH/model.safetensors.index.json" ]]
  [[ $(find "$MODEL_PATH" -maxdepth 1 -type f -name 'model-*.safetensors' -size +0c | wc -l) -eq 15 ]]
  [[ $(sha256sum /cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json | awk '{print $1}') == cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a ]]
  [[ $(sha256sum /cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl | awk '{print $1}') == 3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14 ]]
  (( MAX_NUM_BATCHED_TOKENS >= 16392 )) || { echo "max-num-batched-tokens must be >= 16392 for 16384-token suffix plus seam-sink=8" >&2; return 1; }
  docker image inspect "$IMAGE" >/dev/null
  python3 -m py_compile "$ANALYZER" "$QUALITY" "$BENCHMARK"
  if [[ "$E2E_GATES" == 1 ]]; then
    python3 -m py_compile "$CANARY" \
      "$E2E_RECORDS/baseline_contract.py" \
      "$E2E_RECORDS/assess_hypic_e2e_gates.py"
  fi
}

owned_npu_pids() {
  npu-smi info | awk -v first="$HOST_NPU_FIRST" -v last="$HOST_NPU_LAST" '
    /^\|[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]+\|[[:space:]]+[0-9]+[[:space:]]+\|/ {
      if ($2 >= first && $2 <= last) print $5
    }
  ' | sort -nu
}

assert_owned_lane_empty() {
  local observed
  observed=$(owned_npu_pids)
  if [[ -n "$observed" ]]; then
    printf '%s unexpectedly occupied by pid(s): %s\n' "$OWNED_LANE" "$observed" >&2
    return 1
  fi
}

wait_for_owned_lane_empty() {
  until assert_owned_lane_empty; do
    write_status "waiting-for-resource" "$OWNED_LANE occupied; no workload state changed" || true
    printf '%s waiting for host %s; devices outside this lane are not modified\n' "$(date -Is)" "$OWNED_LANE"
    sleep 60
  done
}

container_state() {
  local value
  value=$(docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null || true)
  if [[ -n "$value" ]]; then
    printf '%s\n' "$value"
  else
    printf 'absent\n'
  fi
}

verify_container() {
  local name=$1 expected_state=$2 expected_hypic=$3
  python3 - "$name" "$expected_state" "$expected_hypic" "$IMAGE" "$CPUSET" "$HOST_NPU_FIRST" "$HOST_NPU_LAST" "$TP_SIZE" "$MAX_NUM_BATCHED_TOKENS" "$VISIBLE_DEVICES" <<'PY'
import json
import re
import subprocess
import sys

name, expected_state, expected_hypic, image, cpuset, first, last, tp_size, max_num_batched_tokens, visible_devices = sys.argv[1:]
first, last, tp_size, max_num_batched_tokens = int(first), int(last), int(tp_size), int(max_num_batched_tokens)
item = json.loads(subprocess.run(
    ["docker", "inspect", name], check=True, text=True, capture_output=True
).stdout)[0]
if item["State"]["Status"] != expected_state:
    raise SystemExit(
        f"{name}: state={item['State']['Status']!r}, expected {expected_state!r}"
    )
if item["Image"] != image:
    raise SystemExit(f"{name}: image={item['Image']!r}, expected {image!r}")
if item["HostConfig"]["CpusetCpus"] != cpuset:
    raise SystemExit(f"{name}: invalid CPU set")
devices = [
    entry["PathOnHost"]
    for entry in item["HostConfig"]["Devices"]
    if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
]
if devices != [f"/dev/davinci{i}" for i in range(first, last + 1)]:
    raise SystemExit(f"{name}: invalid host devices {devices!r}")
env = dict(entry.split("=", 1) for entry in item["Config"]["Env"] if "=" in entry)
if env.get("ASCEND_RT_VISIBLE_DEVICES") != visible_devices:
    raise SystemExit(
        f"{name}: invalid container-visible devices "
        f"{env.get('ASCEND_RT_VISIBLE_DEVICES')!r}, expected {visible_devices!r}"
    )
if env.get("VLLM_ASCEND_HYPIC_ENABLE") != expected_hypic:
    raise SystemExit(f"{name}: invalid HYPIC switch")
if env.get("VLLM_ASCEND_HYPIC_ENABLE_PREFIX_CACHE_COEXISTENCE") != "0":
    raise SystemExit(f"{name}: coexistence must be disabled")
if env.get("VLLM_ASCEND_HYPIC_REQUIRE_POSITION_DEPENDENT_PREFIX_CACHE") != "0":
    raise SystemExit(f"{name}: position-dependent prefix cache must not be required")
command = " ".join(item["Config"].get("Cmd") or [])
required = [
    "/cache/efim/Qwen3.6-27B",
    f"--tensor-parallel-size {tp_size}",
    "--max-model-len 40960",
    f"--max-num-batched-tokens {max_num_batched_tokens}",
    "--max-num-seqs 16",
    "--no-enable-prefix-caching",
]
missing = [value for value in required if value not in command]
if missing:
    raise SystemExit(f"{name}: missing command invariants {missing!r}")
print(json.dumps({
    "container": name,
    "id": item["Id"],
    "state": item["State"]["Status"],
    "image": item["Image"],
    "cpuset": item["HostConfig"]["CpusetCpus"],
    "host_devices": devices,
    "hypic_enable": expected_hypic,
}, sort_keys=True))
PY
}

assert_owned_lane_owned_by() {
  local name=$1
  python3 - "$name" "$HOST_NPU_FIRST" "$HOST_NPU_LAST" <<'PY'
import re
import subprocess
import sys

name, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
output = subprocess.run(
    ["npu-smi", "info"], check=True, text=True, capture_output=True
).stdout
marker = "| NPU     Chip              | Process id"
if marker not in output:
    raise SystemExit("npu-smi process table marker not found")
observed = {}
for line in output.split(marker, 1)[1].splitlines():
    match = re.match(r"^\|\s*([0-7])\s+\d+\s+\|\s+(\d+)\s+\|", line)
    if match:
        device, pid = map(int, match.groups())
        if first <= device <= last:
            observed.setdefault(device, set()).add(pid)
expected_devices = set(range(first, last + 1))
if set(observed) != expected_devices:
    raise SystemExit(
        f"{name}: expected ownership on NPU{first}-{last}, got {observed!r}"
    )
container_pids = {
    int(line.strip())
    for line in subprocess.run(
        ["docker", "top", name, "-eo", "pid"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()[1:]
    if line.strip().isdigit()
}
foreign = set().union(*observed.values()) - container_pids
if foreign:
    raise SystemExit(
        f"{name}: foreign NPU{first}-{last} pids {sorted(foreign)!r}"
    )
print(f"NPU{first}-{last} ownership verified for {name}")
PY
}

write_status() {
  local phase=$1 detail=$2
  python3 - "$STATUS_FILE" "$phase" "$detail" "$$" <<'PY'
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "schema": "hypic-historical-controller-status/v1",
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "controller_pid": int(sys.argv[4]),
    "phase": sys.argv[2],
    "detail": sys.argv[3],
}
temporary = path.with_suffix(".tmp")
temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
os.replace(temporary, path)
PY
}

create_container() {
  local arm=$1 name=$2 hypic_enable=$3
  local state
  state=$(container_state "$name")
  if [[ "$state" != absent ]]; then
    verify_container "$name" "$state" "$hypic_enable"
    return
  fi

  local serve_command
  serve_command="set -euo pipefail; mkdir -p /results/$arm; : > /results/$arm/hypic-evidence.jsonl; cp -a /source-hypic /opt/hypic; python3 -m pip install --no-deps -e /opt/hypic; exec vllm serve $MODEL_PATH --served-model-name $MODEL_NAME --host 127.0.0.1 --port $PORT --data-parallel-size 1 --tensor-parallel-size $TP_SIZE --max-model-len 40960 --max-num-batched-tokens $MAX_NUM_BATCHED_TOKENS --max-num-seqs 16 --gpu-memory-utilization 0.9 --no-enable-prefix-caching --compilation-config '{\"cudagraph_capture_sizes\":[1,4,8,12,16,24,32,48,56,64,72,84,96,108,112,128,160,172,196,200,212,232,272,288,312,328,344,360,384,400,416,432,448,480,512],\"cudagraph_mode\":\"FULL_DECODE_ONLY\"}' --trust-remote-code --async-scheduling"

  local device_args=()
  local device
  local container_device=$CONTAINER_DEVICE_FIRST
  for ((device = HOST_NPU_FIRST; device <= HOST_NPU_LAST; device++)); do
    device_args+=(--device "/dev/davinci$device:/dev/davinci$container_device")
    container_device=$((container_device + 1))
  done

  local args=(
    --name "$name"
    --label hypic.experiment="$EXPERIMENT_ID"
    --label hypic.arm="$arm"
    --network host
    --shm-size 800g
    --cpuset-cpus "$CPUSET"
    "${device_args[@]}"
    --device /dev/davinci_manager:/dev/davinci_manager
    --device /dev/devmm_svm:/dev/devmm_svm
    --device /dev/hisi_hdc:/dev/hisi_hdc
    -v /usr/local/dcmi:/usr/local/dcmi
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi
    -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info
    -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool
    -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64
    -v /etc/ascend_install.info:/etc/ascend_install.info
    -v /cache/efim:/cache/efim:ro
    -v "$SOURCE_HYPIC:/source-hypic:ro"
    -v "$OUTPUT_ROOT:/results"
    -e ASCEND_RT_VISIBLE_DEVICES="$VISIBLE_DEVICES"
    -e HCCL_OP_EXPANSION_MODE=AIV
    -e HCCL_NPU_SOCKET_PORT_RANGE="$HCCL_PORT_RANGE"
    -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
    -e TASK_QUEUE_ENABLE=1
    -e VLLM_ASCEND_ENABLE_FLASHCOMM=1
    -e OMP_NUM_THREADS=1
    -e VLLM_ASCEND_HYPIC_ENABLE="$hypic_enable"
    -e VLLM_ASCEND_HYPIC_EVIDENCE_FILE="/results/$arm/hypic-evidence.jsonl"
    -e VLLM_ASCEND_HYPIC_MODE=transition_rope_recompute
    -e 'VLLM_ASCEND_HYPIC_SEPARATOR=<<PIC_SEP>>'
    -e VLLM_ASCEND_HYPIC_SEAM_SINK=8
    -e VLLM_ASCEND_HYPIC_MIN_SEGMENT_TOKENS=1
    -e VLLM_ASCEND_HYPIC_STRICT=1
    -e VLLM_ASCEND_HYPIC_REQUIRE_RUNTIME_HOOKS=1
    -e VLLM_ASCEND_HYPIC_TRUE_POSITION_INDEPENDENT=1
    -e VLLM_ASCEND_HYPIC_CACHE_ONLY_CUMULATIVE_PREFIX=0
    -e VLLM_ASCEND_HYPIC_ENABLE_ASYNC=1
    -e VLLM_ASCEND_HYPIC_ENABLE_FULL_DECODE_ONLY=1
    -e VLLM_ASCEND_HYPIC_ENABLE_PLANNING=1
    -e VLLM_ASCEND_HYPIC_ENABLE_PREFILL_PRUNING=1
    -e VLLM_ASCEND_HYPIC_ENABLE_SEGMENT_CACHE_WRITE=1
    -e VLLM_ASCEND_HYPIC_ENABLE_FULL_ATTN_KV_REPAIR=1
    -e VLLM_ASCEND_HYPIC_ENABLE_GDN_TRANSITION_COMPOSE=1
    -e VLLM_ASCEND_HYPIC_REQUIRE_MATERIALIZED_CACHE=1
    -e VLLM_ASCEND_HYPIC_ENABLE_PREFIX_CACHE_COEXISTENCE=0
    -e VLLM_ASCEND_HYPIC_REQUIRE_POSITION_DEPENDENT_PREFIX_CACHE=0
    -e VLLM_ASCEND_HYPIC_REQUIRE_DISTRIBUTED_C3=0
    -e VLLM_ASCEND_HYPIC_ENABLE_COLD_PREFIX_CHUNKING=0
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_COLD_PREFIX=0
    -e VLLM_ASCEND_HYPIC_UNSAFE_ASSUME_MATERIALIZED_CACHE=0
    -e VLLM_ASCEND_HYPIC_ALLOW_POSITION_MISMATCH=0
    -e VLLM_ASCEND_HYPIC_EXPERIMENTAL_NONCONTIG=0
    -e VLLM_ASCEND_HYPIC_AUTO_SEGMENT_TEXT=1
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_TEXT=0
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_TOKENS=2048
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_MIN_TOKENS=4096
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_MIN_TAIL_TOKENS=256
    -e VLLM_ASCEND_HYPIC_AUTO_CHUNK_MAX_SEGMENTS=64
    -e VLLM_ASCEND_HYPIC_MATERIALIZATION_PREFIX_TOKENS=16384
    -e VLLM_ASCEND_HYPIC_MATERIALIZE_AFTER_OBSERVATIONS=2
    -e VLLM_ASCEND_HYPIC_MAX_MATERIALIZATION_CANDIDATES_PER_STEP=1
    -e VLLM_ASCEND_HYPIC_MAX_MATERIALIZED_SEGMENTS=4
    -e VLLM_ASCEND_HYPIC_MATERIAL_CACHE_DEVICE=cpu
    -e VLLM_ASCEND_HYPIC_GDN_MATERIAL_CACHE_DEVICE=auto
    -e VLLM_ASCEND_HYPIC_GDN_MATERIAL_CACHE_MAX_MB=256
    -e VLLM_ASCEND_HYPIC_PIN_CPU_MATERIAL=1
    -e VLLM_ASCEND_HYPIC_MATERIAL_CACHE_MAX_MB=1536
    -e VLLM_ASCEND_HYPIC_MATERIAL_CACHE_MIN_FREE_MB=1024
    -e VLLM_ASCEND_HYPIC_REPLAY_CHUNK_TOKENS=16384
    -e VLLM_ASCEND_HYPIC_REPLAY_BATCH_ROWS=4
    -e VLLM_ASCEND_HYPIC_MIN_REWRITE_TOKENS=4096
    -e VLLM_ASCEND_HYPIC_MAX_MATERIALIZATION_RETRIES=1
    -e VLLM_ASCEND_HYPIC_MATERIALIZATION_REPORT_TIMEOUT_SECONDS=300
    -e VLLM_ASCEND_HYPIC_STATS_INTERVAL=20
  )
  if [[ -n "$MEMORY_LIMIT" ]]; then
    args+=(--memory "$MEMORY_LIMIT" --memory-swap "$MEMORY_LIMIT")
  fi
  docker create "${args[@]}" "$IMAGE" bash -lc "$serve_command" >/dev/null
  verify_container "$name" created "$hypic_enable"
}

wait_for_health() {
  local name=$1
  local deadline=$((SECONDS + 2400))
  until curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null; do
    if [[ $(container_state "$name") != running ]]; then
      docker logs --tail 240 "$name" >&2 || true
      return 1
    fi
    if (( SECONDS >= deadline )); then
      docker logs --tail 240 "$name" >&2 || true
      printf 'health timeout for %s\n' "$name" >&2
      return 1
    fi
    sleep 10
  done
  local ownership_deadline=$((SECONDS + 180))
  until assert_owned_lane_owned_by "$name"; do
    if (( SECONDS >= ownership_deadline )); then
      return 1
    fi
    sleep 5
  done
}

start_arm() {
  local arm=$1 name=$2 hypic_enable=$3
  local state
  state=$(container_state "$name")
  if [[ "$state" == running ]]; then
    CURRENT_CONTAINER=$name
    verify_container "$name" running "$hypic_enable"
  elif [[ "$state" == created || "$state" == exited ]]; then
    wait_for_owned_lane_empty
    CURRENT_CONTAINER=$name
    docker start "$name" >/dev/null
    verify_container "$name" running "$hypic_enable"
  else
    printf 'unexpected container state %s=%s\n' "$name" "$state" >&2
    return 1
  fi
  write_status "$arm-service-starting" "$name"
  wait_for_health "$name"
  write_status "$arm-service-ready" "$name"
}

stop_arm() {
  local arm=$1 name=$2 phase=$3
  if [[ $(container_state "$name") == running ]]; then
    verify_container "$name" running "${4}"
    docker stop --time 60 "$name" >/dev/null
  fi
  verify_container "$name" exited "${4}"
  CURRENT_CONTAINER=
  wait_for_owned_lane_empty
  docker logs --timestamps "$name" > "$OUTPUT_ROOT/$arm/service.$phase.log" 2>&1 || true
  write_status "$arm-$phase-stopped" "$name"
}

verify_performance_run() {
  local path=$1 arm=$2 run_index=$3
  python3 - "$path" "$arm" "$run_index" <<'PY'
import json
import sys

path, arm, run_index = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = json.load(open(path))
config = data["config"]
expected = {
    "input_tokens": 32768,
    "prefix_tokens": 16384,
    "output_tokens": 1024,
    "requests": 40,
    "concurrency": 16,
    "warmup_requests": 2,
    "ignore_eos": True,
    "segment_ends": [16384, 32768],
}
for key, value in expected.items():
    if config.get(key) != value:
        raise SystemExit(f"{path}: {key} mismatch")
summary = data["summary"]
if not (
    summary.get("requests") == 40
    and summary.get("successful") == 40
    and summary.get("failed") == 0
    and summary.get("fixed_output_verified") is True
):
    raise SystemExit(f"{path}: incomplete performance run")
if arm == "hypic-only" and run_index == 1:
    if summary.get("hot_path_verified") is not True:
        raise SystemExit(f"{path}: HYPIC hot path not verified")
PY
}

archive_invalid() {
  local path=$1
  if [[ -e "$path" ]]; then
    local archive="$path.invalid.$(date -u +%Y%m%dT%H%M%SZ)"
    [[ ! -e "$archive" ]]
    mv -- "$path" "$archive"
  fi
}

render_progress() {
  python3 "$ANALYZER" \
    --root "$OUTPUT_ROOT" \
    --reference "$REFERENCE" \
    --quality-max-out-len "$QUALITY_MAX_OUT_LEN" \
    --allow-incomplete
}

run_performance() {
  local arm=$1
  mkdir -p "$OUTPUT_ROOT/$arm"
  for run_index in 1 2 3; do
    local output="$OUTPUT_ROOT/$arm/performance.run$run_index.json"
    if verify_performance_run "$output" "$arm" "$run_index" 2>/dev/null; then
      printf '%s verified existing %s\n' "$(date -Is)" "$output"
      continue
    fi
    archive_invalid "$output"
    write_status "$arm-performance-run$run_index" "$output"
    local args=(
      "$BENCHMARK"
      --base-url "http://127.0.0.1:$PORT"
      --model "$MODEL_NAME"
      --input-tokens 32768
      --prefix-tokens 16384
      --output-tokens 1024
      --requests 40
      --concurrency 16
      --warmup-requests 2
      --warmup-evidence-timeout 300
      --timeout 2400
      --json-output "$output"
    )
    if [[ "$arm" == hypic-only && "$run_index" == 1 ]]; then
      args+=(
        --evidence-file "$OUTPUT_ROOT/$arm/hypic-evidence.jsonl"
        --require-hot-path
      )
    fi
    python3 "${args[@]}" 2>&1 | tee "$OUTPUT_ROOT/$arm/performance.run$run_index.log"
    verify_performance_run "$output" "$arm" "$run_index"
    render_progress
  done
}

verify_quality_run() {
  local path=$1 expected=$2 expected_max_out_len=$3
  python3 - "$path" "$expected" "$expected_max_out_len" "$MODEL_NAME" "$QUALITY" "$OUTPUT_ROOT" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

data = json.load(open(sys.argv[1]))
expected = int(sys.argv[2])
expected_max_out_len = int(sys.argv[3])
model_name = sys.argv[4]
evaluator = Path(sys.argv[5])
root = Path(sys.argv[6]).resolve()
expected_dataset_hash = {
    "longbenchv2": "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a",
    "gsm8k": "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
}
details = Path(data.get("details_path", "")).resolve()
if not (
    data.get("schema") == "hypic-quality-eval/v1"
    and data.get("requests") == expected
    and data.get("successful") == expected
    and data.get("failed") == 0
    and data.get("max_out_len") == expected_max_out_len
    and data.get("ignore_eos") is False
    and data.get("model") == model_name
    and data.get("concurrency") == 32
    and data.get("seed") == 0
    and data.get("temperature") == 0
    and data.get("enable_thinking") is False
    and data.get("data_sha256") == expected_dataset_hash.get(data.get("dataset"))
    and data.get("evaluator_script_sha256")
        == hashlib.sha256(evaluator.read_bytes()).hexdigest()
    and details.is_file()
    and details.is_relative_to(root)
    and data.get("details_sha256") == hashlib.sha256(details.read_bytes()).hexdigest()
):
    raise SystemExit(f"{sys.argv[1]}: incomplete quality run")
PY
}

performance_complete() {
  local arm=$1
  local run_index
  for run_index in 1 2 3; do
    verify_performance_run \
      "$OUTPUT_ROOT/$arm/performance.run$run_index.json" \
      "$arm" \
      "$run_index" \
      >/dev/null 2>&1 || return 1
  done
}

quality_complete() {
  local arm=$1
  local dataset expected run_index
  for dataset in longbenchv2 gsm8k; do
    if [[ "$dataset" == longbenchv2 ]]; then
      expected=127
    else
      expected=1319
    fi
    for run_index in 1 2 3; do
      verify_quality_run \
        "$OUTPUT_ROOT/quality/$arm/$dataset.run$run_index.summary.json" \
        "$expected" \
        "$QUALITY_MAX_OUT_LEN" \
        >/dev/null 2>&1 || return 1
    done
  done
}

run_quality() {
  local arm=$1
  local output_dir="$OUTPUT_ROOT/quality/$arm"
  mkdir -p "$output_dir"
  for dataset in longbenchv2 gsm8k; do
    local data expected
    if [[ "$dataset" == longbenchv2 ]]; then
      data=/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json
      expected=127
    else
      data=/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl
      expected=1319
    fi
    for run_index in 1 2 3; do
      local summary="$output_dir/$dataset.run$run_index.summary.json"
      if verify_quality_run "$summary" "$expected" "$QUALITY_MAX_OUT_LEN" 2>/dev/null; then
        printf '%s verified existing %s\n' "$(date -Is)" "$summary"
        continue
      fi
      archive_invalid "$summary"
      write_status "$arm-quality-$dataset-run$run_index" "$summary"
      python3 "$QUALITY" \
        --dataset "$dataset" \
        --data "$data" \
        --base-url "http://127.0.0.1:$PORT" \
        --model "$MODEL_NAME" \
        --output-dir "$output_dir" \
        --run-id "run$run_index" \
        --concurrency 32 \
        --max-out-len "$QUALITY_MAX_OUT_LEN" \
        --seed 0 \
        --timeout 2400 \
        --retries 2
      verify_quality_run "$summary" "$expected" "$QUALITY_MAX_OUT_LEN"
      render_progress
    done
  done
}

verify_canary_run() {
  local path=$1 arm=$2
  python3 - "$path" "$arm" <<'PY'
import json
import sys
path, arm = sys.argv[1:]
data = json.load(open(path))
if not (
    data.get("schema") == "hypic-active-semantic-canary/v1"
    and data.get("phase") == arm
    and data.get("answer_contains_key") is True
    and data.get("input_tokens") == 32768
    and data.get("request") == {
        "max_tokens": 32, "temperature": 0,
        "seed": 0, "ignore_eos": False,
    }
):
    raise SystemExit(f"{path}: incomplete semantic canary")
PY
}

run_canary() {
  local arm=$1
  local output="$OUTPUT_ROOT/$arm/semantic-canary.json"
  if verify_canary_run "$output" "$arm" 2>/dev/null; then
    printf '%s verified existing %s\n' "$(date -Is)" "$output"
    return
  fi
  archive_invalid "$output"
  write_status "$arm-real-weight-canary" "$output"
  python3 "$CANARY" \
    --base-url "http://127.0.0.1:$PORT" \
    --model "$MODEL_NAME" \
    --phase "$arm" \
    --output "$output" \
    --timeout 2400 \
    2>&1 | tee "$OUTPUT_ROOT/$arm/semantic-canary.log"
  verify_canary_run "$output" "$arm"
}

cleanup() {
  local rc=$?
  trap - EXIT
  if [[ -n "$CURRENT_CONTAINER" ]] && [[ $(container_state "$CURRENT_CONTAINER") == running ]]; then
    docker stop --time 60 "$CURRENT_CONTAINER" >/dev/null || true
    CURRENT_CONTAINER=
  fi
  if [[ -d "$OUTPUT_ROOT" ]]; then
    if [[ "$E2E_GATES" == 1 ]]; then
      python3 - "$OUTPUT_ROOT" "$rc" <<'PY' || true
import json
import pathlib
import sys
from datetime import datetime, timezone

root, rc = pathlib.Path(sys.argv[1]), int(sys.argv[2])
failed_gate = None
for name in ("canary-gate.json", "performance-gate.json"):
    path = root / name
    if path.exists():
        record = json.loads(path.read_text())
        if record.get("passed") is False:
            failed_gate = name
            break
if rc == 0:
    status = "pending-independent-audit"
elif failed_gate:
    status = "rejected"
elif rc in (124, 137, 143):
    status = "inconclusive"
else:
    status = "failed"
result = {
    "schema": "hypic-e2e-terminal-decision/v1",
    "status": status,
    "controller_exit_code": rc,
    "failed_gate": failed_gate,
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "scope": "controller; independent audit may still be pending",
}
(root / "terminal-decision.json").write_text(json.dumps(result, indent=2) + "\n")
PY
    fi
    write_status "controller-exit" "exit_code=$rc" || true
  fi
  exit "$rc"
}

verify_static_inputs

if (( SELF_TEST )); then
  [[ "$HOST_NPU_FIRST" =~ ^[0-7]$ ]]
  [[ "$HOST_NPU_LAST" =~ ^[0-7]$ ]]
  [[ "$TP_SIZE" =~ ^[1-8]$ ]]
  [[ $((HOST_NPU_LAST - HOST_NPU_FIRST + 1)) -eq "$TP_SIZE" ]]
  assert_owned_lane_empty
  for item in "$BASELINE_CONTAINER:0" "$TREATMENT_CONTAINER:1"; do
    name=${item%:*}
    enabled=${item#*:}
    state=$(container_state "$name")
    if [[ "$state" != absent ]]; then
      verify_container "$name" "$state" "$enabled"
    fi
  done
  printf 'historical reproduction self-test passed for %s TP%s; no workload state changed\n' "$OWNED_LANE" "$TP_SIZE"
  exit 0
fi

mkdir -p "$OUTPUT_ROOT"/{no-cache,hypic-only,quality/no-cache,quality/hypic-only}
exec 9>"$OUTPUT_ROOT/controller.lock"
if ! flock -n 9; then
  printf 'another historical reproduction controller owns the lock\n' >&2
  exit 75
fi
exec > >(tee -a "$OUTPUT_ROOT/controller.log") 2>&1
trap cleanup EXIT
trap 'exit 124' TERM INT

write_status preflight "creating or validating exact experiment containers"
if [[ $(container_state "$BASELINE_CONTAINER") == running && $(container_state "$TREATMENT_CONTAINER") == running ]]; then
  printf 'both experiment arms are running; refusing simultaneous ownership\n' >&2
  exit 1
fi
create_container no-cache "$BASELINE_CONTAINER" 0
create_container hypic-only "$TREATMENT_CONTAINER" 1

{
  date -Is
  git -c safe.directory="$SOURCE_HYPIC" -C "$SOURCE_HYPIC" status --short --branch
  git -c safe.directory="$SOURCE_HYPIC" -C "$SOURCE_HYPIC" rev-parse HEAD
  sha256sum "$BENCHMARK" "$QUALITY" "$ANALYZER" "$REFERENCE"
  docker inspect "$BASELINE_CONTAINER" "$TREATMENT_CONTAINER"
  npu-smi info
} > "$OUTPUT_ROOT/environment-and-container-snapshot.txt"

if [[ "$E2E_GATES" == 1 ]]; then
  python3 "$E2E_RECORDS/baseline_contract.py" \
    --root "$OUTPUT_ROOT" \
    --source "$SOURCE_HYPIC" \
    --image "$IMAGE" \
    --container "$BASELINE_CONTAINER" \
    --benchmark "$BENCHMARK" \
    --quality "$QUALITY" \
    --quality-max-out-len "$QUALITY_MAX_OUT_LEN"

  if ! verify_canary_run "$OUTPUT_ROOT/no-cache/semantic-canary.json" no-cache 2>/dev/null; then
    start_arm no-cache "$BASELINE_CONTAINER" 0
    run_canary no-cache
    stop_arm no-cache "$BASELINE_CONTAINER" canary 0
  else
    write_status no-cache-canary-reused "validated existing real-weight baseline canary"
  fi
  if ! verify_canary_run "$OUTPUT_ROOT/hypic-only/semantic-canary.json" hypic-only 2>/dev/null; then
    start_arm hypic-only "$TREATMENT_CONTAINER" 1
    run_canary hypic-only
    stop_arm hypic-only "$TREATMENT_CONTAINER" canary 1
  fi
  python3 "$E2E_RECORDS/assess_hypic_e2e_gates.py" canary --root "$OUTPUT_ROOT"

  if performance_complete no-cache; then
    write_status no-cache-performance-reused "all three accepted baseline runs reused"
  else
    start_arm no-cache "$BASELINE_CONTAINER" 0
    run_performance no-cache
    stop_arm no-cache "$BASELINE_CONTAINER" performance 0
  fi
  if performance_complete hypic-only; then
    write_status hypic-only-performance-reused "all three accepted treatment runs reused"
  else
    start_arm hypic-only "$TREATMENT_CONTAINER" 1
    run_performance hypic-only
    cp -- "$OUTPUT_ROOT/hypic-only/hypic-evidence.jsonl" "$OUTPUT_ROOT/hypic-only/performance.hypic-evidence.jsonl"
    stop_arm hypic-only "$TREATMENT_CONTAINER" performance 1
  fi
  python3 "$E2E_RECORDS/assess_hypic_e2e_gates.py" performance --root "$OUTPUT_ROOT"

  if quality_complete no-cache; then
    write_status no-cache-quality-reused "all six accepted 2048-token baseline runs reused"
  else
    start_arm no-cache "$BASELINE_CONTAINER" 0
    run_quality no-cache
    stop_arm no-cache "$BASELINE_CONTAINER" quality 0
  fi
  if quality_complete hypic-only; then
    write_status hypic-only-quality-reused "all six accepted treatment runs reused"
  else
    start_arm hypic-only "$TREATMENT_CONTAINER" 1
    run_quality hypic-only
    cp -- "$OUTPUT_ROOT/hypic-only/hypic-evidence.jsonl" "$OUTPUT_ROOT/hypic-only/quality.hypic-evidence.jsonl"
    stop_arm hypic-only "$TREATMENT_CONTAINER" quality 1
  fi
else
  if performance_complete no-cache; then
    write_status no-cache-performance-complete "all three accepted runs reused"
  else
    start_arm no-cache "$BASELINE_CONTAINER" 0
    run_performance no-cache
    stop_arm no-cache "$BASELINE_CONTAINER" performance 0
  fi
  if quality_complete no-cache; then
    write_status no-cache-quality-complete "all six accepted runs reused"
  else
    start_arm no-cache "$BASELINE_CONTAINER" 0
    run_quality no-cache
    stop_arm no-cache "$BASELINE_CONTAINER" quality 0
  fi
  start_arm hypic-only "$TREATMENT_CONTAINER" 1
  run_performance hypic-only
  cp -- "$OUTPUT_ROOT/hypic-only/hypic-evidence.jsonl" "$OUTPUT_ROOT/hypic-only/performance.hypic-evidence.jsonl"
  stop_arm hypic-only "$TREATMENT_CONTAINER" performance 1
  start_arm hypic-only "$TREATMENT_CONTAINER" 1
  run_quality hypic-only
  cp -- "$OUTPUT_ROOT/hypic-only/hypic-evidence.jsonl" "$OUTPUT_ROOT/hypic-only/quality.hypic-evidence.jsonl"
  stop_arm hypic-only "$TREATMENT_CONTAINER" quality 1
fi

python3 "$ANALYZER" \
  --root "$OUTPUT_ROOT" \
  --reference "$REFERENCE" \
  --quality-max-out-len "$QUALITY_MAX_OUT_LEN"
sha256sum \
  "$OUTPUT_ROOT/historical-reproduction-summary.json" \
  "$OUTPUT_ROOT/HISTORICAL_REPRODUCTION_REPORT.md" \
  "$OUTPUT_ROOT/hypic-only/performance.hypic-evidence.jsonl" \
  > "$OUTPUT_ROOT/FINAL_SHA256SUMS"
write_status completed "historical-ruler performance and available quality suites completed"
CURRENT_CONTAINER=
