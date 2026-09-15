#!/usr/bin/env bash
set -euo pipefail

REPO=/opt/host/vnf/austinov/model-tuning-lab
WORKSTREAM=.agents/workstreams/dasc-qwen36-ascend-piercing-20260915
EXPERIMENT=dasc-qwen36-physical-cache-v12
ARTIFACT_BASE=/cache/cch/dasc-qwen36-ascend-20260915
RESULT_ROOT=$ARTIFACT_BASE/physical-cache-order-fix-v12
CONTROLLER_ROOT=$ARTIFACT_BASE/controllers
CONTROLLER_LOG=$CONTROLLER_ROOT/$EXPERIMENT.log
LOCK_DIR=/cache/cch/.locks
LOCK_FILE=$LOCK_DIR/npu4-7.lock
CONTAINER=dasc_qwen36_physical_order_fix_v12_20260915
IMAGE=quay.io/ascend/vllm-ascend:v0.23.0
MODEL_HOST=/cache/efim/Qwen3.6-27B
MODEL_CONTAINER=/models/Qwen3.6-27B
PLUGIN_HOST=$RESULT_ROOT/plugin-snapshot
PORT=8030
POLL_SECONDS=${DASC_POLL_SECONDS:-60}
READY_POLLS=${DASC_READY_POLLS:-360}

mkdir -p "$CONTROLLER_ROOT" "$LOCK_DIR"
exec > >(tee -a "$CONTROLLER_LOG") 2>&1

timestamp() {
    date --iso-8601=seconds
}

card_snapshot() {
    local device
    for device in 4 5 6 7; do
        echo "NPU${device}"
        npu-smi info -t proc-mem -i "$device" -c 0 2>&1 || true
    done
}

card_info_snapshot() {
    local device
    for device in 4 5 6 7; do
        echo "NPU${device}"
        npu-smi info -i "$device" -c 0 2>&1 || true
    done
}

cards_are_idle() {
    local device output
    for device in 4 5 6 7; do
        output=$(npu-smi info -t proc-mem -i "$device" -c 0 2>&1) || return 1
        if grep -q 'Process id:' <<<"$output"; then
            return 1
        fi
    done
    return 0
}

self_test() {
    local required
    for required in docker curl npu-smi flock python3 sha256sum ss; do
        command -v "$required" >/dev/null
    done
    test -d "$REPO/.git"
    test -r "$REPO/$WORKSTREAM/run_physical_canary.py"
    test -r "$MODEL_HOST/config.json"
    docker image inspect "$IMAGE" >/dev/null
    local device
    for device in 4 5 6 7; do
        test -c "/dev/davinci${device}"
    done
    echo "self-test: ok"
}

if [[ ${1:-} == "--self-test" ]]; then
    self_test
    exit 0
fi

self_test
cd "$REPO"
CURRENT_HEAD=$(git rev-parse HEAD)
if ! git merge-base --is-ancestor c5c6fadb1270bab419caa36a0918529251902df0 "$CURRENT_HEAD"; then
    echo "refusing: HEAD $CURRENT_HEAD does not descend from the v12 frozen base"
    exit 2
fi
if [[ -n $(git status --porcelain) ]]; then
    echo "refusing: repository is dirty"
    git status --short
    exit 2
fi
if [[ -e "$RESULT_ROOT" ]]; then
    echo "refusing: immutable result directory already exists: $RESULT_ROOT"
    exit 2
fi
if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "refusing: exact owned container name already exists: $CONTAINER"
    exit 2
fi

echo "$(timestamp) waiting for physical NPU4-7; NPU0-3 are outside scope"
while true; do
    if cards_are_idle; then
        exec 9>"$LOCK_FILE"
        if flock -n 9; then
            sleep 2
            if cards_are_idle; then
                break
            fi
            flock -u 9
        fi
    fi
    echo "$(timestamp) NPU4-7 still unavailable"
    card_snapshot
    sleep "$POLL_SECONDS"
done

echo "$(timestamp) acquired NPU4-7 lock and passed post-lock idle recheck"
if ss -ltn | awk '{print $4}' | grep -Eq "(^|:)$PORT$"; then
    echo "refusing: port $PORT is already listening"
    exit 2
fi

