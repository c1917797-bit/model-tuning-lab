# T16: KKT task-count de-specialization admission

Status: planned; no live candidate or performance pass is claimed.
Owner: existing `work/qwen35-performance-delivery` workstream. Do not create
another long-lived worktree, overwrite its pre-existing dirty changes, or
revive a rejected runtime candidate.

## Goal chain

Long term: deliver a removable BF16 runtime Python plugin for the unchanged
official vLLM-Ascend 0.23.0 image. Each c1/c5/c8/c16 cell must show at least
40% lower TTFT P95 and 20% lower TPOT P95, using the median of three per-run
P95 values and the owning task's comparable MTP-off denominator. Require
zero errors, natural EOS, and all-357 paired semantic no-regression.
No quantization, retraining, MTP, speculative decoding, or source overlays.

Medium term: obtain a service candidate with credible unseen-shape TTFT
benefit and preserved warmed execution and quality, suitable for c1/c16
screening followed by the complete matrix. This prefill change does not
itself establish decode TPOT improvement.

Short term: decide whether removing only KKT `task_num` specialization is
admissible and can reduce newly compiled variants without violating the
BF16 numerical oracle or adding more than 5% warmed operator latency.
An implementation, report, or commit is not the acceptance objective.

## Evidence and source contract

T15 evidence root:
`/cache/austinov/qwen35-t15-generalization-audit-20260909-01`.
Report SHA256:
`80635bcb1b5e0899fbd683946e9e44ae0c42d3ba6a8fe2bcff4bcacd8322b81c`.
Finite warmup did not cover all new shapes. First-versus-warmed request
gaps motivate a TTFT experiment; they are not exclusive compiler-time
attribution or an estimated plugin speedup. T15 measured no TPOT.

The following identities were re-read from a network-none, no-device,
read-only-rootfs disposable official-image container:

- image ID: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`;
- `vllm_ascend/ops/triton/fla/chunk_scaled_dot_kkt.py` SHA256:
  `bcd1e9d8d4ec4f44ba24955ac9b85c6ce26e019802e12c49337f11a31bf64a98`;
- `vllm_ascend/device/device_op.py` SHA256:
  `de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47`;
- installed `triton/runtime/jit.py` SHA256:
  `8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad`.

The kernel uses `task_num` only as the end of `tl.range`; the arithmetic,
block extents, head grouping, core count, and launch options are unchanged.
The exact JIT binder handles constexpr values before do_not_specialize.
Adding the latter alone cannot remove a constexpr from the cache key.
DeviceOperator holds a separately imported kernel global, so definition-only
replacement is insufficient. Both aliases need identity-checked activation
and restoration; do not mutate the retained original JIT object.

## Bounded sequence and stop conditions

1. Record and push this planned checkpoint to the existing task branch before
   product edits or live candidate execution. A bounded fetch timed out in
   AWMCP operation `exec-0000000000001040` (25 seconds, exit 124). Do not
   disable TLS, change global network settings, or repeat unchanged retries.
2. While the remote checkpoint is unresolved, allow only external no-device
   source-admission probes: exact hashes, AST-body identity, actual pinned-JIT
   parameter/cache-key behavior, negative hash/drift tests, and alias/rollback
   contracts in a synthetic module fixture. Such probes do not install a
   candidate, compile for an NPU, or establish numerical/performance support.
3. After the checkpoint is verified, create an opt-in, source-hash-guarded
   isolated kernel clone: remove only the `task_num` annotation and add
   `task_num` to do_not_specialize. Preserve arithmetic and all other flags.
   Fail closed on unexpected original identities or a pre-existing patch.
4. Re-prove host/container/port/memory/physical-device ownership and hold the
   cooperative NPU0-3 lease for the complete lifetime. Use one physical NPU0
   for the independent TP4-local KKT operator gate; never map NPU4-7. Abort
   on a competing owner and stop only the exact labeled owned container.
5. One initial operator gate, maximum 900 seconds. Freeze exact model-local
   H/Hg/K, BF16, BT/BK, variable-length grouping, gates, and deterministic
   inputs before execution. Cover observed shapes plus declared length and
   multi-sequence boundary cases. Compare stock/candidate against a fixed
   FP32 mathematical reference: finite outputs, mixed atol=rtol=2^-6,
   matched fraction >=0.99, max absolute error <=1.0. Record byte equality
   separately. Do not relax the numerical oracle after observing failure.
6. Only after numerics pass: separate fresh cache namespaces for initial
   compile/variant coverage, then rotated-order warmed timings with five
   repeats per case. Require candidate/stock warmed latency <=1.05 in every
   admitted case, no extra same-family task-count variant after warmup, and
   record cold costs separately. Neither binder equality nor a cache-file
   count is a real compiler/runtime performance pass.
7. Only after the operator gate passes, prepare actual four-worker service
   activation/disable/rollback proof, the 32-row quality canary and c1/c16
   natural-EOS screens. No full-service launch is admitted by a CPU test.

## Decision routing

Pass: proceed to service validation with the same candidate bytes, identical
control/candidate warmup, independent fresh services/cache namespaces and
fresh prefix salts. Select final held-out data after freezing warmup. Report
startup including warmup, first unseen shape, steady execution and resources.
Keep the frozen historical baseline and comparable fresh control distinct.

Failure: retain exact bytes and the first failing phase, restore aliases and
close the unchanged route. Return to measured TTFT/TPOT candidate selection.

Inconclusive: preserve partial evidence; repair only a demonstrated source,
activation or measurement defect. Do not enlarge the budget or alter the
final 20/10, quality, precision or serving-capacity contract automatically.

## Validation and integration boundary

Run `./scripts/validate-mst.sh` and `git diff --check` before each coherent
checkpoint. Stage only files created for this iteration. Existing unrelated
dirty files are not part of this plan. Keep raw source snapshots, caches,
logs, model weights and data outside Git. No main merge, final plugin
promotion, or production-performance claim is authorized by this plan.
