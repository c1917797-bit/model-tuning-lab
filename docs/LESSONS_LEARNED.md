# Ascend Tuning Lessons Learned

This document is the durable success/failure memory for Model Tuning Lab.
It deliberately separates **observed local history** from **upstream-known risk
patterns** so future maintainers do not turn advice into fake experiment history.

## 1. Observed successes

### 1.1 Orient the real machine before tuning

The host was explicitly identified as EulerOS/aarch64 with 4x Kunpeng-920
sockets, 192 physical CPU cores, 4 NUMA nodes, about 2 TiB RAM, and 8x Ascend
910B4 devices. Driver `25.2.0` and firmware `7.7.0.3.220` were verified.

**Reusable rule:** performance evidence starts with exact hardware, software,
model, launch-command, topology, and target-device proof. A service that merely
starts is not sufficient evidence that the intended NPU is doing the work.

### 1.2 The missing host memory was correctly attributed to HugeTLB

The machine appeared to have only roughly 68 GiB of ordinary `MemAvailable`
despite about 2 TiB physical RAM. Process RSS/cache did not explain the gap.
The investigation found about 1916 GiB reserved as 1 GiB HugeTLB pages across
the four NUMA nodes; most were free inside the hugepage pool but unavailable to
ordinary allocation.

**Reusable rule:** on an NFV/DPDK/OVS-style host, inspect HugeTLB before blaming
application memory. `free_hugepages` is not ordinary free RAM.

### 1.3 The personal repository was moved with rollback and integrity checks

Canonical repository path:

```text
/opt/host/vnf/austinov/model-tuning-lab
```

Compatibility symlink:

```text
/cache/austinov/model-tuning-lab -> /opt/host/vnf/austinov/model-tuning-lab
```

The migration was verified with matching Git state, working-tree hashes, and
`git fsck`; a pre-migration backup remains under `/cache/austinov/`.

**Reusable rule:** repository relocation is not complete until both Git object
integrity and working-tree identity are checked and a rollback path exists.

### 1.4 Git HTTPS was repaired without weakening TLS

Initial failure:

```text
git-remote-https: error while loading shared libraries: libcurl-gnutls.so.4
```

The helper expected a GNU TLS libcurl stack that already existed under
`/opt/git/lib`, but that directory was inaccessible to the normal operator.
The repair preserved the original helper, injected `/opt/git/lib` only for the
Git HTTP helper, made the library directory readable/traversable but not
writable by ordinary users, and configured the trusted CA bundle. TLS
verification remained enabled.

**Reusable rule:** repair the runtime and trust chain. Do not solve Git TLS
problems with `sslVerify=false` or an ABI-unsafe libcurl symlink.

### 1.5 Upstream source workspaces were prepared deliberately

The following source trees were checked out under `/home/mtuser/cch`:

- `vllm-ascend` (recorded `main` HEAD `222677fc...`)
- `ops-transformer` (recorded `9.1.0` HEAD `06842472...`)
- `cannbot-skills` (recorded `master` HEAD `d5e0d44b...`)
- `cann-recipes-infer` (recorded `master` HEAD `3ed96817...`)

`ops-transformer` was intentionally aligned to the CANN 9.1.0 line rather than
blindly using master.

**Reusable rule:** low-level CANN/operator source must match the installed CANN
release before compiling it or comparing performance paths.

### 1.6 vLLM-Ascend profiling capability was proven, not assumed

The serving image was verified to contain `torch_npu.profiler`, `msprof`, and
`asys`. The checked-out vLLM-Ascend profiler implementation uses
`ProfilerLevel.Level1` with `AiCMetrics.PipeUtilization`.

**Reusable rule:** first inspect the real serving container; host `PATH` is not
an authoritative inventory of available profiling tools.

### 1.7 The prefix-cache experiment was isolated from a drifting service

The first tuning workstream rejected the historical 8100/NPU0-3 service as a
formal baseline after an independent ablation runner replaced it. Instead, it
created an isolated baseline service on `127.0.0.1:8200`, using physical
NPU4-7 serially for baseline/candidate comparison. Host `npu-smi` proved the
four vLLM TP worker PIDs on those exact devices.

The workstream also froze MMLU, GSM8K, and HumanEval data snapshots with hashes
and added a repeatable evaluation harness before measuring the hypothesis.

**Reusable rule:** if the service identity or resource ownership drifts, reject
it as baseline evidence. Re-isolate the workload and prove target ownership.

