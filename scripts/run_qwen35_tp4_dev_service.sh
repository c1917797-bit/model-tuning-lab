#!/usr/bin/env bash
set -euo pipefail

mode="${1:-}"
case "$mode" in
  baseline|mtp|mtp-local-argmax|mtp-k3-local-argmax-mmar-prefetch-gateup-0p1|draft4b-k3-mmar-prefetch-gateup-0p1|suffix-k15-mmar-prefetch-gateup-0p1|suffix-k16-mmar-prefetch-gateup-0p1|ngram-gpu|profile|profile-mmar-off|profile-msprof-mmar-on|profile-msprof-mmar-off|control-mmar-off|mmar-on|mmar-on-hccl-aiv|mmar-on-weight-prefetch-gateup|mmar-on-weight-prefetch-gateup-0p1|qwen35-gdn-gateup-prefetch-0p1|qwen35-gdn-prefetch0p1-sp-pass|mmar-on-weight-prefetch-gateup-0p1-fused-tail|mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024|mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024-static-kernel|mmar-on-weight-prefetch-gateup-0p1-taskqueue2|mmar-on-weight-prefetch-gateup-0p1-static-kernel|tp2-pp2-mmar-on-weight-prefetch-gateup-0p1|tp2-dp2-mmar-on|tp2-dp2-mmar-on-text-only|tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384|tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192|tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95|flashcomm1|flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1|flashcomm2-oproj1-mmar-prefetch-gateup-0p1|flashcomm2-oproj2-mmar-prefetch-gateup-0p1|bf16-nz|bf16-nz-mmar-off|flashcomm1-bf16-nz|selective-ffn-nz) ;;
  *)
    echo "usage: $0 {baseline|mtp|mtp-local-argmax|draft4b-k3-mmar-prefetch-gateup-0p1|suffix-k15-mmar-prefetch-gateup-0p1|suffix-k16-mmar-prefetch-gateup-0p1|ngram-gpu|...}" >&2
    exit 64
    ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
device_set="${DEVICE_SET:-4-7}"
case "$device_set" in
  0-3)
    physical_npus=(0 1 2 3)
    physical_npu_csv="0,1,2,3"
    cpuset_cpus="0-95"
    ;;
  4-7)
    physical_npus=(4 5 6 7)
    physical_npu_csv="4,5,6,7"
    cpuset_cpus="0-95"
    ;;
  *)
    echo "DEVICE_SET must be 0-3 or 4-7 for this workstream" >&2
    exit 64
    ;;
esac
tensor_parallel_size=4
data_parallel_size=1
pipeline_parallel_size=1
if [[ "$mode" == tp2-dp2-mmar-on ||
      "$mode" == tp2-dp2-mmar-on-text-only ||
      "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384 ||
      "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192 ||
      "$mode" == tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95 ]]; then
  tensor_parallel_size=2
  data_parallel_size=2
elif [[ "$mode" == tp2-pp2-mmar-on-weight-prefetch-gateup-0p1 ]]; then
  tensor_parallel_size=2
  pipeline_parallel_size=2
