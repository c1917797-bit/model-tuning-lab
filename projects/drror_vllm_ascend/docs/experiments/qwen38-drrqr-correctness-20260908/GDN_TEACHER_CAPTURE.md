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

The distinct captured-dense-reference replay is now resolved. Its first isolated
container attempt is retained as invalid environment evidence: a second container
mapped physical NPU4-7 while the dedicated container already owned them, so CANN
device enumeration aborted before any numerical trajectory. The report SHA256 is
35047cd0718b0b4470a464af771f5e0fe652bcd05d699cbff113d95c12ad7c2f;
it supports no algorithm claim. A bounded repair ran the committed source copy
inside the already-audited dedicated container and used a fresh v2 output.

The v2 replay completed all 144 trajectories (dense128, energy64 and beta64 over
48 layer/rank/sequence groups). Every trajectory, full-state continuation,
eager/NPUGraph byte check, graph reset, beta transform, dense capture replay and
candidate numerical gate passed. Fixed beta improved the global post-RMS
relative-L2 mean from 0.2936645543 to 0.2610229455, a ratio of
0.8888472975, which passes the global 0.9 threshold. It nevertheless failed
the frozen robustness gate: 5/144 layer/rank/sequence windows exceeded 1.05,
with the worst late-decode ratio 1.3546492282 at layer62/rank2/teacher-1.
Therefore fixed retained-key beta is rejected for model integration; this does
not reject other compensation functions or DRRQR.

The valid report SHA256 is
ef3df3559bd0ae234c79dda6bafd643177bb412020cb31d8988d0a98150ef3a2;
token-fidelity SHA256 is
4f55edde266cf6a26203d3838f49aabeff846e7c529d5d9c7dd600b99dabe384.
The compact committed summary is
gdn-teacher-captured-reference.v2.summary.json. Postflight found no NPU
process and only the original container bash. No accuracy or endpoint
performance test was run.

The subsequent aligned-width replay completed once inside the same audited
dedicated container on logical0 (physical4). Dense128, energy48, energy64 and
energy80 each completed 48/48 trajectories; all 192 trajectories and all 1728
prefill/decode steps passed native eager, full-state and NPUGraph byte gates.
The aggregate post-RMS relative-L2 means were 0.4080521737, 0.2936645543 and
0.2059228392 for Dk48, Dk64 and Dk80. The curve was monotonic, and the Dk80
to Dk64 ratio was 0.7012178902, exceeding the required 15 percent improvement.
All 144 robustness windows passed; the worst ratio was 1.0264260557, below
the frozen 1.05 limit. The valid report SHA256 is
f635211b4e06dea25a9cf16aa047e403fe6c5ab4fda2506d45bc554882338803 and
the token-fidelity SHA256 is
26660a65d1edab252dae6a2ab4aaa6b4fdf3d46a5efc23b9decf4c3f9a9eb522.
Postflight found no NPU process. This result admits an all-48-layer teacher
sensitivity capture and equal-cost aligned-width allocation study only. It
does not admit mixed-cache implementation, endpoint performance, task
accuracy, exact StrongRRQR, or portability claims. See
gdn-teacher-width-curve.v1.summary.json.

The next one-case NPU diagnosis ran only Ascend prefill L2(raw_K), not a model,
chunk or candidate replay. Actual BF16 K exactly matched CPU-normalized K; the
original FP32 reference state was reproduced byte-for-byte and all 43 original
violations remained after substituting the observed K. Thus normalization does
not explain this saved discrepancy. The unchanged reference gate remains failed;
chunk intermediate rounding/accumulation is the next narrow source investigation.
See gdn-prefill-k-reference-v1.result.json. Later replay changes only preserve
raw/canonical library evidence and the primary failure; they do not change math
or thresholds. The original failed implementation is saved in local commit
440251e; its push and a read-only remote check timed out, so remote publication
is unconfirmed. No automatic repeated push or experiment retry was started.

The frozen chunk source has additional finite-precision boundaries: intermediate
H, W/U, v_new and its decayed variant use BF16 storage although the final state
ABI is FP32. This source evidence is not resolved device-binary attribution.
A CPU-only counterfactual using the immutable failed NPU artifact reproduced the
original state/output bytes and all 43 violations. Splitting recurrence 64+64
without rounding also preserved bytes. Rounding only S64 through BF16 left 41
old violations, removed 2 and introduced 6 (47 total); the original gate still
failed. Therefore a single cross-chunk H rounding is not a sufficient explanation.
See gdn-prefill-boundary-reference-v1.result.json. Do not replace the reference
or loosen its tolerance on this basis. A separate real-input incremental probe
is being prepared to compare CPU-prequantized beta with NPU beta transformation,
including eager/graph state checks; it is not full qualification or performance
admission and does not overturn this failed replay.

That single beta incremental NPU run completed in gdn-beta-incremental-v1:
four independent prefills and four private state lanes through eight decode
steps, including two decode graphs, matched finite bytes for beta, output,
full state and actual post-RMS. Both B lanes also matched the CPU FP32 product;
graph reset, persistent metadata and unselected slots passed. Prefill was eager,
not a prefill-graph qualification. The 69 related CPU/mock tests also passed.
However the run remains failed_runtime_evidence: all six teacher library paths
and hashes matched, but three additional CANN batch_invariant vendor libraries
were mapped. Their loading cause is not yet attributed; no whitelist change or
same-hash shortcut is allowed. The launch caller lost its acknowledgement before
retaining a handle; completion was recovered by target-verified read-only report,
artifact hashes and process checks, without a second launch. No execution handle,
process duration or exit code is invented. See gdn-beta-incremental-v1.result.json.
The original dense reference gate remains failed and unmodified. These local
incremental bytes do not admit candidate performance, prove beta fidelity, or
establish task accuracy or portability. Postflight found no task NPU process.

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

## Frozen replay decision contract

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
