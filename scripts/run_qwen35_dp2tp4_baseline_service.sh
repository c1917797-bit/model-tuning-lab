#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config="${CONFIG:-$repo_root/configs/qwen35-query-rewrite-baseline.yaml}"
container_name="${CONTAINER_NAME:?set a new unique CONTAINER_NAME}"
manifest_path="${MANIFEST_PATH:?set a new immutable MANIFEST_PATH}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
docker_bin="${DOCKER_BIN:-docker}"
image="quay.io/ascend/vllm-ascend:v0.23.0"

case "$manifest_path" in
  /*) ;;
  *) echo "MANIFEST_PATH must be absolute" >&2; exit 64 ;;
esac
if [[ -e "$manifest_path" ]]; then
  echo "refusing to replace runtime manifest: $manifest_path" >&2
  exit 44
fi
if "$docker_bin" container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' '
    $2 ~ /^[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      print "NPU" substr($2, 1, 1) ":pid=" $3
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: NPU0-7 are not exclusively idle" >&2
  echo "$occupied" >&2
  exit 42
fi

python3 "$repo_root/scripts/render_qwen35_runtime.py" --config "$config" --output "$manifest_path"

mapfile -d '' runtime_env < <(
  python3 -c '
import json, sys
payload=json.load(open(sys.argv[1]))
for key, value in sorted(payload["environment"].items()):
    sys.stdout.buffer.write(f"{key}={value}".encode() + b"\0")
' "$manifest_path"
)
mapfile -d '' runtime_argv < <(
  python3 -c '
import json, sys
payload=json.load(open(sys.argv[1]))
for value in payload["argv"]:
    sys.stdout.buffer.write(str(value).encode() + b"\0")
' "$manifest_path"
)

docker_args=(
  run -d
  --name "$container_name"
  --network host
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
)
for index in {0..7}; do
  docker_args+=(--device "/dev/davinci$index")
done
for item in "${runtime_env[@]}"; do
  docker_args+=(-e "$item")
done

"$docker_bin" "${docker_args[@]}" "$image" "${runtime_argv[@]}"
