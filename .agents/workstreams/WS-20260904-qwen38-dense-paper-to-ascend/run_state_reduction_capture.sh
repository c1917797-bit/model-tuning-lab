#!/usr/bin/env bash
set -euo pipefail

REPO=/cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
WS="$REPO/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend"
OUTPUT=/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906
CAPTURE="$OUTPUT/calibration/captures"
CALIBRATION="$OUTPUT/calibration/longbenchv2-16x2048-tokenids.jsonl"
CONTAINER=qwen36_state_reduction_capture_npu4_7_tp4
IMAGE=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
PORT=8225

cleanup() {
  rm -f "$CAPTURE/.armed"
  if docker inspect "$CONTAINER" >/dev/null 2>&1; then
    docker stop --time 30 "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

test "$(sha256sum "$CALIBRATION" | awk '{print $1}')" = d146eede2a438154ea8c1bf9785dffa12f8a81e56fa370ff48be4d924e908111
test "$(sha256sum "$REPO/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/install_gdn_rrqr_capture_v023.py" | awk '{print $1}')" = fb50b47130bbcd326faf4250755a44e9b2eea638f9df7b97c6fc8943172480d2
test "$(sha256sum /cache/cch/LinearAttentionPruning/src/key_reduction/pruners/rrqr.py | awk '{print $1}')" = fa4bacf516011ba1c88f2e0e92957bbe4513cc1bb6634912fdb0d06ba7821a62

for device in 4 5 6 7; do
  output="$(npu-smi info -t proc-mem -i "$device")"
  grep -q "No process in device" <<<"$output" || {
    echo "host NPU${device} is not empty" >&2
    exit 2
  }
done
if ss -ltn | grep -qE ":${PORT}[[:space:]]"; then
  echo "port ${PORT} is already in use" >&2
  exit 2
fi
if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "container already exists: $CONTAINER" >&2
  exit 2
fi
mkdir -p "$CAPTURE"
if find "$CAPTURE" -maxdepth 1 -type f | grep -q .; then
  echo "capture directory is not empty: $CAPTURE" >&2
  exit 2
fi

docker_args=(
  create
  --name "$CONTAINER"
  --network host
  --cpuset-cpus 0-95
  --memory 48g
  --device /dev/davinci4:/dev/davinci0
  --device /dev/davinci5:/dev/davinci1
  --device /dev/davinci6:/dev/davinci2
  --device /dev/davinci7:/dev/davinci3
  --device /dev/davinci_manager
  --device /dev/devmm_svm
  --device /dev/hisi_hdc
  -v /usr/local/dcmi:/usr/local/dcmi
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool
  -v /etc/ascend_install.info:/etc/ascend_install.info
  -v /cache/efim:/cache/efim:ro
  -v "$REPO":/source-vllm-ascend:ro
  -v "$OUTPUT":/results
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_OP_EXPANSION_MODE=AIV
  -e HCCL_NPU_SOCKET_PORT_RANGE=26910-27010
  -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
  -e TASK_QUEUE_ENABLE=1
  -e OMP_NUM_THREADS=1
  -e VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE=1
  -e VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR=/results/calibration/captures
  -e VLLM_ASCEND_GDN_RRQR_MAX_TOKENS=2048
  -e VLLM_ASCEND_GDN_RRQR_MAX_CAPTURES_PER_LAYER=16
  "$IMAGE"
  bash -lc
  "set -euo pipefail; python3 /source-vllm-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/install_gdn_rrqr_capture_v023.py /vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py; exec vllm serve /cache/efim/Qwen3.6-27B --served-model-name qwen36-state-reduction-calibration --host 127.0.0.1 --port $PORT --data-parallel-size 1 --tensor-parallel-size 4 --max-model-len 40960 --max-num-batched-tokens 16384 --max-num-seqs 16 --gpu-memory-utilization 0.9 --no-enable-prefix-caching --compilation-config '{\"cudagraph_capture_sizes\":[1,4,8,12,16,24,32,48,56,64,72,84,96,108,112,128,160,172,196,200,212,232,272,288,312,328,344,360,384,400,416,432,448,480,512],\"cudagraph_mode\":\"FULL_DECODE_ONLY\"}' --trust-remote-code --async-scheduling"
)
docker "${docker_args[@]}" >"$OUTPUT/calibration/container-id.txt"

docker inspect "$CONTAINER" --format 'status={{.State.Status}} cpuset={{.HostConfig.CpusetCpus}} memory={{.HostConfig.Memory}} devices={{json .HostConfig.Devices}} image={{.Image}}' >"$OUTPUT/calibration/container-inspect-before-start.txt"
docker start "$CONTAINER" >/dev/null
docker logs -f "$CONTAINER" >"$OUTPUT/calibration/service.log" 2>&1 &
LOGGER_PID=$!

ready=0
for _ in $(seq 1 180); do
  if curl -fsS "http://127.0.0.1:${PORT}/v1/models" >"$OUTPUT/calibration/health.json" 2>/dev/null; then
    ready=1
    break
  fi
  if test "$(docker inspect "$CONTAINER" --format '{{.State.Running}}')" != true; then
    break
  fi
  sleep 5
done
if test "$ready" != 1; then
  docker logs "$CONTAINER" | tail -300 >&2
  exit 2
fi

touch "$CAPTURE/.armed"
replay_args=(
  exec "$CONTAINER" python3
  /source-vllm-ascend/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_calibration.py
  replay
  --calibration /results/calibration/longbenchv2-16x2048-tokenids.jsonl
  --endpoint "http://127.0.0.1:${PORT}"
  --model-name qwen36-state-reduction-calibration
  --output /results/calibration/replay-results.jsonl
  --seq-len 2048
)
docker "${replay_args[@]}"
rm -f "$CAPTURE/.armed"
sleep 2

count="$(find "$CAPTURE" -maxdepth 1 -type f -name '*.pt' | wc -l)"
test "$count" -eq 3072 || {
  echo "expected 3072 capture files, got $count" >&2
  exit 2
}
find "$CAPTURE" -maxdepth 1 -type f -name '*.pt' -print0 |
  sort -z |
  xargs -0 sha256sum >"$OUTPUT/calibration/capture-sha256.txt"
sha256sum "$OUTPUT/calibration/replay-results.jsonl" "$OUTPUT/calibration/capture-sha256.txt" >"$OUTPUT/calibration/calibration-artifact-sha256.txt"
docker inspect "$CONTAINER" --format 'status={{.State.Status}} oom={{.State.OOMKilled}} exit={{.State.ExitCode}} error={{json .State.Error}}' >"$OUTPUT/calibration/container-inspect-after-replay.txt"
kill "$LOGGER_PID" >/dev/null 2>&1 || true
wait "$LOGGER_PID" >/dev/null 2>&1 || true
echo "DRRQR calibration capture complete: files=$count"