fi
device_tag="${device_set//-/_}"
container_name="${CONTAINER_NAME:-qwen35_query_rewrite_tp${tensor_parallel_size}_dp${data_parallel_size}_${mode}_$device_tag}"
port="${PORT:-10010}"
profile_dir="${PROFILE_DIR:-/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/profiles/tp4-baseline-v1}"
npu_smi_bin="${NPU_SMI_BIN:-npu-smi}"
mtp_local_argmax_root="${MTP_LOCAL_ARGMAX_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-mtp-local-argmax}"
mtp_local_argmax_commit="${MTP_LOCAL_ARGMAX_COMMIT:-37d32edf5a2626b4b6b1c6ed57fcad8d3ed9c8cd}"
mtp_qwen_patch_sha256=d0b0ce744a0ada28ff8a773fce596ca2b2617e01875e5a254e7e32a62fdf7d4b
mtp_proposer_patch_sha256=753a67c644dcb2654ba7d63e0e0abb609e935a90f59b9ea153dbbb8f09a6dc99
selective_ffn_nz_root="${SELECTIVE_FFN_NZ_ROOT:-/cache/cch/.worktrees/exp-20260904-qwen35-selective-ffn-nz}"
selective_ffn_nz_commit="71c25ec9"
qwen35_gdn_prefetch_root="${QWEN35_GDN_PREFETCH_ROOT:-/cache/cch/.worktrees/exp-20260906-qwen35-gdn-gateup-prefetch}"
qwen35_gdn_prefetch_commit="${QWEN35_GDN_PREFETCH_COMMIT:-82a2dce763eb39c285744f6fc36e37728471a1c7}"
qwen35_gdn_prefetch_weight_sha256=a6b6c41e0524c5eabb79c5d54dda24d66d96dfed0420829a8cda0aab7c8c0269
qwen35_gdn_prefetch_layernorm_sha256=5eadde6bc398050ef2dac524bbb20e5ae4340801b92dd44830078103291d7e15
flashcomm2_mmar_root="${FLASHCOMM2_MMAR_ROOT:-/cache/cch/.worktrees/exp-20260904-qwen35-flashcomm2-oproj-mmar-mlp}"
flashcomm2_mmar_commit="65f780ee"
flashcomm1_gdn_root="${FLASHCOMM1_GDN_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-flashcomm1-gdn-shape}"
flashcomm1_gdn_commit="${FLASHCOMM1_GDN_COMMIT:-dc7ebdd55421d543e2e87398c2d601742d4a8336}"
mmar_add_rmsnorm_root="${MMAR_ADD_RMSNORM_ROOT:-/cache/cch/.worktrees/exp-20260905-qwen35-mmar-add-rmsnorm-vllm}"
mmar_add_rmsnorm_commit="${MMAR_ADD_RMSNORM_COMMIT:-bca160315fd29f0ecbf3b1fc69ee7af410f7d11c}"
mmar_add_rmsnorm_extension="$mmar_add_rmsnorm_root/build-mmar-add-rmsnorm/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so"
mmar_add_rmsnorm_kernels="$mmar_add_rmsnorm_root/build-mmar-add-rmsnorm/lib/libvllm_ascend_kernels.so"
mmar_add_rmsnorm_extension_sha256="6006e113bf7f52ba5561d9847dbdcc6960b89eff56228d5ab584344719347d23"
mmar_add_rmsnorm_kernels_sha256="6a9fc72a66a6055eb522a251fa48632b0ba257f22fb8f91a2deedc05e03e8b6a"
flashcomm1_env=0
weight_nz_env=1
matmul_allreduce_env=1
selective_ffn_nz_env=0
hccl_op_expansion_mode=""
hccl_buffsize=512
task_queue_enable=1
max_num_batched_tokens="${MAX_NUM_BATCHED_TOKENS:-32768}"
max_model_len=133000
gpu_memory_utilization=0.90
draft4b_model=/cache/Qwen3.5-4B
draft4b_config_sha256=ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670
draft4b_index_sha256=cf3f798ee02ba45f9622aa8892a47369ab667d0afbf154ee7c2212de42e6302d
draft_model_fix_root=/cache/cch/.worktrees/exp-20260906-vllm-draft-model-contract-fix
draft_model_fix_commit=e132e799a681ed10160ed86dbd216ed6035e96dc
draft_model_fix_sha256=a1d14995e80d9b82f37585e95b0b532d4c6d7bd42c36b4e6cc0e8363c5402cca
if [[ "$mode" == flashcomm1 || "$mode" == flashcomm1-bf16-nz ||
      "$mode" == flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1 ]]; then
  flashcomm1_env=1
fi
if [[ "$mode" == bf16-nz || "$mode" == bf16-nz-mmar-off ||
      "$mode" == flashcomm1-bf16-nz ]]; then
  weight_nz_env=2
fi
if [[ "$mode" == profile-mmar-off || "$mode" == profile-msprof-mmar-off ||
      "$mode" == control-mmar-off || "$mode" == ngram-gpu ||
      "$mode" == bf16-nz-mmar-off ]]; then
  matmul_allreduce_env=0
fi
if [[ "$mode" == selective-ffn-nz ]]; then
  if [[ "$device_set" != 4-7 ]]; then
    echo "selective-ffn-nz is restricted to physical NPU4-7" >&2
    exit 43
  fi
  actual_ref="$(
    git -c safe.directory="$selective_ffn_nz_root" -C "$selective_ffn_nz_root" rev-parse --short=8 HEAD
  )"
  if [[ "$actual_ref" != "$selective_ffn_nz_commit" ]]; then
    echo "selective FFN NZ source must be $selective_ffn_nz_commit, got $actual_ref" >&2
    exit 45
  fi
  selective_ffn_nz_env=1
