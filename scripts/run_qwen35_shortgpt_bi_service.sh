#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container_name="${CONTAINER_NAME:-qwen35_shortgpt_bi_npu4_7}"
port="${PORT:-10020}"
docker_bin="${DOCKER_BIN:-docker}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
ss_bin="${SS_BIN:-ss}"
source_root="${SHORTGPT_SOURCE_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-shortgpt-vllm}"
source_commit="${SHORTGPT_SOURCE_COMMIT:-18c4d061529d226dd0d699d9e3e1df16dadf29d7}"
model_root="${MODEL_ROOT:-/cache/austinov/Qwen3.8-27B}"
model_config_sha256="${MODEL_CONFIG_SHA256:-191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab}"
bi_allowed_root="${BI_ALLOWED_ROOT:-/cache/austinov/eval-runs/exp-20260905-qwen35-shortgpt}"
bi_dir="${QWEN35_BI_DIR:-}"
reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"

if [[ -z "$bi_dir" ]]; then
  echo "QWEN35_BI_DIR is required" >&2
  exit 64
fi
case "$bi_dir" in
  "$bi_allowed_root"/*) ;;
  *)
    echo "QWEN35_BI_DIR must be below $bi_allowed_root" >&2
    exit 64
    ;;
esac
if [[ -e "$bi_dir" ]]; then
  echo "refusing to reuse Block Influence directory: $bi_dir" >&2
  exit 44
fi

actual_source_commit="$(
  git -c safe.directory="$source_root" -C "$source_root" rev-parse HEAD
)"
if [[ "$actual_source_commit" != "$source_commit" ]]; then
  echo "ShortGPT source must be $source_commit, got $actual_source_commit" >&2
  exit 45
fi
actual_model_hash="$(sha256sum "$model_root/config.json" | awk '{print $1}')"
if [[ "$actual_model_hash" != "$model_config_sha256" ]]; then
  echo "model config hash mismatch: $actual_model_hash" >&2
  exit 46
fi
if "$docker_bin" container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

container_reservations="$(
  for running_id in $("$docker_bin" ps -q); do
    "$docker_bin" inspect "$running_id" --format +      '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}'
  done | awk -v ignored_csv="$reservation_ignore_names" '
    BEGIN {
      split(ignored_csv, ignored_names, ",")
      for (item in ignored_names) {
        ignored[ignored_names[item]] = 1
      }
    }
    $0 ~ /\/dev\/davinci[4-7]([[:space:]]|$)/ && !($1 in ignored)
  '
)"
if [[ -n "$container_reservations" ]]; then
  echo "refusing to start: a running container reserves physical NPU4-7" >&2
  echo "$container_reservations" >&2
  exit 48
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[4-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU4-7 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi
if command -v "$ss_bin" >/dev/null 2>&1 &&
    "$ss_bin" -lntH | awk -v port="$port" '
      $4 ~ (":" port "$") { found = 1 }
      END { exit(found ? 0 : 1) }
    '; then
  echo "refusing to start: port $port is already listening" >&2
  exit 43
fi

mkdir -p "$bi_dir"
image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
docker_args=(
  run -d
  --name "$container_name"
  --network host
  --cpuset-cpus 0-95
  --device /dev/davinci4:/dev/davinci0
  --device /dev/davinci5:/dev/davinci1
  --device /dev/davinci6:/dev/davinci2
  --device /dev/davinci7:/dev/davinci3
  --device /dev/davinci_manager
  --device /dev/devmm_svm
  --device /dev/hisi_hdc
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info
  -v /etc/ascend_install.info:/etc/ascend_install.info
  -v /usr/local/dcmi:/usr/local/dcmi
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi
  -v /cache/austinov:/cache/austinov
  -v /cache/cch:/cache/cch:ro
  -v "$repo_root":/experiment:ro
  -v "$source_root/vllm_ascend/patch/worker/patch_qwen3_5.py:$image_source_root/patch/worker/patch_qwen3_5.py:ro"
  -v "$source_root/vllm_ascend/patch/worker/qwen35_shortgpt.py:$image_source_root/patch/worker/qwen35_shortgpt.py:ro"
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_BUFFSIZE=512
  -e OMP_PROC_BIND=false
  -e OMP_NUM_THREADS=1
  -e TASK_QUEUE_ENABLE=1
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0
  -e VLLM_ASCEND_ENABLE_NZ=1
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
  -e VLLM_ASCEND_QWEN35_BI_DIR="$bi_dir"
  -e VLLM_ASCEND_QWEN35_BI_MIN_TOKENS=17
  -e VLLM_ASCEND_QWEN35_BI_MAX_SAMPLES=256
)
serve_args=(
  vllm serve "$model_root"
  --host 127.0.0.1
  --port "$port"
  --tensor-parallel-size 4
  --data-parallel-size 1
  --seed 1024
  --served-model-name Qwen3-5/Qwen3.5-27B
  --max-num-seqs 16
  --max-model-len 133000
  --max-num-batched-tokens 32768
  --trust-remote-code
  --gpu-memory-utilization 0.90
  --mamba-cache-mode align
  --mamba-cache-dtype bfloat16
  --mamba-ssm-cache-dtype bfloat16
  --additional-config '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
  --default-chat-template-kwargs '{"enable_thinking":false}'
  --enforce-eager
  --no-async-scheduling
)

"$docker_bin" "${docker_args[@]}" +  quay.io/ascend/vllm-ascend:v0.23.0 "${serve_args[@]}"
