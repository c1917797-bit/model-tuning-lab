# Qwen3.5-27B Sparse Prefix Caching reproduction

## Current authoritative status (2026-09-12)

User-approved target is Qwen3.8-27B BF16 TP4. Historical Qwen3.5 directory
names are not model identity. Either physical0-3 or physical4-7 may be used
after live compute, lease, device initialization and memory checks.

Native cache repeat gate U9JADE passed: six natural-stop requests; identical
tokens for each repeated question; all four repeat-round requests reused1536
tokens. Raw smoke.json was inspected, not merely the PASS marker.
This is native-cache feasibility, NOT paper activation or performance proof.
The original operation0108 is no longer in the peer journal. Its run.log contains
NATIVE_CACHE_REPEAT_GATE_PASS_NOT_PAPER_PROOF and shutdown records.
Do not poll or restart this historical handle as a live experiment.

Artifact root: /cache/austinov/sparse-prefix-smoke-U9JADE
- smoke.json SHA256 a38dc58269be18d1e328ca4da279825e50307f56a7d15204d4552148e4a24be0
- identity.json SHA256 a0653f32df768ed07b3a25edd3266c95ca91f724068cfba54fc2c1fce9ef9288
- run.log SHA256 a661e0e2d325b6f18b67e8716bf7a126d7605ef9b788b23161f297a3f9dfce18

Implementation started: src/model_tuning_lab/sparse_checkpoint_plan.py contains
an independent budgeted block-aligned placement DP and a KV-coverage-bounded
restore-position selector. It is NOT wired into vLLM; it does not retain or
restore tensors. scripts/test_sparse_checkpoint_plan.py compares plans to an
exhaustive oracle at block sizes1/2/3/1536. Never claim this as model activation.

Next: implement the paper's budgeted checkpoint selection/retention mechanism
against the resolved native cache manager; prove selection and actual restoration
before matched performance/quality measurement. Preserve native caching as the
incremental-benefit comparator. The historical no-reuse TP4 baseline cannot
attribute benefit specifically to the paper. No paper speedup is established.

