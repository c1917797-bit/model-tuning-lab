# Qwen3.8 Paper-to-Ascend Manual Piercing (Current Environment)

This is the environment-specific adaptation of the successful Hypic manual piercing practice. It is a recovery/runbook, not evidence that the full experiment has run.

## 0. Verified environment

- Host control peer is topology-resolved at resume time; do not persist a stale peer id.
- Image: `quay.io/ascend/vllm-ascend:v0.23.0`.
- Image digest: `sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a`.
- Device: 8 x Ascend 910B4.
- Allowed lane: host NPU0-3 and CPU112-191 only, after ownership is re-confirmed.
- Protected lane: host NPU4-7 and CPU0-95; never inspect inside, restart, stop, remove, or reuse its container.
- Base model: `/cache/austinov/Qwen3.8-27B`.
- Algorithm checkpoint target: a true DRRQR checkpoint (not the L1 checkpoint and not the fixed-first-channel speed oracle).
- Existing baseline: `qwen38_paper_baseline_npu0_3`, port 8211, host NPU0-3, CPU112-191.

Unlike the historical Hypic example, do not mount all eight cards, do not use `--privileged`, and do not pull or change the image during a frozen comparison.

## 1. Mandatory preflight (read-only)

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
git -c safe.directory="$PWD" status --short --branch
docker ps -a --format '{{.Names}}|{{.Status}}|{{.Image}}' |
  grep -E 'qwen38_paper|qwen38_gdn_fused_candidate'
docker inspect qwen38_paper_baseline_npu0_3 \
  --format 'status={{.State.Status}} cpuset={{.HostConfig.CpusetCpus}} devices={{json .HostConfig.Devices}}'
npu-smi info
```

Stop here unless the operator explicitly confirms ownership of the existing NPU0-3 baseline and authorizes replacing it. The current observation is that NPU0-3 and NPU4-7 are both occupied.

## 2. Frozen G1-G4 mapping

| Group | Native Ascend change | Algorithm/DRRQR |
|---|---:|---:|
| G1 | off | off |
| G2 | on | off |
| G3 | off | on |
| G4 | on | on |

The model, prompts, sample order, seeds, request shape, TP=4, CPU set, device set, image digest, CANN environment, compilation mode, cache policy, warmup, repetitions, and parser must remain invariant. Each cell runs three repetitions.

Do not use `Qwen3.8-27B-gdn-dk64-speed-oracle` as G3/G4 quality evidence. Do not use `Qwen3.8-27B-gdn-dk64-l1` as DRRQR.

## 3. Service invariant copied from the live baseline

```bash
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
export OMP_NUM_THREADS=1
export TASK_QUEUE_ENABLE=1

vllm serve MODEL_PATH \
  --host 127.0.0.1 \
  --port 8211 \
  --served-model-name GROUP_MODEL_NAME \
  --tensor-parallel-size 4 \
  --max-num-seqs 16 \
  --max-model-len 41984 \
  --max-num-batched-tokens 16384 \
  --kv-cache-memory=14495514624 \
  --trust-remote-code \
  --no-enable-prefix-caching \
  --compilation-config '{"cudagraph_mode":"FULL_DECODE_ONLY"}' \
  --additional-config '{"enable_cpu_binding":true}'
```

Run this only inside a container whose host mapping is exactly `/dev/davinci0..3 -> /dev/davinci0..3` and whose host CPU set is `112-191`.

The native treatment is now concretely identified as upstream commit `77d13e2c0bfa9862b711b68811889e36b9d56aca`, patch SHA256 `d16712f909810c1dd1a7704d0a7d53434032f800cb2af1f9562d11475489a76e`, using `torch_npu.npu_chunk_gated_delta_rule`. Because it can probe and fall back, source presence is not proof of activation. True DRRQR checkpoint paths remain REQUIRED.

The second-model candidate is `/cache/Qwen3.5-4B`: the same `qwen3_5_text` architecture at a different size, with 32 layers (24 GDN/linear-attention and 8 full-attention) and two local safetensors shards. It still needs its own DRRQR conversion and load/correctness validation.

## 4. Dataset and result flow

Required frozen suite: NIAH+, LongBench v2, GSM8K, CEval. GSM8K is currently available at:

`/cache/austinov/eval-data/general/prepared/gsm8k_test.jsonl`

NIAH+, exact LongBench v2, and CEval are not yet materialized, so the full run is blocked. Once all inputs exist:

```bash
d=.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend
python3 "$d/freeze_test_contract.py" \
  --contract "$d/test-contract.json" \
  --runtime-config "$d/runtime-config.json" \
  --output "$d/frozen-inputs.json" \
  --dataset NIAH+=/ABSOLUTE/FROZEN/NIAH_PLUS \
  --dataset 'LongBench v2=/ABSOLUTE/FROZEN/LONGBENCH_V2' \
  --dataset GSM8K=/cache/austinov/eval-data/general/prepared/gsm8k_test.jsonl \
  --dataset CEval=/ABSOLUTE/FROZEN/CEVAL

