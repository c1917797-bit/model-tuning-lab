#!/usr/bin/env bash
set -euo pipefail

PHYSICAL_NPU="${1:-0}"
IMAGE="${PAPER_TO_ASCEND_IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ ! -e "/dev/davinci${PHYSICAL_NPU}" ]]; then
  echo "missing /dev/davinci${PHYSICAL_NPU}" >&2
  exit 2
fi

echo "Paper-to-Ascend Dynamic MoE smoke: physical NPU${PHYSICAL_NPU} -> container npu:0" >&2
echo "Live-check npu-smi before running; this script does not override another workstream's resource lease." >&2

docker run --rm \
  --name "dynamic_moe_router_smoke_${PHYSICAL_NPU}" \
  --device="/dev/davinci${PHYSICAL_NPU}:/dev/davinci0" \
  --device=/dev/davinci_manager:/dev/davinci_manager \
  --device=/dev/devmm_svm:/dev/devmm_svm \
  --device=/dev/hisi_hdc:/dev/hisi_hdc \
  -e ASCEND_RT_VISIBLE_DEVICES=0 \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64 \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v "${ROOT}:/workspace:ro" \
  -w /workspace \
  "${IMAGE}" \
  python scripts/paper_to_ascend/dynamic_moe_npu_smoke.py \
    --device npu:0 \
    --experts "${DYNAMIC_MOE_EXPERTS:-8}" \
    --tokens "${DYNAMIC_MOE_TOKENS:-4096}" \
    --top-p "${DYNAMIC_MOE_TOP_P:-0.4}" \
    --warmup "${DYNAMIC_MOE_WARMUP:-20}" \
    --iterations "${DYNAMIC_MOE_ITERATIONS:-50}"
