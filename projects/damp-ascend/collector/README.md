# DAMP FP32 live reference collector

Status: **offline implementation; no live NPU run or calibration success yet**.
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
No training manifest currently exists. Missing/unpinned/unlicensed source bytes,
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
The suggested v1 paths must be freshly absent. Do not rerun/overwrite on failure.

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
  --output /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v1.json
```

The old smoke text source SHA256 is
`2ad23073422f443ac35a90af82812f236ceea2da998a5fe8cb7c65b83a0b0ec3`.
Its source/license revision is not independently established. It is never used
for full calibration or task accuracy. The manifest records source and token hashes.

Run the native same-eager oracle and capture in **separate processes**:

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.run \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v1.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v1-off \
  --capture off --batch-size 2 --memory-utilization 0.80
```

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.run \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v1.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v1-on \
  --capture on --batch-size 2 --memory-utilization 0.80
```

All output IDs must match the same-eager capture-off oracle:

```bash
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.validate \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/smoke-hook-v1.json \
  --output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v1-on \
  --dense-output-dir /cache/cch/qwen36-damp-20261006/smoke-hook-v1-off
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

Minimal verified source leads, **not yet downloaded or pinned**:

- MATH: EleutherAI/hendrycks_math train metadata/card; MIT card must be bound to
  actual snapshot and source terms, not generalized to every source problem.
- APPS: codeparrot/apps train mirror. Original dataset appendix specifies
  **CC BY-SA3.0 data**; MIT repository/card does not erase that obligation.
- ARC-Challenge: allenai/ai2_arc ARC-Challenge train; publisher card CC BY-SA4.0.

Prefer one bounded immutable TRAIN artifact per domain. Metadata selection must
precede downloading, preserve license/revision/hash, and explicitly limit size.
The exact 1024-token construction for short ARC questions needs a documented
project choice and distinct TRAIN-only context records; it cannot be silently
called the author's original sample. Full data/prompt construction remains open.

## CPU checks

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/damp-ascend/collector \
  /usr/bin/python3 -B -m unittest discover \
  -s projects/damp-ascend/collector/tests -v
```

29 stdlib tests passed on chicaihong01; all10 Python files parsed; plugin entry
point discovered; prepare/run/validate CLI help loaded without torch/NPU imports.
These checks do **not** replace real Ascend smoke, full calibration, compressed
recurrence/graph correctness, paired E2E performance or final task accuracy.

Prelaunch repair: pinned vLLM scheduler.py SHA256
`36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86`
lines259-270 requires max_num_batched_tokens >= max_model_len when chunked prefill
is disabled. The launcher therefore uses max(8192,batch_size*1024), not4096.
The AST-only regression test checks all admitted batch sizes1..4 without importing
torch or executing a model. No numerical acceptance criterion was relaxed.
