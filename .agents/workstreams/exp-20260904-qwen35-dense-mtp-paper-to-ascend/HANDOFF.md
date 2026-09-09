# Qwen3.5 Dense MTP Paper-to-Ascend

## Maintainer task boundary — 2026-09-07

This branch is the Paper-to-Ascend research/migration track, not the active
Qwen3.5 production performance loop. It owns paper selection, mechanism
applicability, a bounded Ascend prototype, and a paper-level accept/reject
record. It does not own the frozen `query_rewrite.jsonl` denominator, the
c1/c5/c8/c16 1.5x P95 stop gate, or the final serving-stack decision; those
belong to `exp-20260904-qwen35-query-rewrite-3x-e2e`.

The selected MTP/speculative-decoding candidate is now superseded by the
user's no-MTP/no-speculative constraint. Preserve its inconclusive baseline
and failed-start evidence as history, but do not resume or present it as the
current Qwen3.5 optimization task. This workstream has no active NPU or port
lease. Its next valid loop is to select a non-speculative, no-retraining,
no-quantization inference-time paper whose mechanism addresses a measured
dense Qwen3.5/vLLM-Ascend bottleneck. Any resulting implementation is a
candidate input to the performance workstream and must pass that workstream's
independent baseline, quality, and delivery-contract gates.

## State

- Execution: `completed-superseded-policy`; integration: `superseded`; decision:
  `rejected-policy` for the MTP candidate.
- Branch: `work/exp-20260904-qwen35-dense-mtp-paper-to-ascend`.
- Base: `origin/main@fbc79c41c37c8900f0623ce8941304e9bfde5cf1`.
- Latest local checkpoint before this handoff update: `5b0f328`.
- No experiment container remains. This workstream owns no NPU or port lease.
- Do not stop or change `qwen38_paper_baseline_npu0_3` (physical NPU0-3,
  port 8211) or `qwen38_gdn_fused_candidate` (physical NPU4-7, port 8210).

## Historical selected method

The candidate is distribution-preserving speculative decoding with the
checkpoint's built-in Qwen3.5 MTP head. It requires no retraining or external
draft checkpoint. Selection is backed by the local model's
`mtp_num_hidden_layers=1`, 15 MTP tensors, installed vLLM/vLLM-Ascend
`qwen3_5_mtp` source paths, and historical Decode profiles dominated by
repeated MatMul and TP communication.

Frozen candidate delta:

```text
baseline: FULL_DECODE_ONLY graph, speculative decoding off
candidate: --enforce-eager --speculative-config
           '{"method":"qwen3_5_mtp","num_speculative_tokens":3}'
```

## Evidence obtained

- A diagnostic concurrency-8 baseline completed three 64-request repetitions:
  output throughput 163.088 / 163.988 / 165.085 tok/s; median 163.988 tok/s.
- Median request throughput was 0.6406 req/s; median TPOT was 44.403 ms.
- Eight deterministic greedy outputs were captured as the correctness reference.
- Raw evidence is under
  `/cache/austinov/paper-to-ascend/qwen35-dense-mtp/baseline`.
- Treat all baseline numbers as non-decisional: a pre-existing NPU0-3 workload
  was discovered afterward, so exclusive ownership was not proven.
- The candidate made zero measured requests. Its first start failed before
  weight load when the model-inspection subprocess could not query Ascend
  device count/architecture; NPU0-3 were already occupied.

## Historical resume sequence (superseded; do not execute)

The sequence below records what would have been required to complete the MTP
experiment before the policy change. It is audit history only. The current
resume action is the non-speculative paper-selection loop in the task-boundary
section above.

1. Confirm an owner has explicitly released either physical NPU0-3 or NPU4-7.
2. Run host `npu-smi info`, container device-map inspection, port checks, and
   process ownership checks in the same session. Do not infer availability from
   container age or an idle API alone.
3. Wait at least 20 seconds after worker teardown and re-check HBM/processes.
4. Use a fresh endpoint and run baseline then candidate serially on the same
   physical devices. Repeat concurrency 8 three times with 256 input and 256
   output tokens, 64 requests, seed 20260904, and eight warmups.
5. Compare the eight greedy canary texts and completion-token counts exactly.
6. Record speculative acceptance metrics and collect comparable steady Decode
   profiles for both arms before deciding.
7. Accept only for at least 5% median output-throughput improvement with exact
   correctness; otherwise reject or retain inconclusive with the observed gate.

## Historical maintainer lessons

- Prefix Cache: a plausible feature can regress the actual traffic shape.
  On exact 2048/40, concurrency-8 traffic it reduced output throughput by
  20.18% and increased wall time by 25.28%; workload-specific repeated A/B beats
  feature-level intuition.
- Dynamic MoE: reduced compute is not end-to-end speedup. Expert pairs fell
  about 12-13.5% and expert GMM improved 8.85%, but sort/cumsum/compaction made
  routing 6.36x slower and whole-block latency 82-96% worse. Profile the glue,
  not only the target kernel.
- Dynamic MoE environment recovery: mapping device nodes alone was insufficient;
  driver/DCMI binds from a known-good vLLM container were required.
- This MTP attempt: prove physical-device exclusivity immediately before every
  arm. A benchmark that completes under contention is evidence to retain, but
  not evidence from which to make a production decision.
- Preserve failed starts and invalid runs with an explicit validity label;
  never silently average them into successful repetitions.

## Validation and rollback

- Repository validation: `./scripts/validate-mst.sh` and `git diff --check`.
- Rollback for this workstream is complete: `qwen35_dense_mtp_ab` was removed.
- The 2026-09-09 consolidation audit found a clean, pushed worktree with no
  process CWD, command-line reference, container mount, NPU/port lease, or
  active experiment container. The remote branch retains all negative evidence
  and is eligible for worktree reclamation without merging the superseded MTP
  candidate into `main`.
- Large artifacts remain outside Git and are referenced from the experiment
  record; hashes should be regenerated after the final uncontended run.