fi
if [[ "$mode" == qwen35-gdn-gateup-prefetch-0p1 ||
      "$mode" == qwen35-gdn-prefetch0p1-sp-pass ]]; then
  actual_ref="$(
    git -c safe.directory="$qwen35_gdn_prefetch_root" \
      -C "$qwen35_gdn_prefetch_root" rev-parse HEAD
  )"
  [[ "$actual_ref" == "$qwen35_gdn_prefetch_commit" ]] || {
    echo "Qwen3.5 GDN prefetch source must be $qwen35_gdn_prefetch_commit, got $actual_ref" >&2
    exit 45
  }
  [[ "$(sha256sum "$qwen35_gdn_prefetch_root/vllm_ascend/ops/weight_prefetch.py" | awk '{print $1}')" == "$qwen35_gdn_prefetch_weight_sha256" ]] || {
    echo "Qwen3.5 GDN weight-prefetch patch hash mismatch" >&2
    exit 47
  }
  [[ "$(sha256sum "$qwen35_gdn_prefetch_root/vllm_ascend/ops/layernorm.py" | awk '{print $1}')" == "$qwen35_gdn_prefetch_layernorm_sha256" ]] || {
    echo "Qwen3.5 GDN layernorm patch hash mismatch" >&2
    exit 47
  }
fi
if [[ "$mode" == mtp-local-argmax ||
      "$mode" == mtp-k3-local-argmax-mmar-prefetch-gateup-0p1 ]]; then
  actual_ref="$(
    git -c safe.directory="$mtp_local_argmax_root" \
      -C "$mtp_local_argmax_root" rev-parse HEAD
  )"
  if [[ "$actual_ref" != "$mtp_local_argmax_commit" ]]; then
    echo "Qwen3.5 MTP local-argmax source must be $mtp_local_argmax_commit, got $actual_ref" >&2
    exit 45
  fi
  [[ "$(sha256sum "$mtp_local_argmax_root/vllm_ascend/patch/worker/patch_qwen3_5.py" | awk '{print $1}')" == "$mtp_qwen_patch_sha256" ]] || {
    echo "Qwen3.5 MTP patch hash mismatch" >&2
    exit 47
  }
  [[ "$(sha256sum "$mtp_local_argmax_root/vllm_ascend/spec_decode/llm_base_proposer.py" | awk '{print $1}')" == "$mtp_proposer_patch_sha256" ]] || {
    echo "Ascend local-argmax proposer patch hash mismatch" >&2
    exit 47
  }
fi
if [[ "$mode" == draft4b-k3-mmar-prefetch-gateup-0p1 ]]; then
  [[ -f "$draft4b_model/config.json" &&
     -f "$draft4b_model/model.safetensors.index.json" ]] || {
    echo "missing pinned Qwen3.5-4B draft model at $draft4b_model" >&2
    exit 66
  }
  [[ "$(sha256sum "$draft4b_model/config.json" | awk '{print $1}')" == "$draft4b_config_sha256" ]] || {
    echo "Qwen3.5-4B draft config hash mismatch" >&2
    exit 65
  }
  [[ "$(sha256sum "$draft4b_model/model.safetensors.index.json" | awk '{print $1}')" == "$draft4b_index_sha256" ]] || {
    echo "Qwen3.5-4B draft weight-index hash mismatch" >&2
    exit 65
  }
  actual_ref="$(
    git -c safe.directory="$draft_model_fix_root" \
      -C "$draft_model_fix_root" rev-parse HEAD
  )"
  [[ "$actual_ref" == "$draft_model_fix_commit" ]] || {
    echo "vLLM draft-model contract fix must be $draft_model_fix_commit, got $actual_ref" >&2
    exit 45
  }
  [[ "$(sha256sum "$draft_model_fix_root/vllm/config/speculative.py" | awk '{print $1}')" == "$draft_model_fix_sha256" ]] || {
    echo "vLLM draft-model contract fix hash mismatch" >&2
    exit 47
  }
