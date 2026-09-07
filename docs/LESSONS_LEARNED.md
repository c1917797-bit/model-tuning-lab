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

## 7. Paper-to-Ascend lessons from HYPIC

### 7.1 Reproduction success requires a named denominator

HYPIC succeeded as a historical/practice-result reproduction because the
scientific question was narrowed to a same-denominator A/B: native prefix cache
was disabled in both arms and the only treatment switch was
`VLLM_ASCEND_HYPIC_ENABLE`.

The reference practice remained contextual rather than pooled evidence because
model version, accelerator generation, and tensor parallel degree changed.
The local result could reproduce direction and approximate magnitude, not
absolute latency equality.

**Reusable rule:** name the denominator before comparing gains. HYPIC-only vs
no-cache, PDC-only vs PDC+HYPIC, and native prefix-cache experiments answer
different questions and need separate ledgers.

### 7.2 Activation evidence is part of performance evidence

The HYPIC run did not accept favorable TTFT/TPOT/throughput numbers by
correlation alone. The treatment also required strict runtime evidence that the
HYPIC mechanism entered the intended hot path, with no missing required events.

**Reusable rule:** configuration flags and import logs are not enough. A
paper-derived mechanism needs planner/scheduler and worker/device hot-path
activation proof before a performance delta can support adoption.

### 7.3 Capacity arithmetic can invalidate an otherwise plausible ruler

An earlier HYPIC configuration with a 16384-token budget could not admit a
16384 private suffix plus an 8-token seam sink. That case was rejected and was
not pooled with the corrected 40960-budget experiment.

**Reusable rule:** admission budget must cover the full physical requirement,
including private suffix, seam/sink, block alignment, workspace, and reserved
tokens. Changing this identity requires a new baseline and artifact root.

### 7.4 Host/container device mapping is experiment identity

A preflight attempt reused host NPU IDs inside a remapped container. Measurement
never began and the failure was archived. The corrected run recorded host NPU
IDs separately from container-visible IDs.

**Reusable rule:** prove host-to-container mapping and TP degree before
measurement. Do not infer owned devices from container-local numbering.

### 7.5 Performance and quality are separate execution contracts

The HYPIC workflow separated fixed-output performance sampling from deterministic
EOS-respecting quality sampling. It also restarted the identical arm between
performance and quality phases so profiler, compilation, cache, and capture
state could not leak across contracts.

**Reusable rule:** `ignore_eos`, thinking mode, capture/profiler state, cache
state, and scorer semantics must be phase-specific. A single global sampling
block can silently invalidate either performance or quality evidence.

### 7.6 Long runs must resume by verified unit, not by hope

When service loss or long-tail behavior interrupted quality work, accepted rows
were preserved with stable indexes and response hashes; only missing or invalid
indexes were retried. Completed units were hash-validated and skipped on resume.

**Reusable rule:** write per-request/per-sample JSONL with stable identity,
`ok` state, and response/content hash. Never restart a live authoritative
controller, and never average partial rows as if they were complete.

### 7.7 Completion is an independent audit boundary

HYPIC completion required an independent fail-closed audit over raw artifacts:
planned performance and quality units, request counts, unique indexes, zero
failures, response hashes, dataset/evaluator identity, mechanism activation,
summary-to-details consistency, and resource release.

**Reusable rule:** rendered reports and file presence are not enough. Adoption
requires an independent raw-artifact audit plus explicit allowed and forbidden
claims.

### 7.8 Operational failures are not algorithm failures

HYPIC preserved several failure classes without relabeling them as algorithmic
regressions: wrong container device IDs, invalid capacity budget, evaluator or
renderer defects, service lifecycle exits, and first-pass auditor bugs. Each was
classified, repaired or superseded, and revalidated.

**Reusable rule:** keep separate decisions for feasibility, mechanism
activation, performance, quality, profiling, adoption, and generalization. A
valid operational failure should stop or repair the run, not become a fake paper
conclusion.

## 8. Qwen3.5 parallel-task boundary

### 8.1 Paper migration and production performance are different decisions

Two Qwen3.5 tasks shared the model family, Ascend 910B4 host, vLLM-Ascend
runtime, and initially the same NPU lane. That similarity caused the historical
dense-MTP Paper-to-Ascend experiment to be described as if it were the active
production optimization loop. The tasks actually use different workloads,
metrics, acceptance gates, implementation policies, and evidence scopes.

The performance workstream owns the frozen real `query_rewrite.jsonl`
denominator, c1/c5/c8/c16 repeated P95/P99 evidence, semantic-quality gate,
and final serving-stack decision. Paper-to-Ascend owns paper selection,
architecture/source fit, bounded Ascend implementation, and paper-level
mechanism evidence. A paper result can enter the performance loop only as a
new candidate; it cannot inherit or replace the production baseline.

The old MTP paper candidate is now policy-rejected because the active user
constraint forbids MTP/speculative decoding. Its invalid contested baseline,
failed startup, and selection rationale remain useful history, but it owns no
current hardware lease.

**Reusable rule:** every parallel task needs a unique task ID, branch, workload,
metric gate, evidence root, implementation boundary, and resource lease.
Shared model and hardware do not make two experiments comparable.

### 8.2 Near-target and negative evidence must keep their scope

The historical Qwen3.5 GDN projection-fusion plus gate/up-prefetch stack
reached median-of-three P95 speedups of
2.206x/1.938x/1.930x/1.910x for TTFT and
1.381x/1.651x/1.753x/1.980x for TPOT at c1/c5/c8/c16. This passes seven of
the eight current 1.5x latency cells, but c1 TPOT misses and the implementation
used source overlays. It therefore selects the next hypothesis but is not a
compliant production result.

**Reusable rule:** retain successful ingredients and failed treatments, but
never widen a microbenchmark, sampled-quality, source-overlay, or paper-level
result into a final serving claim.