## 2. Observed failures and near-misses

### 2.1 `git --version` passed while Git HTTPS was broken

The Git binary itself ran, but HTTPS clone failed in the remote helper.

**Lesson:** environment orientation should include a protocol-level Git health
check such as a bounded `git ls-remote`, not only `git --version`.

### 2.2 Alternative HTTPS access initially failed CA verification

Python HTTPS reached the network but failed certificate validation until the
existing CA bundle was supplied.

**Lesson:** network reachability and a correct trust chain are independent.

### 2.3 A root-only repair did not fix the real operator account

After the Git helper runtime was repaired, root could access it but `mtuser`
still could not traverse `/opt/git/lib`.

**Lesson:** acceptance tests must run as the account that will perform normal
development work, not only as root.

### 2.4 Agent control-plane timeouts were not host failures

One management route timed out intermittently while another manager peer on the
same physical host continued to work.

**Lesson:** separate control-channel failure, command failure, and application
failure. Do not mutate the target because a management route was transiently
unhealthy.

### 2.5 Runtime readiness changed during container restart/loading

During one observation window, the model container existed but 8100 was not yet
listening and NPU process listings were temporarily empty.

**Lesson:** static config and container existence do not prove serving
readiness. Claims about ports, active NPU devices, or free devices require
same-session live evidence.

### 2.6 Host and container tool inventories differed

`msprof` was not available as a host command while it was present inside the
CANN-equipped vLLM container.

**Lesson:** inspect the execution environment where collection will actually
run before installing additional tooling.

### 2.7 The original 8100 service drift invalidated it as experiment baseline

An unrelated ablation runner changed the original NPU0-3/8100 workload. The
prefix-cache workstream explicitly stopped using that service as its baseline.

**Lesson:** environment drift is not an inconvenience to average away; it
invalidates apples-to-apples evidence and requires re-baselining.

### 2.8 GitHub transport was temporarily intermittent during handoff work

While creating the handoff workstream, one successful `git fetch` was followed
by bounded `git ls-remote`/push attempts that stalled. DNS remained healthy;
`api.github.com` was reachable, and `ssh.github.com:443` was reachable, but no
authorized SSH key was available. A later bounded Git HTTPS read succeeded and
the remote start checkpoint then pushed normally.

**Lesson:** use bounded network operations, distinguish transient Git transport
failure from AWMCP authorization, and do not continue protected-path edits
until the required remote start checkpoint actually exists.

## 3. Deliberately avoided risky actions

### 3.1 HugeTLB was not released merely because most pages looked free

The host has OVS/NFV/DPDK characteristics. Releasing the hugepage pool could
break unrelated workloads, so no release was performed without consumer proof,
pre/post checks, and rollback.

### 3.2 Qwen3-32B was not declared ready from HBM arithmetic alone

Four 32 GiB NPUs plausibly fit BF16 weights plus runtime at conservative
settings, but ordinary host RAM remained constrained by HugeTLB reservation.

**Lesson:** model feasibility is a system-capacity question, not HBM-only math.

## 4. Upstream-known profiling failure modes

The following are durable guidance from `cannbot-skills`, not claimed as local
incidents unless a future experiment records them:

- Missing detailed `ExperimentalConfig` can produce shallow kernel data.
- Standard first-pass NPU analysis should use Level1 + PipeUtilization.
- Profiler schedules must exit the active RECORD window cleanly.
- First compile/JIT/graph build should be warmed outside the measurement window.
- Prefill and Decode should normally be profiled separately.
- Some filesystems can cause CANN offline parsing failures; if raw collection
  looks valid but CSV/trace parsing fails, test the same data on another local
  filesystem before changing model code.

## 5. How future lessons must be recorded

Every meaningful accepted, rejected, inconclusive, or failed experiment should
capture:

1. context and exact environment;
2. hypothesis and one primary variable;
3. benchmark/profiling protocol;
4. correctness guardrails and thresholds;
5. evidence and artifact hashes/paths;
6. outcome and root cause;
7. reusable rule;
8. rollback/recovery state;
9. exact Git stage commits.

Negative results are part of the tuning knowledge base. Preserve them in pushed
history while recovering failed active code before integration.

## 6. Paper-to-Ascend lessons from Dynamic MoE

### 6.1 A theoretically useful compute reduction can still lose end to end

