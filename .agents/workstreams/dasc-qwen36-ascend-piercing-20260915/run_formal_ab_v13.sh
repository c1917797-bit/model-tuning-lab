#!/usr/bin/env bash
set -euo pipefail

REPO=/opt/host/vnf/austinov/model-tuning-lab
WS=.agents/workstreams/dasc-qwen36-ascend-piercing-20260915
BASE=/cache/cch/dasc-qwen36-ascend-20260915
V12=$BASE/physical-cache-order-fix-v12
ROOT=$BASE/formal-ab-v13
IMAGE=quay.io/ascend/vllm-ascend:v0.23.0
MODEL_HOST=/cache/efim/Qwen3.6-27B
MODEL=/models/Qwen3.6-27B
PLUGIN=$V12/plugin-snapshot
BENCH=/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py
QUALITY=$REPO/$WS/dasc_quality_eval.py
METRICS=$REPO/$WS/capture_prometheus_metrics.py
IDENTITY=$REPO/$WS/extract_formal_identity.py
NORMALIZER=$REPO/$WS/build_formal_evidence.py
DECIDER=$REPO/$WS/verify_formal_decision.py
CAPACITY=$REPO/$WS/verify_cache_capacity.py
PERF_RESUME=$REPO/$WS/verify_performance_triplet.py
VERIFY_V12=$REPO/$WS/verify_physical_v12.py
PORT=8031
LOCK=/cache/cch/.locks/npu4-7.lock
CURRENT=

container_name() { echo "dasc_qwen36_formal_v13_${1}_20260916"; }
container_state() { docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null || echo absent; }
cards_idle() {
  local i out
  for i in 4 5 6 7; do
    out=$(npu-smi info -t proc-mem -i "$i" -c 0 2>&1) || return 1
    grep -q 'Process id:' <<<"$out" && return 1
  done
}
snapshot_cards() {
  local i
  for i in 4 5 6 7; do echo "NPU$i"; npu-smi info -t proc-mem -i "$i" -c 0 2>&1 || true; done
}
static_checks() {
  command -v docker >/dev/null; command -v npu-smi >/dev/null; command -v flock >/dev/null
  test -r "$MODEL_HOST/config.json"; test -r "$REPO/projects/dasc_vllm_ascend/pyproject.toml"
  test -r "$BENCH"; test -r "$QUALITY"; test -r "$METRICS"; test -r "$IDENTITY"
  test -r "$NORMALIZER"; test -r "$DECIDER"; test -r "$CAPACITY"; test -r "$PERF_RESUME"; test -r "$VERIFY_V12"
  printf '%s  %s\n' cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822 "$BENCH" | sha256sum -c -
  docker image inspect "$IMAGE" >/dev/null
  local i; for i in 4 5 6 7; do test -c "/dev/davinci$i"; done
  test -z "$(git -C "$REPO" status --porcelain)"
}
gate_checks() {
  test -f "$V12/SUCCESS"
  test -r "$PLUGIN/pyproject.toml"
  python3 "$VERIFY_V12" --root "$V12" --repo "$REPO" --output "$BASE/controllers/dasc-qwen36-v12-verification.json"
}
if [[ ${1:-} == --self-test ]]; then static_checks; echo 'v13 static self-test passed; no NPU workload started'; exit 0; fi

cleanup() {
  local rc=$?
  set +e
  if [[ -n "$CURRENT" && $(container_state "$CURRENT") == running ]]; then docker stop --time 60 "$CURRENT" >/dev/null; fi
  [[ -d "$ROOT" ]] && echo "$rc" >"$ROOT/controller-last-exit-code.txt"
  exit "$rc"
}
trap cleanup EXIT

static_checks
gate_checks
mkdir -p "$ROOT"/{dense,candidate,quality/dense,quality/candidate}
exec 8>"$ROOT/controller.lock"; flock -n 8 || { echo 'another v13 controller owns the lock'; exit 75; }
exec 9>"$LOCK"; flock -n 9 || { echo 'NPU4-7 lock is held'; exit 75; }
cards_idle || { echo 'NPU4-7 are occupied'; snapshot_cards; exit 75; }
exec > >(tee -a "$ROOT/controller.log") 2>&1

HEAD=$(git -C "$REPO" rev-parse HEAD)
if [[ -f "$ROOT/source-commit.txt" ]]; then test "$(cat "$ROOT/source-commit.txt")" = "$HEAD"; else echo "$HEAD" >"$ROOT/source-commit.txt"; fi
MODEL_SHA=$(sha256sum "$MODEL_HOST/config.json" | awk '{print $1}')
PLUGIN_SHA=$(sha256sum "$V12/plugin-files.sha256" | awk '{print $1}')
docker image inspect "$IMAGE" >"$ROOT/image-inspect.json"
snapshot_cards >"$ROOT/npu-before.txt"

