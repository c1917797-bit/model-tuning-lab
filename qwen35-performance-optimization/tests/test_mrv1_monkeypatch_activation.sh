#!/usr/bin/env bash
set -euo pipefail

image=quay.io/ascend/vllm-ascend:v0.23.0
expected_image_id=sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
patch_root="$root/runtime-monkeypatch"

[[ "$(docker image inspect --format '{{.Id}}' "$image")" == "$expected_image_id" ]]

docker_args=(
  run
  --rm
  --network none
  --read-only
  --tmpfs /tmp:rw,noexec,nosuid,size=256m
  --env PYTHONDONTWRITEBYTECODE=1
  --env PYTHONPATH=/opt/qwen35-runtime-monkeypatch
  --env QWEN35_ASCEND_MONKEYPATCH=1
  --env QWEN35_ASCEND_SUPER_KERNEL=1
  --mount "type=bind,src=$patch_root,dst=/opt/qwen35-runtime-monkeypatch,readonly"
  --mount type=bind,src=/usr/local/Ascend/driver/lib64,dst=/usr/local/Ascend/driver/lib64,readonly
  --mount type=bind,src=/usr/local/Ascend/driver/version.info,dst=/usr/local/Ascend/driver/version.info,readonly
  --entrypoint python3
)

docker "${docker_args[@]}" "$image" -c '
import sitecustomize
import vllm_ascend.compilation.acl_graph as acl_graph
import vllm_ascend.compilation.compiler_interface as compiler_interface

sitecustomize._activate_runtime_patches()
assert acl_graph.ACLGraphWrapper._qwen35_super_kernel_monkeypatched
assert compiler_interface._qwen35_super_kernel_monkeypatched
print("PASS_MRV1_MONKEYPATCH_ACTIVATION")
'
