# DAMP FP32 live reference collector

Status: **v4 generation completed; the original validator failed the external/internal
request-ID join. A separate source-bound read-only v4 audit now passed TP4/all48
capture coverage and exact output parity. Original failed evidence is retained.
The new observer has passed software checks but has not run live. No compressed
recurrence, full calibration, performance or quality acceptance is claimed.**
This is a diagnostic/calibration hook, not the compressed recurrence candidate,
not a graph implementation, and never a performance measurement.

## What is observed

- Explicit `DAMP_CAPTURE_ENABLE=1` installs the `vllm.general_plugins` entry point.
- Frozen v0.23 GDN/runner source SHA256s; recurrent operator schema and source hashes
  are recorded per worker. It calls the original gating and original `_forward_core`
  and returns their original objects. It never writes recurrent state, model output,
  weights, Q/K/V, g or beta.
- Current native FP32 state is `[slot,Hv=12,Dv=128,Dk=128]`. Quantization/value
  channel statistics run along Dv, not native last-axis Dk.
- Exact prompt token fingerprints bind manifest rows to real runtime request IDs.
  Runner positions prove decode-first/prefill ordering, including mixed turns.
  Slot aliasing, moves, stale owners, prefix restoration, repeated/continuation
  prefill, canceled incomplete captures, speculation and graph mode fail closed.
- Each real turn must observe all 48 GDN layers exactly once, all TP4 workers must
  produce matching manifest/source/request evidence. No partial-rank acceptance.
- Both source-proven Ascend donor and actual Qwen receiver get the same core
  wrapper after their original function-object alias is verified. On the first
  real runner forward, all48 actual dispatcher instances, class/source identities,
  wrapper and original owning functions must be proved before native execution.
- Only anchor state is copied to CPU. Future log-g is copied every decode step;
  RMS is accumulated in FP64 over the key dimension only for the fit partition.
  An anchor at update t stores state after t; its future starts at t+1.
  Retention is `1 + sum(exp(2*cumsum(g[t+1:t+H])))`, separately for 12 value heads.

Full mode requires 36 distinct TRAIN prompts: MATH/APPS/ARC-Challenge, 12/domain,
four/domain in each disjoint fit/tune/validation partition, exactly 1024 native
chat-template input IDs, fixed4096 output with ignore_eos, anchors
256/512/768/2304/2560/2816, next256 decays.
These author sample IDs and prompt construction are not published, so provenance
must say **project-selected-paper-training-domains**, not author-exact data.
The parent has downloaded and hash/size-verified nine pinned TRAIN artifacts,
110296287 bytes total, in external `calibration-inputs/source-v2/SOURCE_INDEX.json`.
The first no-device builder failed because pyarrow was absent. The parent isolated
hash-pinned PyArrow22 without changing the image; v2 then found a real1024 native
chat-template boundary gap. The bounded TRAIN-only context repair passed the same-image no-device v3 builder:
36 exact1024 inputs with 398 disjoint target/context TRAIN records; file SHA256
f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33.
This input readiness is not completed model calibration.
Missing/unpinned/unlicensed source bytes,
test sources, wrong geometry or absent rows are hard errors; no fallback.
GSM8K and LongBench-v2 final-evaluation records are forbidden calibration sources.

Smoke mode uses at most12 project smoke rows, 9 fixed output tokens, anchors2/4
and future2. It proves only hook/evidence/output preservation. Prefill emits the
first output token, so nine outputs normally contain eight recurrent updates.

## Parent-owned single-pair smoke launch

Before running anything, parent must freshly prove direct chicaihong01 routing,
actual NPU4-7 idle/ownership and parent-created **nonprivileged** TP4 container
with physical4..7 mapped to logical0..3, model/repo read-only and the result tree
writable. Confirm the Python executable and exact image/source hashes. Do not
reuse a stopped single-card gate container as a TP4 container.

Use these exact process arguments inside that parent-owned container.
The commands below use v5 paths, which must be freshly absent. v1/v2/v3/v4 failed
evidence/container records must be preserved. Do not rerun/overwrite on failure.

