#!/usr/bin/env bash
# One owned service lifecycle; never cleans up containers by name/pattern.
set -Eeuo pipefail
label="${1:?qwen3 or qwen38}"
out="${2:?absolute fresh artifact directory}"
stage="${3:-chat}"
[[ "$stage" == performance ]] || exit 64
if [[ "$stage" == performance ]]; then
 [[ "${4:-}" =~ ^[123]$ ]] || exit 64
fi
case "$label" in
 qwen3) model_path=/cache/austinov/Qwen3-32B; model=Qwen/Qwen3-32B; extra=();;
 qwen38) model_path=/cache/austinov/Qwen3.8-27B; model=Qwen/Qwen3.8-27B; extra=(--mamba-cache-mode align --mamba-cache-dtype bfloat16 --mamba-ssm-cache-dtype bfloat16);;
 *) exit 64;;
esac
[[ "$out" == /cache/austinov/eval-runs/switch12h-* ]] || exit 64
[[ -d "$out" && ! -e "$out/status.json" ]] || exit 65
gpu_memory_utilization=0.90
max_batched_tokens=32768
if [[ "$stage" == quality || "$stage" == quality-full ]]; then
 # Prompt-logprob scoring materializes FP32 vocabulary probabilities. Reserve
 # workspace and bound prefill chunks; use the SAME quality profile for both models.
 gpu_memory_utilization=0.75
 max_batched_tokens=2048
fi
printf '{"gpu_memory_utilization":%s,"max_num_batched_tokens":%s,"stage":"%s"}\n' \
 "$gpu_memory_utilization" "$max_batched_tokens" "$stage" > "$out/server-profile.json"
code="$(cd "$(dirname "$0")" && pwd)"
image=quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a
container_id=''
evaluator_id_file=''
exec 9>/tmp/model-tuning-lab-switch-npu0-7.lock
flock -n 9 || exit 75
status() { printf '{"phase":"%s","state":"%s","updated":"%s"}\n' "$1" "$2" "$(date -u +%FT%TZ)" > "$out/status.json"; }
cleanup() {
 rc=$?; trap - EXIT INT TERM
 if [[ -n "$evaluator_id_file" && -f "$evaluator_id_file" ]]; then
  evaluator_id="$(cat "$evaluator_id_file")"
  if [[ "$evaluator_id" =~ ^[0-9a-f]{64}$ ]] && docker inspect "$evaluator_id" >/dev/null 2>&1; then
   docker logs --timestamps "$evaluator_id" > "$out/evaluator.final.log" 2>&1 || true
   docker inspect "$evaluator_id" > "$out/evaluator.final.inspect.json" || true
   docker stop --time 30 "$evaluator_id" >> "$out/cleanup.log" 2>&1 || true
  fi
 fi
 if [[ -n "$container_id" ]] && docker inspect "$container_id" >/dev/null 2>&1; then
  docker logs --timestamps "$container_id" > "$out/service.final.log" 2>&1 || true
  docker inspect "$container_id" > "$out/service.final.inspect.json" || true
  docker stop --time 60 "$container_id" >> "$out/cleanup.log" 2>&1 || true
 fi
 status complete "$([[ "$rc" == 0 ]] && echo passed || echo failed)"
 exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
npu-smi info > "$out/npu.before.txt"
[[ "$(grep -c 'No running processes found in NPU' "$out/npu.before.txt")" == 8 ]] || exit 75
[[ -z "$(ss -lntH 'sport = :10010')" ]] || exit 75
available="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)"
[[ "$available" -ge 50331648 ]] || exit 75
docker ps --no-trunc > "$out/containers.before.txt"
sha256sum "$model_path/config.json" "$model_path/tokenizer_config.json" "$model_path/tokenizer.json" "$model_path/model.safetensors.index.json" "$code/chat_benchmark.py" /cache/austinov/eval-runs/normalized-query-fGnFWXQa/data/query_rewrite.normalized.jsonl > "$out/inputs.sha256"
docker image inspect "$image" > "$out/image.inspect.json"
status startup running
container_id="$(docker run -d --rm --network host --shm-size 16g --label model-tuning-lab.task=qwen38-switch12h \
 --device /dev/davinci0 --device /dev/davinci1 --device /dev/davinci2 --device /dev/davinci3 \
 --device /dev/davinci4 --device /dev/davinci5 --device /dev/davinci6 --device /dev/davinci7 \
 --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
 -v "$model_path:/model:ro" -v /usr/local/dcmi:/usr/local/dcmi:ro \
 -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
 -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
 -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
 -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool:ro \
 -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
 -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 -e HCCL_BUFFSIZE=512 \
 -e OMP_NUM_THREADS=1 -e OMP_PROC_BIND=false -e TASK_QUEUE_ENABLE=1 \
 -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0 -e VLLM_LOGGING_LEVEL=INFO \
 "$image" vllm serve /model --host 127.0.0.1 --port 10010 --served-model-name "$model" \
 --dtype bfloat16 --tensor-parallel-size 8 --data-parallel-size 1 --seed 1024 \
 --max-num-seqs 16 --max-model-len 40960 --max-num-batched-tokens "$max_batched_tokens" \
 --trust-remote-code --gpu-memory-utilization "$gpu_memory_utilization" --enable-prefix-caching --enable-chunked-prefill \
 --disable-custom-all-reduce --async-scheduling "${extra[@]}" \
 --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,8,16,24,32]}' \
 --additional-config '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false}' \
 --default-chat-template-kwargs '{"enable_thinking":false}')"
printf '%s\n' "$container_id" > "$out/container.id"
docker logs --follow --timestamps "$container_id" > "$out/service.live.log" 2>&1 &
docker inspect "$container_id" > "$out/service.start.inspect.json"
ready=false
for i in $(seq 1 360); do
 if curl -fsS --max-time 3 http://127.0.0.1:10010/health >/dev/null 2>&1; then ready=true; break; fi
 [[ "$(docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null)" == true ]] || exit 70
 sleep 5
done
$ready || exit 70
npu-smi info > "$out/npu.ready.txt"
[[ "$(grep -c VLLMWorker_TP "$out/npu.ready.txt")" == 8 ]] || exit 70
curl -fsS http://127.0.0.1:10010/v1/models > "$out/models.json"
status canary running
python3 "$code/chat_benchmark.py" --base-url http://127.0.0.1:10010 --model "$model" \
 --dataset /cache/austinov/eval-runs/normalized-query-fGnFWXQa/data/query_rewrite.normalized.jsonl --dataset-sha256 ec22de93e406d6c0706a8bd38a1ace12a74d04f503daf3a7f3577daf9a62b2e2 \
 --concurrency 1 --repeat-index 1 --limit 32 --seed 1024 --max-output-tokens 4096 --timeout 300 \
 --cache-salt-prefix "$(basename "$out")" --output "$out/canary.json" > "$out/canary.log" 2>&1
if [[ "$stage" == performance ]]; then
 status performance_repeat running
 python3 "$code/run_normalized_performance_repeat.py" --base-url http://127.0.0.1:10010 \
  --model "$model" --dataset /cache/austinov/eval-runs/normalized-query-fGnFWXQa/data/query_rewrite.normalized.jsonl --canary "$out/canary.json" \
  --repeat "$4" --output "$out/performance" > "$out/performance.log" 2>&1
fi
