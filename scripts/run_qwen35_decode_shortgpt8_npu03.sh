#!/usr/bin/env bash
set -euo pipefail

readonly container_name="qwen35_decode_shortgpt8_npu03_v1"
readonly image="quay.io/ascend/vllm-ascend:v0.23.0"
readonly adapter_root="/cache/cch/.worktrees/exp-20260906-qwen35-decode-shortgpt-ascend"

test "$(git -C "${adapter_root}" rev-parse HEAD)" = \
  "0f28129ef8716c36999d63796061cc654d854306"
test -z "$(git -C "${adapter_root}" status --porcelain)"
if docker inspect "${container_name}" >/dev/null 2>&1; then
  echo "refusing to replace existing container ${container_name}" >&2
  exit 64
fi

exec docker run -d \
  --name "${container_name}" \
  --network host \
  --device /dev/davinci0 \
  --device /dev/davinci1 \
  --device /dev/davinci2 \
  --device /dev/davinci3 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
  -e HCCL_BUFFSIZE=512 \
  -e OMP_PROC_BIND=false \
  -e OMP_NUM_THREADS=1 \
  -e TASK_QUEUE_ENABLE=1 \
  -e TRITON_KERNEL_DUMP=1 \
  -e TRITON_DUMP_DIR=/cache/efim/triton_dump \
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 \
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0 \
  -e VLLM_ASCEND_ENABLE_NZ=1 \
  -e VLLM_ASCEND_ENABLE_DENSE_FFN_NZ=0 \
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1 \
  -e VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1 \
  -e VLLM_ASCEND_QWEN35_DECODE_SKIP_LAYERS=3-5,7-9,12-13 \
  -e VLLM_ASCEND_QWEN35_DECODE_SHORTGPT_COMMIT=0f28129ef8716c36999d63796061cc654d854306 \
  -e VLLM_ASCEND_QWEN35_GDN_PROJ_FUSION_ASCEND_COMMIT=d98e37ebb72acd71b5a35222fd7ab7f8049d41cb \
  -e VLLM_ASCEND_QWEN35_GDN_PREFETCH_COMMIT=82a2dce763eb39c285744f6fc36e37728471a1c7 \
  -e VLLM_ASCEND_QWEN35_GDN_PROJ_FUSION_COMMIT=685fdf22098fb3a0aa8d582dda57063773606a02 \
  -e VLLM_LOGGING_LEVEL=DEBUG \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64 \
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v /cache/austinov:/cache/austinov \
  -v /cache/cch:/cache/cch:ro \
  -v /opt/host/vnf/austinov/worktrees/exp-20260904-qwen35-query-rewrite-3x-e2e:/experiment:ro \
  -v /cache/cch/.worktrees/exp-20260906-qwen35-gdn-projection-fusion-ascend/vllm_ascend/ops/gdn.py:/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py:ro \
  -v /cache/cch/.worktrees/exp-20260906-qwen35-gdn-gateup-prefetch/vllm_ascend/ops/weight_prefetch.py:/vllm-workspace/vllm-ascend/vllm_ascend/ops/weight_prefetch.py:ro \
  -v /cache/cch/.worktrees/exp-20260906-qwen35-gdn-gateup-prefetch/vllm_ascend/ops/layernorm.py:/vllm-workspace/vllm-ascend/vllm_ascend/ops/layernorm.py:ro \
  -v "${adapter_root}/vllm_ascend/patch/worker/patch_qwen3_5.py:/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py:ro" \
  -v "${adapter_root}/vllm_ascend/patch/worker/qwen35_decode_shortgpt.py:/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/qwen35_decode_shortgpt.py:ro" \
  -v /cache/cch/.worktrees/exp-20260906-qwen35-gdn-projection-fusion/vllm/model_executor/models/qwen3_5.py:/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py:ro \
  -v /cache/cch/.worktrees/exp-20260906-qwen35-gdn-projection-fusion/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py:/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py:ro \
  "${image}" \
  vllm serve /cache/austinov/Qwen3.8-27B \
  --host 127.0.0.1 \
  --port 10012 \
  --tensor-parallel-size 4 \
  --pipeline-parallel-size 1 \
  --data-parallel-size 1 \
  --seed 1024 \
  --served-model-name Qwen3-5/Qwen3.5-27B \
  --max-num-seqs 16 \
  --max-model-len 133000 \
  --max-num-batched-tokens 32768 \
  --trust-remote-code \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching \
  --mamba-cache-mode align \
  --mamba-cache-dtype bfloat16 \
  --mamba-ssm-cache-dtype bfloat16 \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}' \
  --additional-config '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}' \
  --default-chat-template-kwargs '{"enable_thinking":false}' \
  --async-scheduling
