#!/usr/bin/env bash
# Start the BF16 control on physical NPU0-3 only after the maintainer gates pass.
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a}"
model_path="${MODEL_PATH:-/cache/austinov/Qwen3.8-27B}"
artifact_root="${ARTIFACT_ROOT:?set ARTIFACT_ROOT outside Git}"
port="${PORT:-10110}"
name="${CONTAINER_NAME:-qwen38_bf16_tp4_$(date -u +%Y%m%dT%H%M%SZ)}"

case "${port}" in ''|*[!0-9]*) echo "PORT must be numeric" >&2; exit 64 ;; esac
[[ -d "${model_path}" ]] || { echo "missing MODEL_PATH: ${model_path}" >&2; exit 66; }
mkdir -p "${artifact_root}"

exec docker run --detach --rm \
  --name "${name}" --network host --shm-size=800g \
  --device=/dev/davinci0 --device=/dev/davinci1 \
  --device=/dev/davinci2 --device=/dev/davinci3 \
  --device=/dev/davinci_manager --device=/dev/devmm_svm --device=/dev/hisi_hdc \
  --mount "type=bind,src=${model_path},dst=/model,readonly" \
  --mount "type=bind,src=${artifact_root},dst=/artifacts" \
  --mount type=bind,src=/usr/local/dcmi,dst=/usr/local/dcmi,readonly \
  --mount type=bind,src=/usr/local/bin/npu-smi,dst=/usr/local/bin/npu-smi,readonly \
  --mount type=bind,src=/usr/local/Ascend/driver/lib64,dst=/usr/local/Ascend/driver/lib64,readonly \
  --mount type=bind,src=/usr/local/Ascend/driver/version.info,dst=/usr/local/Ascend/driver/version.info,readonly \
  --mount type=bind,src=/etc/ascend_install.info,dst=/etc/ascend_install.info,readonly \
  --env ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
  --env HCCL_BUFFSIZE=512 --env OMP_PROC_BIND=false --env OMP_NUM_THREADS=1 \
  --env TASK_QUEUE_ENABLE=1 --env VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 \
  --env VLLM_ASCEND_PTO_CHUNK_GDN=1 --env VLLM_LOGGING_LEVEL=DEBUG \
  "${image}" vllm serve /model \
  --host 127.0.0.1 --port "${port}" --tensor-parallel-size 4 --seed 1024 \
  --served-model-name Qwen3.8-27B --max-num-seqs 16 --max-model-len 32768 \
  --max-num-batched-tokens 32768 --trust-remote-code --gpu-memory-utilization 0.90 \
  --enable-prefix-caching --mamba-cache-mode align \
  --additional-config '{"enable_cpu_binding":true}' \
  --default-chat-template-kwargs '{"enable_thinking":false}' \
  --mamba-cache-dtype bfloat16 --mamba-ssm-cache-dtype bfloat16 --async-scheduling