On physical Ascend 910B4, Dynamic MoE reduced token/expert pairs by about 12.8%
at the 4096-token case and the actual expert GMM stage became about 8.85% faster.
However, the direct `sort + cumsum + boolean compaction` routing path was about
6.36x slower than fixed Top-2 routing in the stage breakdown. Whole-block median
latency regressed by roughly 82-96% across 128, 512, 2048, and 4096 tokens.

**Lesson:** measure the whole migration unit. Saved FLOPs or faster GMM is not a
performance win when selection/packing overhead dominates. Profile before
lowering further; for dynamic routing, a bounded/fused router is the next
credible path, not more GMM tuning.

### 6.2 Reject the implementation at the scope actually measured

The direct Dynamic MoE lowering was rejected. The paper itself was not: a
matched full-model MoE checkpoint was unavailable, so the full-model result was
recorded as `inconclusive`.

**Lesson:** keep `implementation`, `operator/block`, and `full-model` decision
scopes separate. Never promote a valid negative result beyond the evidence it
actually covers.

### 6.3 Architecture applicability is a gate before paper selection

The current installed target is dense. Dynamic MoE was valuable as a pipeline
exemplar, but its production mechanism is not the active model architecture.

**Lesson:** before spending NPU time on a paper, prove that the installed model
contains the required mechanism and that the method targets an observed
bottleneck. For dense inference, prefer methods such as exact speculative/MTP,
attention/KV/decode improvements, or other inference-time techniques that do
not require retraining unless retraining is explicitly in scope.

## 7. Qwen3.6 portfolio and Ada-KV lessons

This section synthesizes the branch-local Qwen3.6 evidence accumulated through
commit 01c3abb on branch work/qwen36-adakv-ascend-20260925. It records reusable
rules, not an integration claim. Detailed gates, hashes, and scope boundaries
remain in projects/qwen36-paper-portfolio/ and the owning experiment records.

### 7.1 Portfolio triage and profiling prevented false additive claims

The ten-paper audit separated mutually exclusive implementations and overlapping
mechanisms before estimating benefit. A fresh dense TP4 profile identified a
shape-filtered GDN decode seam representing 14.15340% of the diagnostic decode
profile; reaching a 10% decode-phase gain would require at least a 2.79680x
local speedup under that model. This prevented small local wins from being
summed into an unsupported end-to-end claim.

HYPIC remains a prior workload-conditional success rather than a new portfolio
result. Its historical segmented-prefix reproduction averaged +36.0663% output
throughput with small LongBench-v2 and GSM8K quality deltas, but it used a
1024-output quality protocol. It cannot be promoted to the newer 2048-output
quality gate without a fresh, non-overwriting run.

**Reusable rule:** de-duplicate mechanism scope, separate measured critical-path
share from summed operator time, and calculate the required local speedup before
commissioning implementation work. Historical success is a ruler, not evidence
under a changed model, runtime, output cap, or workload.

### 7.2 Ada-KV established a strong staged correctness pattern

The Ada-KV prototype progressed from operator ABI checks to real-model,
all-full-layer execution, request-indexed compact arenas, mixed prefill/decode,
two asymmetric concurrent requests, and a sampled 1024-output lifecycle gate.
The hard-gated long run completed both requests with finite outputs; the worst
selected-support relative RMS was 0.002046 against a frozen 0.005 limit and the
minimum cosine was 0.99999797 against a 0.99998 floor.

A grouped native FIA ABI probe also showed bitwise equality with separate native
calls for the tested variable KV lengths. These are valuable backend and
lifecycle results even though they are not model-quality or performance wins.

**Reusable rule:** expand a paper port in explicit gates: synthetic ABI, real
layer, all layers, scheduler states, multiple request identities, long output,
then matched performance and task quality. Each gate proves only its declared
scope.

### 7.3 Numerical success did not translate into serving performance

The only matched profiler-off eager TP4 dense/candidate screen for the current
per-request implementation showed:

- output throughput: -2.168832%;
- mean TTFT: +7.273002%;
- mean TPOT: +2.205706%.

The candidate therefore lost end to end despite passing scoped numerical and
lifecycle gates. The ordinary dense cache allocation also remained present, so
the prototype did not prove an HBM-capacity saving. The grouped variant passed
an ABI gate but did not complete a matched end-to-end screen before the
time-box closed.

**Reusable rule:** a numerical pass, graph pass, ABI pass, or reduced logical
work is admission evidence, not a serving win. Require an audit-disabled,
same-stack baseline/candidate screen before spending on the full performance
matrix or final accuracy suite.

