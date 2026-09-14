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

After these corrections the complete repository suite reported:

    35 passed in 8.79s

One intermediate run reported 34 passed and 1 failed because a digest fixture
still contained the old forced-recent block. Only the stale expected set was
updated.

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