## Historical chronology (superseded status statements below)
CURRENT: operation exec-0000000000000108 on ma submitted cross-block native
cache gate. Poll exact handle before any new launch. Previous00fb exited1.
ZGFLju resolved_runtime proves block_size1536 but prompts511/515 tokens:
zero hits are explained by below-block stimulus, not demonstrated framework bug.
New stimulus repeats context320 times and asserts block_size < prompt length
and prompt length+128 <=2048 before requests. Output/hit gate unchanged.
CURRENT OPERATION: exec-00000000000000fb (ma), same native-cache stimulus
with resolved-runtime diagnostics from232289a. Poll before any launch.
Prior00e0 is confirmed terminal exit1; this retry changes diagnostics only,
not the zero-hit acceptance gate. Do not claim paper activation.
LATEST NATIVE GATE: YvM1go smoke.json contains all six natural-stop outputs,
identical Beijing/42 tokens across three rounds, but num_cached_tokens=0 for
every request. Gate correctly raised Native cache hit was not proven.
Cache configuration was True/align in actual engine log. Do not call this
restoration success. Inspect scheduler chunk alignment and checkpoint publication
conditions before changing the stimulus; preserve this failed attempt.
At last observation operation00e0 was tearing down, so poll for terminal state
and verify resource release before another launch.
CURRENT LIVE CHECK: native-cache repeat gate operation exec-00000000000000e0
on ma is running, container0313c1764e96 / qwen38_sparse_smoke_YvM1go.
Artifact /cache/austinov/sparse-prefix-smoke-YvM1go. Poll before starting another
job. Uses physical0-3, official native cache, long prefix and three rounds;
requires positive cached-token counts and identical repeat output tokens.
This is not the paper algorithm nor a matched cache-off quality comparison.
LATEST ACCEPTED GATE: operation00bc completed exit0. Qwen3.8 BF16 TP4 on
physical0-3 with spawn passed two prompts twice: Beijing and 42, natural stop,
identical token IDs across repeats. Artifact /cache/austinov/sparse-prefix-smoke-K3EF2a.
smoke.json SHA256 1b7f13f5cd592b70889528ae5628131896bf385a3f1290ec693f7b41f00aa611
identity.json SHA256 2d415a08ab1135e753f48c3f951fe6e7f8bfa01c896ecd20ae74f08e880781a8
run.log SHA256 890ce624615a0401b85e0f7e577f61e3697f537d64900c0ff6819dc515315d5f
Container c5294dccc42a auto-removed; operation00d4 found no NPU processes.
Shutdown logged worker SIGTERM/shared-memory cleanup warnings; do not hide them.
This is official cache-off feasibility only, NOT paper activation, full quality,
or performance evidence. Next implement/test cache restoration and paper mechanism.
Lane selector checkpoint763f751 pushed. The historical running note below is terminal.
CURRENT RESUME: physical0-3 became free. Device preflight operation00b5 exited0
using SPARSE_NPU_LANE=0-3; evidence /cache/austinov/sparse-prefix-smoke-1Ng56O.
Qwen3.8 TP4 spawn smoke submitted as exec-00000000000000bc on chicaihong01/ma.
Poll that exact handle and inspect its container before any new launch.
Launcher holds npu0-3.lock during execution. External4-7 container untouched.
This supersedes waiting-for4-7 as the next action; model smoke is not yet proven.
LATEST DEVICE CHECK: operation07ae completed exit1, DEVICE_COUNT0 and DCMI
-8020 (device is used). Raw evidence /cache/austinov/sparse-prefix-smoke-RLFnK6.
No model inference was attempted. The external container restarted since the
previous authorized stop and again maps physical4-7. Do not repeatedly launch
full smoke or stop this new running instance without renewed coordination.
Spawn fix b5ce821 is pushed but remains untested on a live four-rank model.
2026-09-11 current diagnostic: dTOScp first fatal error is PyTorch
ParallelOpenMP.cpp:64 Invalid thread pool following multithreaded fork.
Pinned image envs.py lines 889-894 explicitly supports spawn. Launcher now
sets VLLM_WORKER_MULTIPROC_METHOD=spawn; this fix is NOT yet model-tested.
Live operation 07a7 found all NPUs without compute processes, but external
a41efa7fcf8b is RUNNING AGAIN. Previous stopped-container status below is
historical. Do not repeat its stop based on stale ownership/permission.
Recheck device binding and current ownership before another model launch.
Raw TP4 c1/c16 repeat1 baseline JSONs verified by operation079f; no full
matrix or native-cache comparison has been established.
LATEST USER SCOPE: explicitly authorized Qwen3.8-27B for this paper piercing,
and requested existing FOUR-card TP4 baseline, not TP8. Historical worktree
name retained to avoid another tree; all new results MUST say Qwen3.8-27B.
Qwen3.5 smoke b993f42d20e6 exited on engine initialization failure before the
scope-change stop request (0793 returned No such container); its artifacts at
/cache/austinov/sparse-prefix-smoke-dTOScp are not Qwen3.8 evidence.
Baseline metadata in qwen35-performance-delivery/agentic/baseline/
baseline_metadata.json is actually Qwen3.8 TP4 and may now be considered.
It has only c1/c16 repeat1 plus cold tails; per-request unique cache_salt
disables cross-request reuse. It is not a matched native-cache baseline.
Reuse verified raw cells with these limitations; do not silently claim full
matrix or sparse-cache incremental speedup. User asked not to rerun full baseline.
RESOLVED DEVICE GATE: user explicitly authorized temporary stop of
drrqr_qwen38_energy_preflight_20260908. Through live chicaihong01/mb,
operation0095 stopped a41efa7fcf8b (not deleted; autoremove=false).
After stop, -8020 disappeared. With physical device nodes4-7 preserved but
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3 (container logical numbering), device-only
operation009d passed exit0. Evidence /cache/austinov/sparse-prefix-smoke-jgLoZU.
The external container remains stopped temporarily; do not delete it. Restore
with docker start drrqr_qwen38_energy_preflight_20260908 after releasing this lane,
coordinating any new external use first. No model inference has passed yet.
ma was missing from topology; mb direct target and exact container ID verified.
Device-rootfs control 0746 completed exit1: writable disposable rootfs still
gave DCMI -8020 / DEVICE_COUNT0. Evidence /cache/austinov/sparse-prefix-smoke-eljuzX.
Restored --read-only after this negative control; no host/image content changed.
Rootfs write permission alone does not explain the remaining driver failure.
Latest device-only evidence: 0733 (remap physical4-7 to0-3, visible0-3)
and 073e (preserve physical4-7, visible4-7) both exited1 with DEVICE_COUNT0
and DCMI -8020. Artifacts respectively sparse-prefix-smoke-0iNXFv and
sparse-prefix-smoke-7g09xQ under /cache/austinov. No model load occurred.
Read-only host check 0739: no NPU processes on any card; fuser found no open
4-7/manager handles; outside container a41efa7fcf8b contained only bash1991839.
Thus neither actual external compute nor a device-renumbering-only cause is
proven. Do not stop the outside container or claim it is the confirmed cause.
Device-only mode SPARSE_DEVICE_PREFLIGHT=1 now permits bounded diagnostics.
SUPERSEDING STATUS: 0715 completed exit1 before weights loaded. Triton could not
map npu_utils.so from tmpfs; log SHA256
04e9702d5aa1a8c259d31ead6a90e5433cd9614f1290480dcddbabc4ed7d9b51.
Explicit tmpfs exec permissions fixed that error on retry 0721, but the new
run /cache/austinov/sparse-prefix-smoke-7ubVgM failed with get_arch returning
NULL and ascend_hal device count unavailable. Do not repeat full model launch
unchanged; first isolate a device-count/driver preflight in the same container
configuration. No successful model request or performance claim exists.
Previous checkpoint (historical): baseline smoke operation exec-0000000000000715 was running
at last poll. Container 8767e41c2bc9 / qwen35_sparse_smoke_qfye7H;
artifacts /cache/austinov/sparse-prefix-smoke-qfye7H. Poll the operation and
inspect run.log before any new launch. Launcher holds flock npu4-7.lock.
Only physical 4-7 are mapped, to container 0-3. Official image/weights unchanged.
Startup reached LLM config but warned it could not get ascend_hal device count;
no successful request or actual NPU worker execution has been proven yet.
First attempt exec-0000000000000711 failed exit125 before model startup because
Docker permits at most 7 CPUs. Evidence /cache/austinov/sparse-prefix-smoke-7ZDcnC.
CPU quota corrected from 16 to 6; original smoke scripts pushed at a3a24b4.
This smoke is not paper implementation or benchmark completion.
Reproduce Sparse Prefix Caching for Hybrid and Recurrent LLM Serving
(arXiv:2605.05219), then measure performance and quality on the actual
Qwen3.5-27B checkpoint on Ascend 910B4. Status: planned, not baselined.
No model execution, accuracy result, or performance improvement is claimed.

