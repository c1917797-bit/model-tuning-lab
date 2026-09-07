#!/usr/bin/env bash
set -euo pipefail

OUTPUT=/cache/cch/state-reduction-qwen36-formal-npu4-7-tp4-20260906/smoke-dk96
MODEL=/cache/cch/Qwen3.6-27B-gdn-drrqr-dk96
CONTAINER=qwen36_drrqr_dk96_smoke_npu4_7
IMAGE=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
PORT=8225

cleanup() {
  if docker inspect "$CONTAINER" >/dev/null 2>&1; then
    docker stop --time 30 "$CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

test "$(sha256sum "$MODEL/drrqr_manifest.json" | awk '{print $1}')" = a8f8f162f15fb6e4717ed509927d93c549a2ef01eca4c88e45e75cdf900b16fc
for device in 4 5 6 7; do
  output="$(npu-smi info -t proc-mem -i "$device")"
  grep -q "No process in device" <<<"$output" || {
    echo "host NPU $device is not empty" >&2
    exit 2
  }
done
if ss -ltn | grep -qE ":$PORT[[:space:]]"; then
  echo "port $PORT is already in use" >&2
  exit 2
fi
if docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "container already exists: $CONTAINER" >&2
  exit 2
fi
mkdir -p "$OUTPUT"

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
  -v /cache/cch:/cache/cch:ro
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_OP_EXPANSION_MODE=AIV
  -e HCCL_NPU_SOCKET_PORT_RANGE=26910-27010
  -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
  -e TASK_QUEUE_ENABLE=1
  -e OMP_NUM_THREADS=1
  "$IMAGE"
  vllm serve "$MODEL"
  --served-model-name qwen36-drrqr-dk96
  --host 127.0.0.1
  --port "$PORT"
  --data-parallel-size 1
  --tensor-parallel-size 4
  --max-model-len 40960
  --max-num-batched-tokens 16384
  --max-num-seqs 16
  --gpu-memory-utilization 0.9
  --no-enable-prefix-caching
  --compilation-config '{"cudagraph_capture_sizes":[1,4,8,12,16,24,32,48,56,64,72,84,96,108,112,128,160,172,196,200,212,232,272,288,312,328,344,360,384,400,416,432,448,480,512],"cudagraph_mode":"FULL_DECODE_ONLY"}'
  --trust-remote-code
  --async-scheduling
)
docker "${docker_args[@]}" >"$OUTPUT/container-id.txt"

docker inspect "$CONTAINER" --format 'status={{.State.Status}} cpuset={{.HostConfig.CpusetCpus}} memory={{.HostConfig.Memory}} devices={{json .HostConfig.Devices}} image={{.Image}}' >"$OUTPUT/container-inspect-before-start.txt"
docker start "$CONTAINER" >/dev/null
docker logs -f "$CONTAINER" >"$OUTPUT/service.log" 2>&1 &
logger_pid=$!

ready=0
for _ in $(seq 1 180); do
  if curl -fsS "http://127.0.0.1:$PORT/v1/models" >"$OUTPUT/health.json" 2>/dev/null; then
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

curl_args=(
  -fsS "http://127.0.0.1:$PORT/v1/chat/completions"
  -H 'Content-Type: application/json'
  -d '{"model":"qwen36-drrqr-dk96","messages":[{"role":"user","content":"Return exactly: ASCEND_DRRQR_OK"}],"temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":false}}'
)
curl "${curl_args[@]}" >"$OUTPUT/completion.json"
python3 -c 'import json,sys; x=json.load(open(sys.argv[1])); assert x["choices"][0]["message"]["content"].strip() == "ASCEND_DRRQR_OK"' "$OUTPUT/completion.json"
docker inspect "$CONTAINER" --format 'status={{.State.Status}} oom={{.State.OOMKilled}} exit={{.State.ExitCode}} error={{json .State.Error}}' >"$OUTPUT/container-inspect-after-smoke.txt"
kill "$logger_pid" >/dev/null 2>&1 || true
wait "$logger_pid" >/dev/null 2>&1 || true
echo "DRRQR dk96 load and exact completion smoke passed"
