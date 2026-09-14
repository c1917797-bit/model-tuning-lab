# SlimInfer Semantic Selection Shadow Preparation — 2026-09-14

## Decision scope

This checkpoint implements and tests the paper-faithful semantic block score
needed by a later Qwen3.6-27B TP4 Ascend shadow canary. It does not alter model
outputs, attention masks, token rows, KV-cache rows, or scheduler state.
Therefore it is not evidence of algorithmic pruning, NPU correctness,
performance, or quality.

## Implemented contract

- Input Q and K are flattened, request-local whole-prompt tensors with shapes
  [T, Hq_local, D] and [T, Hkv_local, D].
- A block contains 64 prompt tokens.
- A semantic key unit contains 8 tokens.
- The local query is the mean of the request's most recent 4 query rows.
- Each semantic representative key is the mean of its unit's key rows.
- GQA KV heads are repeated over their corresponding query heads.
- Each TP rank computes a per-unit local query-head sum.
- The per-unit vectors are sum-reduced across TP ranks before dividing by the
  global query-head count.
- Only after the collective is each block score formed by the maximum of its
  semantic-unit scores.
- Request boundaries and partial final units/blocks are explicit and
  fail-closed.

The first runtime canary remains limited to complete whole-prompt prefill.
Later stages must add an explicit compact-row to absolute-block mapping; they
must not silently treat post-pruning compact ordinals as original block IDs.

## Verification

The first focused test run reported 28 passed and 1 failed. The failing test
intended to prove that a collective changing the score-vector shape is rejected,
but its two input tokens used the default 8-token unit size and therefore
produced only one unit. Slicing to one element did not change the shape. The
fixture was corrected to use unit_size=1; no production logic was weakened.

The corrected full repository run in the pinned vLLM-Ascend v0.23.0 image:

    29 passed in 8.51s

Additional gates:

- Maintainer Skill Tree: 26 skills valid.
- git diff --check: passed.
- Ruff was not installed in the pinned image; a manual 100-column line-length
  check passed and the missing tool is recorded rather than treated as a pass.
- No NPU device was exposed to either validation container.

Tests cover a hand-computed score, GQA head replication, TP reduction before
unit max, cross-request isolation, partial units and blocks, invalid shapes,
non-finite values, collective contract failures, and deterministic selection
digest integration.

## Remaining gates

The offline implementation now includes a post-import wrapper that is installed
after the final vLLM-Ascend Qwen3.5 patch. At layers 19, 39, and 59 it
duplicates the pinned Ascend QKV projection and fused split only to obtain the
normalized, position-encoded Q/K; reads request boundaries from the live
attention query_start_loc; performs a real tensor-model-parallel per-unit
all-reduce; and emits staged request-local selection evidence. The original
attention forward is still called exactly once and the wrapper does not mutate
outputs or cache state.

During this audit two semantics were corrected before NPU execution:

- query_start_loc is used as the authoritative cumulative request boundary;
  actual_seq_lengths_q is not assumed to be a vector of ordinary lengths;
- only the first sink prompt block is mandatory, matching the paper. The
  previous planner also forced the most recent prompt block.

A later integration audit found the same obsolete forced-recent rule still in
the compact-cache stream contract. It was removed there as well. Generated
response tokens remain a separate always-retained decode stream; they are not a
reason to force the newest prompt block.

After these corrections the complete repository suite reported:

    35 passed in 8.79s

One intermediate run reported 34 passed and 1 failed because a digest fixture
still contained the old forced-recent block. Only the stale expected set was
updated.

A fail-closed evidence auditor is now available at
tools/summarize_sliminfer_shadow.py. It requires all expected TP ranks, all
three boundary layers, identical score and selection digests across ranks,
monotonically shrinking staged block sets, and at least one actual block-count
reduction. Tests prove that rank disagreement, a missing rank, and activation
without pruning are rejected. With this audit included, the complete suite is:

    38 passed in 8.97s

A no-device plugin startup smoke also passed in selection-shadow mode. It
emitted plugin_build_active, model_patch_deferred, and
selection_shadow_patch_deferred in that order. This proves the opt-in package
registers both hooks; it does not prove that the live model imports or executes
them.

A stronger no-device import of the real vLLM-Ascend worker patch was attempted.
It stopped before the Qwen patch module imported because Ascend Triton could not
obtain a SoC target without an exposed NPU. The SlimInfer hook did not execute,
so this is an environment-precondition result, not a failed hook result. Patch
order must be verified by the first TP4 worker canary.

Two deterministic canary tools were also added. The request tool sends an exact
13,000-token explicit token-ID prompt at temperature 0 and seed 0. The parity
tool rejects field or request-hash drift and compares generated text, returned
token strings, finish and stop reasons, and prompt/completion token counts while
ignoring response IDs and timestamps. The request tool also rejects a service
response whose observed prompt-token count differs from the requested 13,000.
With these tools included, the complete suite is:

    42 passed in 8.51s

`tools/run_sliminfer_shadow_tp4.sh` now composes the first live TP4 gate. It
fails before mutation unless physical NPU4-7 are all idle, the pinned image and
model exist, the source tree is clean, the port is free, and a fresh output
root and container names are available. It then runs disabled and enabled arms
sequentially, verifies container ownership of all four devices, preserves
container/log/device evidence, audits TP-rank selection agreement, compares
the deterministic outputs, and stops only containers bearing its experiment
label. This controller has passed Bash syntax and diff checks but has not been
run because NPU4-7 are occupied. Its corrected dry preflight returned exit 1
with the four observed foreign worker PIDs, while the fresh output root and
experiment-labeled container set both remained absent.

Remaining gates:

1. Run the wrapper in the pinned image on physical NPU4-7 after proving the
   lane is free.
2. Prove all four ranks loaded the final Ascend source and produced identical
   staged selection digests.
3. Prove enabled and disabled outputs are exactly equal.
4. Only then implement actual row/cache pruning and run a paired performance
   screen.

At this checkpoint physical NPU4-7 were occupied by external VLLMWorker_TP
processes and were left untouched.