## Completed CPU reproduction checkpoint
- Planning checkpoint fa36a34 pushed; local branch matched its own upstream.
- Author source cloned separately at /cache/cch/paper-sources/sparse-prefix-caching-reproduction,
  pinned d3050d44ed9d878c396cf3fcf632d63743ffed5b; checkout remains clean.
- No license file was found in this checkout. Do not redistribute author code.
- scripts/test_sparse_prefix_author_dp.py runs the unmodified author planner
  against an independent exhaustive oracle: 868 cases, zero failures, plus
  empty/zero histogram and zero budget checks. Legacy missing-type error reproduced.
- Executed in the pinned official image, CPU only, no devices, no network,
  read-only root/source, two CPUs, 2 GiB limit, and a writable artifact mount.
- Raw per-case artifact: /cache/austinov/sparse-prefix-cpu-sRpewC/author-dp-oracle.json
- Artifact SHA256: be5528e45ca6df64dfad944aada7d9c897ecf4786a8cc728f7ef9c1bda9d8ead
- Test SHA256: f618af75bcb610c1684904a82cfe69c9c4364e1dec5302efbcdcef40655f4a78
- Author strategies.py SHA256: 9d2d1ba380a5f74121dec11bb5ba7e34388844c02844458ebe4b7f89dd13360e
- AWMCP operation exec-000000000000069f completed exit 0; disposable container
  qwen35_sparse_prefix_cpu_oracle_20260911 no longer exists. No NPU used.
- This does not validate streaming histogram behavior, checkpoint restoration,
  real-model outputs or NPU latency. Next: inspect actual image model/cache APIs,
  identify exact Qwen3.5-27B weights, then restore-state canary on NPU4-7.

## Scope and ownership
- Parent business task: Qwen3.5 performance; this is a bounded paper reproduction,
  not another permanent business stream. Archive this worktree after integration.
- User now authorizes physical NPU4-7 when no actual compute process uses them.
  A running/exited container device declaration alone does not block use.
- Do not stop or modify external containers. Recheck actual processes before
  allocation, coordinate cooperative leases, check ports and MemAvailable >=48 GiB.
- No NPU lease currently held; no controller or experiment container exists.
- Preserve BF16, original weights, no retraining/quantization/MTP/speculation.
- Preserve original host/image vLLM-Ascend; use removable runtime injection into
  disposable containers with read-only code mounts. No source overlay or commit.
- Existing performance worktree is dirty and ahead of upstream; do not stage,
  overwrite, reset or absorb those changes.

## Frozen known identity (2026-09-11)
- Starting repository: 31c43a4c249c9d4c597372f47d989a7c10b2c9c4.
- Local official image ID:
  sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
- Repository digest:
  quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a
- Model path, model/tokenizer hashes, source import paths, CANN versions,
  CPU binding and service port: not yet frozen. Never substitute Qwen3.6/3.8.

## Source intake and reproduction risks
- Paper: https://arxiv.org/abs/2605.05219
- Experimental repository: https://github.com/arabel1a/sparse-prefix-caching
- Repository revision and code license: must be pinned/verified before reuse or
  redistribution. No author source has been vendored here.
