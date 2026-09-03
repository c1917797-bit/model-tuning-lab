#!/usr/bin/env bash
set -euo pipefail

PHYSICAL_NPU="${1:-0}"
IMAGE="${PAPER_TO_ASCEND_IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARTIFACT_DIR="${PAPER_TO_ASCEND_ARTIFACT_DIR:-/cache/austinov/paper-to-ascend/dynamic-moe-block-ab/${STAMP}}"

if [[ ! -e "/dev/davinci${PHYSICAL_NPU}" ]]; then
  echo "missing /dev/davinci${PHYSICAL_NPU}" >&2
  exit 2
fi

mkdir -p "${ARTIFACT_DIR}"
echo "Dynamic MoE block A/B: physical NPU${PHYSICAL_NPU} -> container npu:0" >&2
echo "Artifact: ${ARTIFACT_DIR}/result.json" >&2
echo "Caller must live-check that the physical NPU is free before this run." >&2

docker run --rm \
  --name "dynamic_moe_block_ab_${PHYSICAL_NPU}" \
  --device="/dev/davinci${PHYSICAL_NPU}:/dev/davinci0" \
  --device=/dev/davinci_manager:/dev/davinci_manager \
  --device=/dev/devmm_svm:/dev/devmm_svm \
  --device=/dev/hisi_hdc:/dev/hisi_hdc \
  -e ASCEND_RT_VISIBLE_DEVICES=0 \
  -e PYTORCH_NPU_ALLOC_CONF=expandable_segments:True \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64 \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v "${ROOT}:/workspace:ro" \
  -v "${ARTIFACT_DIR}:/artifacts" \
  -w /workspace \
  "${IMAGE}" \
  python scripts/paper_to_ascend/dynamic_moe_block_ab.py \
    --device npu:0 \
    --experts "${DYNAMIC_MOE_EXPERTS:-8}" \
    --hidden-size "${DYNAMIC_MOE_HIDDEN_SIZE:-2048}" \
    --intermediate-size "${DYNAMIC_MOE_INTERMEDIATE_SIZE:-768}" \
    --top-p "${DYNAMIC_MOE_TOP_P:-0.4}" \
    --warmup "${DYNAMIC_MOE_WARMUP:-20}" \
    --iterations "${DYNAMIC_MOE_ITERATIONS:-100}" \
    --repetitions "${DYNAMIC_MOE_REPETITIONS:-5}" \
    --tokens ${DYNAMIC_MOE_TOKEN_COUNTS:-128 512 2048 4096} \
    --output /artifacts/result.json

sha256sum "${ARTIFACT_DIR}/result.json" | tee "${ARTIFACT_DIR}/result.sha256"
echo "RESULT_PATH=${ARTIFACT_DIR}/result.json"
