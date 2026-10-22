# BOLE reduction diagnosis — source/preflight checkpoint

Recorded 2026-10-22 20:31 UTC. This is not a paper acceptance result.

## Current execution

- Canonical host checkout remains /opt/host/vnf/austinov/model-tuning-lab,
  work/qwen36-damp-ascend-20261006.
- Direct target chicaihong01/ma was freshly resolved and proven.
- Source-only ON freeze: exec-00000000000007d6, exit0.
- Exact source audit: exec-00000000000007d8, exit0.
- Bound source SOURCE_BOUND.json: 1643301 bytes,
  SHA256 5ac4e1404f51f2bccf43d4a45b5be2bcbac4f4f3a90b79af0dabb5ab463ceeb8.
- MAIN fresh snapshot exec-00000000000007df completed without error;
  launcher was dispatched with the actual snapshot age90.32 seconds.
- Live unit bole-reduction-on-v5-20261022t200000z-u1.service,
  host owner PID1613469. Dispatch receipt exec-00000000000007e3.
- CPU preflight container a7654d39736ea168899ed2dc913b9b342912def11a41b7ef7b5eb1b303762111
  completed software/parser children exit0 and stopped retained.
- Actual model container b2be61054ac21c311a2a28f21d9abe7ef8bfc5474245b2f603f4b20f0ed5014e
  started20:28:28 UTC. exec07f4 proves physical4–7 mapped to logical0–3,
  four-device tiny canary passed, and the server was compiling.
- Source/output root:
  bound-reduction-ON-v5_20261022T200000Z under this workstream;
  /opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z.
- Shared MAIN_ADMISSION.lock is held by the exec-owned lifecycle.
  Inspect the exact unit/container before any new overlapping dispatch.
- Unchanged internal cutoff23:10 UTC, phase3600, cleanup180. This does not
  rewrite the expired original report deadline or the original48-hour goal.

## Actual purpose and limits

The preceding V4 result completed two131-input/8-output requests. All four
local pre-reduce hashes agreed across generations within rank, while reduced
output hashes differed across generations. V4 did not retain complete reduction
operands. Native all_reduce is in-place by design; alias alone is not a defect.
This is the first observed divergence, not a proved HCCL or BOLE root cause.

V5 saves complete pre/post-reduce BF16 operands and existing worker execution
flags. It does not modify mathematics, thresholds, device-read volume, or
original64MiB/1GiB aggregate evidence caps. Its8MiB raw suballocation is charged
inside those caps. G1 remains warmup and G2 measured, not two warmed repeats.

Prepared ON/OFF means observation policy in the same BOLE/MTP configuration.
OFF is NOT native_AR/dense and cannot be used as the paper performance control.
Only ON has been frozen and launched.

## Preparation corrections and checks

The initial preparation had two real interface defects caught before NPU:
incorrect ON_v5 versus ON-v5 producer paths, and a stale auditor lacking fields
consumed by the actual launcher. Both original failures are preserved. Repaired
auditor derives the actual V4 auditor and preserves complete readsets and literal
MODEL/CPU source operands. Actual15 host preparation checks and both pure renders
passed; they do not replace the original same-image20 or NPU checks.

Independent BF16 analysis has13 software checks and a full-shape software budget
measurement about31.9s/39MiB. That measures the diagnostic consumer, not inference.
The replay worker has15 host checks and independent source review, not NPU PASS.
Replay WORLD and production vLLM TP groups may differ; an absent replay failure
cannot by itself blame BOLE. Mapping semantics require MAIN evidence.

## Next executable edges

1. Observe this same unit through HTTP/raw capture and own retained cleanup;
   preserve any first fault and do not launch a duplicate.
2. Validate actual8 projection envelopes,16 full raw files and4 completion
   records using consumer_handoff_prepare. Never manufacture a legacy PASS.
3. Run independent exact-sum/rounding-order analysis on actual captures.
4. If diagnostic evidence warrants it and the fixed clock/resources permit,
   execute separate default and deterministic HCCL replays with fresh owners.
5. BOLE numerical/state qualification, native_AR/candidate fixed1024 performance,
   three paired repetitions, and GSM8K/HumanEval/MMLU remain uncompleted.

No model_ready, candidate_qualification, performance improvement, task accuracy,
paper-wide failure, or full-window NPU utilization claim follows from this file.

Checkpoint validation: Maintainer Skill Tree20 passed; Python sources compiled
and default-OFF launchers were exercised. Staged diff check found only five
extra blank lines at EOF, including immutable pinned helpers. These bytes are
preserved rather than invalidating live source Refs for formatting. The scoped
trailing-space/space-before-tab check is reported separately from the default
EOF-sensitive check; no algorithm or numerical test is weakened.
