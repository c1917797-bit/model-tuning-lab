# Qwen3.8 NVFP4 on Ascend 910B4 Handoff

## Current goal — latest user clarification 2026-09-13

LATEST RESOURCE AUTHORITY / DEADLINE: user explicitly authorized stopping
qwen35_t37_pa_workspace_service_v1 and other containers proven to interfere with
this test. This supersedes earlier never-stop-external-container wording only
for conflicting containers, not unrelated services or arbitrary host processes.
Preserve inspect/logs, stop exact IDs, do not delete model/source/bind-mounted data.
Deadline for an evidence-backed result: 2026-09-14 07:40 UTC (12 hours from request).
Report completed results and explicit missing gates by then; never call partial
coverage complete. Continue full objective, not just the canary.
Stopped exact container 58dfe81c55e6a66d1ec377422c04443c822698c0ef5146473de5d2de682fac2b;
it auto-removed by its original --rm policy. Logs/inspect/diff saved under
/cache/austinov/eval-runs/switch-takeover-20260913-POeM1v. Eight NPUs and port10010
were verified released afterward. Maxon4ick_torch_910_dev was not stopped.
Use run_switch_canary.sh for fresh exact-ID-owned lifecycle and protected mounts.

User now explicitly requests trustworthy continued testing to decide whether to
switch to Qwen3.8-27B. Current pair: Qwen3-32B BF16 vs Qwen3.8-27B BF16.
This supersedes the earlier Qwen3.5 correction below. Use SWITCH_VALIDATION.md.
The original NVFP4 QUALITY_PROTOCOL.md is historical, not this switch contract.

Resource gate now BLOCKS launch (exec-0000000000000bcf and subsequent inspect):
qwen35_t37_pa_workspace_service_v1 owns devices0-3, with VLLMWorker_TP PIDs
1735149/1735151/1735153/1735154. Port10010 is held by vllm PID1722640.
MemAvailable64578876kB. No external workload was changed. No lease acquired.
App heartbeat qwen3-8 is ACTIVE every30minutes for this task; unchanged blocked
resource state stays quiet. It must follow existing live jobs, never double-launch.
SSE timing/output guard dependency-free tests passed; MST26skills passed.

Historical chat sentinel has 92/357 empty candidate outputs despite status=valid.
That is not a business-valid run. v3 counts finish-only events as first token.
New chat_benchmark.py v4 fixes that, keeps raw SSE and response text outside Git,
marks one-token TPOT undefined, and rejects empty, whitespace-only, truncated or
reasoning-bearing output. Do not pool v3/v4 timings. Next gate: paired 32-request
diagnostic, not an unchanged full matrix.

Executable lm-eval text-task construction passed in the offline CPU-only image:
exec-0000000000000bc2, 58 tasks, 15361 rows, known-right/wrong MMLU scored 1/0.
HumanEval runtime scoring is separate and not proven by that test.
Prior checkpoint 6b5e8b6 is now pushed.

Latest offline scoring gates: HumanEval164 canonical solutions all passed;
164 intentional RuntimeError completions all failed in the existing restricted
CPU sandbox (exec-0000000000000bd4). evaluator-preflight-evidence.json contains
input/output/evaluator hashes; this is not model accuracy. Added external
NoThinkingCompletions evaluator subclass because upstream template rendering
does not forward enable_thinking. Actual tokenizers for Qwen3 and Qwen3.8 passed
no-thinking/continuation/tokenized payload checks (exec-0000000000000bdb).
The first import probe failed due missing PYTHONPATH, fixed by mounting and
selecting the pinned harness source; no package or framework installation.
Next: live paired32 chat diagnostic and a small MMLU/GSM8K API scoring canary
once the eight-card resource gate permits. No new model inference ran here.

### Superseded Qwen3.5 correction and preserved audit

Latest checkpoint: see `qwen38-nvfp4-ascend/BASELINE_REUSE.md` for the audited
Qwen3-32B c1/c5/c8 repeat-1 cells, hashes, truncation exceptions and conditional
reuse rules. Do not discard valid cells because their parent controller failed.
Offline standard-task data preflight now passes in the fixed device-free,
network-disabled container: 59 configs / 15525 test rows. HumanEval function
resolution is deliberately disabled for this inspection because upstream utils
runs a code_eval sample at import time. Executable evaluator wiring and scoring
remain incomplete; this is not a quality-score result. No NPU lease was taken.

