# Tail-Replay recurrence-only Ascend result

Updated: 2026-09-14

## Outcome

The first complete recurrence-only NPU gate passed as an experiment harness
and produced a negative mechanism signal for zero-state tail-only recurrence.
It is not yet a terminal Tail-Replay result.

The successful run used Qwen3.6-27B, TP4, physical NPU4-7, eager execution and
a single 650-token prompt. It covered all 48 GDN layers, all four ranks and the
paper's 5% and 10% replay ratios. The service output was not mutated.

| Ratio | Rows | Exact-split mean/max rel-L2 | Zero-tail mean/max rel-L2 | Zero-tail mean cosine |
|---|---:|---:|---:|---:|
| 5% | 192 | 0.002167 / 0.003025 | 0.518888 / 0.886842 | 0.830751 |
| 10% | 192 | 0.002701 / 0.003491 | 0.494324 / 0.877730 | 0.846344 |

All 384 exact-split controls passed the frozen 0.01 global relative-L2 limit.
This validates the sliced Ascend chunk metadata and continuation harness.
The zero-state tail-only final state is nevertheless far from the full-prefix
state at both ratios. Ten percent is only modestly better on average.

## Evidence boundary

This oracle starts after causal convolution and reuses the full model's
projected per-layer inputs. It does not reconstruct convolution state, replay
the three-layer GDN group from an attention boundary, propagate replayed hidden
states, compare first-token logits, use prefix-cache hits, or measure TTFT.
Those omissions prevent both a quality claim and a terminal rejection.

The next gate is a full GDN-group replay canary with exact-replay controls,
causal-convolution state, inter-layer hidden propagation, boundary-hidden
metrics and first-token comparison. Performance work remains blocked until
that numerical gate passes.

## Failed-attempt lessons

- v1 and v2 failed before model load because a top-level torch import caused an
  early torch_npu probe in the model-inspection subprocess. Moving torch imports
  behind runtime hooks fixed startup; CPU affinity was not the cause.
- v3 reached NPU but the sliced replay passed no prebuilt chunk metadata. The
  dynamic fallback was not ABI-safe for this live AscendC path and raised an
  AICore out-of-bounds exception. The failure was preserved.
- v4 rebuilt the same GDNChunkedPrefillMetadata fields used by the live
  vLLM-Ascend builder, added per-call attempt evidence, and synchronized after
  each diagnostic NPU call. It completed successfully.

Primary artifacts:

- `/cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/summary.json`
- `/cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/runtime.jsonl`
- `/cache/cch/tail-replay-qwen36-ascend-tp4-20260914/recurrence-oracle/short-v4/response.json`

After the run, the service was stopped and physical NPU4-7 were verified free.
Physical NPU0-3 remained occupied by an unrelated task and were never mapped
into the Tail-Replay container.
