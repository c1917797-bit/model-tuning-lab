#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
bundle_root="$repo_root/qwen35-performance-optimization"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory under /cache/austinov}"
candidate_opp_root="${CANDIDATE_OPP_ROOT:?set CANDIDATE_OPP_ROOT}"
candidate_opp_env="${CANDIDATE_OPP_ENV:?set CANDIDATE_OPP_ENV}"
candidate_commit="${CANDIDATE_OPERATOR_COMMIT:?set CANDIDATE_OPERATOR_COMMIT}"
candidate_sha256="${CANDIDATE_PACKAGE_SHA256:?set CANDIDATE_PACKAGE_SHA256}"
cooldown="${MMAR_DEVICE_COOLDOWN_SECONDS:-30}"
image="${VLLM_ASCEND_IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
lease_file="/cache/austinov/.locks/npu0-3.lock"

case "$output_root" in /cache/austinov/*) ;; *) echo "invalid OUTPUT_ROOT" >&2; exit 64;; esac
[[ -d "$candidate_opp_root" ]] || { echo "missing OPP root: $candidate_opp_root" >&2; exit 66; }
[[ -f "$candidate_opp_env" ]] || { echo "missing OPP environment: $candidate_opp_env" >&2; exit 66; }
[[ ! -e "$output_root" ]] || { echo "refusing to reuse output root" >&2; exit 44; }

mkdir -p /cache/austinov/.locks
exec 9>"$lease_file"
flock -n 9 || { echo "NPU0-3 cooperative lease is held" >&2; exit 46; }

assert_npu03_idle() {
  local npu_snapshot occupied container_id devices privileged mem_available_kb
  mem_available_kb="$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)"
  [[ "$mem_available_kb" -ge 50331648 ]] || {
    echo "MemAvailable below 48 GiB: $mem_available_kb kB" >&2
    exit 48
  }
  npu_snapshot="$(npu-smi info)"
  occupied="$(awk -F '|' '$2 ~ /^[[:space:]]*[0-3][[:space:]]+[0-9]+[[:space:]]*$/ && $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {print $3}' <<<"$npu_snapshot")"
  [[ -z "$occupied" ]] || { echo "physical NPU0-3 are occupied" >&2; exit 42; }
  while read -r container_id; do
    [[ -n "$container_id" ]] || continue
    privileged="$(docker inspect --format '{{.HostConfig.Privileged}}' "$container_id")"
    devices="$(docker inspect --format '{{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$container_id")"
    [[ "$privileged" != true ]] || { echo "running privileged container blocks allocation: $container_id" >&2; exit 43; }
    [[ ! "$devices" =~ /dev/davinci[0-3]([^0-9]|$) ]] || {
      echo "running container reserves NPU0-3: $container_id $devices" >&2
      exit 43
    }
  done < <(docker ps -q)
  for port in 29953 29954; do
    ! ss -ltnH "sport = :$port" | grep -q . || {
      echo "required master port is occupied: $port" >&2
      exit 45
    }
  done
}

assert_npu03_idle
mkdir -p "$output_root"
npu-smi info >"$output_root/npu-before.txt"
docker ps --no-trunc >"$output_root/docker-before.txt"
ps -eo pid,ppid,user,stat,etime,args >"$output_root/process-before.txt"
ss -ltnp >"$output_root/ports-before.txt"
grep -RniE 'NPU0-3|NPU4-7|lease|租约' /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams >"$output_root/resource-claims-before.txt" || true
image_id="$(docker image inspect --format '{{.Id}}' "$image")"
image_digests="$(docker image inspect --format '{{json .RepoDigests}}' "$image")"
protocol_commit="$(git -C "$repo_root" rev-parse HEAD)"
benchmark_sha256="$(sha256sum "$bundle_root/scripts/benchmark_qwen35_mmar_async_finalize.py" | awk '{print $1}')"
evaluator_sha256="$(sha256sum "$bundle_root/scripts/evaluate_qwen35_mmar_async_finalize.py" | awk '{print $1}')"
launcher_sha256="$(sha256sum "$bundle_root/scripts/run_qwen35_mmar_async_finalize_frozen_ab_npu03.sh" | awk '{print $1}')"
{
  echo "image=$image"
  echo "image_id=$image_id"
  echo "image_repo_digests=$image_digests"
  echo "container_policy=one-shot --rm; no docker commit; no package install in image"
  echo "lease_file=$lease_file"
  echo "baseline=official stock operator from immutable image"
  echo "candidate_operator_commit=$candidate_commit"
  echo "candidate_package_sha256=$candidate_sha256"
  echo "candidate_opp_root=$candidate_opp_root"
  echo "protocol_commit=$protocol_commit"
  echo "benchmark_sha256=$benchmark_sha256"
  echo "evaluator_sha256=$evaluator_sha256"
  echo "launcher_sha256=$launcher_sha256"
  echo "candidate_env_ASCEND_MATMUL_ALLREDUCE_M1_IPC_FULLMESH=1"
  echo "stress_gate=numerical max-abs and relative-L2 envelope versus stock"
  echo "warmup=40"
  echo "iterations=200"
  echo "repeats=7"
  echo "stress_calls_per_rank=5000"
  echo "stress_batch=250"
  echo "cooldown_seconds=$cooldown"
} >"$output_root/provenance.txt"

for label in default candidate; do
  assert_npu03_idle
  if [[ "$label" == default ]]; then
    commit="official-stock"
    sha256="not-applicable"
    opp_mount_args=()
    candidate_args=()
    run_prefix=""
    master_port=29953
  else
    commit="$candidate_commit"
    sha256="$candidate_sha256"
    opp_mount_args=(-v "$candidate_opp_root:$candidate_opp_root:ro")
    candidate_args=(-e ASCEND_MATMUL_ALLREDUCE_M1_IPC_FULLMESH=1)
    run_prefix="source '$candidate_opp_env'; "
    master_port=29954
  fi
  container_name="qwen35_mmar_ipc_fullmesh_${label}_npu03"
  ! docker container inspect "$container_name" >/dev/null 2>&1 || {
    echo "existing container: $container_name" >&2
    exit 41
  }
  timeout --signal=TERM --kill-after=60s 1800s docker run --rm --name "$container_name" --network host --cpuset-cpus 0-95 \
    --device /dev/davinci0 --device /dev/davinci1 \
    --device /dev/davinci2 --device /dev/davinci3 \
    --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
    -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
    -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
    -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
    -v /usr/local/dcmi:/usr/local/dcmi:ro \
    -v /usr/local/Ascend/driver/tools/hccn_tool:/usr/local/Ascend/driver/tools/hccn_tool:ro \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
    -v "$output_root:$output_root" \
    -v "$repo_root":/experiment:ro \
    "${opp_mount_args[@]}" \
    -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    -e HCCL_BUFFSIZE=512 -e OMP_PROC_BIND=false -e OMP_NUM_THREADS=1 \
    -e TASK_QUEUE_ENABLE=1 \
    -e QWEN35_MMAR_OPERATOR_COMMIT="$commit" \
    -e QWEN35_MMAR_PACKAGE_SHA256="$sha256" \
    "${candidate_args[@]}" "$image" \
    bash -lc "${run_prefix}exec python3 /experiment/qwen35-performance-optimization/scripts/benchmark_qwen35_mmar_async_finalize.py \
      --label '$label' --output '$output_root/$label.json' \
      --warmup 40 --iterations 200 --repeats 7 \
      --stress-calls 5000 --stress-batch 250 --master-port '$master_port'" \
      >"$output_root/$label.log" 2>&1
  [[ "$label" != default ]] || sleep "$cooldown"
done

set +e
python3 "$bundle_root/scripts/evaluate_qwen35_mmar_async_finalize.py" --root "$output_root"
decision_rc=$?
set -e
npu-smi info >"$output_root/npu-after.txt"
docker ps --no-trunc >"$output_root/docker-after.txt"
ps -eo pid,ppid,user,stat,etime,args >"$output_root/process-after.txt"
ss -ltnp >"$output_root/ports-after.txt"
final_image_id="$(docker image inspect --format '{{.Id}}' "$image")"
final_image_digests="$(docker image inspect --format '{{json .RepoDigests}}' "$image")"
[[ "$final_image_id" == "$image_id" ]] || { echo "image ID changed" >&2; exit 47; }
[[ "$final_image_digests" == "$image_digests" ]] || { echo "image digest changed" >&2; exit 47; }
sha256sum "$output_root"/*.json "$output_root"/*.log "$output_root"/*.txt >"$output_root/SHA256SUMS"
echo "completed official-stock vs opt-in IPC-fullmesh A/B: $output_root"
exit "$decision_rc"
