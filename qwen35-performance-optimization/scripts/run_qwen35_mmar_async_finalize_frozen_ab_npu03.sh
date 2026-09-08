#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
bundle_root="$repo_root/qwen35-performance-optimization"
output_root="${OUTPUT_ROOT:?set OUTPUT_ROOT to a new absolute directory under /cache/austinov}"
baseline_opp_root="${BASELINE_OPP_ROOT:?set BASELINE_OPP_ROOT}"
baseline_opp_env="${BASELINE_OPP_ENV:?set BASELINE_OPP_ENV}"
candidate_opp_root="${CANDIDATE_OPP_ROOT:?set CANDIDATE_OPP_ROOT}"
candidate_opp_env="${CANDIDATE_OPP_ENV:?set CANDIDATE_OPP_ENV}"
baseline_commit="${BASELINE_OPERATOR_COMMIT:?set BASELINE_OPERATOR_COMMIT}"
baseline_sha256="${BASELINE_PACKAGE_SHA256:?set BASELINE_PACKAGE_SHA256}"
candidate_commit="${CANDIDATE_OPERATOR_COMMIT:?set CANDIDATE_OPERATOR_COMMIT}"
candidate_sha256="${CANDIDATE_PACKAGE_SHA256:?set CANDIDATE_PACKAGE_SHA256}"
cooldown="${MMAR_DEVICE_COOLDOWN_SECONDS:-30}"
image="${VLLM_ASCEND_IMAGE:-quay.io/ascend/vllm-ascend:v0.23.0}"
lease_file="/cache/austinov/.locks/npu0-3.lock"

case "$output_root" in /cache/austinov/*) ;; *) echo "invalid OUTPUT_ROOT" >&2; exit 64;; esac
for path in "$baseline_opp_root" "$candidate_opp_root"; do
  [[ -d "$path" ]] || { echo "missing OPP root: $path" >&2; exit 66; }
done
for path in "$baseline_opp_env" "$candidate_opp_env"; do
  [[ -f "$path" ]] || { echo "missing OPP environment: $path" >&2; exit 66; }
done
[[ ! -e "$output_root" ]] || { echo "refusing to reuse output root" >&2; exit 44; }

mkdir -p /cache/austinov/.locks
exec 9>"$lease_file"
flock -n 9 || { echo "NPU0-3 cooperative lease is held" >&2; exit 46; }

assert_npu03_idle() {
  local npu_snapshot occupied container_id devices privileged
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
  for port in 29943 29944; do
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
{
  echo "image=$image"
  echo "image_id=$image_id"
  echo "image_repo_digests=$image_digests"
  echo "container_policy=one-shot --rm; no docker commit; no package install in image"
  echo "lease_file=$lease_file"
  echo "baseline_operator_commit=$baseline_commit"
  echo "baseline_package_sha256=$baseline_sha256"
  echo "baseline_opp_root=$baseline_opp_root"
  echo "candidate_operator_commit=$candidate_commit"
  echo "candidate_package_sha256=$candidate_sha256"
  echo "candidate_opp_root=$candidate_opp_root"
  echo "candidate_env_ASCEND_MATMUL_ALLREDUCE_M1_ASYNC_FINALIZE=1"
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
    opp_root="$baseline_opp_root"
    opp_env="$baseline_opp_env"
    commit="$baseline_commit"
    sha256="$baseline_sha256"
    candidate_args=()
    master_port=29943
  else
    opp_root="$candidate_opp_root"
    opp_env="$candidate_opp_env"
    commit="$candidate_commit"
    sha256="$candidate_sha256"
    candidate_args=(-e ASCEND_MATMUL_ALLREDUCE_M1_ASYNC_FINALIZE=1)
    master_port=29944
  fi
  container_name="qwen35_mmar_async_finalize_${label}_npu03"
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
    -v /cache/austinov:/cache/austinov \
    -v "$repo_root":/experiment:ro \
    -v "$opp_root:$opp_root:ro" \
    -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    -e HCCL_BUFFSIZE=512 -e OMP_PROC_BIND=false -e OMP_NUM_THREADS=1 \
    -e TASK_QUEUE_ENABLE=1 \
    -e QWEN35_MMAR_OPERATOR_COMMIT="$commit" \
    -e QWEN35_MMAR_PACKAGE_SHA256="$sha256" \
    "${candidate_args[@]}" "$image" \
    bash -lc "source '$opp_env'; exec python3 /experiment/qwen35-performance-optimization/scripts/benchmark_qwen35_mmar_async_finalize.py \
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
echo "completed frozen-predecessor vs opt-in async-finalize A/B: $output_root"
exit "$decision_rc"