fi
if [[ "$mode" == flashcomm2-oproj1-mmar-prefetch-gateup-0p1 ||
      "$mode" == flashcomm2-oproj2-mmar-prefetch-gateup-0p1 ]]; then
  actual_ref="$(
    git -c safe.directory="$flashcomm2_mmar_root" -C "$flashcomm2_mmar_root" rev-parse --short=8 HEAD
  )"
  if [[ "$actual_ref" != "$flashcomm2_mmar_commit" ]]; then
    echo "FlashComm2/MMAR source must be $flashcomm2_mmar_commit, got $actual_ref" >&2
    exit 45
  fi
fi
if [[ "$mode" == flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1 ]]; then
  actual_ref="$(
    git -c safe.directory="$flashcomm1_gdn_root" \
      -C "$flashcomm1_gdn_root" rev-parse HEAD
  )"
  if [[ "$actual_ref" != "$flashcomm1_gdn_commit" ]]; then
    echo "FlashComm1 GDN source must be $flashcomm1_gdn_commit, got $actual_ref" >&2
    exit 45
  fi
fi
if [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-fused-tail ]]; then
  actual_ref="$(
    git -c safe.directory="$mmar_add_rmsnorm_root" \
      -C "$mmar_add_rmsnorm_root" rev-parse HEAD
  )"
  if [[ "$actual_ref" != "$mmar_add_rmsnorm_commit" ]]; then
    echo "MMAR AddRMSNorm source must be $mmar_add_rmsnorm_commit, got $actual_ref" >&2
    exit 45
  fi
  if [[ "$(sha256sum "$mmar_add_rmsnorm_extension" | awk '{print $1}')" != \
        "$mmar_add_rmsnorm_extension_sha256" ||
        "$(sha256sum "$mmar_add_rmsnorm_kernels" | awk '{print $1}')" != \
        "$mmar_add_rmsnorm_kernels_sha256" ]]; then
    echo "MMAR AddRMSNorm build artifact hash mismatch" >&2
    exit 47
  fi
fi
if [[ "$mode" == mmar-on-hccl-aiv ]]; then
  hccl_op_expansion_mode=AIV
fi
if [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024 ||
      "$mode" == mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024-static-kernel ]]; then
  hccl_buffsize=1024
fi
if [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-taskqueue2 ]]; then
  task_queue_enable=2
