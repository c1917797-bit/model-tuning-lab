#!/usr/bin/env bash
set -euo pipefail

# Runtime-only Qwen3.5 GDN projection-fusion activation on physical NPU0-3.
# Keep this process alive for the full service lifetime so fd 9 owns the
# cooperative lease until the one-shot container exits.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
patch_root="$repo_root/qwen35-performance-optimization/runtime-monkeypatch"
patch_file="$patch_root/sitecustomize.py"
patch_sha256=45dbb02879989244e833e525694e7aeeeca4b8768c327ab20e3041055b773640
image_ref=quay.io/ascend/vllm-ascend:v0.23.0
image_id=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
image_digest=quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a
operator_feature_env=ASCEND_MATMUL_ALLREDUCE_M1_AICPU_FIRST
operator_commit=41515133cadc7e2de54bb6f2297887bfefc7e4ad
operator_package_sha256=8e22ab5d7b0c5b7eb88a393bc452a60fc377df434e1b8f70986a48723b67c84a
operator_tree_sha256=d324d27a6bb0c957af968d83f8642b94bfb6cb56f9ad0f8402313fb65b434edb
operator_vendor=qwen35_mmar_aicpu_first_transformer_transformer
operator_container_root=/opt/qwen35-mmar-aicpu-first-opp
operator_container_vendor="$operator_container_root/vendors/$operator_vendor"
variant="${VARIANT:-candidate}"
case "$variant" in
  candidate) patch_enabled=1 ;;
  control) patch_enabled=0 ;;
  *) echo "VARIANT must be candidate or control" >&2; exit 64 ;;
esac
container_name="${CONTAINER_NAME:-qwen35_gdn_runtime_t12_${variant}_npu03}"
port="${PORT:-10010}"
lease_path="${NPU_LEASE_PATH:-/cache/austinov/.locks/npu0-3.lock}"
minimum_mem_available_kb="${MIN_MEM_AVAILABLE_KB:-50331648}"
enable_dynamic_profiling="${ENABLE_DYNAMIC_PROFILING:-0}"
profile_dir="${PROFILE_DIR:-}"
qwen35_diagnostics="${QWEN35_ASCEND_DIAGNOSTICS:-0}"
qwen35_diagnostics_interval="${QWEN35_ASCEND_DIAGNOSTICS_INTERVAL:-32}"
: "${OUTPUT_ROOT:?set OUTPUT_ROOT to a new directory under /cache/austinov}"

