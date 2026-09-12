# Qwen3.5 t12 Runtime Monkeypatch Candidate

## Immutable final delivery contract

The final Qwen3.5-27B optimization must remain a removable runtime Python
monkeypatch loaded at service startup into the unchanged official
vLLM-Ascend image. Reusing effective implementations or engineering patterns
from upstream vLLM-Ascend and ops-transformer is encouraged, but the delivered
integration must still cross this monkeypatch/package boundary. It must not
require editing installed vLLM or vLLM-Ascend sources, source overlays, a
custom final image, or `docker commit`. Disabling the patch and restarting
the service must restore the official behavior.

Every candidate starts with an upstream-first audit of vLLM, vLLM-Ascend,
CANN/ops-transformer, and relevant accepted PRs. Prefer direct reuse,
composition, or the smallest Qwen3.5-27B/Ascend 910B4 compatibility adapter.
Do not independently rewrite an upstream capability. New functionality is
allowed only after the audit records that no compatible upstream mechanism
exists and a profile identifies the exact uncovered bottleneck; even then,
implement only the missing delta behind the runtime monkeypatch boundary.

Upstream origin is necessary but not sufficient for promotion. A component
under an `experimental/` namespace, absent from a stable release, or not yet
accepted by vLLM-Ascend must be treated as untrusted experimental input. Before
device admission, record the apparent non-promotion reason from upstream commit
history, tests, issues/reviews, release notes, and support matrices. If the
reason cannot be established, classify that uncertainty as risk. Such a
component must independently pass exact-shape numerical equivalence,
performance, repeated-call stress, end-to-end paired quality, rollback, and
the complete concurrency matrix; upstream provenance must never waive a gate.

Use an evidence ladder instead of treating all upstream code equally:

1. Prefer code that is merged, present in a stable release, covered by upstream
   tests, and listed for the exact model/hardware/runtime combination.
2. For merged but unreleased code, audit release-branch drift, dependencies,
   backportability, and the reason it has not shipped before adapting it.
3. For an open or abandoned change, record maintainer review, failed checks,
   unresolved comments, benchmark scope, issue history, and any superseding
   implementation. Separate an upstream-stated reason from our own inference.
4. If no authoritative non-merge reason is discoverable, record `unknown`;
   never reinterpret silence as approval or maturity.
5. Reject rather than repair around evidence of ABI mismatch, known
   correctness gaps, unsupported shapes/hardware, or a superseding upstream
   design. Only queue reasons such as missing adapter work or release timing for
   local validation, and still require every project gate.

This process cannot guarantee upstream quality by reputation. It guarantees
that borrowed code has pinned provenance, an explainable adoption decision,
independent validation on the target stack, and an immediate rollback path.

Performance and accuracy are separate fail-closed gates. The 357-row
`query_rewrite` file has empty reference answers, so its latency metrics and
paired outputs must never be presented as reference-backed accuracy. Final
promotion additionally requires the frozen 1,319-row AISBench GSM8K evaluation
for fresh official control and candidate, three complete repetitions each,
with no candidate repetition or median accuracy below its control. See
`../T22_ACCURACY_NO_REGRESSION_GATE.md`.

This directory contains a source-overlay-free Python candidate for the
unchanged vLLM-Ascend 0.23.0 image. It is not the final commercial performance
deliverable: offline installation and contract tests pass, and live activation
plus smoke passed on physical NPU0-3, but the c1/32 fail-fast performance gate
missed the current TTFT >=20% and TPOT >=10% targets.

The candidate installs five coordinated runtime changes:

- fused Qwen3.5 GDN qkvz/ba projection construction;
- six-way checkpoint weight mapping into the fused projection;
- Ascend GDN forward consumption of the fused outputs;
- linear-attention gate/up weight prefetch;
- Gemma RMSNorm prefetch postprocessing.

It also contains an opt-in t13 diagnostic hook for the DyntraLBScheduler. The
diagnostic hook is disabled by default and is activated only with
`QWEN35_ASCEND_DIAGNOSTICS=1`; it emits privacy-safe scheduler aggregates such
as scheduled-token counts, queue sizes, prefill counts, and schedule-call wall
time. This is for bottleneck attribution only and is not a performance claim.

The base t12 behavior keeps ordinary MMAR enabled. A new opt-in
`candidate-prefill` variant restores only the historically effective bounded
prefill rewrite: compile ranges above 512 and at most 16384 tokens decompose
MMAR into GEMM plus AllReduce, while decode-sized ranges stay on the stock
MMAR path. This variant does not mount the rejected AICPU-first custom OPP and
is disabled unless the launcher explicitly selects it. The expected
sitecustomize.py SHA256 is:

    cc9ed4125822dd06a9899da42619685d2814ac62259d3ad7ef57bd3ec566d5f1

