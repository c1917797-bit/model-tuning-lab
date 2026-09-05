#!/usr/bin/env bash
set -euo pipefail

mode="${1:-shortgpt-fused-tail}"
case "$mode" in
  shortgpt-retained|shortgpt-fused-tail) ;;
  *)
    echo "usage: $0 {shortgpt-retained|shortgpt-fused-tail}" >&2
    exit 64
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container_name="${CONTAINER_NAME:-qwen35_shortgpt_fused_npu4_7}"
port="${PORT:-10020}"
docker_bin="${DOCKER_BIN:-docker}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
ss_bin="${SS_BIN:-ss}"
source_root="${SHORTGPT_SOURCE_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-shortgpt-vllm}"
source_commit="${SHORTGPT_SOURCE_COMMIT:-18c4d061529d226dd0d699d9e3e1df16dadf29d7}"
fused_root="${FUSED_BUILD_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-mmar-add-rmsnorm-vllm}"
fused_source_commit=573ea2940bdc546923c698de16ea49465e6976f5
custom_extension="$fused_root/build-mmar-add-rmsnorm/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
custom_kernels="$fused_root/build-mmar-add-rmsnorm/lib/libvllm_ascend_kernels.so"
custom_extension_sha256=6006e113bf7f52ba5561d9847dbdcc6960b89eff56228d5ab584344719347d23
custom_kernels_sha256=6a9fc72a66a6055eb522a251fa48632b0ba257f22fb8f91a2deedc05e03e8b6a
model_root="${MODEL_ROOT:-/cache/austinov/Qwen3.8-27B}"
model_config_sha256="${MODEL_CONFIG_SHA256:-191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab}"
layer_set_file="${SHORTGPT_LAYER_SET_FILE:?set SHORTGPT_LAYER_SET_FILE to a frozen JSON artifact}"
layer_set_sha256="${SHORTGPT_LAYER_SET_SHA256:?set SHORTGPT_LAYER_SET_SHA256}"
reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"

if [[ ! -f "$layer_set_file" ]]; then
  echo "frozen layer-set file does not exist: $layer_set_file" >&2
  exit 44
fi
actual_layer_set_sha256="$(sha256sum "$layer_set_file" | awk '{print $1}')"
if [[ "$actual_layer_set_sha256" != "$layer_set_sha256" ]]; then
  echo "frozen layer-set hash mismatch" >&2
  exit 46
fi
mapfile -t layer_metadata < <(
  python3 - "$layer_set_file" "$source_commit" "$model_config_sha256" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
if payload.get("schema") != "qwen35-shortgpt-layer-set/v1":
    raise SystemExit("unexpected layer-set schema")
if payload.get("status") != "frozen":
    raise SystemExit("layer-set status is not frozen")
if payload.get("source_commit") != sys.argv[2]:
    raise SystemExit("layer-set source commit mismatch")
if payload.get("model_config_sha256") != sys.argv[3]:
    raise SystemExit("layer-set model config mismatch")
layers = [int(layer) for layer in payload["layers"]]
count = int(payload["removed_layer_count"])
if count not in (8, 16, 20) or len(layers) != count:
    raise SystemExit("layer-set count is not a planned point")
if layers != sorted(set(layers)) or any(layer < 0 or layer >= 64 for layer in layers):
    raise SystemExit("layer-set ids are invalid")
print(count)
print(payload["env_spec"])
PY
)
removed_layer_count="${layer_metadata[0]}"
layer_spec="${layer_metadata[1]}"

actual_source_commit="$(git -c safe.directory="$source_root" -C "$source_root" rev-parse HEAD)"
if [[ "$actual_source_commit" != "$source_commit" ]]; then
  echo "ShortGPT source must be $source_commit, got $actual_source_commit" >&2
  exit 45
fi
if [[ -n "$(git -c safe.directory="$source_root" -C "$source_root" status --porcelain --untracked-files=no)" ]]; then
  echo "ShortGPT source has tracked modifications; refusing unpinned service" >&2
  exit 45
