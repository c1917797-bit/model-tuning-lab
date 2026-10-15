# Actual binding, observation order and single-factor evidence — 2026-10-15

Scope: Qwen3.6-27B / Qwen3_5 hybrid GDN, image660, vLLM-Ascend0.23/CANN9.1/910B4. These are scoped implementation and causal lessons, NOT a new technology acceptance. Fixed cutoff remains2026-10-16T07:18:17Z; only physical4–7.

## Source identity is not the call target

Actual installed patch_qwen3_5.py (8743B,21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3) copies AscendGatedDeltaNetAttention._forward_core onto QwenGatedDeltaNetAttention. Patching the original class later does not replace an already copied function. Actual qwen_gdn_linear_attn.py (68663B,885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0) resolves self from forward_context.no_compile_layers before invoking self._forward_core.

Original007 stopped on missing prefix context. It is an adaptation failure, not evidence against MXR math. The new source-bound prefix binding must prove actual target identity, actual algorithm-core closure/counter identity, native unwrapped core, real self.prefix mapping, and per-instance execution. Software fixtures alone do not prove the real model path.

Do not repair this by inventing a prefix or accepting missing counters. Production and diagnostic observers have different wrappers; preserve an explicit composed call-chain proof instead of asserting pointer equality to an intermediate function.

## Wrapper installation order is executable behavior

Actual010 installed memory_observer on Owned before replacing inherited S.Controller.observe with an ownership diagnostic. The memory wrapper retained the old observe function in its closure. Thus it bypassed the later diagnostic and no pre-guard operand receipts were written. The original safety guard still ran.

013 changes installation order, then validates the actual MRO/closure chain, guard global helper identity and actual started binding. Three actual-source-AST regressions reproduce old missing diagnostics, owned recording and unchanged foreign-cgroup rejection. A real013 startup has now written OWNERSHIP_OBSERVER_CHAIN.json. This is startup evidence only; the numerical result is pending.

Do not infer that the old extra physical5 PID was ours or foreign: retained SMI listed3229636, but historical cgroup/start/exe evidence was unavailable after departure. The original010 failure and cleanup-failure report remain FAILED; a later stopped/Pid0/noExec/OOMfalse audit proves release, not retroactive success.

## Single-factor negative evidence should change the hypothesis

DeltaLog A007 changes only ReduceRows to the native K128 AddFold/WholeReduceSum organization, preserving merge and other ABI/math. Its actual independent namespace library compiled and passed real same-image Meta registration. Actual physical5 smoke still failed B16 step3 output relative error0.003105590062111801 above the frozen0.00303 limit; state relative3.864163302108374e-8 passed7.92e-7. The independent saved-raw consumer confirmed failure. Full160 was not run after the first failure; all owned guests were released.

Conclusion: this reduction-only change did not resolve the observed native-peer output gate. It does not prove DeltaLog mathematics invalid, hardware impossibility, task accuracy loss, or an end-to-end regression. Do not repeat the identical failed candidate or relax the gate merely to pass.

A saved-frame CPU64 comparison can diagnose a BF16 rounding boundary, but one closer candidate output does not qualify the whole candidate. B009 is a new, explicitly labelled self-developed per-value-head key-projection organization based on the paper; it is not author repository code or the fully shared ReplayPrep implementation. Its build/Meta/NPU/model gates remain pending.

## A DEVICE receipt can arrive after the SMI snapshot

Actual064 owner353777B/495a818e3313ff2a07613c95e7ea20d9c5f1b883c88c254799a22ad7e3def29e failed before numeric/child/actual_owner publication. Last SMI snapshot09:09:27.781017Z had no physical6 compute; DEVICE appeared09:09:28.128Z. The controller then rejected that stale empty proof set rather than taking the next observation inside its original handshake time.

This supports a minimal fresh-observation handshake repair, not accepting a self-reported guest as host ownership. Empty evidence is not positive identity. Any nonempty mismatch, genuine foreign holder, unknown live identity, child exit or original timeout must still fail. The original run has no host-PID proof and no matrix result. Cleanup retained the exact owned CID and reported no errors. A corrected implementation needs its own source, cold tests and new run; never rewrite064 as PASS.

## Shape qualification must reach real task inputs

Old production005 dispatch domain covered32768/40960, while frozen official task prompts have maxima212/407/3139. Good task scores from entirely native fallback would not validate the candidate mechanism. Task-only counter deltas must exclude long warmup and require actual candidate execution.

006 is explicitly tested-geometry-only. All-tail software/property tests and a planned396-row matrix do not prove unmeasured lengths or arbitrary matrix content. Triton num_aicore is not source-equivalent to torch cube_core_num; absent actual algorithm.blocks must not be invented to claim kernel dispatch branch coverage. Preserve exact original prompts, independent references and the actual task-smoke gate. Generalization needs a bounded structural argument plus actual numerical anchors, not a whitelist expanded because tests are inconvenient.

## Actual evidence locations

- MXR010: /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-mxr-qwen-core-binding-main-NEW48H_010_001/RESULT.json (3881B,2c000ca7499a1139d912fb25eab62024ff5e4cc1ba93e87c8655846c860ac7f8).
- DeltaLog A007: /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dlnative-reduce007-numeric-new48h-MAIN-20261015-001/RESULT.json (1614B,caed6149e7a8fcec31d2e2eac15d194001051c0959de9d0165ca04bef8ebaa41).
- GE064: /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-mxr-event-single6-owned-main-NEW48H_064_NPU_001/RESULT.json (353777B,495a818e3313ff2a07613c95e7ea20d9c5f1b883c88c254799a22ad7e3def29e).
- Actual013 source audit0553: exit0,46 exact files/AST,718 source refs,28 inverse deltas. Actual numerical operation0555 was running when this case was written; query it, do not restart from this prose.

Remaining: actual short/long GDN qualification, relevant state/lifecycle/graph scope, unprofiled whole-model paired screening and three repeats, final official task smoke/full. Continuous30-minute utilization is UNMEASURED. No new whole-model benefit or task score is claimed here.