### 7.4 Failed canaries localized integration defects without rejecting papers

Several failures were useful because they were preserved with exact scope:

- one launch used the image's default shell entrypoint instead of the intended
  Python process and failed before model initialization;
- a two-request candidate failed closed when a new prefill request overlapped
  an existing decode request in ChunkedPrefill;
- early Ada-KV numerical thresholds failed at specific rank/layer/step points;
  later diagnostics calibrated the native BF16 envelope instead of silently
  relabeling those runs as passes;
- a concurrent-client barrier failed before HTTP submission because futures
  were created lazily; the corrected retry used a unique result path;
- an all-device container running only sleep infinity could hold the UDA
  namespace while npu-smi showed no compute process.

**Reusable rule:** classify the earliest failed phase before changing the
algorithm. Launch, scheduler-state, backend-envelope, client-harness, and
device-namespace failures are different hypotheses. Preserve the failed run,
use a unique retry artifact root, and never loosen a gate merely to rescue the
same bytes.

### 7.5 Several attractive routes were correctly closed

- The tested Faster Flash Decoding selector route was closed after source-faithful
  KV-group semantics and bounded threshold/subblock probes still failed its
  investment gate. No matched FFD service or task-quality result exists.
- The tested QQQ native per-channel V5 dynamic A8W4 pipeline passed some
  numerical/graph checks but mutated its INT8 activation on replay and was
  slower than BF16 at the measured shapes. This rejects that existing pipeline,
  not the QQQ paper or every fused A8W4 implementation.
- Sparse-prefix replay exposed warmup and repeated-run divergence that an
  earlier three-run pass had missed. The current v0.23 integration was closed
  until a materially new state-lifecycle hypothesis exists.
- Direct relabeling of native FIA cache quantization as KIVI was rejected at the
  contract gate: generic native quantization does not implement KIVI's
  groupwise cache method or establish its paper result.

**Reusable rule:** close deterministic routes with their exact implementation,
shape, runtime, and failure phase. Reopen only with a materially different
mechanism and a bounded test aimed at the recorded cause.

### 7.6 Accuracy resumability must bind protocol identity

The historical HYPIC evaluator resumes successful rows from an existing result
path without proving that each row used the current output cap, prompt identity,
or runtime identity. Changing only the command-line maximum from 1024 to 2048
could therefore mix incompatible responses.

**Reusable rule:** resumable quality evaluation must store and verify a protocol
fingerprint per output root and fail closed on stale rows. Output-cap changes
require a fresh baseline and a new non-overwriting artifact root.

### 7.7 Time-boxed rejection is part of the optimization flywheel

The first Ada-KV loop ended with a no-go for promoting the current plugin:
the measured implementation missed the +10% end-to-end target, retained dense
allocation, and left graph, mixed continuation-prefill, final task quality, and
full concurrency coverage unproven. The result does not reject Ada-KV on every
future Ascend cache manager.

**Reusable rule:** stop at the declared budget when the current implementation
cannot meet the acceptance contract. Preserve the strongest positive gates and
the negative end-to-end result, recover resources, and require a distinct
allocator/graph mechanism before reopening.

## 8. Experience-ingestion map for this synthesis

| Future trigger | Required future behavior | Durable destination | Verification |
| --- | --- | --- | --- |
| Qwen3.6 paper selection or resumption | Run architecture, overlap, Amdahl, and method-chain gates before implementation | paper-to-ascend plus the portfolio gate documents | validate-mst, focused portfolio tests, and exact experiment hashes |
| Ascend device appears idle but a canary reports Resource_Busy | Inspect Docker device mappings, UDA namespace ownership, and exact owner before stopping anything | chicaihong01-host-maintenance | Same-session npu-smi, process/container mapping, and rollback evidence |
| Numerical or ABI canary passes | Require a matched audit-disabled service screen before performance promotion | ascend-inference-tuning-loop and this durable lesson | Frozen baseline/candidate commands and repeated E2E evidence |
| Quality output cap or evaluator invariant changes | Use a new output root and reject stale resumable rows without a matching protocol fingerprint | Paper-to-Ascend quality gate and this durable lesson | Manifest/preflight check plus fresh paired baseline |
| Deterministic route fails | Keep the route closed until bytes or hypothesis materially change | Experiment record, workstream handoff, and Git history | Exact source hash, first failure phase, cleanup state, and successor-specific test |
