# Training-free paper selection — 2026-10-06

## Maintainer preference and unchanged acceptance

The maintainer explicitly prioritizes methods requiring neither training nor
distillation. Prefer exact serving/cache transformations, lossless algebraic
operator changes, and post-training compression based on offline statistics.
Calibration and deterministic weight-coordinate reordering are not gradient
training; disclose their data, cost and model transformations nonetheless.
Do not silently introduce LoRA, optimizer-based recovery, teacher/student
distillation, a new trained checkpoint, or speculative decoding to rescue a
candidate. Such routes are outside the current preferred workstream.

This preference does not relax evidence requirements: physical NPU4–7 only,
plugin/monkeypatch delivery, relevant NPU correctness before a performance
candidate, matched dense control, fixed 1024 output tokens for throughput,
TTFT/TPOT separately, and final non-thinking LongBench-v2/GSM8K evaluation
with max_tokens=2048 and normal EOS. The latest explicit maintainer allowance
is up to 1% end-to-end task accuracy loss, not an intermediate tensor limit;
report both percentage-point and relative loss instead of conflating them.

## Next candidate: DAMP, conditional rather than accepted

Primary source: <https://arxiv.org/html/2608.27513v2> (30 September 2026).
DAMP uses offline quantization-error and future decay-retention statistics to
protect high-risk key channels in FP16 while storing the remainder in INT8.
Value scaling/reordering, independent key-channel selection, packed storage,
and fused reconstruct/update/requantize are part of the mechanism. An ordinary
uniform INT8 cast or an FP32 sidecar roundtrip is not the paper's deployment.

The current target is dense Qwen3.6-27B/TP4 on Ascend910B4; the paper's Qwen
performance result uses a different MoE model, GPU backend and batching.
Its reported TPOT reduction therefore does not establish our +10% throughput
target. Its reasoning accuracy table also contains losses larger than one
percentage point on some tasks, so final task quality remains an open gate.
No official implementation link was verified in the inspected paper; any
equation-derived implementation must be labeled as such, not an official port.

Before a new one-day implementation loop starts, checkpoint the hypothesis,
thresholds, runtime seam and exact source identities in a dedicated work/
branch. Reuse the existing Ascend recurrent ABI and plugin/cache lifecycle
scaffolds where compatible. First verify the selector/calibration mathematics
and state trajectory on real NPU inputs; then packed-state numerical, slot,
multi-step and graph behavior. Only a valid candidate enters a profiler-off
matched fixed-output E2E screen. Missing evidence is inconclusive, not a
paper-wide no-go. This note itself is not an experiment or a formal start.

## Do not lose earlier scoped evidence

KVBuffer is also training-free, but it is not an untouched second candidate.
The inspected branch `work/kvbuffer-qwen36-ascend-piercing-20260920`, commit
`d5c5987`, preserves targeted AscendC development, native eager/graph numerical
gates, service memory adaptations, paired serial-prototype performance and
profiling. Its later capacity-16 vector fast path produced 106.005430 tok/s
versus a same-day, same-config but noncontemporaneous dense screen at
108.996204 tok/s (about -2.744%). That is a scoped negative screening result,
not a fresh paired final acceptance or rejection of all paper variants.
Do not rerun that unchanged path or describe it as unimplemented.

Raw evidence remains outside Git at
`/cache/cch/qwen36-kvbuffer-20260923`; the branch's workstream HANDOFF records
report hashes and limitations. HYPIC remains a previous successful migration
example, not a new success in this workstream. Training/distillation-dependent
hybrid model conversion and trained supernet papers are not next priorities.

## Checkpoint status

The inherited KIVI closeout was committed locally as `fe93b5b` after focused
software tests passed; it adds no new NPU or E2E result. Its normal push did
not complete: a bounded subsequent push returned HTTP low-speed timeout on
2026-10-06. Preserve the local commit and do not claim remote synchronization
or start product edits before the required remote-start checkpoint exists.
No force push or change to main was performed.