Environment for every command:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=/opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/collector
ASCEND_RT_VISIBLE_DEVICES=0,1,2,3
```

Create only the CPU smoke token manifest (no model execution):

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.prepare \
  --mode smoke --limit 2 \
  --input /cache/cch/qwen36-awq-w4a8-20260923/calibration_text_v1.jsonl \
  --output /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v5.json
```

The old smoke text source SHA256 is
`2ad23073422f443ac35a90af82812f236ceea2da998a5fe8cb7c65b83a0b0ec3`.
Its source/license revision is not independently established. It is never used
for full calibration or task accuracy. The manifest records source and token hashes.

The real tokenizer gate was run in a separately parent-owned same-image container
with NO NPU device mappings. Its reproducible command (CPU tokenization only):

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.tokenizer_gate \
  --input /cache/cch/qwen36-awq-w4a8-20260923/calibration_text_v1.jsonl
```

Require DAMP_NO_DEVICE_TOKENIZER_GATE=1, ASCEND_RT_VISIBLE_DEVICES empty and no
/dev/davinci[0-9]*. Keep model/repo read-only. The gate fingerprints two actual
smoke inputs and checks explicit return_dict=False returns deterministic list[int].
Transformers' default return may be BatchEncoding; coercing its keys to tokens
is forbidden. Preserve failed v1/v2/v3 directories; use independent v5 paths.

The same-image tokenizer gate passed under Transformers5.5.4: default return
was BatchEncoding, explicit return_dict=False returned85/72 native token IDs.
The real gate is separately evidenced; the stdlib suite skips it by default.

VLLM_PLUGINS filters both platform and general groups in this pinned image.
Both arms keep ascend,ascend_kv_connector,ascend_model,ascend_model_loader,damp_capture.
The source-confirmed connector/loader registration invokes _ensure_global_patch;
model registration supplies Ascend model classes. Service profiling, Arctic and
unrelated LoRA plugins are not enabled. Parent must run platform_gate in a fresh
NO-NPU same-image process with this allowlist and DAMP_CAPTURE_ENABLE=0; it verifies
the actual NPUPlatform, required entrypoints, global runtime patch and frozen
sources. It intentionally does NOT load native libraries or establish recurrent
ABI/NPU dispatch; those require mapped live import/canary and actual model hooks.
The source-only preflight is not a model/NPU result.

Run the native same-eager oracle and capture in **separate processes**:

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.run \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v5.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v5-off \
  --capture off --batch-size 2 --memory-utilization 0.80
```

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.run \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v5.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v5-on \
  --capture on --batch-size 2 --memory-utilization 0.80
```

All output IDs must match the same-eager capture-off oracle:

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.validate \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v5.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v5-on \
  --dense-output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v5-off
```

The validator checks source/schema fingerprints, all4ranks x48layers, per-request
anchor/future files, exclusive creation and file hashes, completion and exact
client output parity. Parent must preserve raw stdout/stderr and outer Docker
inspect/device checks beside the run. The collector deliberately does not stop,
create or inspect containers, reset devices, or schedule external resources.

## Full-mode input boundary

`prepare --mode full --input prepared-training-rows.json --output ...` accepts
already-tokenized 36-row input with construction provenance. Each row includes
`id, input_ids, input_ids_sha256, prompt_text_sha256, domain, split, source`.
Each source includes actual TRAIN dataset name, immutable40/64-hex revision,
record ID and hash, raw artifact path+SHA256, source URL and verified data license.
Artifacts must reside under
`/cache/cch/qwen36-damp-20261006/calibration-inputs`, outside Git.
Do not pass test sources, historical DRRQR calibration, fabricated padding, or
short smoke text as full data.

Pinned TRAIN source selection (external byte receipts belong to the parent):

- MATH: EleutherAI/hendrycks_math train metadata/card; MIT card must be bound to
  actual snapshot and source terms, not generalized to every source problem.
- APPS: codeparrot/apps train mirror. Original dataset appendix specifies
  **CC BY-SA3.0 data**; MIT repository/card does not erase that obligation.
- ARC-Challenge: allenai/ai2_arc ARC-Challenge train; publisher card CC BY-SA4.0.