- Observed public strategies.py uses O(M*N^2) enumeration, whereas the paper
  describes an O(M*N) solver. Reproduce original first; evaluate solver changes
  separately. Include planning cost when paid online.
- checkpoint_cache.py correctness helper calls checkpoint_positions with tag
  instead of required type. Full-hit path returns dummy hidden output; it is not
  a first-token correctness oracle. Validate logits and generated sequences.
- Author timing separates checkpoint capture into untimed runs. Our deployment
  measurements must include capture, restore, copies, replay and eviction.
- Prior independent JS recurrence screen: 700 tiny cases matched brute force,
  maximum difference 8.881784197001252e-16. This is NOT execution of author Python,
  full algorithm verification, Qwen accuracy or NPU evidence; rerun durably.
- Main checkout under /cache/cch/vllm-ascend has Mamba hit/alignment code, but is
  not proven identical to the official image. Inspect pinned image before edits.

## Planned comparisons
1. Author algorithm reproduction: original DP vs exhaustive tiny-case oracle;
   zero budget/histogram, concentrated/tied distribution, block alignment,
   update/replan and memory budget cases. Pin sources and hash inputs/results.
2. Workload opportunity: tokenize actual query_rewrite with exact chat template;
   estimate checkpoint benefit using past-only observations, no future leakage.
3. Baseline arms: no reuse (context only), native cache, fixed shared-prefix
   checkpoint, uniform checkpoints. Treatment: distribution-aware checkpoints.
   Equal memory budgets and identical arrival order; distinguish cold/warm cache.
4. Validate entire model state: Attention KV, GDN recurrent state, convolution
   history and positional/cache metadata. Cover full/partial/no hit, repeated
   restore, branch divergence, one-token suffix and eviction. Check immutable
   checkpoint ownership; device .to() may alias, so prevent in-place corruption.
5. Real-weight smoke, paired 32-sample canary, then c1/c16 screen and
   c1/c5/c8/c16 three repetitions with per-request TTFT/TPOT, P50/P95/P99,
   throughput, memory and failures; paired all-357 query_rewrite natural-EOS
   quality gate. Ground-truth-free equality is not general task accuracy.
6. Baseline-repeat variability, exact tokens/logits where meaningful and
   adjudicated differences determine the quality claim. Report improvements,
   regressions and inconclusive results alike. No invented performance numbers.
7. Legacy delivery target (TTFT -40%, TPOT -20% each concurrency) remains a
   separate acceptance question; this prefill algorithm is not presumed to
   accelerate decode. Reproduction completion does not require hiding a null result.

## Next action
2026-09-11 identity gate PASSED: all 11 local weight SHA256 values from completed
exec-00000000000006e2 match official Qwen/Qwen3.5-27B blob/main file pages.
Official source: https://huggingface.co/Qwen/Qwen3.5-27B/tree/main
Each shard page exposes SHA256 under Xet Pointer Details; all 11 were read.
Expected values are stored in qwen35-official-weights.sha256 beside this handoff.
This supersedes the upstream-unproven note below; no weights were changed.
Planning and CPU checkpoints fa36a34/c0cb9cb are pushed; do not repeat them.
Use ONLY /cache/efim/Qwen3.5-27B, subject to weight verification. Eleven
safetensors shards are present. Hashing operation: exec-00000000000006e2.
Poll that handle rather than duplicating it. Official HF API retrieval from
the host failed with curl exit 28; upstream weight equivalence remains unproven.
IMPORTANT: the old launcher used /cache/austinov/Qwen3.8-27B while advertising
Qwen3.5-27B. Do not reuse those results as Qwen3.5 evidence. User explicitly
requires model identities and measurements to remain separate.
Pinned image sources: /vllm-workspace/vllm/vllm and
/vllm-workspace/vllm-ascend/vllm_ascend (editable installs).
Image Qwen3.5 rejects mamba_cache_mode=all; native align is the starting point.
GDN prefill accepts initial state and emits final state at chunk boundaries;
arbitrary checkpoint retention is NOT implemented or verified yet.
Latest snapshot: external VLLM workers occupy NPU0-3; NPU4-7 have no compute
process; MemAvailable 64274020 kB. Snapshot is not a lease or future proof.
ascend-canary-implementation has been fully read. Recheck resources before smoke.
Read .agents/skills/paper-to-ascend-reproduction and its evidence contract.
All long commands use one tracked operation handle; poll rather than duplicate.
Git fetch timed out once, then succeeded on bounded retry. AWMCP was healthy.

## Evidence and release
Raw model/data/log outputs belong outside Git under a unique /cache/austinov
artifact root (not yet allocated). Record SHA256 and exact commands per stage.
No experiment resources have been allocated, so there is nothing to stop.