Identity audit: /cache/austinov/Qwen3.8-27B has a Qwen3.8 model card and
config SHA256 191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab.
Its qwen3_5 architecture does NOT identify it as Qwen3.5 weights. Exclude those
historical candidate results from the requested Qwen3.5 switch decision.
The local Qwen3.5 candidate is /cache/efim/Qwen3.5-27B, with a matching model
card, 11 visible safetensor shards, and config SHA256
f8d190c5b89c1521220f935d2567a587d6e291ed69066a45a106560b05a2174c.
Full shard/index and upstream provenance validation is still required.
Qwen3-32B control at /cache/austinov/Qwen3-32B has config SHA256
97e295b63283935788fac5e4f8860862a56d4089538cafc93f0431f2ebe483bb.

Resource observation at 2026-09-13 18:42 UTC: NPU0-7 report no processes;
fuser reports no holders of davinci0-7; port 10010 is free; MemAvailable is
84210248 kB. The sole running Maxon4ick_torch_910_dev container is privileged
and docker top shows only bash. This is a point-in-time observation, not an
acquired lease. User requires eight-card exclusive operation: stop this task's
launch/measurement if another owner uses any card, never stop their workload.

The current business decision is whether to switch Qwen3-32B BF16 to
Qwen3.5-27B BF16 under vLLM-Ascend. NVFP4 exploration is paused. The directory
and branch names are historical and intentionally retained to avoid creating
another worktree. Do not treat an automated old objective as a new model choice.

Acceptance needs matched query_rewrite c1/c5/c8/c16 repeated performance,
MMLU, GSM8K and HumanEval scores, plus output-length and business-quality
context. Verify actual model/checkpoint identity; a Qwen3.8-labelled path and
a Qwen3.5 served alias alone prove neither identity. Historical TP8/DP1 data
must not be represented as TP4/DP2. Preserve the original official image.

Existing artifact roots to audit before rerunning:
- /cache/austinov/eval-runs/qwen3-32b-comparison
- /cache/austinov/eval-runs/qwen-switch-chat-natural-eos-gate1b
- /cache/austinov/eval-runs/qwen38-tp8-full-baseline

The standard-quality controller failed loading cais/mmlu over an unavailable
network. Local datasets exist. offline_standard_data.py now provides local
lm-eval custom_dataset callables without changing prompts or scoring. Host
data validation passed: MMLU 57 subjects/14042 test/285 dev, GSM8K 7473 train/
1319 test, HumanEval 164 unique tasks; malformed subject paths are rejected.
This is data-layer validation only: task wiring and datasets-library execution
still need testing, then serving/quality gates. No model test was launched.

All status, resource assignments and next actions below are historical unless
revalidated against this corrected goal and live ownership.

## Status

- Dedicated worktree: `/opt/host/vnf/austinov/worktrees/qwen38-nvfp4-ascend-910b4`.
- At 2026-09-10T17:09:35Z the live gates changed to available: NPU0-7 had no
  processes, Docker had no running containers, port 10110 was free, and
  MemAvailable was 81,485,876 kB. The current workstream may use physical
  NPU0-3 for its exact disposable-container lifetime; NPU4-7 remain protected.
  Re-prove all of these immediately before launch.
- The mandatory pre-launch recheck at 2026-09-10T17:18:37Z found 81 retained
  Docker containers declaring one or more of physical NPU0-3: 79 are exited
  and 2 are created. Although no container is running and NPU0-7 have no
  process, the user's explicit gate rejects any external container device
  declaration. No service was started and no container was stopped, removed,
  or modified.
- The fixed image's vLLM core can parse this official checkpoint through
  `modelopt_mixed` and already handles its Qwen3.5 prefix aliases. Do not
  translate it into the separate ModelSlim `quant_model_description.json`
  format.
- The actual blocker is that the Ascend platform does not list
  `modelopt_mixed` as supported, and vLLM core's selected per-layer methods are
  GPU implementations rather than Ascend execution methods.
- The checkpoint is mixed precision: 193 dense NVFP4 layers at group size 16
  and 208 FP8 layers. The fixed image registers `W4A16_MXFP4` only for MoE and
  defaults that path to group size 32; no dense group-16 registration exists.