The `candidate-prefill-no-prefetch` ablation keeps the same bounded-prefill
rewrite and GDN projection patch while disabling both the official weight
prefetch configuration and the two runtime prefetch hooks. Its activation
report must show zero prefetch-hook markers; this prevents a configuration-only
toggle from being mistaken for a true code-path ablation.

## Editable installation

Run this before starting vLLM workers:

    cd /path/to/runtime-monkeypatch
    ./install_editable.sh
    source ./load_patch.sh
    ./run_with_patch.sh vllm serve /path/to/model <existing arguments>

install_editable.sh uses the familiar editable-install model, but adds
--no-index and --no-build-isolation. This matters with pip 26 in the pinned
image: plain pip install --no-deps -e . tried to download an isolated
setuptools build dependency, while the maintained installer passed with no
network and no NPU devices.

The installation changes only the disposable container writable layer and the
editable Python path. It does not modify the image and must never be followed
by docker commit. Installing after vLLM workers have already started does not
retroactively patch those processes; recreate or restart the service after
installation.

## Current evidence boundary

Passed:

- Python and shell syntax;
- static projection-fusion contract tests;
- exact official-image source-contract validation without network or devices;
- device-free behavior checks for fused/fallback projection construction,
  weight mapping, Ascend forward selection, linear-attention gate/up prefetch,
  and Gemma RMSNorm prefetch postprocessing;
- activation-checker positive and negative fixtures;
- offline editable installation in the exact v0.23.0 image with network=none
  and no NPU device mapping.

Live evidence now recorded:

- activation passed in a disposable official-image container on physical NPU0-3;
- no physical NPU4-7 devices were mounted into the candidate container;
- the patch was mounted read-only and injected through Python path mechanics;
- fixed-input smoke completed 1/1 with natural EOS and the same response hash
  as control;
- c1/32 fail-fast completed 32/32 with natural EOS, but only reduced TTFT P95
  from 6502.636 ms to 5697.694 ms (12.38%) and TPOT P95 from 31.754 ms to
  31.641 ms (0.36%);
- only 16/32 response hashes matched the paired control run, so this candidate
  must not be promoted as precision-lossless without deeper paired review.

Still pending for a final money patch:

- four-rank live activation on physical NPU0-3;
- fresh same-environment MTP-off control;
- c1/c5/c8/c16, three repeats, TTFT P95 reduction at least 20%;
- c1/c5/c8/c16, three repeats, TPOT P95 reduction at least 10%;
- paired quality validation over all 357 frozen rows.

An additional opt-in T21 path is now available behind
`QWEN35_ASCEND_T21_DENSE_MLP=1`. It registers the pinned upstream fused local
MLP as a traceable torch operator through public ACL/torch-npu interfaces,
admits only exact Qwen3.5-27B BF16 TP4 model shapes, passes zero-copy
transposed model-weight views, and composes the result with vLLM's existing TP
AllReduce. The upstream operator accepts every positive flattened M; keeping
the former Python M<=16 branch caused AOT fullgraph capture at large M to
permanently select the fallback path. The branch is removed, and numerical
gates now cover M through 4096. Python performs only static module admission;
the C++ bridge validates tensor dtype, device, exact shape, and layout at
runtime so non-Tensor metadata calls cannot break fullgraph capture. It is
disabled by default. For the pinned v0.23.0 image it also backports current
upstream vLLM's graph-split guard that leaves scalar `x.size(dim)` calls
untouched; this is required only after the traceable T21 node enters the AOT
graph and is applied with an exact source anchor. T21 is not promoted until TP4 service,
ablation, complete matrix, and quality gates pass. See
`../T28_PUBLIC_ACL_TORCH_BRIDGE_FINDINGS.md`.

Historical t11 reached a 47.7% c1 TTFT P95 reduction and 17.3% TPOT P95
reduction, which clears the corrected c1 thresholds. Those measurements remain
provenance, not a final claim, because they lack the current complete matrix
and quality evidence.
The latest standalone t12 run reached only 12.38% TTFT P95 reduction and 0.36%
TPOT P95 reduction at c1/32, so t12 is a validated loader/activation baseline,
not the final optimization.

On 2026-09-09 a fresh control service showed that the cold c1 repeat was
polluted by shape-specific Triton compilation: TTFT P95 was 6461.68 ms while
new GDN prefill kernel binaries were generated during the run. Repeating the
same frozen c1 workload on the same service created no new Triton binaries and
reduced TTFT P95 to 840.46 ms. Warm-control TPOT P95 was 28.97 ms, already
below the current 31.24 ms c1 threshold. This shifts the next live experiment
to TTFT: `candidate-prefill` should recover the bounded-prefill TTFT benefit
without changing the already-passing decode path.

Run `../tests/test_official_image_source_contract.sh` on the host to detect
class, method, signature, or exact source-anchor drift in the pinned image.
This intentionally does not import the Qwen GDN stack: that import initializes
the Triton Ascend target and therefore belongs to the live NPU activation gate.

See ../VALIDATION_PLAN.md for the ordered gates and rollback boundary.
