#!/usr/bin/env bash
# Disposable official-image smoke. No patch or existing container is modified.
set -euo pipefail
cd /opt/host/vnf/austinov/worktrees/qwen35-sparse-prefix-reproduction
exec 9>/cache/austinov/.locks/npu4-7.lock
flock -n 9 || { echo "NPU4-7 lease unavailable"; exit 75; }
snapshot=$(npu-smi info)
for card in 4 5 6 7; do
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
sha256sum scripts/sparse_prefix_smoke.py >"$artifact/script.sha256"
name="qwen35_sparse_smoke_${artifact##*-}"
printf '%s\n' "$name" >"$artifact/container-name.txt"
docker run --rm --name "$name" --network host --read-only --shm-size 8g \
 --memory 48g --memory-swap 48g --cpus 16 \
 --tmpfs /tmp:rw,size=4g --tmpfs /root:rw,size=1g \
 --device /dev/davinci4:/dev/davinci0 --device /dev/davinci5:/dev/davinci1 \
 --device /dev/davinci6:/dev/davinci2 --device /dev/davinci7:/dev/davinci3 \
 --device /dev/davinci_manager --device /dev/devmm_svm --device /dev/hisi_hdc \
 -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
 -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware:ro \
 -v /usr/local/dcmi:/usr/local/dcmi:ro \
 -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
 -v /etc/vnpu.cfg:/etc/vnpu.cfg:ro \
 -v /cache/efim/Qwen3.5-27B:/model/Qwen3.5-27B:ro \
 -v "$PWD/scripts/sparse_prefix_smoke.py":/smoke.py:ro \
 -v "$artifact":/output \
 -e PYTHONDONTWRITEBYTECODE=1 -e HF_HUB_OFFLINE=1 \
 -e OMP_NUM_THREADS=4 -e HCCL_BUFFSIZE=512 \
 -e SPARSE_SMOKE_CACHE=off \
 --entrypoint python3 \
 sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1 \
 /smoke.py 2>&1 | tee "$artifact/run.log"