create_arm() {
  local arm=$1 name candidate plugins enable
  name=$(container_name "$arm")
  [[ "$arm" == candidate ]] && { candidate=1; plugins=ascend,dasc_vllm_ascend; enable=1; } || { candidate=0; plugins=ascend; enable=0; }
  if [[ $(container_state "$name") == absent ]]; then
    local envs=( -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 -e VLLM_PLUGINS="$plugins" -e MST_DASC_ENABLE="$enable" -e HCCL_NPU_SOCKET_PORT_RANGE=27000-27100 -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True )
    if (( candidate )); then envs+=( -e MST_DASC_MODE=physical-cache-eager -e MST_DASC_W_MAX=64 -e MST_DASC_EVIDENCE_PATH=/dasc-results/candidate/evidence.jsonl -e PYTHONPATH=/workspace/dasc ); fi
    docker create --name "$name" --label mst.owner=c1917797-bit --label mst.experiment=dasc-qwen36-formal-ab-v13 --label mst.arm="$arm" --network host \
      --device /dev/davinci4:/dev/davinci0 --device /dev/davinci5:/dev/davinci1 --device /dev/davinci6:/dev/davinci2 --device /dev/davinci7:/dev/davinci3 \
      --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
      -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
      -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro -v /etc/ascend_install.info:/etc/ascend_install.info:ro -v /usr/local/dcmi:/usr/local/dcmi:ro \
      -v "$MODEL_HOST:$MODEL:ro" -v "$PLUGIN:/workspace/dasc:ro" -v "$ROOT:/dasc-results:rw" "${envs[@]}" "$IMAGE" \
      vllm serve "$MODEL" --served-model-name qwen36-dasc-formal-v13 --tensor-parallel-size 4 --mamba-cache-mode align --enable-prefix-caching \
      --max-model-len 44032 --max-num-seqs 32 --block-size 128 --kv-cache-memory 9663676416 \
      --compilation-config '{"cudagraph_capture_sizes":[1,2,4,8,16,32],"cudagraph_mode":"FULL_DECODE_ONLY"}' --port "$PORT" >/dev/null
  fi
  docker inspect "$name" >"$ROOT/$arm/container-inspect.json"
  python3 "$IDENTITY" --inspect "$ROOT/$arm/container-inspect.json" --arm "$arm" --source-commit "$HEAD" --model-config-sha256 "$MODEL_SHA" --plugin-manifest-sha256 "$PLUGIN_SHA" --output "$ROOT/$arm/identity.json"
}

start_arm() {
  local arm=$1 name deadline
  name=$(container_name "$arm"); CURRENT=$name
  [[ $(container_state "$name") == running ]] || docker start "$name" >/dev/null
  deadline=$((SECONDS + 2400))
  until curl -fsS "http://127.0.0.1:$PORT/v1/models" >/dev/null; do
    [[ $(container_state "$name") == running ]] || { docker logs --tail 200 "$name"; return 1; }
    (( SECONDS < deadline )) || return 1; sleep 10
  done
}
stop_arm() {
  local arm=$1 name; name=$(container_name "$arm")
  docker logs "$name" >"$ROOT/$arm/service.log" 2>&1 || true
  [[ $(container_state "$name") == running ]] && docker stop --time 60 "$name" >/dev/null
  docker inspect "$name" >"$ROOT/$arm/container-final-inspect.json"; CURRENT=
  cards_idle
}
archive() { local stamp; stamp=$(date -u +%Y%m%dT%H%M%SZ); for x in "$@"; do [[ ! -e "$x" ]] || mv "$x" "$x.invalid.$stamp"; done; }
capture() { python3 "$METRICS" --url "http://127.0.0.1:$PORT/metrics" --output "$1"; }

run_performance() {
  local arm=$1 run out before after
  for run in run1 run2 run3; do
    out=$ROOT/$arm/performance.$run.json; before=$ROOT/$arm/performance.$run.metrics.before.json; after=$ROOT/$arm/performance.$run.metrics.after.json
    if python3 "$PERF_RESUME" --report "$out" --metrics-before "$before" --metrics-after "$after" >/dev/null 2>&1; then continue; fi
    archive "$out" "$before" "$after"; capture "$before"
    python3 "$BENCH" --base-url "http://127.0.0.1:$PORT" --model qwen36-dasc-formal-v13 --input-tokens 32768 --prefix-tokens 16384 --output-tokens 1024 \
      --requests 40 --concurrency 16 --warmup-requests 2 --timeout 2400 --json-output "$out" 2>&1 | tee "$ROOT/$arm/performance.$run.log"
    capture "$after"
  done
}
run_quality() {
  local arm=$1 dataset run data dir summary
  dir=$ROOT/quality/$arm
  for dataset in longbenchv2 gsm8k; do
    [[ "$dataset" == longbenchv2 ]] && data=/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json || data=/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl
    for run in run1 run2 run3; do
      summary=$dir/$dataset.$run.summary.json
      [[ -s "$summary" && -s "$dir/$dataset.$run.jsonl" ]] && continue
      python3 "$QUALITY" --repo "$REPO" --shared-prefix-lines 96 --require-cache-hit --dataset "$dataset" --data "$data" \
        --base-url "http://127.0.0.1:$PORT" --model qwen36-dasc-formal-v13 --output-dir "$dir" --run-id "$run" \
        --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2
    done
  done
}

create_arm dense; create_arm candidate
for arm in dense candidate; do start_arm "$arm"; run_performance "$arm"; run_quality "$arm"; stop_arm "$arm"; done
python3 "$CAPACITY" --dense-log "$ROOT/dense/service.log" --candidate-log "$ROOT/candidate/service.log" --candidate-evidence "$ROOT/candidate/evidence.jsonl" --output "$ROOT/cache-capacity.json"
python3 - "$ROOT/candidate/evidence.jsonl" "$ROOT/candidate/activation.json" "$REPO/$WS" <<'PY'
import json, pathlib, sys
sys.path.insert(0, sys.argv[3])
from verify_physical_v12 import evidence_verdict, load_jsonl
path = pathlib.Path(sys.argv[2]); path.write_text(json.dumps(evidence_verdict(load_jsonl(pathlib.Path(sys.argv[1]))), indent=2, sort_keys=True) + "\n")
PY
python3 "$NORMALIZER" --root "$ROOT" --output "$ROOT/normalized-evidence.json"
python3 "$DECIDER" --input "$ROOT/normalized-evidence.json" --output "$ROOT/decision.json"
snapshot_cards >"$ROOT/npu-after.txt"; touch "$ROOT/SUCCESS"; echo 'v13 accepted'