- ops-transformer contains useful E2M1/A16F4 source, but it is not proof of
  910B4 support: FP4-specific kernels are under `arch35`, and the per-group
  checker accepts only 32/64/128/256 while this checkpoint requires 16.
- A device-free, network-disabled build probe in the fixed image selected the
  real top-level `matmul_all_reduce` target for `ascend910b`. Configuration,
  host/arch22 tiling compilation, and 298 kernel objects succeeded before the
  deliberately bounded probe was stopped. The op contract explicitly says
  FP8/FP4 support is new on Ascend 950 and requires antiquant group sizes that
  are multiples of 32. This closes direct reuse for the checkpoint's group-16
  NVFP4 tensors; it is not an NPU execution or speed result.
- A dependency-free exact-format reference codec and tests are now present.
- A separately installable vLLM general plugin now registers
  `modelopt_mixed_ascend_bf16_reference`. It preserves core ModelOpt layer
  resolution, reconstructs NVFP4/FP8 weights with per-fused-shard scales, uses
  BF16 linear compute, and refuses construction unless the explicit reference
  opt-in is set. It does not emulate activation quantization and is therefore
  an integration/quality upper-bound reference, not the final quantized path.
- The reference test passed both on the host and in a network-disabled,
  device-free, disposable `quay.io/ascend/vllm-ascend:v0.23.0` container.
- The fixed image itself contains CANN 9.1.0, Bisheng, ATC, OPP, msprof and
  cannsim. A read-only CANNBot environment check passed inside a disposable
  container, so it can also be used as the isolated build environment.
- The exact official snapshot is complete at
  `/cache/cch/Qwen3.8-27B-NVFP4`. All three shards have recorded SHA256
  identities in `checkpoint-evidence.json`.
- The BF16 control is complete at `/cache/austinov/Qwen3.8-27B`: all 18
  safetensor shards are present (55,563,006,776 bytes), its architecture is
  `Qwen3_5ForConditionalGeneration`, and it has no quantization config.
- A fail-closed checkpoint inspector passes host and fixed-image tests.
- Representative rows from all three shards were independently decoded against
  NVIDIA ModelOpt commit
  `079078de9d3cd26fa5baafdb754bba29dde24f7d`: all 15,360 sampled values
  matched exactly (maximum absolute error `0.0`). Together with the full
  checkpoint inspector, this verifies the packed-nibble, finite-E4M3 local
  scale, FP32 global scale, and group-16 storage contract. It does not yet
  prove end-to-end model accuracy.
- The checkpoint inspector now also validates every FP8 layer's rank-2
  `F8_E4M3` weight plus scalar FP32 `input_scale` and `weight_scale`. All 208
  FP8 layers pass, so all 401 mixed-precision layer declarations now have a
  checked tensor-storage contract. This still does not validate an Ascend FP8
  execution path.
- A proposed `nvfp4_group16_matmul` L0 operator contract now exists under
  `qwen38-nvfp4-ascend/operator/`. CANNBot strict validation passes stages
  1-7 with no warnings. Stages 8-11 are explicitly skipped because the current
  formula harness cannot preserve relational `K:K/2:K/16` symbolic shapes;
  executable tensor truth remains covered by `validate_real_tensor.py`.
- The contract correctly exposes finite-E4M3 checkpoint data as raw `uint8`
  bytes because Ascend 910B4 has no native FP8 dtype. It does not claim native
  FP8 hardware support.
- No NPU kernel, performance result, or accuracy result is claimed yet.
- The quality protocol is now frozen in `QUALITY_PROTOCOL.md`. Stable request
  manifests were generated for 57-subject MMLU (14,042 tests), GSM8K (1,319),
  and HumanEval (164), with source/output SHA256 identities recorded in
  `quality-protocol-evidence.json`. Strict MMLU/GSM8K paired scoring code and
  fixed-image unit tests pass. Generated artifacts remain ignored by Git.
- The old eight-device DP2 launcher has been removed. Matched launchers now
  expose only physical NPU0-3 and use TP4: `start_bf16_tp4.sh` for the control
  and `start_nvfp4_reference_tp4.sh` for the external reference plugin. Model
  and plugin mounts are read-only; candidate installation is confined to its
  disposable container layer. Shell syntax validation passes, but neither
  launcher has been executed while the lease is unavailable.
