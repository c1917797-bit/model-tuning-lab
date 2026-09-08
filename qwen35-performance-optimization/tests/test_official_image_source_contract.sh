#!/usr/bin/env bash
set -euo pipefail

IMAGE="quay.io/ascend/vllm-ascend:v0.23.0"
EXPECTED_IMAGE_ID="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
EXPECTED_DIGEST="sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CHECKER="$SCRIPT_DIR/../runtime-monkeypatch/check_official_image_source_contract.py"

actual_image_id="$(docker image inspect --format '{{.Id}}' "$IMAGE")"
if [[ "$actual_image_id" != "$EXPECTED_IMAGE_ID" ]]; then
  echo "unexpected image id: $actual_image_id" >&2
  exit 2
fi

repo_digests="$(docker image inspect --format '{{json .RepoDigests}}' "$IMAGE")"
if [[ "$repo_digests" != *"$EXPECTED_DIGEST"* ]]; then
  echo "expected image digest is not present: $repo_digests" >&2
  exit 3
fi

docker run --rm \
  --network none \
  --read-only \
  --mount "type=bind,src=$CHECKER,dst=/opt/qwen35-source-contract.py,readonly" \
  --entrypoint /bin/bash \
  "$IMAGE" \
  -lc 'python3 /opt/qwen35-source-contract.py'