python3 "$d/run_analysis_pipeline.py" \
  --performance-results /ABSOLUTE/RESULTS/performance.jsonl \
  --quality-results /ABSOLUTE/RESULTS/quality.jsonl \
  --profile-evidence /ABSOLUTE/RESULTS/profile-evidence.json \
  --output-dir /ABSOLUTE/RESULTS/final-analysis \
  --noise-threshold-pp MEASURED_FROM_REPEATED_G1 \
  --minimum-improvement-percent REQUIRED_MINIMUM

Production analysis fails closed without `--profile-evidence`. Build it from
separate G1 and winning-candidate profiler captures using
`profile-evidence.template.json`; capture hooks must be disabled during
profiling.
```

Exit 0 permits inspection of an adoption recommendation. Exit 2 is fail-closed and should leave an `iterate` decision artifact.

Before any service mutation, run the fail-closed readiness checker. It is read-only and does not start or stop containers:

```bash
python3 "$d/preflight_piercing.py" \
  --runtime-config "$d/runtime-config.json" \
  --frozen-inputs "$d/frozen-inputs.json" \
  --treatment-matrix "$d/treatment-matrix.json" \
  --drrqr-checkpoint qwen38-27b=/ABSOLUTE/QWEN38_TRUE_DRRQR \
  --drrqr-checkpoint qwen35-4b=/ABSOLUTE/QWEN35_4B_TRUE_DRRQR
```

Each checkpoint must contain a completed `drrqr_manifest.json` based on `drrqr-manifest.template.json`. Preflight re-hashes the source config, calibration data, selection evidence, checkpoint config/index, verifies every indexed output shard is non-empty, and requires `changed_layers` to equal that model's full GDN layer count.

If the existing baseline is still running, the checker blocks replacement unless the operator deliberately adds `--replacement-authorization I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT`.

## 4.1 Per-group phase lifecycle

The successful employee run established an important isolation rule: performance and quality are separate service lifecycles even when they use the same group configuration. Apply this exact order independently to every model and G1-G4 cell:

1. Start the frozen group configuration on the authorized NPU0-3 lane.
2. Wait for HTTP health 200; record the service instance ID and config SHA256.
3. Warm up according to the frozen policy.
4. Run performance three times. Fixed-output load may use `ignore_eos=true`.
5. Stop that service; do not reuse profiler, graph, cache or RRQR-capture state.
6. Restart the exact same group configuration and verify the same config SHA256.
7. Wait for HTTP health 200 again.
8. Run quality three times using seed 0, temperature 0, thinking disabled, `ignore_eos=false`, `trust_remote_code=false` in the evaluator, and `extract_non_reasoning_content`.
9. Stop the service before advancing to the next group.

The known successful performance point `32768 input / 1024 output / 40 requests / concurrency 16` is reference evidence, not automatically the frozen current load. Request rate, full load matrix and parser version remain REQUIRED until the original benchmark bundle/config is delivered.

Before accepting centrally delivered resources:

```bash
python3 "$d/verify_resource_intake.py" \
  --manifest /ABSOLUTE/resource-intake.json \
  --output /ABSOLUTE/resource-intake-verification.json
```

Do not copy historical IPs, ports, `/dev/davinci10,11`, container names or user paths. Only the evaluation semantics and lifecycle are portable; current device/CPU/image invariants remain authoritative.

## 5. Current execution status

- Preflight completed read-only.
- Baseline endpoint `http://127.0.0.1:8211/v1/models` is healthy and reports `qwen38-paper-baseline`.
- NPU0-3 are occupied by that baseline.
- NPU4-7 are occupied by the protected fused-candidate workload.
- No container or NPU workload was changed.
- Full G1-G4 execution is blocked on explicit NPU0-3 replacement authority, true DRRQR checkpoints for both models, three missing frozen datasets, fused-op runtime activation proof, and measured G1 noise threshold.