Prefer one bounded immutable TRAIN artifact per domain. Metadata selection must
precede downloading, preserve license/revision/hash, and explicitly limit size.
The exact 1024-token construction for short ARC questions needs a documented
project choice and distinct TRAIN-only context records; it cannot be silently
called the author's original sample. The project full-training-36x1024-v3 manifest is complete; full model capture remains open.

## CPU checks

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/damp-ascend/collector \
  /usr/bin/python3 -B -m unittest discover \
  -s projects/damp-ascend/collector/tests -v
```

The current stdlib suite includes exact copied-function alias, actual48-instance,
text MRoPE and native decode ABI regressions;
software-only test/AST receipts are separate from same-image tokenizer and NPU
receipts. Plugin entry point and prepare/run/validate CLI checks do not load a model.
These checks do **not** replace real Ascend smoke, full calibration, compressed
recurrence/graph correctness, paired E2E performance or final task accuracy.

Prelaunch repair: pinned vLLM scheduler.py SHA256
`36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86`
lines259-270 requires max_num_batched_tokens >= max_model_len when chunked prefill
is disabled. The launcher therefore uses max(8192,batch_size*1024), not4096.
The AST-only regression test checks all admitted batch sizes1..4 without importing
torch or executing a model. No numerical acceptance criterion was relaxed.

## Source-proven metadata and actual receiver repair

The v2 logs show the old `positions.ndim == 1` gate failed on all TP4 workers.
They did not print the tensor shape. Preserved v3 rank0 evidence now records
native `[3,157]` prefill and `[3,2]` decode, identical rows and unchanged native
arguments. This is metadata evidence, not completed capture acceptance.
Qwen3_5ForConditionalGeneration inherits Qwen3VL MRoPE.
For no media, qwen3_vl.py lines2580-2589 broadcasts `arange(prompt_len)` to three
rows and returns delta0; gpu_model_runner.py lines2634-2680 copies prompt rows
and mrope.py lines402-414 broadcasts completion positions. The Ascend runner
uses_mrope branch passes the original multirow tensor to the model.

Admission now requires no mm_features, no prompt_embeds, no mixed-token mask,
zero MRoPE delta, exact prompt `[3,prompt_len]` arange proof, three identical live
rows matching the existing CPU unpadded GDN query/computed-token mirrors, and no
context parallel/XD-RoPE. Row0 is selected ONLY for collector bookkeeping after
that proof; original native call arguments and position tensor remain unchanged.
Different rows, wrong ordering, nonzero/unknown delta and all unverified media
paths fail closed. Every admitted turn records actual shape and timeline hash.

Pinned `_build_actual_seq_lengths` is `[query_start[0], diff(query_start)]`,
not cumulative ends. Eager one-token decode therefore uses `[0,1,...,1]`, length
num_decodes+1. It is checked against CPU scheduled boundaries and actual native
state-slot cardinality/uniqueness, including a mixed prefill tail. The old
`[1,2,...,num_decodes]` expectation was a collector bug, not native invalidity.

All six supporting source paths/SHA256s are frozen in `text_positions.py` and
verified in each worker; validation requires those identities and one position
proof for every completed turn. This source audit does not substitute for v4's
same-eager token-output parity, 4 ranks x48 layers, anchors and future decays.

The v3 first native model forward reached exact48 coverage validation with zero
collector core calls. The actual model constructs `QwenGatedDeltaNetAttention`,
not `AscendGatedDeltaNetAttention`. The native patch copier at
`vllm_ascend/patch/worker/patch_qwen3_5.py` lines207-208 copies ordinary function
objects from donor to receiver. Replacing the donor later does not update that
receiver. The custom dispatcher dynamically looks up each real instance's
`_forward_core` from `forward_context.no_compile_layers`; changing the dispatcher
or clearing failed turn IDs would hide rather than fix the cause.

`bindings.py` freezes copier SHA256
`21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3`,
receiver SHA256 `885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0`,
and forward-context SHA256
`1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5`.
The loaded copier/target identity and both original native aliases must match;
one wrapper is explicitly assigned to both classes. The first real forward
records `worker_dispatch_verified` for exact48 actual Qwen instances with class,
wrapper, original core and native outer-forward paths/hashes. Missing layers,
subclasses, prefix mismatches and instance method overrides fail closed. No
request identity, gating/state check or per-turn coverage criterion is relaxed.

## Native request-ID observer and explicit v4 recovery

In this exact runtime, InputProcessor.assign_request_id stores the supplied
external ID, then constructs internal ID external+"-"+eight random hex digits.
LLMEngine.add_request returns that internal ID. RequestOutput returns the
external ID. v4 incorrectly persisted the latter as client.runtime_id, so its
worker/client join failed even though IDs referred to the same request.

For new v5 runs, only the parent process's **engine instance** add_request is
observed. Source/class/owning-function gates precede installation. Original
arguments, native return object and generation are unchanged. The observer
requires unique manifest token sources, n=1 and plain token EngineInput, writes
request-identities.jsonl, and joins outputs by their explicit external ID.
client.jsonl retains both external_request_id and actual internal runtime_id.
Both off/on arms use the same observer. Validation requires its full source
receipt, unique identity coverage and every worker's internal ID/prompt match.
The observer is not applied to workers or to the upstream class.

Three frozen identity sources (all beneath
/vllm-workspace/vllm/vllm/v1/engine/):

- input_processor.py: c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15
- llm_engine.py: 2900f6732a1e507f6ced6f75f05f1fcaf2cc2929df0f5066574e9077ad3fbde1
- output_processor.py: 464c3cda347512cf1090f8e6471d0d3f0f65e286eb9a7b97be52efbc1ffd572a

The stopped original v4 container was independently inspected read-only:
qwen36_damp_collector_tp4_20261006_v4,
ID 4d28e606bfd804ddfbcb2835800d2f3a63b26fd528ac568e5401798f2e74b981,
image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1,
nonprivileged, exact physical4-7 to logical0-3. No container was restarted.

Recovery is restricted to that original two-request smoke pair, not arbitrary
old evidence. Parent must save unchanged Docker inspect JSON and three source
file bytes into an independent external preflight directory. Then create this
input description, **not** a success receipt or source-lock:

```json
{
  "schema": "damp.legacy-v4-source/v1",
  "container_name": "qwen36_damp_collector_tp4_20261006_v4",
  "container_id": "4d28e606bfd804ddfbcb2835800d2f3a63b26fd528ac568e5401798f2e74b981",
  "image_id": "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
  "on_root": "/cache/cch/qwen36-damp-20261006/smoke-hook-v4-on",
  "off_root": "/cache/cch/qwen36-damp-20261006/smoke-hook-v4-off",
  "manifest_semantic_sha256": "<original smoke manifest canonical hash>",
  "docker_inspect": {"path": "<unchanged original-container inspect JSON>", "sha256": "<file hash>"},
  "native_sources": {
    "/vllm-workspace/vllm/vllm/v1/engine/input_processor.py": {"path": "<saved bytes>", "sha256": "<pinned source hash>"},
    "/vllm-workspace/vllm/vllm/v1/engine/llm_engine.py": {"path": "<saved bytes>", "sha256": "<pinned source hash>"},
    "/vllm-workspace/vllm/vllm/v1/engine/output_processor.py": {"path": "<saved bytes>", "sha256": "<pinned source hash>"}
  }
}
```

After complete source review, parent runs one CPU-only independent audit:

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.identity \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v4.json \
  --on-root /cache/cch/qwen36-damp-20261006/smoke-hook-v4-on \
  --off-root /cache/cch/qwen36-damp-20261006/smoke-hook-v4-off \
  --legacy-source <parent-prepared-legacy-v4-source.json> \
  --output-dir /cache/cch/qwen36-damp-20261006/legacy-v4-identity-audit-v1
```

The output directory must not exist. The audit requires unique known external
IDs 0/1, an exact external+"-"+8 lowercase-hex relation, identical internal IDs
on all four ranks, matching immutable prompts and native-off/on output token
IDs/hashes. It does **not** remove a suffix blindly. It additionally re-runs
all existing source/schema, 48-layer, anchor/future payload hash, text-position,
completion and output-parity gates. A report references all original file
hashes, retains the old failure unchanged, and cannot become a compressed-state,
performance, full-calibration or task-accuracy claim. Missing source bytes,
wrong container/image/mapping, rank disagreement or partial coverage fails.