case "$OUTPUT_ROOT" in
  /cache/austinov/*) ;;
  *) echo "OUTPUT_ROOT must be under /cache/austinov" >&2; exit 64 ;;
esac
[[ ! -e "$OUTPUT_ROOT" ]] || {
  echo "refusing to reuse OUTPUT_ROOT: $OUTPUT_ROOT" >&2
  exit 44
}
case "$enable_dynamic_profiling" in
  0) [[ -z "$profile_dir" ]] || {
       echo "PROFILE_DIR requires ENABLE_DYNAMIC_PROFILING=1" >&2
       exit 64
     } ;;
  1)
    case "$profile_dir" in
      /cache/austinov/*) ;;
      *) echo "PROFILE_DIR must be a new directory under /cache/austinov" >&2; exit 64 ;;
    esac
    [[ ! -e "$profile_dir" ]] || {
      echo "refusing to reuse PROFILE_DIR: $profile_dir" >&2
      exit 44
    }
    ;;
  *) echo "ENABLE_DYNAMIC_PROFILING must be 0 or 1" >&2; exit 64 ;;
esac
case "$qwen35_diagnostics" in
  0|1) ;;
  *) echo "QWEN35_ASCEND_DIAGNOSTICS must be 0 or 1" >&2; exit 64 ;;
esac
[[ "$qwen35_diagnostics_interval" =~ ^[0-9]+$ && "$qwen35_diagnostics_interval" -ge 1 ]] || {
  echo "QWEN35_ASCEND_DIAGNOSTICS_INTERVAL must be a positive integer" >&2
  exit 64
}
[[ "$port" =~ ^[0-9]+$ ]] || { echo "invalid PORT: $port" >&2; exit 64; }
[[ -f "$patch_file" ]] || { echo "missing runtime patch: $patch_file" >&2; exit 66; }
[[ "$(sha256sum "$patch_file" | awk '{print $1}')" == "$patch_sha256" ]] || {
  echo "runtime patch SHA256 mismatch" >&2
  exit 47
}
[[ "$(docker image inspect "$image_ref" --format '{{.Id}}')" == "$image_id" ]] || {
  echo "base image ID mismatch" >&2
  exit 47
}
actual_image_digests="$(docker image inspect "$image_ref" --format '{{range .RepoDigests}}{{println .}}{{end}}')"
grep -Fxq "$image_digest" <<<"$actual_image_digests" || {
  echo "base image digest mismatch" >&2
  exit 47
}
operator_mount_args=()
operator_env_args=()
operator_feature_label=disabled
operator_commit_label=official-stock
operator_package_label=not-applicable
if [[ "$variant" == candidate ]]; then
  : "${CANDIDATE_OPP_ROOT:?set CANDIDATE_OPP_ROOT for candidate}"
  : "${CANDIDATE_OPERATOR_COMMIT:?set CANDIDATE_OPERATOR_COMMIT for candidate}"
  : "${CANDIDATE_PACKAGE_SHA256:?set CANDIDATE_PACKAGE_SHA256 for candidate}"
  [[ "$CANDIDATE_OPERATOR_COMMIT" == "$operator_commit" ]] || {
    echo "candidate operator commit mismatch" >&2
    exit 47
  }
  [[ "$CANDIDATE_PACKAGE_SHA256" == "$operator_package_sha256" ]] || {
    echo "candidate operator package SHA256 mismatch" >&2
    exit 47
  }
  [[ -f "$CANDIDATE_OPP_ROOT/vendors/$operator_vendor/bin/set_env.bash" ]] || {
    echo "candidate OPP layout is incomplete" >&2
    exit 66
  }
  actual_operator_tree_sha256="$(
    find "$CANDIDATE_OPP_ROOT" -type f -print0 |
      sort -z |
      xargs -0 sha256sum |
      sha256sum |
      awk '{print $1}'
  )"
  [[ "$actual_operator_tree_sha256" == "$operator_tree_sha256" ]] || {
    echo "candidate OPP tree SHA256 mismatch" >&2
    exit 47
  }
  image_ld_library_path="$(
    docker image inspect "$image_ref" --format '{{range .Config.Env}}{{println .}}{{end}}' |
      sed -n 's/^LD_LIBRARY_PATH=//p'
  )"
  operator_mount_args=(-v "$CANDIDATE_OPP_ROOT:$operator_container_root:ro")
  operator_env_args=(
    -e "ASCEND_CUSTOM_OPP_PATH=$operator_container_vendor"
    -e "LD_LIBRARY_PATH=$operator_container_vendor/op_api/lib:${image_ld_library_path}"
    -e "$operator_feature_env=1"
    -e "QWEN35_MMAR_OPERATOR_COMMIT=$operator_commit"
    -e "QWEN35_MMAR_PACKAGE_SHA256=$operator_package_sha256"
  )
  operator_feature_label="$operator_feature_env"
  operator_commit_label="$operator_commit"
  operator_package_label="$operator_package_sha256"
fi
[[ -f /cache/austinov/Qwen3.8-27B/config.json ]] || {
  echo "missing frozen Qwen3.5-27B model" >&2
  exit 66
}
docker container inspect "$container_name" >/dev/null 2>&1 && {
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
}
ss -ltnH "sport = :$port" | grep -q . && {
  echo "refusing to use occupied port: $port" >&2
  exit 46
}

mkdir -p "$(dirname "$lease_path")"
exec 9>"$lease_path"
flock -n 9 || { echo "NPU0-3 cooperative lease is held" >&2; exit 49; }

container_reservations="$(
  for running_id in $(docker ps -q); do
    docker inspect --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$running_id"
  done | awk '
    /\/dev\/davinci0([[:space:]]|$)|\/dev\/davinci1([[:space:]]|$)|\/dev\/davinci2([[:space:]]|$)|\/dev\/davinci3([[:space:]]|$)/ { print }
  '
)"
[[ -z "$container_reservations" ]] || {
  echo "refusing to start: a running container reserves physical NPU0-3" >&2
  echo "$container_reservations" >&2
  exit 48
}

npu_snapshot="$(npu-smi info)"
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
[[ -z "$occupied" ]] || {
  echo "refusing to start: physical NPU0-3 are not idle" >&2
  echo "$occupied" >&2
  exit 42
}

mem_available_kb="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)"
[[ "$mem_available_kb" -ge "$minimum_mem_available_kb" ]] || {
  echo "refusing to start: MemAvailable ${mem_available_kb}kB is below ${minimum_mem_available_kb}kB" >&2
  exit 50
}

mkdir -p "$OUTPUT_ROOT"
profile_mount_args=()
profile_env_args=()
if [[ "$enable_dynamic_profiling" == 1 ]]; then
  mkdir -p "$profile_dir"
  profile_mount_args=(-v "$profile_dir:/profile:rw")
  profile_env_args=(-e PROFILING_MODE=dynamic)
fi
printf '%s\n' "$variant" >"$OUTPUT_ROOT/variant.txt"
printf '%s\n' "$patch_sha256  $patch_file" >"$OUTPUT_ROOT/patch.sha256"
printf '%s\n' "$image_id" >"$OUTPUT_ROOT/image-id.before.txt"
printf '%s\n' "$image_digest" >"$OUTPUT_ROOT/image-digest.before.txt"
git -C "$repo_root" rev-parse HEAD >"$OUTPUT_ROOT/repository-commit.txt"
{
  echo "feature=$operator_feature_label"
  echo "operator_commit=$operator_commit_label"
  echo "package_sha256=$operator_package_label"
  echo "expected_tree_sha256=$operator_tree_sha256"
  echo "loading=relocated read-only OPP; packaged set_env.bash is not sourced"
} >"$OUTPUT_ROOT/operator-opp.txt"
docker ps --no-trunc >"$OUTPUT_ROOT/docker-ps.before.txt"
printf '%s\n' "$npu_snapshot" >"$OUTPUT_ROOT/npu-smi.before.txt"
ss -lntp >"$OUTPUT_ROOT/ports.before.txt"
grep -E '^(MemTotal|MemAvailable|HugePages_|Hugepagesize|Hugetlb):' /proc/meminfo >"$OUTPUT_ROOT/meminfo.before.txt"

compilation_config='{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}'
additional_config='{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
python_path='/opt/qwen35-t12-monkeypatch:/usr/local/Ascend/ascend-toolkit/latest/python/site-packages:/usr/local/Ascend/ascend-toolkit/latest/opp/built-in/op_impl/ai_core/tbe:/usr/local/Ascend/cann-9.1.0/python/site-packages:/usr/local/Ascend/cann-9.1.0/opp/built-in/op_impl/ai_core/tbe:'

docker_args=(
  run -d --rm
  --name "$container_name"
  --label com.c1917797.qwen35-t12=1
  --label com.c1917797.qwen35-variant="$variant"
  --label com.c1917797.qwen35-output-root="$OUTPUT_ROOT"
  --label com.c1917797.qwen35-operator-feature="$operator_feature_label"
  --label com.c1917797.qwen35-operator-commit="$operator_commit_label"
  --label com.c1917797.qwen35-operator-package-sha256="$operator_package_label"
  --network host
  --shm-size 64g
  --cpuset-cpus 0-95
  --device /dev/davinci0
  --device /dev/davinci1
  --device /dev/davinci2
  --device /dev/davinci3
  --device /dev/davinci_manager
  --device /dev/devmm_svm
  --device /dev/hisi_hdc
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro
  -v /usr/local/dcmi:/usr/local/dcmi:ro
  -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool:ro
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro
  -v /cache/austinov/Qwen3.8-27B:/cache/austinov/Qwen3.8-27B:ro
  -v "$repo_root":/experiment:ro
  -v "$patch_root":/opt/qwen35-t12-monkeypatch:ro
  "${operator_mount_args[@]}"
  "${profile_mount_args[@]}"
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
  -e VLLM_ASCEND_ENABLE_DENSE_FFN_NZ=0
  -e VLLM_ASCEND_DISABLE_MMAR_DOWN_PROJ=0
  -e VLLM_ASCEND_DISABLE_MMAR_ATTN_OUT_PROJ=0
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
  -e QWEN35_ASCEND_MONKEYPATCH="$patch_enabled"
  -e QWEN35_ASCEND_DIAGNOSTICS="$qwen35_diagnostics"
  -e QWEN35_ASCEND_DIAGNOSTICS_INTERVAL="$qwen35_diagnostics_interval"
  -e VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS="$patch_enabled"
  -e PYTHONPATH="$python_path"
  "${operator_env_args[@]}"
  "${profile_env_args[@]}"
)
serve_args=(
  vllm serve /cache/austinov/Qwen3.8-27B
  --host 127.0.0.1
  --port "$port"
  --tensor-parallel-size 4
  --pipeline-parallel-size 1
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
  --compilation-config "$compilation_config"
  --additional-config "$additional_config"
  --default-chat-template-kwargs '{"enable_thinking":false}'
  --async-scheduling
)

container_id="$(
  docker "${docker_args[@]}" "$image_ref" "${serve_args[@]}"
)"
printf '%s\n' "$container_id" >"$OUTPUT_ROOT/container-id.txt"
printf '%s\n' "$$" >"$OUTPUT_ROOT/supervisor-pid.txt"

# Keep both the cooperative lease and a complete service log until this exact
# one-shot container exits. The launcher itself is intended to run under a
# detached host supervisor (for example nohup) so an AWMCP request deadline
# cannot release the lease while the container remains live.
docker logs --follow "$container_id" >"$OUTPUT_ROOT/service.log" 2>&1 &
log_follower_pid=$!

set +e
service_rc="$(docker wait "$container_id")"
wait_rc=$?
wait "$log_follower_pid"
log_rc=$?
set -e
if [[ "$wait_rc" -ne 0 || ! "$service_rc" =~ ^[0-9]+$ ]]; then
  printf 'docker wait failed: rc=%s output=%s\n' "$wait_rc" "$service_rc" >&2
  service_rc=125
fi
printf '%s\n' "$log_rc" >"$OUTPUT_ROOT/log-follower.exit-code"

printf '%s\n' "$service_rc" >"$OUTPUT_ROOT/service.exit-code"
npu-smi info >"$OUTPUT_ROOT/npu-smi.after.txt" 2>&1 || true
docker ps --no-trunc >"$OUTPUT_ROOT/docker-ps.after.txt" 2>&1 || true
ss -lntp >"$OUTPUT_ROOT/ports.after.txt" 2>&1 || true
docker image inspect "$image_ref" --format '{{.Id}}' >"$OUTPUT_ROOT/image-id.after.txt" 2>&1 || true
docker image inspect "$image_ref" --format '{{range .RepoDigests}}{{println .}}{{end}}' >"$OUTPUT_ROOT/image-digests.after.txt" 2>&1 || true
exit "$service_rc"
