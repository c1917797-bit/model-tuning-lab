# DASC Qwen3.6 Ascend Piercing Handoff

## NPU4-7 v12 resumable controller

The next immutable attempt is dasc-qwen36-physical-cache-v12. It is pinned to
physical NPU4-7 and port 8030; NPU0-3 are explicitly outside scope. Validate and
start exactly once with run_physical_cache_v12.sh --self-test, followed by the
same script without arguments.

The controller waits while any physical NPU4-7 has a live device process, then
takes /cache/cch/.locks/npu4-7.lock, repeats the occupancy check, checks port
8030, snapshots the plugin bytes, and starts the exact owned v12 container. Do
not start a second controller. Poll its authoritative remote exec handle and
inspect the controller log at
/cache/cch/dasc-qwen36-ascend-20260915/controllers/dasc-qwen36-physical-cache-v12.log.
The immutable result directory is
/cache/cch/dasc-qwen36-ascend-20260915/physical-cache-order-fix-v12.

## Current Status

Workstream opened on 2026-09-15 for arXiv:2608.30386 DASC. Paper ingestion,
architecture fit, the state-lifecycle source map, and the first plugin-owned
DASC-NR numerical canary are complete and verified on physical NPU4-7.

The canary lives under `projects/dasc_vllm_ascend`. It is disabled by default,
version/source guarded, and only changes temporal-state copying on a genuine
new/resumed prefix restore. It keeps dense allocation and therefore is not yet
a cache-capacity or performance implementation.

## Mainline Goal

Pierce whether DASC can produce a real cache-hit TTFT or throughput gain on Qwen3.6-27B in the chicaihong01 Ascend environment, while keeping E2E quality within the user's gate. Do not judge it with no-cache decode throughput.

## Delivery Constraint

The final runnable implementation must be a plugin-owned monkeypatch that runs on Ascend. Do not modify upstream vLLM, vLLM-Ascend, CANN, model weights, or original images. CPU/offline probes and source inspection are allowed only as gates; they are not a valid final delivery.

## Short-Term Plan

1. Inspect Qwen3.6 GDN weights and vLLM-Ascend state layout.
2. Generate a DASC-GDN head-retention plan for `W_max` values such as 16, 64, 128, and 512.
3. Compute dense vs compressed checkpoint bytes including recurrent temporal state and convolution state.
4. Source-map vLLM-Ascend prefix-cache/state-checkpoint store/load behavior.
   This is complete: `MambaManager` and `preprocess_mamba` preserve and copy
   aligned convolution and temporal checkpoints by block ID.
5. Review, package, and run the implemented DASC-NR numerical canary with a
   disabled control on physical NPU4-7.
6. After all-rank activation and correctness pass, implement compact temporal
   pages plus dense active-state workspace. Do not mistake the current
   zero-filled dense storage for a capacity optimization.
7. Prove real cache-block admission growth before any service performance claim.

## HYPIC Lessons Applied

- Use one denominator and one treatment switch.
- Prove mechanism activation before timing.
- Separate source compatibility, canary correctness, service integration, performance, and quality.
- Keep per-run artifacts resumable and auditable.
- Do not claim the paper result from a partial primitive.

## Current Decision

Open, with a narrower integration risk. The paper has credible relevance to
Qwen-GDN and the current stack already supports aligned recurrent-state prefix
checkpoints. Local feasibility now depends on whether a plugin monkeypatch can
replace dense block storage with compact retained-head storage plus a dense
active-request workspace while keeping native Ascend GDN kernels unchanged.

## Verified NPU canary and decision

The W64 dense-storage canary ran on Qwen3.6-27B with TP4, vLLM/vLLM-Ascend
v0.23.0, eager mode, Mamba align cache, and physical NPU4-7. Two 2,350-token
prompts shared one 1,536-token cache page. All 48 GDN layers fired on all four
TP workers, yielding exactly 192 temporal-restore events. Candidate and
plugin-disabled control returned identical 16-token continuations.

The steady cache-reuse request was 4.213 s for the canary and 4.008 s for the
control, so the dense-storage canary regressed by 5.095%. It is rejected as a
performance candidate but accepted as runtime-path and semantic evidence.
First-request latency is excluded because both runs included cold operator
initialization.

Runtime artifacts:
`/cache/cch/dasc-qwen36-ascend-20260915/`

The next admissible successor must change the physical representation:
compact retained-head checkpoint storage, dense workspace expansion on restore,
and measured post-alignment cache capacity. Repeating or tuning the existing
dense masking route is closed.

## Physical-cache integration attempts

Two bounded service launches advanced the integration boundary without
producing performance or quality results:

- `physical-cache-eager-v1` reached cache-spec collection on all four TP ranks
  and failed because independently selected local head counts produced
  different shapes for the same layer across workers. Logs and activation
  evidence are retained under the runtime artifact root; their SHA256 values
  are `24732fd...e83854` and `f51df7d...40fcf`.
- Commit `fc1fb2b` added a per-layer HCCL MAX of retained counts. Each rank
  keeps its own weight-derived indices and pads only with its longest-horizon
  omitted heads. The complete v0.23 suite passed 37 tests.
- `physical-cache-eager-v2` proved that collective on physical NPU4-7. All
  four workers emitted identical 48-layer common-count vectors, and the run
  passed the former cross-worker merge assertion. It then failed at the next
  framework gate because heterogeneous Mamba pages were sent through vLLM's
  global page-divisibility path. Logs/evidence SHA256 are
  `831fcf5...09644` and `2237ca8...8e18`.
- Commit `e4587c3` represents aligned attention plus heterogeneous Mamba specs
  as one `UniformTypeKVCacheSpecs` aggregate, retaining the exact inner page
  sizes instead of padding every layer to the dense maximum. It fails closed
  if hidden-state cache or unequal token block sizes appear. The v0.23 suite
  passes 39 tests and the commit is pushed.

No TTFT, TPOT, throughput, or E2E accuracy conclusion follows from v1/v2.
The next run must use a new `physical-cache-eager-v3` artifact directory and
first prove service readiness, physical bytes, real prefix reuse, and retained
state correctness. At the latest orientation, NPU4-7 were occupied by the
separate `vllm_23_au` DeltaLog/fused-GDN piercing process, so v3 was not
started and that workload was not interrupted.
