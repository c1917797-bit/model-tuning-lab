#!/usr/bin/env bash
set -euo pipefail

image="${IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
repo_root="${REPO_ROOT:-/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_root="${OUTPUT_ROOT:-/cache/austinov/qwen35-t21-public-acl-bridge-$timestamp}"
container_name="${CONTAINER_NAME:-qwen35_t21_public_acl_bridge_build}"
source_relative="qwen35-performance-optimization/runtime-monkeypatch/native/qwen35_t21_public_acl_bridge.cpp"
builder_relative="qwen35-performance-optimization/runtime-monkeypatch/build_t21_bridge.py"
test_relative="qwen35-performance-optimization/tests/test_qwen35_t21_public_acl_bridge_source.py"

for path in "$repo_root" "$repo_root/$source_relative" "$repo_root/$builder_relative" "$repo_root/$test_relative"; do
  [[ -e "$path" ]] || { echo "required path is missing: $path" >&2; exit 64; }
done
[[ ! -e "$output_root" ]] || { echo "refusing to reuse output root: $output_root" >&2; exit 44; }
! docker container inspect "$container_name" >/dev/null 2>&1 || {
  echo "refusing to reuse existing container: $container_name" >&2
  exit 41
}

mkdir -p "$output_root"
{
  echo "scope=device-free-public-acl-pytorch-bridge-build"
  echo "image=$image"
  echo "image_id=$(docker image inspect --format '{{.Id}}' "$image")"
  echo "network=none"
  echo "device_mapping=none"
  echo "protocol_commit=$(git -C "$repo_root" rev-parse HEAD)"
  echo "source_sha256=$(sha256sum "$repo_root/$source_relative" | awk '{print $1}')"
  echo "builder_sha256=$(sha256sum "$repo_root/$builder_relative" | awk '{print $1}')"
} >"$output_root/provenance.txt"

set +e
docker run --rm --name "$container_name" \
  --network none \
  -v "$repo_root":/experiment:ro \
  -v "$output_root":/evidence \
  "$image" bash -lc '
    set -euo pipefail
    source /usr/local/Ascend/cann-9.1.0/set_env.sh
    mkdir -p /tmp/t21-build/native
    cp /experiment/qwen35-performance-optimization/runtime-monkeypatch/build_t21_bridge.py /tmp/t21-build/
    cp /experiment/qwen35-performance-optimization/runtime-monkeypatch/native/qwen35_t21_public_acl_bridge.cpp /tmp/t21-build/native/
    cd /tmp/t21-build
    python /experiment/qwen35-performance-optimization/tests/test_qwen35_t21_public_acl_bridge_source.py
    MAX_JOBS=2 python build_t21_bridge.py build_ext --inplace
    bridge="$(find . -maxdepth 1 -type f -name "qwen35_t21_bridge*.so" -print -quit)"
    [[ -n "$bridge" ]]
    python - <<"PY"
import sys
import torch_npu  # noqa: F401
sys.path.insert(0, "/tmp/t21-build")
import qwen35_t21_bridge  # noqa: F401
print("PASS: public ACL bridge imports after torch_npu")
PY
    nm -D --undefined-only "$bridge" | c++filt > /evidence/undefined-symbols.txt
    ! grep -E "NPUBridge|NPUStorageImpl" /evidence/undefined-symbols.txt
    ldd "$bridge" > /evidence/ldd.txt
    cp "$bridge" /evidence/qwen35_t21_bridge.so
    sha256sum /evidence/qwen35_t21_bridge.so > /evidence/bridge.sha256
  ' >"$output_root/build.log" 2>&1
run_rc=$?
set -e
printf '%s\n' "$run_rc" >"$output_root/exit-code.txt"
if [[ "$run_rc" -ne 0 ]]; then
  cat "$output_root/build.log" >&2
  echo "public ACL bridge build failed; evidence: $output_root" >&2
  exit "$run_rc"
fi

cat "$output_root/bridge.sha256"
echo "PASS: public ACL bridge built and private-symbol audit passed"
echo "evidence=$output_root"