fi
if [[ "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384 ]]; then
  max_num_batched_tokens=16384
elif [[ "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192 ]]; then
  max_num_batched_tokens=8192
fi
if [[ "$mode" == tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95 ]]; then
  max_num_batched_tokens=8192
  max_model_len=32768
  gpu_memory_utilization=0.95
fi

if docker container inspect "$container_name" >/dev/null 2>&1; then
  echo "refusing to replace existing container: $container_name" >&2
  exit 41
fi

# npu-smi can briefly report no device process while another container is
# starting its runtime. Treat a running container that reserves any assigned
# physical device as occupied before checking the process table. The two exact
# names below are long-lived, operator-verified monitor/admin shells: they only
# mount device files and have no NPU runtime process. An explicit empty override
# disables this host-local allowlist.
reservation_ignore_names="${NPU_RESERVATION_IGNORE_NAMES-/vllm-ep-310p-research-910b-monitor,/vllm-19.1-Qwen3.5-4B-1065}"
container_reservations="$(
  for running_id in $(docker ps -q); do
    docker inspect --format '{{.Name}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' "$running_id"
  done | awk -v ignored_csv="$reservation_ignore_names" -v wanted="$physical_npu_csv" '
    BEGIN {
      split(ignored_csv, ignored_names, ",")
      for (item in ignored_names) {
        ignored[ignored_names[item]] = 1
      }
      split(wanted, ids, ",")
      for (item in ids) selected[ids[item]] = 1
    }
    {
      reserved = 0
      for (id in selected) {
        if ($0 ~ ("/dev/davinci" id "([[:space:]]|$)")) reserved = 1
      }
      if (reserved && !($1 in ignored)) print
    }
  '
)"
if [[ -n "$container_reservations" ]]; then
  echo "refusing to start: a running container reserves physical NPU$device_set" >&2
  echo "$container_reservations" >&2
  exit 48
fi

npu_snapshot="$("$npu_smi_bin" info)"
occupied="$(
  awk -F '|' -v wanted="$physical_npu_csv" '
    BEGIN {
      split(wanted, ids, ",")
      for (item in ids) {
        selected[ids[item]] = 1
      }
    }
    $2 ~ /^[[:space:]]*[0-7][[:space:]]+[0-9]+[[:space:]]*$/ &&
    $3 ~ /^[[:space:]]*[0-9]+[[:space:]]*$/ {
      gsub(/[[:space:]]/, "", $2)
      gsub(/[[:space:]]/, "", $3)
      npu = substr($2, 1, 1)
      if (selected[npu]) {
        print "NPU" npu ":pid=" $3
      }
    }
  ' <<<"$npu_snapshot"
)"
if [[ -n "$occupied" ]]; then
  echo "refusing to start: physical NPU$device_set are not idle" >&2
  echo "$occupied" >&2
  exit 42
fi

serve_args=(
  vllm serve /cache/austinov/Qwen3.8-27B
  --host 127.0.0.1
  --port "$port"
  --tensor-parallel-size "$tensor_parallel_size"
  --pipeline-parallel-size "$pipeline_parallel_size"
  --data-parallel-size "$data_parallel_size"
  --seed 1024
  --served-model-name Qwen3-5/Qwen3.5-27B
  --max-num-seqs 16
  --max-model-len "$max_model_len"
  --max-num-batched-tokens "$max_num_batched_tokens"
  --trust-remote-code
  --gpu-memory-utilization "$gpu_memory_utilization"
  --enable-prefix-caching
  --mamba-cache-mode align
  --mamba-cache-dtype bfloat16
  --mamba-ssm-cache-dtype bfloat16
  --compilation-config "$(
    if [[ "$mode" == qwen35-gdn-prefetch0p1-sp-pass ]]; then
      printf '%s' '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584],"pass_config":{"enable_sp":true,"sp_min_token_num":1}}'
    elif [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-fused-tail ]]; then
      printf '%s' '{"cudagraph_mode":"FULL_DECODE_ONLY","compile_ranges_endpoints":[16,32768],"cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}'
    else
      printf '%s' '{"cudagraph_mode":"FULL_DECODE_ONLY","cudagraph_capture_sizes":[1,2,4,6,8,10,12,14,16,32,64,128,256,384,512,640,768,896,1024,1280,1536,1792,2048,2304,2560,2816,3072,3328,3456,3584]}'
    fi
  )"
  --additional-config "$(
    if [[ "$mode" == flashcomm2-oproj1-mmar-prefetch-gateup-0p1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"enable_flashcomm2_parallel_size":1,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
    elif [[ "$mode" == flashcomm2-oproj2-mmar-prefetch-gateup-0p1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"enable_flashcomm2_parallel_size":2,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
    elif [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-fused-tail ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}},"ascend_compilation_config":{"fuse_decode_mmar_add_rmsnorm":true}}'
    elif [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-static-kernel ||
            "$mode" == mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024-static-kernel ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}},"ascend_compilation_config":{"enable_npugraph_ex":true,"enable_static_kernel":true}}'
    elif [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1 ||
          "$mode" == qwen35-gdn-gateup-prefetch-0p1 ||
          "$mode" == qwen35-gdn-prefetch0p1-sp-pass ||
          "$mode" == draft4b-k3-mmar-prefetch-gateup-0p1 ||
          "$mode" == suffix-k15-mmar-prefetch-gateup-0p1 ||
          "$mode" == suffix-k16-mmar-prefetch-gateup-0p1 ||
          "$mode" == mtp-local-argmax ||
          "$mode" == mtp-k3-local-argmax-mmar-prefetch-gateup-0p1 ||
          "$mode" == mmar-on-weight-prefetch-gateup-0p1-hccl-buff1024 ||
          "$mode" == mmar-on-weight-prefetch-gateup-0p1-taskqueue2 ||
          "$mode" == tp2-pp2-mmar-on-weight-prefetch-gateup-0p1 ||
          "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384 ||
          "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192 ||
          "$mode" == tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
    elif [[ "$mode" == mmar-on-weight-prefetch-gateup ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":1.0,"down":0.0}}}}'
    elif [[ "$mode" == flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true,"weight_nz_mode":1,"weight_prefetch_config":{"enabled":true,"prefetch_ratio":{"attn":{"qkv":0.0,"o":0.0},"moe":{"gate_up":0.0},"mlp":{"gate_up":0.1,"down":0.0}}}}'
    elif [[ "$mode" == flashcomm1-bf16-nz ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true,"weight_nz_mode":2}'
    elif [[ "$mode" == flashcomm1 ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":true}'
    elif [[ "$mode" == profile-mmar-off ||
            "$mode" == profile-msprof-mmar-off ||
            "$mode" == control-mmar-off ||
            "$mode" == ngram-gpu ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":false,"enable_flashcomm1":false,"weight_nz_mode":1}'
    elif [[ "$mode" == bf16-nz-mmar-off ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":false,"enable_flashcomm1":false,"weight_nz_mode":2}'
    elif [[ "$mode" == bf16-nz ]]; then
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":2}'
    else
      printf '%s' '{"enable_cpu_binding":true,"enable_matmul_allreduce":true,"enable_flashcomm1":false,"weight_nz_mode":1}'
    fi
  )"
  --default-chat-template-kwargs '{"enable_thinking":false}'
)

if [[ "$mode" == tp2-dp2-mmar-on-text-only ||
      "$mode" == suffix-k15-mmar-prefetch-gateup-0p1 ||
      "$mode" == suffix-k16-mmar-prefetch-gateup-0p1 ||
      "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt16384 ||
      "$mode" == tp2-dp2-mmar-on-weight-prefetch-gateup-0p1-text-only-bt8192 ||
      "$mode" == tp2-dp2-mmar-prefetch-0p1-text-ctx32k-bt8192-gmu0p95 ]]; then
  # query_rewrite contains text only. Disable unused image/video capacity so
  # vLLM does not load or profile the multimodal encoder on 32 GB 910B4 cards.
  serve_args+=(--limit-mm-per-prompt '{"image":0,"video":0}')
fi

# torch_npu's external profiler callback must be started and stopped from the
# same execution thread. vLLM 0.23.0 async scheduling violates that invariant
# at /stop_profile and cancels the multiprocess response queue. Profiling is
# diagnostic-only, so preserve async scheduling for performance candidates and
# use the synchronous scheduler only for the isolated profiler service.
if [[ "$mode" == profile || "$mode" == profile-mmar-off || "$mode" == suffix-k15-mmar-prefetch-gateup-0p1 || "$mode" == suffix-k16-mmar-prefetch-gateup-0p1 ]]; then
  # Omitting --async-scheduling is not sufficient in vLLM 0.23.0: the
  # effective default can still enable it.  Force profiling onto the
  # synchronous scheduler, and do the same for suffix decoding because vLLM
  # 0.23.0 rejects that proposer when async scheduling is enabled.
  serve_args+=(--no-async-scheduling)
else
  serve_args+=(--async-scheduling)
fi

if [[ "$mode" == mtp ]]; then
  serve_args+=(--speculative-config '{"method":"mtp","num_speculative_tokens":1}')
fi
if [[ "$mode" == mtp-local-argmax ]]; then
  # Greedy query_rewrite requests can use an exact vocab-parallel argmax:
  # gather one value/index pair per TP rank instead of full draft logits.
  serve_args+=(--speculative-config '{"method":"mtp","num_speculative_tokens":1,"use_local_argmax_reduction":true}')
fi
if [[ "$mode" == mtp-k3-local-argmax-mmar-prefetch-gateup-0p1 ]]; then
  # The repaired proposer honors local argmax and avoids full draft logits.
  # Three target-verified drafts are the only primary change from the retained
  # MMAR + dense gate/up prefetch stack.
  serve_args+=(--speculative-config '{"method":"mtp","num_speculative_tokens":3,"use_local_argmax_reduction":true}')
fi
if [[ "$mode" == draft4b-k3-mmar-prefetch-gateup-0p1 ]]; then
  # A separate BF16 Qwen3.5-4B proposer is verified by the 27B target. TP4 is
  # required by vLLM 0.23.0 when the target is TP4. Reserve model headroom by
  # bounding target KV memory without changing the 133K serving contract.
  serve_args+=(
    --kv-cache-memory=5000000000
    --speculative-config '{"model":"/cache/Qwen3.5-4B","method":"draft_model","num_speculative_tokens":3,"draft_tensor_parallel_size":4}'
  )
fi
if [[ "$mode" == suffix-k16-mmar-prefetch-gateup-0p1 ]]; then
  # Suffix Decoding is training-free and target-verified. It adapts proposal
  # depth to repeated prompt/generated suffixes and does not load another model.
  serve_args+=(--speculative-config '{"method":"suffix","num_speculative_tokens":16}')
fi
if [[ "$mode" == suffix-k15-mmar-prefetch-gateup-0p1 ]]; then
  # Ascend's fused TND attention accepts a decode threshold of at most 16.
  # The threshold includes the current token, so at most 15 suffix drafts fit.
  serve_args+=(--speculative-config '{"method":"suffix","num_speculative_tokens":15}')
fi
if [[ "$mode" == ngram-gpu ]]; then
  # Prompt Lookup Decoding is training-free and lossless under target-model
  # verification. Keep proposal generation on NPU so async scheduling remains
  # enabled and the CPU proposer does not become a host-side bottleneck.
  serve_args+=(--speculative-config '{"method":"ngram_gpu","num_speculative_tokens":5,"prompt_lookup_min":2,"prompt_lookup_max":5}')
fi

if [[ "$mode" == profile || "$mode" == profile-mmar-off ]]; then
  if [[ -e "$profile_dir" ]]; then
    echo "refusing to reuse profile directory: $profile_dir" >&2
    exit 44
  fi
  mkdir -p "$profile_dir"
  serve_args+=(
    --profiler-config.profiler torch
    --profiler-config.torch_profiler_dir "$profile_dir"
  )
fi

device_args=()
for index in "${!physical_npus[@]}"; do
  physical_id="${physical_npus[$index]}"
  device_args+=(--device "/dev/davinci$physical_id:/dev/davinci$index")
done

docker_args=(
  run -d
  --name "$container_name"
  --network host
  --cpuset-cpus "$cpuset_cpus"
  "${device_args[@]}"
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
  -e ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
  -e HCCL_BUFFSIZE="$hccl_buffsize"
  -e OMP_PROC_BIND=false
  -e OMP_NUM_THREADS=1
  -e TASK_QUEUE_ENABLE="$task_queue_enable"
  -e TRITON_KERNEL_DUMP=1
  -e TRITON_DUMP_DIR=/cache/efim/triton_dump
  -e VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE="$matmul_allreduce_env"
  -e VLLM_ASCEND_ENABLE_FLASHCOMM1="$flashcomm1_env"
  -e VLLM_ASCEND_ENABLE_NZ="$weight_nz_env"
  -e VLLM_ASCEND_ENABLE_DENSE_FFN_NZ="$selective_ffn_nz_env"
  -e VLLM_ASCEND_PTO_CHUNK_GDN=1
  -e VLLM_LOGGING_LEVEL=DEBUG
)

if [[ "$mode" == draft4b-k3-mmar-prefetch-gateup-0p1 ]]; then
  docker_args+=(
    -v "$draft4b_model:$draft4b_model:ro"
    -v "$draft_model_fix_root/vllm/config/speculative.py:/vllm-workspace/vllm/vllm/config/speculative.py:ro"
    -e VLLM_DRAFT_MODEL_CONFIG_FIX_COMMIT="$draft_model_fix_commit"
  )
fi

if [[ -n "$hccl_op_expansion_mode" ]]; then
  docker_args+=(-e HCCL_OP_EXPANSION_MODE="$hccl_op_expansion_mode")
fi

if [[ "$mode" == selective-ffn-nz ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$selective_ffn_nz_root/vllm_ascend/envs.py:$image_source_root/envs.py:ro"
    -v "$selective_ffn_nz_root/vllm_ascend/utils.py:$image_source_root/utils.py:ro"
    -v "$selective_ffn_nz_root/vllm_ascend/ops/linear.py:$image_source_root/ops/linear.py:ro"
  )
fi
if [[ "$mode" == qwen35-gdn-gateup-prefetch-0p1 ||
      "$mode" == qwen35-gdn-prefetch0p1-sp-pass ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$qwen35_gdn_prefetch_root/vllm_ascend/ops/weight_prefetch.py:$image_source_root/ops/weight_prefetch.py:ro"
    -v "$qwen35_gdn_prefetch_root/vllm_ascend/ops/layernorm.py:$image_source_root/ops/layernorm.py:ro"
    -e VLLM_ASCEND_QWEN35_GDN_PREFETCH_COMMIT="$qwen35_gdn_prefetch_commit"
  )
fi
if [[ "$mode" == mtp-local-argmax ||
      "$mode" == mtp-k3-local-argmax-mmar-prefetch-gateup-0p1 ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$mtp_local_argmax_root/vllm_ascend/patch/worker/patch_qwen3_5.py:$image_source_root/patch/worker/patch_qwen3_5.py:ro"
    -v "$mtp_local_argmax_root/vllm_ascend/spec_decode/llm_base_proposer.py:$image_source_root/spec_decode/llm_base_proposer.py:ro"
    -e VLLM_ASCEND_MTP_LOCAL_ARGMAX_COMMIT="$mtp_local_argmax_commit"
  )
fi
if [[ "$mode" == flashcomm2-oproj1-mmar-prefetch-gateup-0p1 ||
      "$mode" == flashcomm2-oproj2-mmar-prefetch-gateup-0p1 ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$flashcomm2_mmar_root/vllm_ascend/ops/linear_op.py:$image_source_root/ops/linear_op.py:ro"
    -v "$flashcomm2_mmar_root/vllm_ascend/ascend_forward_context.py:$image_source_root/ascend_forward_context.py:ro"
    -v "$flashcomm2_mmar_root/vllm_ascend/platform.py:$image_source_root/platform.py:ro"
  )
fi
if [[ "$mode" == mmar-on-weight-prefetch-gateup-0p1-fused-tail ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$mmar_add_rmsnorm_root/vllm_ascend/ascend_config.py:$image_source_root/ascend_config.py:ro"
    -v "$mmar_add_rmsnorm_root/vllm_ascend/compilation/compiler_interface.py:$image_source_root/compilation/compiler_interface.py:ro"
    -v "$mmar_add_rmsnorm_root/vllm_ascend/compilation/graph_fusion_pass_manager.py:$image_source_root/compilation/graph_fusion_pass_manager.py:ro"
    -v "$mmar_add_rmsnorm_root/vllm_ascend/compilation/passes/decode_mmar_add_rmsnorm_fusion_pass.py:$image_source_root/compilation/passes/decode_mmar_add_rmsnorm_fusion_pass.py:ro"
    -v "$mmar_add_rmsnorm_extension:$image_source_root/vllm_ascend_C.cpython-312-aarch64-linux-gnu.so:ro"
    -v "$mmar_add_rmsnorm_kernels:$image_source_root/lib/libvllm_ascend_kernels.so:ro"
    -e VLLM_ASCEND_CUSTOM_EXTENSION_COMMIT="$mmar_add_rmsnorm_commit"
  )
fi
if [[ "$mode" == flashcomm1-gdn-shape-mmar-prefetch-gateup-0p1 ]]; then
  image_source_root=/vllm-workspace/vllm-ascend/vllm_ascend
  docker_args+=(
    -v "$flashcomm1_gdn_root/vllm_ascend/ascend_forward_context.py:$image_source_root/ascend_forward_context.py:ro"
    -v "$flashcomm1_gdn_root/vllm_ascend/ops/gdn.py:$image_source_root/ops/gdn.py:ro"
    -v "$flashcomm1_gdn_root/vllm_ascend/ops/linear_op.py:$image_source_root/ops/linear_op.py:ro"
    -e VLLM_ASCEND_FLASHCOMM1_GDN_SOURCE_COMMIT="$flashcomm1_gdn_commit"
  )
fi

if [[ "${ENABLE_DYNAMIC_PROFILING:-0}" == 1 ||
      "$mode" == profile-msprof-mmar-off ||
      "$mode" == profile-msprof-mmar-on ]]; then
  # CANN dynamic attach is initialized with the application, then msprof
  # controls the bounded collection window by worker PID. This avoids vLLM
  # 0.23.0's broken lazy torch-profiler initialization on a different thread.
  # The on mode intentionally falls through the normal MMAR-enabled config.
  docker_args+=(-e PROFILING_MODE=dynamic)
fi

docker "${docker_args[@]}" quay.io/ascend/vllm-ascend:v0.23.0 "${serve_args[@]}"