mkdir "$RESULT_ROOT"
card_snapshot >"$RESULT_ROOT/npu-before.txt"
git rev-parse HEAD >"$RESULT_ROOT/source-commit.txt"
git status --short --branch >"$RESULT_ROOT/source-status.txt"
sha256sum "$MODEL_HOST/config.json" >"$RESULT_ROOT/model-config.sha256"
docker image inspect "$IMAGE" >"$RESULT_ROOT/image-inspect.json"
card_info_snapshot >"$RESULT_ROOT/npu-smi-info.txt"
cp -a "$REPO/projects/dasc_vllm_ascend" "$PLUGIN_HOST"
cp "$REPO/$WORKSTREAM/run_physical_canary.py" "$RESULT_ROOT/run_physical_canary.py"
find "$PLUGIN_HOST" -type f -print0 | sort -z | xargs -0 sha256sum >"$RESULT_ROOT/plugin-files.sha256"
sha256sum "$RESULT_ROOT/run_physical_canary.py" >"$RESULT_ROOT/canary.sha256"

cleanup() {
    local status=$?
    set +e
    if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
        docker logs "$CONTAINER" >"$RESULT_ROOT/service.log" 2>&1
        docker inspect "$CONTAINER" >"$RESULT_ROOT/container-inspect.json"
        if [[ $(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null) == true ]]; then
            docker stop --time 30 "$CONTAINER" >"$RESULT_ROOT/container-stop.txt" 2>&1
        fi
        docker inspect "$CONTAINER" >"$RESULT_ROOT/container-final-inspect.json"
    fi
    card_snapshot >"$RESULT_ROOT/npu-after.txt"
    echo "$status" >"$RESULT_ROOT/controller-exit-code.txt"
    find "$RESULT_ROOT" -maxdepth 1 -type f ! -name artifacts.sha256 -print0 |
        sort -z |
        xargs -0 sha256sum >"$RESULT_ROOT/artifacts.sha256.tmp"
    mv "$RESULT_ROOT/artifacts.sha256.tmp" "$RESULT_ROOT/artifacts.sha256"
    echo "$(timestamp) controller exit=$status"
}
trap cleanup EXIT

docker run -d \
    --name "$CONTAINER" \
    --label mst.owner=c1917797-bit \
    --label mst.workstream=dasc-qwen36-ascend-piercing-20260915 \
    --label mst.experiment="$EXPERIMENT" \
    --network host \
    --device /dev/davinci4:/dev/davinci0 \
    --device /dev/davinci5:/dev/davinci1 \
    --device /dev/davinci6:/dev/davinci2 \
    --device /dev/davinci7:/dev/davinci3 \
    --device /dev/davinci_manager \
    --device /dev/devmm_svm \
    --device /dev/hisi_hdc \
    -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
    -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
    -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
    -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
    -v /usr/local/dcmi:/usr/local/dcmi:ro \
    -v "$MODEL_HOST:$MODEL_CONTAINER:ro" \
    -v "$PLUGIN_HOST:/workspace/dasc:ro" \
    -v "$RESULT_ROOT:/dasc-results:rw" \
    -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 \
    -e VLLM_PLUGINS=ascend,dasc_vllm_ascend \
    -e MST_DASC_ENABLE=1 \
    -e MST_DASC_MODE=physical-cache-eager \
    -e MST_DASC_W_MAX=64 \
    -e MST_DASC_EVIDENCE_PATH=/dasc-results/evidence.jsonl \
    -e PYTHONPATH=/workspace/dasc \
    "$IMAGE" \
    vllm serve "$MODEL_CONTAINER" \
    --tensor-parallel-size 4 \
    --mamba-cache-mode align \
    --enable-prefix-caching \
    --max-model-len 4096 \
    --max-num-seqs 16 \
    --kv-cache-memory 9663676416 \
    --compilation-config '{"cudagraph_capture_sizes":[1,2,4,8,16],"cudagraph_mode":"FULL_DECODE_ONLY"}' \
    --port "$PORT" >"$RESULT_ROOT/container-id.txt"

ready=0
for ((attempt = 1; attempt <= READY_POLLS; attempt++)); do
    if curl -fsS "http://127.0.0.1:$PORT/v1/models" >"$RESULT_ROOT/models.json.tmp" 2>/dev/null; then
        mv "$RESULT_ROOT/models.json.tmp" "$RESULT_ROOT/models.json"
        ready=1
        break
    fi
    if [[ $(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null) != true ]]; then
        echo "service exited before readiness"
        exit 1
    fi
    if (( attempt % 6 == 0 )); then
        echo "$(timestamp) waiting for service readiness attempt=$attempt/$READY_POLLS"
    fi
    sleep 10
done
if (( ready == 0 )); then
    echo "service readiness timed out"
    exit 1
fi

echo "$(timestamp) service ready; running strict physical-cache canary"
python3 "$RESULT_ROOT/run_physical_canary.py" \
    --base-url "http://127.0.0.1:$PORT" \
    --model "$MODEL_CONTAINER" \
    --output-dir "$RESULT_ROOT" \
    --activation "$RESULT_ROOT/evidence.jsonl"
touch "$RESULT_ROOT/SUCCESS"
echo "$(timestamp) v12 passed"
