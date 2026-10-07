# KVBuffer native-order / padding-domain follow-up (NEW draft)

Default OFF; independent namespace `qwen36_kvbuffer_native_order_v2`.
This package and the seven-source `operator/native_order_v2` are a successor,
not an edit of the frozen old49, bridge60, original raw tensors, or old receipts.
No compiler/load/NPU/graph/model/E2E/accuracy result is asserted here.

## Actual failure evidence and preregistered scope

B1 graph trial2 step104, slot3/log9→10, h7/v5: actual BF16 0xbb8b,
native 0xbb8a, difference3.0517578125e-5 / expected maxabs0.00909423828125
=0.003355704697986577. Saved complete-state error remains1.145544e-7.
All B1 floating buffers were finite. MA094e's CPU-double dot diagnostic
straddles the BF16 midpoint by ~1e-10; it is not a FP32/ASC reproducer.

B16 graph trial0 step9 active0: only native expected padding has three NaNs.
The pinned native kernel skips seqLen<=0 without writing output, while this
candidate explicitly emits zero padding. The NEW finite contract selects
only native-defined expected[:active]. It still requires every candidate
output element, six complete state/log buffers, independent complete logical
state, and entire native FP32 state to be finite. Original zero padding,
immutable inputs/pointers, untouched slots, logs, nonflush dense-base and
full/per-head state gates remain unchanged. Raw native padding is never
masked, overwritten, or rewritten.

The actual failed raw files/SHA remain:
- B1 raw-step-b1-graph-t2-step104.pt:
  c53ef1f5263de0a058664d075b7e185fa1b33f06c05481dd0943d5796375a47a.
- B16 raw-step-b16-graph-t0-step9.pt:
  1c7b28d52e21c2d5c28a922cbbe72cbaaa7d403d963defab8dcbd666ba6c3ba8.

The original 160 changing-feedback steps, B1/B16, one eager plus three graph
trials, seeds, resets64/112, active schedule, flush counts, raw-before-metrics
failure retention, output0.00303 and complete/per-head state2e-6 are retained.
No output tolerance adjustment, tie snap, fake PAD batch or successful
reinterpretation of a failed original operation is permitted.

## New numerical source (no dense persistent sidecar)

Only ProcessTile changes after mechanical namespace/target/header renaming.
Each active step reconstructs prior state in the existing UB using the same
parallel log fold, applies current gate, performs native-order K prediction,
native LocalTensor residual expression, beta, outer MulAddDst, then reads
updated FP32 S with scaled Q and one BF16 cast. Dense GM StoreBase occurs
only on actual flush; append still stores compact U/K/decay/lambda/length.
This preserves the algorithm's deferred GM write, but adds substantial
per-step UB reconstruction work. It is not yet a performance candidate.

The original explicit UB allocation remains168736B: tmp131072 plus all
queues37664. Named tmp slices use130432B, leaving640B; Broadcast uses the
original explicit4096B workspace. Compiler/stack/runtime availability is
still unverified for the NEW build. No extra named UB buffer is allocated. Expression-lowering temporaries,
compiled stack/LCM and synchronous hazards still require actual compiler/SDK
and NPU inspection; explicit accounting is not proof of hidden scratch. The actual native header copied under
/cache/austinov/src/vllm-ascend/csrc/build/binary/ascend910b/src/
recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h is used
as source guidance, not a claim that its build provenance has already been
bound to the loaded native SO.

Deferred-state reconstruction is still not bitwise native feedback.
This can remain a BF16 boundary failure, so saved-step same-source
pre-cast/updated-S diagnostics must precede the complete NEW matrix.
A proposed diagnostic must prove old production after-state/output exact
before interpreting a trace; trace values may not self-certify the oracle.

## Producer / consumer boundaries

run.py creates NEW kvbp.split-native-gate/v2 reports only. It injects ops
explicitly into its NEW oracle module; it never rewrites torch.ops or old
loaded modules. contract.validate_cases reuses the hash-bound old
validate_cases for all original numeric/raw/log gates and adds the explicit
v2 finite scope/per-buffer/domain fields. It returns
operation_authority_verified:false and serving_ready:false. It is not an
AWMCP/PID/container authority parser. Old consumer/source49/bridge60 are
frozen and reject this new report; MAIN must supply a separately reviewed
thin raw-terminal/PID/cleanup bridge before service admission. MiddleT2–15,
real cache lifecycle, matched E2E and task accuracy remain pending.