fi
actual_fused_commit="$(git -c safe.directory="$fused_root" -C "$fused_root" rev-parse HEAD)"
if [[ "$actual_fused_commit" != "$fused_source_commit" ]]; then
  echo "fused build source must be $fused_source_commit, got $actual_fused_commit" >&2
  exit 45
fi
if [[ -n "$(git -c safe.directory="$fused_root" -C "$fused_root" status --porcelain --untracked-files=no)" ]]; then
  echo "fused build source has tracked modifications; refusing unpinned service" >&2
  exit 45
fi
if [[ "$(sha256sum "$custom_extension" | awk '{print $1}')" != "$custom_extension_sha256" ]]; then
  echo "custom extension hash mismatch" >&2
  exit 47
fi
if [[ "$(sha256sum "$custom_kernels" | awk '{print $1}')" != "$custom_kernels_sha256" ]]; then
  echo "custom kernel hash mismatch" >&2
  exit 47
fi
if [[ "$(sha256sum "$model_root/config.json" | awk '{print $1}')" != "$model_config_sha256" ]]; then
  echo "model config hash mismatch" >&2
  exit 46
fi
if "$docker_bin" container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

container_reservations="$(
  for running_id in $("$docker_bin" ps -q); do
    "$docker_bin" inspect --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$running_id"
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
  -v "$source_root/vllm_ascend/ascend_config.py:$image_source_root/ascend_config.py:ro"
  -v "$source_root/vllm_ascend/compilation/compiler_interface.py:$image_source_root/compilation/compiler_interface.py:ro"
  -v "$source_root/vllm_ascend/compilation/graph_fusion_pass_manager.py:$image_source_root/compilation/graph_fusion_pass_manager.py:ro"
  -v "$source_root/vllm_ascend/compilation/passes/decode_mmar_add_rmsnorm_fusion_pass.py:$image_source_root/compilation/passes/decode_mmar_add_rmsnorm_fusion_pass.py:ro"
  -v "$custom_extension:$image_source_root/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so:ro"
  -v "$custom_kernels:$image_source_root/lib/libvllm_ascend_kernels.so:ro"
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_BUFFSIZE=512
  -e OMP_PROC_BIND=false
  -e OMP_NUM_THREADS=1
  -e TASK_QUEUE_ENABLE=1
  -e TRITON_KERNEL_DUMP=1
  -e TRITON_DUMP_DIR=/cache/efim/triton_dump
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1=0
  -e VLLM_ASCEND_ENABLE_NZ=1
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
  -e VLLM_ASCEND_QWEN35_SKIP_LAYERS="$layer_spec"
  -e VLLM_ASCEND_QWEN35_REMOVED_LAYER_COUNT="$removed_layer_count"
  -e VLLM_ASCEND_QWEN35_LAYER_SET_SHA256="$layer_set_sha256"
  -e VLLM_ASCEND_QWEN35_SHORTGPT_COMMIT="$source_commit"
  -e VLLM_ASCEND_CUSTOM_EXTENSION_COMMIT="$fused_source_commit"
)
if [[ "$mode" == shortgpt-fused-tail ]]; then
  additional_config='{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}},"ascend_compilation_config":{"fuse_decode_mmar_add_rmsnorm":true}}'
else
  additional_config='{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
fi
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
  --enable-prefix-caching
  --mamba-cache-mode align
  --mamba-cache-dtype bfloat16
  --mamba-ssm-cache-dtype bfloat16
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY","compile_ranges_endpoints":[16,32768],"cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}'
  --additional-config "$additional_config"
  --default-chat-template-kwargs '{"enable_thinking":false}'
  --async-scheduling
)

"$docker_bin" "${docker_args[@]}" quay.io/ascend/vllm-ascend:v0.23.0 "${serve_args[@]}"