- Tokenizer audit found byte-identical `tokenizer.json` and
  `chat_template.jinja`, but different `tokenizer_config.json` defaults,
  including the pad token. Both launchers therefore explicitly mount the BF16
  tokenizer read-only at `/tokenizer` and pass `--tokenizer /tokenizer`.
- A resumable OpenAI-compatible quality request runner now renders each chat
  prompt locally with that tokenizer, records its SHA256, appends the full raw
  response, and fails fast on request error. Its fixed-image unit tests pass;
  it has not sent model requests while NPU0-3 are unavailable.
- HumanEval is now executable only through a bounded CPU sandbox: no network,
  read-only root, no capabilities, no privilege escalation, and explicit CPU,
  memory, PID and per-test limits. The shared evaluator is mounted read-only;
  its recognized execution guard is validated in a temporary copy. The
  official example executed six completions and correctly separated three
  passes from three failures/timeouts (pass@1 0.5). Full response preparation
  and paired 164-task pass@1 comparison code has fixed-image unit coverage.

## Current blockers

1. The earlier NPU0-3 process occupancy has cleared, but 81 retained containers
   still declare NPU0-3 (79 exited, 2 created). Under the explicit gate, the
   NPU0-3 lease is not obtainable. Do not start, stop, remove, or modify any
   container. Wait for owner cleanup or an explicit operator decision that
   narrows the declaration gate, then re-audit. NPU4-7 remain protected.
2. The fixed image now has a device-free validated external, fail-closed
   ModelOpt BF16 reference adapter, but it has not passed a four-rank model
   startup. Native or faithfully emulated activation quantization is still
   required before claiming the official NVFP4/FP8 runtime semantics.
   Native reuse of the ops-transformer FP4 path is closed for 910B4/group16.
   The next correctness-first implementation is exact ModelOpt NVFP4 and FP8
   decoding to BF16 weights at load time. That path can establish checkpoint
   semantics and full-model quality but must be labelled a BF16-compute
   fallback, not native quantized acceleration. A later 910B4 stream-dequant
   kernel is eligible only after this reference path passes.
3. Two pushes of the latest local commits failed with a transient GitHub TLS
   receive error. The commits and unpushed operator spec remain safe locally;
   retry without rewriting history.

## Next actions

1. On the next valid NPU0-3 lease, start the BF16 control with TP4 in a fresh
   disposable container and record four-rank activation, load time and memory.
2. Then start the BF16-compute reference plugin
   through a read-only mount and disposable installation. Require four-rank
   activation and record load-time plus per-rank memory before any request.
3. Run deterministic smoke and a small paired quality canary. Label these
   results as weight-fidelity BF16-compute reference results because activation
   quantization is not yet emulated.
4. Only after the reference adapter passes, evaluate a 910B4 group-16
   stream-dequant + BF16 Cube operator against it; do not port arch35 code.
5. Integrate through a read-only mounted plugin in a
   fresh disposable container and run BF16/NVFP4 paired performance and quality.

## Verified operations

- Chip detection: `exec-0000000000001385`, DCMI `Ascend910B4`.
- Host reference codec: `exec-0000000000001386`, pass.
- Fixed-image device-free codec: `exec-000000000000138c`, pass.
- Fixed-image CANNBot environment: CANN 9.1.0, pass with one non-blocking
  runtime-library-path warning.
- Checkpoint inspector host and fixed-image tests: pass.
- Complete official checkpoint contract: `exec-00000000000013df`; 3/3 shards,
  2,194 tensors, all 193 NVFP4 layers validated with zero ABI errors.
- Representative real rows from all three shards:
  `exec-00000000000013e3`, `exec-00000000000013e4`, and
  `exec-00000000000013e5`; 15,360 decoded values total, exact matches,
  maximum absolute error `0.0`.
- Checkpoint SHA256 manifest: `exec-00000000000013e6`; recorded in
  `checkpoint-evidence.json`.
- CANNBot strict L0 spec validation: `exec-000000000000001c`; stages 1-7
  PASS, stages 8-11 explicit SKIP for the documented relational-shape harness
  limitation, zero warnings and zero failures.
- Real `lm_head.weight` row-0 ModelOpt cross-check:
  `exec-00000000000013cd`, exact match, maximum absolute error `0.0`,
  packed-row SHA256
  `31c1dd3c007d2daca930d927d6217ade2a96ba42826bfd3ae8073c22d7f0c4d7`.
