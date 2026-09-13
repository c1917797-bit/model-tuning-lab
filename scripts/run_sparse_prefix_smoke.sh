#!/usr/bin/env bash
# Disposable official-image smoke. No patch or existing container is modified.
set -euo pipefail
cd /opt/host/vnf/austinov/worktrees/qwen35-sparse-prefix-reproduction
case "${SPARSE_REAL_PHASE:-}" in
  "") entry_script=scripts/sparse_prefix_smoke.py ;;
  quality|performance) entry_script=scripts/sparse_real_workload.py ;;
  *) echo "Unsupported real-workload phase"; exit 64 ;;
esac
lane="${SPARSE_NPU_LANE:-4-7}"
case "$lane" in
  0-3) cards=(0 1 2 3) ;;
  4-7) cards=(4 5 6 7) ;;
  *) echo "Unsupported four-card lane"; exit 64 ;;
esac
exec 9>"/cache/austinov/.locks/npu${lane}.lock"
flock -n 9 || { echo "NPU lane lease unavailable"; exit 75; }
snapshot=$(npu-smi info)
for card in "${cards[@]}"; do
  grep -q "No running processes found in NPU $card " <<<"$snapshot" ||
    { echo "NPU $card is occupied or status is unrecognized"; exit 75; }
done
available=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
(( available >= 50331648 )) || { echo "Insufficient MemAvailable"; exit 75; }
artifact=$(mktemp -d /cache/austinov/sparse-prefix-smoke-XXXXXX)
printf '%s\n' "$artifact"
printf '%s\n' "$snapshot" >"$artifact/npu-before.txt"
docker ps -a --no-trunc >"$artifact/containers-before.txt"
docker image inspect sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 >"$artifact/image.json"
sha256sum "$entry_script" >"$artifact/script.sha256"
name="qwen38_sparse_smoke_${artifact##*-}"
printf '%s\n' "$name" >"$artifact/container-name.txt"
docker run --rm --name "$name" --network host --read-only --shm-size 8g \
 --memory 48g --memory-swap 48g --cpus 6 \
 --tmpfs /tmp:rw,exec,size=4g --tmpfs /root:rw,exec,size=1g \
 --device "/dev/davinci${cards[0]}" --device "/dev/davinci${cards[1]}" \
 --device "/dev/davinci${cards[2]}" --device "/dev/davinci${cards[3]}" \
 --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
 -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
 -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware:ro \
 -v /usr/local/dcmi:/usr/local/dcmi:ro \
 -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
 -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
 -v /etc/vnpu.cfg:/etc/vnpu.cfg:ro \
 -v /cache/austinov/Qwen3.8-27B:/model/Qwen3.8-27B:ro \
 -v "$PWD/$entry_script":/smoke.py:ro \
 -v /cache/cch/query_rewrite.jsonl:/data/query_rewrite.jsonl:ro \
 -v /cache/austinov/sparse-opportunity-8t6gZ0/opportunity.json:/training/opportunity.json:ro \
 -v "$PWD/src":/patch:ro \
 -v "$artifact":/output \
 -e PYTHONDONTWRITEBYTECODE=1 -e HF_HUB_OFFLINE=1 \
 -e SPARSE_CONTEXT_REPEATS="${SPARSE_CONTEXT_REPEATS:-320}" \
 -e SPARSE_DIVERGENT="${SPARSE_DIVERGENT:-0}" \
 -e SPARSE_PREFIX_QA="${SPARSE_PREFIX_QA:-0}" \
 -e SPARSE_REAL_PHASE="${SPARSE_REAL_PHASE:-}" \
 -e SPARSE_REAL_DIAGNOSTIC="${SPARSE_REAL_DIAGNOSTIC:-}" \
 -e SPARSE_TRAINING_REPORT="${SPARSE_TRAINING_REPORT:-}" \
 -e OMP_NUM_THREADS=4 -e HCCL_BUFFSIZE=512 \
 -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
 -e SPARSE_SMOKE_CACHE="${SPARSE_SMOKE_CACHE:-off}" \
 -e SPARSE_DEVICE_PREFLIGHT="${SPARSE_DEVICE_PREFLIGHT:-0}" \
 -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
 --entrypoint /bin/bash \
 sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 \
 -c 'export PYTHONPATH="/patch${PYTHONPATH:+:$PYTHONPATH}"; python3 -c "import acl; print(\"ACL_IMPORT_PASS\", acl.__file__, flush=True)" && exec python3 /smoke.py' 2>&1 | tee "$artifact/run.log"