## Actual build/Meta identity fields (future producer, not a fabricated receipt)

MAIN's actual NEW build must provide status=compiled_no_device,
npu_executed=false, image_id, namespace, sources (the seven exact
repo-local operator source hashes), npu_arch=dav-2201, library_sha256,
commands with exit_code0, and exported_kernel {name,defined:true,type:T/W}.
Meta must provide status=pass, npu_executed=false, namespace,
library_sha256/build_receipt_sha256, actual operator schema string and
meta [{T:1}, {T:16}] in order with actual shape/dtype/Meta/nonalias and prepare-return checks.
meta_probe.py is a NEW no-device producer; it imports only Torch/TorchNPU and
the candidate SO, does not enable vLLM custom/native ops or query device/SoC.
Its inherited Meta registration is deliberately not an ND/layout/metadata
guard and does not establish PrivateUse1 or graph support. These fields are checked only against MAIN's
actual raw Ref bytes. No source-only test can issue these receipts.

NEW source manifest schema kvbp.split-native-sources/v2 contains files
(eight local gate files), exact old49 frozen_dependencies copied from the
original packet, original_packet Ref and NEW operator_sources seven hashes.
It never contains an invented NPU result. A fresh MAIN v2 launch identity
must bind this manifest, all source identities, three artifact Refs, original
resource/mapping/canary Ref bytes, protocol, nonprivileged8GiB, physical5 B1
or physical6 B16→logical0 and preflight<=600s. No card0–3 action is authorized.

## Commands (MAIN fills actual newly produced Refs; no execution in preparation)

```sh
python3 -B tools/split_gate_v2/run.py
python3 -B tools/split_gate_v2/run.py --source-audit-only \
  --source-manifest /ACTUAL/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_SHA

ASCEND_HOME_PATH=/usr/local/Ascend/cann-9.1.0 \
  cmake -S operator/native_order_v2 -B /NEW/NONEXISTENT/build
cmake --build /NEW/NONEXISTENT/build -j2

# No-device worker, real per-exec CANN bootstrap, no davinci compute mappings:
TORCH_DEVICE_BACKEND_AUTOLOAD=0 PYTHONDONTWRITEBYTECODE=1 \\
python3 -B tools/split_gate_v2/meta_probe.py --execute \\
  --source-manifest /ACTUAL/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_SHA \\
  --library /ACTUAL/libqwen36_gdn_kvbuffer_native_order_v2_ops.so --library-sha256 ACTUAL_SHA \\
  --build-receipt /ACTUAL/build-receipt.json --build-receipt-sha256 ACTUAL_SHA \\
  --output /NEW/EXISTING_PARENT/meta-report.json

# In a fresh MAIN-owned nonprivileged single-card worker, CANN bootstrap per exec:
python3 -B tools/split_gate_v2/run.py --execute --batch 1 --physical-device 5 \
  --source-manifest /ACTUAL/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_SHA \
  --identity /ACTUAL/MAIN_identity.json --output-dir /kvbuffer-results/NEW_gate \
  --library /ACTUAL/libqwen36_gdn_kvbuffer_native_order_v2_ops.so --library-sha256 ACTUAL_SHA \
  --build-receipt /ACTUAL/build-receipt.json --build-receipt-sha256 ACTUAL_SHA \
  --meta-receipt /ACTUAL/meta-report.json --meta-receipt-sha256 ACTUAL_SHA
```

Builds require the same immutable image/actual CANN setup as the original
queued ASC build; the CMake ASC target already sets --npu-arch=dav-2201.
The numerical command's actual image Python path/bootstrap/mounts/PID/proof
must be recorded by MAIN, not inferred from the source text. Do not run
unchanged old binary again as the B1 repair or reset KV's registered24h.

## Preserved actual preparation operations (not numerical authority)

MA0962: 30/30 memory-only SYNTHETIC stdlib tests, terminal exit0.
MA0965: normalized source outside ProcessTile unchanged, terminal exit0.
MA096a: 15 old mathematical/helper AST bodies unchanged; only explicit new
ops injection and native-defined padding finite domain added, terminal exit0.
MA096b: other six operator source files differ only by mechanical independent
names, terminal exit0. MA0979: after adding no-device Meta entry, 31/31 stdlib
tests/defaultOFF passed, terminal exit0. Their original operation records
remain separate evidence; none compiled, loaded Torch, or ran NPU.
The external reviewed patch is not a shared-repo application or a receipt
issuing tool. MAIN applies it only after reading the complete source/diff.
