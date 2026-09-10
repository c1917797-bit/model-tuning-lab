#!/usr/bin/env bash
# Start the weight-fidelity BF16-compute reference on physical NPU0-3 only.
# This is a correctness reference, not a native FP4 acceleration claim.
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a}"
model_path="${MODEL_PATH:-/cache/cch/Qwen3.8-27B-NVFP4}"
tokenizer_path="${TOKENIZER_PATH:-/cache/austinov/Qwen3.8-27B}"
patch_path="${PATCH_PATH:-$(cd "$(dirname "$0")" && pwd)}"
artifact_root="${ARTIFACT_ROOT:?set ARTIFACT_ROOT outside Git}"
port="${PORT:-10110}"
name="${CONTAINER_NAME:-qwen38_nvfp4_reference_tp4_$(date -u +%Y%m%dT%H%M%SZ)}"

case "${port}" in ''|*[!0-9]*) echo "PORT must be numeric" >&2; exit 64 ;; esac
[[ -d "${model_path}" ]] || { echo "missing MODEL_PATH: ${model_path}" >&2; exit 66; }
[[ -f "${tokenizer_path}/tokenizer.json" ]] || { echo "missing TOKENIZER_PATH: ${tokenizer_path}" >&2; exit 66; }
[[ -f "${patch_path}/pyproject.toml" ]] || { echo "invalid PATCH_PATH: ${patch_path}" >&2; exit 66; }
mkdir -p "${artifact_root}"

exec docker run --detach --rm \
  --name "${name}" --network host --shm-size=800g \
  --device=/dev/davinci0 --device=/dev/davinci1 \
  --device=/dev/davinci2 --device=/dev/davinci3 \
  --device=/dev/davinci_manager --device=/dev/devmm_svm --device=/dev/hisi_hdc \
  --mount "type=bind,src=${model_path},dst=/model,readonly" \
  --mount "type=bind,src=${tokenizer_path},dst=/tokenizer,readonly" \
  --mount "type=bind,src=${patch_path},dst=/readonly/qwen38-nvfp4-ascend,readonly" \
  --mount "type=bind,src=${artifact_root},dst=/artifacts" \
  --mount type=bind,src=/usr/local/dcmi,dst=/usr/local/dcmi,readonly \
  --mount type=bind,src=/usr/local/bin/npu-smi,dst=/usr/local/bin/npu-smi,readonly \
  --mount type=bind,src=/usr/local/Ascend/driver/lib64,dst=/usr/local/Ascend/driver/lib64,readonly \
  --mount type=bind,src=/usr/local/Ascend/driver/version.info,dst=/usr/local/Ascend/driver/version.info,readonly \
  --mount type=bind,src=/etc/ascend_install.info,dst=/etc/ascend_install.info,readonly \
  --env ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 --env QWEN38_ENABLE_BF16_REFERENCE=1 \
  --env PORT="${port}" --env HCCL_BUFFSIZE=512 --env OMP_PROC_BIND=false \
  --env OMP_NUM_THREADS=1 --env TASK_QUEUE_ENABLE=1 \
  --env VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 --env VLLM_ASCEND_PTO_CHUNK_GDN=1 \
  --env VLLM_LOGGING_LEVEL=DEBUG "${image}" \
  bash /readonly/qwen38-nvfp4-ascend/reference_container_entrypoint.sh
