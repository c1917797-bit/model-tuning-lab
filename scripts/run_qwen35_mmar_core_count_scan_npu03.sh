#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory}"
custom_opp_root="${CUSTOM_OPP_ROOT:?set CUSTOM_OPP_ROOT to the isolated install root}"
custom_opp_env="${CUSTOM_OPP_ENV:?set CUSTOM_OPP_ENV to the vendor set_env.bash}"
operator_commit="${OPERATOR_COMMIT:?set OPERATOR_COMMIT}"
package_sha256="${PACKAGE_SHA256:?set PACKAGE_SHA256}"
core_values="${MMAR_M1_CORE_VALUES:-8 12 16 24}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
image="${VLLM_ASCEND_IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"

for path in "$output_root" "$custom_opp_root" "$custom_opp_env"; do
  case "$path" in
    /*) ;;
    *) echo "path must be absolute: $path" >&2; exit 64 ;;
  esac
done
[[ -d "$custom_opp_root" ]] || { echo "missing custom OPP root" >&2; exit 66; }
[[ -f "$custom_opp_env" ]] || { echo "missing custom OPP environment: $custom_opp_env" >&2; exit 66; }
case "$custom_opp_env" in
  "$custom_opp_root"/*) ;;
  *) echo "CUSTOM_OPP_ENV must be inside CUSTOM_OPP_ROOT" >&2; exit 64 ;;
esac
if [[ -e "$output_root" ]]; then
  echo "refusing to reuse immutable output root: $output_root" >&2
  exit 44
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU0-3 are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

mkdir -p "$output_root"
printf '%s\n' "$npu_snapshot" >"$output_root/npu-before.txt"
{
  echo "operator_commit=$operator_commit"
  echo "package_sha256=$package_sha256"
  echo "custom_opp_root=$custom_opp_root"
  echo "custom_opp_env=$custom_opp_env"
  echo "image=$image"
  echo "core_values=$core_values"
} >"$output_root/provenance.txt"

labels="default $core_values"
index=0
for label in $labels; do
  if [[ "$label" != default && ! "$label" =~ ^[0-9]+$ ]]; then
    echo "invalid AIC core count: $label" >&2
    exit 64
  fi
  container_name="qwen35_mmar_core_${label}_npu03"
  if docker container inspect "$container_name" >/dev/null 2>&1; then
    echo "refusing to replace existing container: $container_name" >&2
    exit 41
  fi
  core_args=()
  if [[ "$label" != default ]]; then
    core_args=(-e "ASCEND_MATMUL_ALLREDUCE_M1_CORE_NUM=$label")
  fi
  docker run --name "$container_name" --network host --cpuset-cpus 0-95 \
    --device /dev/davinci0 \
    --device /dev/davinci1 \
    --device /dev/davinci2 \
    --device /dev/davinci3 \
    --device /dev/davinci_manager \
    --device /dev/devmm_svm \
    --device /dev/hisi_hdc \
    -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64 \
    -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
    -v /etc/ascend_install.info:/etc/ascend_install.info \
    -v /usr/local/dcmi:/usr/local/dcmi \
    -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
    -v /cache/austinov:/cache/austinov \
    -v "$repo_root":/experiment:ro \
    -v "$custom_opp_root:$custom_opp_root:ro" \
    -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    -e HCCL_BUFFSIZE=512 \
    -e OMP_PROC_BIND=false \
    -e OMP_NUM_THREADS=1 \
    -e TASK_QUEUE_ENABLE=1 \
    -e QWEN35_MMAR_OPERATOR_COMMIT="$operator_commit" \
    -e QWEN35_MMAR_PACKAGE_SHA256="$package_sha256" \
    "${core_args[@]}" \
    "$image" \
    bash -lc "source '$custom_opp_env'; exec python3 /experiment/scripts/benchmark_qwen35_mmar_hccl_buffer.py \
      --schema qwen35-mmar-core-count-microbenchmark/v1 \
      --label '$label' \
      --output '$output_root/core-$label.json' \
      --master-port '$((29831 + index))'"
  docker logs "$container_name" >"$output_root/core-$label.log" 2>&1 || true
  docker rm "$container_name" >/dev/null
  index=$((index + 1))
done

python3 "$repo_root/scripts/evaluate_qwen35_mmar_core_count.py" \
  --root "$output_root" --minimum-speedup 1.02
sha256sum "$output_root"/*.json "$output_root"/*.log \
  "$output_root"/npu-before.txt "$output_root"/provenance.txt \
  >"$output_root/SHA256SUMS"
echo "completed MMAR M=1 core-count scan: $output_root"
