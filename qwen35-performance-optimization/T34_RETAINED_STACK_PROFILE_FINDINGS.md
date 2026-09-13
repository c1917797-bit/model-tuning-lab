# T34: retained-stack decode profile findings

## Decision

The retained T32 upstream fused-GDN prefill stack remains the TTFT base, but
the current profile does not admit another copy-only, activation-only, or
configuration-only decode candidate. The next live treatment must change a
complete MMAR/collective boundary and must be materially different from the
already rejected MatmulAllReduceAddRmsNorm integrations.

This is diagnostic profiler evidence, not an unprofiled end-to-end performance
result.

## Captured state

- Service artifacts:
  `/cache/austinov/qwen35-t34-retained-profile-service-20260913-v1`
- Raw four-rank profile:
  `/cache/austinov/qwen35-t34-retained-profile-raw-20260913-v1`
- Analysis root:
  `/cache/austinov/qwen35-t34-retained-profile-analysis-20260913-v1`
- Image: unchanged official `quay.io/ascend/vllm-ascend:v0.23.0`
- Treatment: removable read-only T32 monkeypatch, physical NPU0-3 only
- One real profiled request completed; all four rank `op_summary` files were
  preserved and hashed.
- The owned profile container was stopped after capture and NPU0-3 were
  verified free. No NPU4-7 container was touched.

Analysis digests:

- `mmar-timeline.txt`:
  `7295a8da66a6eeaa6c44e04a365afbeb129d2910d8731f509f0982c3c2a903cf`
- `dense-tail-budget.json`:
  `9497bd941b3c5fef72178e4ea46d54950b2895126af1a853d7fbbd2a84138fa0`
- `gdn-terminal-budget-current.json`:
  `6c88b483ec8eeffa070ab364789f060881f48dac219fdc5b5718eb5cf1486ae4`
- `decode-op-groups.json`:
  `52e55f4f2f82ad0e76213b0a318b2c80cf015bdcd95fa08db6ab79e834cb6520`
- `gdn-decode-chain.json`:
  `5c5d83ad33c6940037e3227fa644be2b58b5adf4130d26025670d2acee06bbd9`

## Hotspot boundary

Across the four rank summaries, summed kernel duration is dominated by
collective/MMAR work:

- collective-class kernels: 69.049 percent;
- matmul-class kernels: 21.706 percent;
- GDN decode kernels: about 1.007 percent;
- Cat: about 0.916 percent;
- transpose: about 0.965 percent;
- norm: about 0.415 percent;
- SwiGLU: about 0.481 percent.

Summed durations overlap and are not wall time. They are used only to reject
sub-one-percent targets as sole TPOT treatments.

## Decode MMAR shapes

The profile contains 105 decode steps and 64 calls per step for each principal
M=1 MMAR shape.

| Shape | Per-rank median core duration |
|---|---:|
| `1x1536 @ 1536x5120` | 51.120 to 53.041 us |
| `1x4352 @ 4352x5120` | 91.582 to 92.120 us |

The K4352 projection alone costs as much as 5922.591 us/step. Together with
SwiGLU, the measured dense-tail chain reaches 6205.585 us/step on the slowest
rank. SwiGLU is only 4.560 percent of that chain, so even a zero-cost
activation has a ceiling of 1.0478x for this local chain.

The dense-tail analyzer's 1.15x local admission gate requires at least
809.424 us/step total saving, including 526.430 us/step from the MMAR side
(8.225 us/call). That local gate is not the final TPOT target.

The retained T32 service still needs 2.2583 ms/token to reach the final c1
TPOT threshold. If K4352 MMAR were the only contributor, it would require
about 35.29 us/call, roughly 38 percent of its current core duration. Small
launch-parameter changes are therefore not budget-credible.

## Cross-rank timing caution

The current report shows roughly 133-134 us median cross-rank start and end
spread for both decode M=1 shapes. Because the start and end offsets are nearly
the same, and an earlier control capture reported only 5-8 us decode start
spread, the current value may include inter-rank profiler clock offset. It is
not admissible evidence of scheduler delay without clock-alignment proof.

Large prefill start skew also converges to much smaller end skew. That remains
a diagnostic clue, not a claimed removable latency.

## GDN terminal budget

The current 48-layer GDN norm-to-K1536-MMAR envelope has a maximum-rank median
of 64.75 us/layer and a zero-cost upper bound of 3.108 ms/token. Covering the
2.2583 ms/token final gap from this boundary alone would require realizing
about 72.7 percent of the entire theoretical envelope. The existing upstream
MatmulAllReduceAddRmsNorm operator has the reverse matmul-to-add-to-norm
semantic order and its prior full-service integrations regressed TPOT.

Do not build a GDN terminal fusion blindly and do not rerun the old fused
AddRMSNorm path unchanged.

## GDN decode preprocessing chain

The four-rank analysis paired all 5,040 GDN calls per rank: 105 decode steps
times 48 GDN layers. On the slowest rank, the median per-layer weight
transpose is 13.22 us, or only 0.63456 ms/token if made completely free. That
is 28.099 percent of the 2.2583 ms/token gap, so one-time conv-weight
prepacking is admissible only as a stack component.

The complete transpose-to-recurrent envelope is 58.25 us/layer, or
2.796 ms/token. This covers 123.81 percent of the measured gap in the
zero-cost upper bound and is the first GDN decode boundary with enough budget
to remain a serious successor. It still requires an upstream-derived
implementation, BF16 equivalence, and end-to-end proof.

## Next admission gate

Audit current upstream vLLM-Ascend, ops-transformer, and CANN-supported A2 BF16
paths for a materially different MMAR/collective boundary. A candidate may use
the device only after all of the following are explicit:

1. pinned upstream source and the reason it is not already active in v0.23.0;
2. a Qwen3.5-specific delta beyond copying upstream code;
3. a conservative whole-token budget that can cover 2.2583 ms/token;
4. exact BF16 numerical and collective-semantics gates;
5. removable activation in the unchanged official image.
