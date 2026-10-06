# DAMP post-reference preparation

This is a stdlib-only adapter, not a new selector. It does not sign SOURCE_LOCK,
start a container/NPU, rebuild an operator, or relabel an offline plan for serving.
The frozen fit/tune/validation math and thresholds are unchanged.

Actual on-resume source routes:
- capture: /cache/cch/qwen36-damp-20261006/full-reference-resume-v1-on
- audit: /cache/cch/qwen36-damp-20261006/full-reference-resume-v1-launch
- source lock: the audit directory's SOURCE_LOCK.json
- new CPU selector output: /cache/cch/qwen36-damp-20261006/calibration-plans-v1

Default plan command (host stdlib, no selector/Torch/NPU execution):

```text
/usr/bin/python3 -B projects/damp-ascend/tools/post_reference_plan_v1/run.py
```

After MAIN independently observes successful RESULT.json and SOURCE_LOCK.json
SHA256, it may run the following INSIDE a fresh no-device immutable-image CPU
environment it owns. The repository, model and original reference/data roots
remain read-only; only the new plan output root is writable. Replace the two
hash placeholders with actual receipts, never guessed values. The adapter
cannot create either receipt and rejects FAILURE/STOP_FAILURE/unfinished finalize.
Do not execute while CPU/RAM demand would compromise the TP4 reference collector.

```text
DAMP_POST_REFERENCE_CPU_EXECUTE=1 /usr/local/python3.12.13/bin/python3 -B projects/damp-ascend/tools/post_reference_plan_v1/run.py --execute --source-lock-sha256 <MAIN_SOURCE_LOCK_SHA256> --parent-result-sha256 <MAIN_RESULT_SHA256>
```

The adapter invokes the exact frozen damp_calibrate.pipeline CLI with eight CPU
threads. It replays full Capture admission:36 TRAIN prompts,48 GDN layers,4 ranks,
six anchors and256 future decays, all native-off/on token IDs, actual receiver
bindings and immutable source receipts. Payload hashes are checked when the
unchanged selector loads every fit/tune/validation sample. Selection uses only
fit/tune; validation remains diagnostic, never feeds parameter selection.
Failure/partial plans remain nonservable, new outputs cannot overwrite old runs.

Expected 192 plans still have schema damp-calibration-plan/v1 and purpose
offline-not-serving. The existing integer_compaction_v1 PlanStore is deliberately
smoke-only; a successful selector is not a reason to rewrite this label.

Next real adapter: tools/calibrated_plan_admission_v2/run.py --index ...,
default plan first, then explicit CPU weights-only admission. It produces a NEW
ready-for-final-plan-validation receipt, never a serving admission. The source
lock explicitly lacks model-weight byte identity; bind actual serving weights
before final same-stack measurements.

No current production run_npu_gate CLI accepts final plans. NEW final_plan_gate_v1
must inject the actual192 arrays into the independently anchored FP32 oracle,
retain B1/B16x160 changing-slot own-feedback/complete-state/pointer/input guards
and adapted graph tests. Kernel graph success is not full model graph success.
Independent frozen TRAIN-validation anchors may seed numerical fixtures but
must not become task accuracy or feedback to tuning. Any additional HOLDOUT
generation requires TRAIN-only disjoint source identity, not GSM8K/LongBench
test samples.

Actual cache shared-arena ABI, prefill packing, scheduler batch2..15, all48x4
receiver bindings and request/reset/exception lifecycle are distinct pending
gates. Formal40 requests C16 input32768 shared-prefix16384 output1024 and same
common dense optimizations are NOT replaced by an eager/max_num_seqs1 screen.
Normal EOS/max2048/think-off quality is separate; no performance/accuracy
claim is issued by this package.
