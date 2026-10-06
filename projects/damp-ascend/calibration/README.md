# DAMP offline calibration selector

This is CPU-only preparation for the DAMP v2 mechanism, not an Ascend performance
result. It never starts a service, touches a device, signs a collection success,
or arms a serving plugin. Parent-controlled source review, model collection and
native-off/on output parity are prerequisites.

## Mechanism and honest project choices

Paper: https://arxiv.org/html/2608.27513v2, equations 14–17 and Appendix A.
Native state is `[Hv,Dv,Dk]=[12,128,128]` per TP4 worker. INT8 groups contain
32 value channels, with FP32 scales and symmetric codes; protected 16 key
channels use FP16. Positive general FP32 SR rescales value channels. PV sorts
value RMS **after** scaling; PK preserves native order within protected and low
regions. Original-coordinate restoration precedes squared-error computation.

For each reference anchor, compute `W=1+sum(exp(2*cumsum(next256 log_decay)))`.
Fit key risk is the joint average `E[e8*W]`, not `E[e8]*E[W]`.
Tune cost includes low-region INT8 and protected-region FP16 error. Selection
is independent per rank/layer/value head. Validation is evaluated only after
selection and cannot adjust SR, PV or protected channels.

No author calibration code or exact SR grid has been verified. The declared
project grid is `SR=RMS**alpha`, `alpha=[0,.25,.5,.75,1]`, rounded to FP32,
with SR=1 only for exactly zero RMS. It is not power-of-two constrained. The
INT8 arithmetic follows the source-bound project contract: FP32 reciprocal
bits `0x3c010204`, FP32 division, round-to-nearest-ties-even, [-127,127].
Risk accumulation uses FP64. Under/overflow is rejected rather than epsilon
clamped. Paper gains and task accuracy are not inferred from these objectives.

## Required data and coverage

Full manifest, independently built in the real model tokenizer:

```text
/cache/cch/qwen36-damp-20261006/calibration-inputs/full-training-36x1024-v3.json
file SHA256: f348e0b0404e2f3a619b986f5c1152427c52f1a3550386ee1f894eafa6986b33
semantic SHA256: 6791283f69290789555d4391312e8d8511fee7787d2ea4257599302486f34bb7
```

It contains 36 project-selected publisher TRAIN rows: MATH, APPS and
ARC-Challenge, 12 each. Fit/tune/validation each contain four rows per domain.
Target and real-context identities are disjoint across the entire manifest.
Pinned revisions, licenses, artifact/record hashes and exact native-template
1024-token fingerprints are retained. These are not unpublished author sample
IDs and are not final GSM8K/LongBench-v2 evaluation data.

The generation protocol is exactly 1024 input/4096 fixed output, thinking off,
temperature=0, seed=0. Each of four ranks must supply all 48 GDN layers, all
36 requests, anchors [256,512,768,2304,2560,2816], and the following 256 log
decays. A smoke receipt cannot substitute for any full row. Reference FP32
state payloads alone are 30.375 GiB (about 32.615 GB). Processing holds at most one rank/layer's
fit+tune data, then its validation data, rather than the full model in memory.

## Independent source lock

The parent controller, not this selector, creates a read-only JSON after real
collection/parity validation. No source-lock writer or auto-PASS routine exists.
Schema `damp.source-lock/v1` requires:

```json
{
  "schema": "damp.source-lock/v1",
  "created_by": "parent-controller",
  "model_config_sha256": "<verified config.json hash>",
  "image_id": "sha256:<64 lowercase hex>",
  "manifest": {
    "path": "<full manifest absolute path>",
    "file_sha256": "<file hash>",
    "semantic_sha256": "<canonical JSON hash>"
  },
  "capture_root": "<full on-capture absolute root>",
  "ranks": [
    {
      "rank": 0,
      "events_path": "<capture-root>/rank-0/events.jsonl",
      "events_sha256": "<file hash>",
      "source": {"<all original worker_started.source fields>": "<unchanged values>"}
    }
  ],
  "smoke_validation": {
    "path": "<parent saved exact smoke validator result JSON>",
    "sha256": "<file hash>",
    "requests": 2
  },
  "native_output_parity": {
    "path": "<parent saved exact full validator result JSON>",
    "sha256": "<file hash>",
    "dense_root": "<same-eager native off full root>"
  }
}
```

The illustrative rank list must in fact contain ranks 0,1,2,3 in that order,
logical devices 0–3 mapped to physical 4–7. Preserve the **entire** original
worker source dictionary, not only its summary. Validation reports must be
the exact JSON returned by the frozen collector validator, not an outer
launcher wrapper. Each requires status=pass, ranks=4, layers=48, correct mode
and request count, and all token IDs bitwise same-eager. The full frozen
validator is re-executed read-only and its result must equal the saved report.
Full audit coverage and raw payload hashes are then rechecked again. Unchanged
smoke success cannot authorize changed full code or source.

## Software checks and execution

From the canonical repository, host-only rules can run with standard Python:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/damp-ascend/calibration:projects/damp-ascend/collector \
  python3 -m unittest discover -s projects/damp-ascend/calibration/tests -v
```

Torch tests are explicitly skipped if host Torch is unavailable. That is **not**
a numerical pass. The parent must run the same command in a new **no-device**
container using the exact runtime image, with `DAMP_REQUIRE_TORCH_TESTS=1`.
Tests include a scalar original-coordinate oracle under nonidentity SR/PV,
zero groups, scale-underflow rejection, mixed-error selection and frozen
validation. Synthetic fixtures never stand in for real model receipts.

After source lock and full raw capture are genuinely complete, the parent can
run this CPU-only command with repository/model/data/reference paths available.
Replace placeholders with independently verified paths; the output parent
already exists and the unique output directory must not exist.

```sh
PYTHONDONTWRITEBYTECODE=1 DAMP_CALIBRATION_CPU_ONLY=1 \
PYTHONPATH=projects/damp-ascend/calibration:projects/damp-ascend/collector \
  /usr/local/python3.12.13/bin/python3 -m damp_calibrate.pipeline \
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/full-training-36x1024-v3.json \
  --capture-root <verified-full-on-root> \
  --source-lock <parent-created-read-only-source-lock.json> \
  --output-dir /cache/cch/qwen36-damp-20261006/calibration-plans-v1 \
  --cpu-threads 8
```

Output contains exactly 192 CPU tensors (`pk,pv,sr`), per-plan fit/tune/frozen
validation reports, file and semantic hashes, and full input/code/source/parity
provenance. `PLAN_INDEX.json` deliberately uses
`damp-calibration-plan/v1`, **offline-not-serving**, not the integration
plan-store admission schema. Partial failures are preserved and unservable.
Finite validation is a diagnostic, not a task-accuracy or numerical recurrence
gate. Parent-reviewed conversion still requires compressed NPU recurrence,
graph/cache correctness, paired end-to-end performance and final task accuracy.
