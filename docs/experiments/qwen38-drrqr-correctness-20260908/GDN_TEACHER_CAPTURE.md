# Real-model teacher capture for DRRQR algorithm screening

## Current execution status

The first real TP4 service loaded all four model ranks but failed during warmup
communication: the new launcher incorrectly set HCCL_DETERMINISTIC=0. Native
HCCL rejected that value. No request was sent and no tensor archive was captured.
The failure, exact environment, source identities and cleanup are retained in
gdn-teacher-capture-v1.failure.json and the immutable external v1 result directory.
This is our launcher error, not a DRRQR numerical or algorithm failure.

The correction removes HCCL/LCCL deterministic overrides and records them as
unset. The same-environment four-rank HCCL smoke passed in 28.283 seconds and
cleaned up. Fresh v2 capture then completed both requests and all 432 archives;
service and collector exited zero, the process group was reaped, and postflight
found no task NPU process (only the original container bash remained).
The service lasted 218.817 seconds. No MTP or alternative algorithm was run.

The first v2 CPU evidence audit rejected the real torch.compiler.disable wrapper
because its torch/_dynamo source was outside the original source-root list.
That failed report is retained. After verifying and admitting only the exact
wrapper path/SHA/symbol and its exact unwrapped Ascend chunk identity, audit v2
passed all 432 archives, byte-state continuity, zero prefill, token binding,
decode cache-view binding, finite/shape/dtype and norm-input checks. No numerical
tolerance or coverage was relaxed, and no model recapture was needed.
Audit report SHA256: 88ad45924021635e3d485b57ad14c7cf3e993836eb9dee5a3e465d0da0994777.
Auditor SHA256: fd9b4f30d47d6f1763683f6dfa62a533c7c365ab73a7503de628445194e2e6f7.

The real NPU replay has been launched once in gdn-teacher-replay-v1, on logical0
(physical4), with a 1800-second internal budget and an external bounded timeout.
It exited after 40.556 seconds at the first dense prefill gate: output, complete
state and actual post-RMS exactly matched capture, but complete state failed
the unchanged FP32-reference per-element tolerance. No candidate or decode graph
ran. A secondary mapped-library identity error was also preserved. Both require
targeted diagnosis; neither is evidence that beta compensation failed or passed.
No task NPU process remained at postflight. See gdn-teacher-replay-v1.result.json.
The script SHA256 is
46fdfe7894e087cd47c10327b683dfc081a041afdcea400c87485c5918087e95.
Before launch, the replay was corrected to match actual decode's generic vLLM
L2 entry (normalize 4D, then squeeze), distinct from Ascend chunk's internal
prefill L2. Captured Q/K byte checks remain mandatory. Software validation was
102 CPU/mock tests, not NPU admission. The prompts and algorithm-screen
thresholds below are unchanged. See gdn-teacher-capture-v2.checkpoint.json and
DRRQR_PORTABILITY_DESIGN.md; design portability is required now, not deferred
until another host is available. No performance or task-accuracy gain is claimed.

After this run, the algorithm-scope software regression completed with 424 tests
passing (26.07 seconds of pytest execution, 14 deprecation warnings). The paused
native build/codegen tests were explicitly excluded. These CPU/mock passes do
not override the failed real-NPU prefill-reference gate.

## Admission frozen before the first service launch

Phase: performance-first candidate selection, with numerical correctness first.
Hypothesis: retained-key beta compensation may reduce the original energy64
recurrence distortion sufficiently to justify one model candidate screen.
Operator/cache work remains subordinate to a concrete DRRQR algorithm candidate.
This capture does not implement that candidate and cannot establish improvement.

One dense128 TP4 eager service, only physical NPU4–7, at most 1800 seconds plus
bounded process-group cleanup. Two sequential self-written non-evaluation text
prompts, each a full 128-token no-thinking chat template. Each requests nine
output tokens with ignore_eos=true solely to obtain one complete prefill and
eight decode executions. This is neither a benchmark nor the final accuracy
protocol (which remains max_tokens=2048, normal EOS, no thinking).
No automatic service/request retry or expanding prompt search.

Selected layers: 0, 12, 25, 38, 50, 62; all four ranks. Expected total:
2 sequences × 9 executions × 6 layers × 4 ranks = 432 tensor records.
Inputs manifest SHA256:
5fb48269fb6919af73040938d35ba82090ae820a41ee61dc440183acf3ec1b12.
The prompts have repeated context padding and are intentionally a small local
screen, not representative LongBench-v2/GSM8K or selector generalization evidence.

All old DRRQR patches/capture, common conv/MC2 optimizations, and graph/profiling
are off for teacher math collection. The checkpoint and upstream runtime remain
unchanged. The installed plugin wheel stays at 0.1.11. No generated native
operator is installed or loaded by this experiment.

## Deciding capture evidence

The observer calls each original computation once, without modifying arguments,
and returns the original outputs. It snapshots actual post-convolution Q/K/V,
g/beta, normalized decode Q/K, sequence boundaries/slot indices, effective
prefill initial state after reset, full selected FP32 initial/final state, and
the actual pre/post gated-RMS tensors, gate z, norm weight/config/source.
Only the selected cache slot is copied, not the whole cache arena.

Require finite captured tensors, zero effective prefill state, byte-identical
state continuity and operator-to-cache propagation, stable cache metadata, and
byte-identical operator output to actual norm input. Reject mixed/speculative,
chunked/padded or unbound requests. Four-rank completion reports must each prove
54 records and nine input-ID sequences, verified against the frozen prompt plus
the API's actual first eight generated token IDs. A passing launcher or CPU test
alone cannot satisfy capture admission. Preserve failed/partial evidence.

## Next decision, not yet a result

Replay dense128, original energy64, and fixed per-head beta-compensated64 from
zero state on the same captured dense-driven layer inputs. Each candidate must
keep its own state trajectory, including candidate prefill. Use the frozen
energy selector and pre-existing calibration-fit retained-key means; do not fit
beta coefficients to these capture prompts. Report actual outputs separately
from any idealized projected/scaled diagnostic.

First qualify dense replay against capture and each candidate against its own
reference, with previously declared phase-specific tolerances and eager/graph
checks. Dense replay failure blocks algorithm attribution, not the whole project.
For research prioritization only, require actual post-RMS mean relative-L2 error
to improve by at least 10% over original64, with no layer/rank/sequence group
worsening over 5% (denominator floor 1e-6), including late sequence windows.
Failure does not authorize relaxing this screen.

Passing local fidelity only permits a model candidate screen. It does not prove
upstream-layer or autoregressive feedback recovery. Final acceptance remains
same-stack/common-optimization dense pairing, three 1024-output performance
rounds with separate TTFT/TPOT, and paired no-thinking 2048-cap LongBench-v2 and
GSM8K without accuracy loss.