- Fixed-image ModelSlim/registry/API audit:
  `exec-000000000000003a` through `exec-0000000000000045`; recorded in
  `runtime-compatibility-evidence.json`. It proves that an external execution
  method adapter and dense group-16 scheme are required. It is device-free evidence,
  not an NPU support or speed claim.
- Mixed NVFP4/FP8 checkpoint inspector: host `exec-000000000000004b` and
  fixed-image read-only mount `exec-000000000000004d`; 193/193 NVFP4 and
  208/208 FP8 layers passed with zero tensor-contract errors.
- Fixed-image `torch_npu` public API contract and ops-transformer source audit:
  `exec-0000000000000064`, `exec-0000000000000066` through
  `exec-0000000000000069`. A2 documentation does not establish FP8/FP4
  `npu_quant_matmul`; ops-transformer group-16/910B4 capability remains
  unproven and must be probed rather than assumed.
- Offline ascend910b build probe: dependency discovery
  `exec-00000000000000d6`; real top-level build
  `exec-00000000000000f5`; bounded stop of the exact disposable container
  `exec-000000000000011a`; source identities and post-build inspection
  `exec-000000000000011e`. Configuration and arch22 host compilation passed,
  298 kernel objects were generated, and no full-build or FP4 capability claim
  is made.
- BF16 reference adapter tests: unit/load-after-process
  `exec-000000000000013a` (7/7 pass); real checkpoint NVFP4 and FP8 rows
  `exec-0000000000000136` (5120 and 6144 values, exact); standard package
  install and vLLM entry-point discovery `exec-0000000000000134`; all 401
  official layer mappings `exec-000000000000013b` (193 NVFP4, 208 FP8).
  Detailed evidence and preserved development failures are in
  `reference-adapter-evidence.json`.
- BF16 control and local evaluation data discovery: `exec-0000000000000148`,
  `exec-0000000000000147`, and dataset structure/count audit
  `exec-0000000000000149` through `exec-000000000000014a`.
- Frozen full quality manifests: `exec-000000000000014e`; fixed-image,
  network-disabled, device-free tests: `exec-000000000000014f` and
  `exec-0000000000000151`. See `quality-protocol-evidence.json`.
- Four-device TP4 launcher syntax validation: `exec-0000000000000159`, pass.
- Paired tokenizer identity/default audit: `exec-0000000000000161` and
  `exec-0000000000000162`.
- Quality request runner fixed-image, device-free tests:
  `exec-0000000000000163` (2/2 pass); updated launcher syntax validation:
  `exec-0000000000000164`.
- HumanEval sandbox development failures before execution or due input naming:
  `exec-0000000000000002`, `exec-0000000000000003`, and
  `exec-0000000000000008`; all are preserved in
  `quality-protocol-evidence.json`. Successful functional smoke:
  `exec-000000000000000c`, 3/6 pass and pass@1 0.5; result artifact SHA256
  `9e47a72acc1ffe3440a15f000f54a7b56233d34c8347a8085c728a52e2673db3`.
  HumanEval preparation/scorer unit tests: `exec-0000000000000017`, 4/4 pass.
- Available-resource snapshot: `exec-0000000000000024` through
  `exec-0000000000000027`; competing worktree/resource-claim audit:
  `exec-000000000000002a`. No running containers or NPU processes, port 10110
  free, MemAvailable 81,485,876 kB. The Qwen3.5 workstream's claim is
  conditional on its own live lease and has no live process/container; this
  workstream now owns the next exact NPU0-3 disposable-container lifetime.
- Mandatory declaration recheck: NPU state `exec-000000000000003a`, running
  containers `exec-0000000000000036`, all retained containers
  `exec-0000000000000039`, exact NPU0-3 declaration list
  `exec-0000000000000040`, and count `exec-0000000000000042`. The result
  supersedes the earlier lease interpretation: 81 retained declarations block
  startup under the user's stated gate.
- Whitespace/error check: `exec-0000000000001387`, pass.
- Live resource audit: `exec-000000000000138a` and
  `exec-000000000000138b`; NPU0-3 unavailable.

## Safety

Do not modify the fixed image, site-packages, host framework sources, external
containers, or NPU4-7. Store raw datasets, weights and runtime artifacts outside
Git and commit only code, protocols, manifests and summarized evidence.
