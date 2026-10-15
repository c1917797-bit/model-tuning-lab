# Actual binding, observation order and single-factor evidence — 2026-10-15

Scope: Qwen3.6-27B / Qwen3_5 hybrid GDN, image660, vLLM-Ascend0.23/CANN9.1/910B4. These are scoped implementation and causal lessons, NOT a new technology acceptance. Fixed cutoff remains2026-10-16T07:18:17Z; only physical4–7.

## Source identity is not the call target

Actual installed patch_qwen3_5.py (8743B,21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3) copies AscendGatedDeltaNetAttention._forward_core onto QwenGatedDeltaNetAttention. Patching the original class later does not replace an already copied function. Actual qwen_gdn_linear_attn.py (68663B,885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0) resolves self from forward_context.no_compile_layers before invoking self._forward_core.

Original007 stopped on missing prefix context. It is an adaptation failure, not evidence against MXR math. The new source-bound prefix binding must prove actual target identity, actual algorithm-core closure/counter identity, native unwrapped core, real self.prefix mapping, and per-instance execution. Software fixtures alone do not prove the real model path.

Do not repair this by inventing a prefix or accepting missing counters. Production and diagnostic observers have different wrappers; preserve an explicit composed call-chain proof instead of asserting pointer equality to an intermediate function.

## Wrapper installation order is executable behavior

Actual010 installed memory_observer on Owned before replacing inherited S.Controller.observe with an ownership diagnostic. The memory wrapper retained the old observe function in its closure. Thus it bypassed the later diagnostic and no pre-guard operand receipts were written. The original safety guard still ran.

013 changes installation order, then validates the actual MRO/closure chain, guard global helper identity and actual started binding. Three actual-source-AST regressions reproduce old missing diagnostics, owned recording and unchanged foreign-cgroup rejection. Actual013 wrote OWNERSHIP_OBSERVER_CHAIN.json, loaded all four workers and captured48 real GDN frames per rank. The original isolated consumer then failed importing prefix_binding. Source-pinned CPU recovery016002 reused the preserved raw data without another model load; rank0 has45 output failures,47 state failures and0 inverse-solve failures across48 rows. Other ranks were not consumed after the original fail-fast. These are real candidate-versus-CPU64 negatives, not yet candidate-specific root-cause evidence.

Do not infer that the old extra physical5 PID was ours or foreign: retained SMI listed3229636, but historical cgroup/start/exe evidence was unavailable after departure. The original010 failure and cleanup-failure report remain FAILED; a later stopped/Pid0/noExec/OOMfalse audit proves release, not retroactive success.

## Single-factor negative evidence should change the hypothesis

DeltaLog A007 changes only ReduceRows to the native K128 AddFold/WholeReduceSum organization, preserving merge and other ABI/math. Its actual independent namespace library compiled and passed real same-image Meta registration. Actual physical5 smoke still failed B16 step3 output relative error0.003105590062111801 above the frozen0.00303 limit; state relative3.864163302108374e-8 passed7.92e-7. The independent saved-raw consumer confirmed failure. Full160 was not run after the first failure; all owned guests were released.

Conclusion: this reduction-only change did not resolve the observed native-peer output gate. It does not prove DeltaLog mathematics invalid, hardware impossibility, task accuracy loss, or an end-to-end regression. Do not repeat the identical failed candidate or relax the gate merely to pass.

A saved-frame CPU64 comparison can diagnose a BF16 rounding boundary, but one closer candidate output does not qualify the whole candidate. B009 is a new, explicitly labelled self-developed per-value-head key-projection organization based on the paper; it is not author repository code or the fully shared ReplayPrep implementation. The LF-only B010 successor built and registered its actual library, but the same step3 peer gate failed. Its owner also reported incomplete protected observation, so the later independent011 saved-raw CPU diagnosis is explicitly separate from the original failed owner; no model gate has passed.

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
- Actual013 source audit0553: exit0,46 exact files/AST,718 source refs,28 inverse deltas. Actual0555 is terminal exit1; its original failed result is retained. Recovery016002 and later diagnostics are new identities, never rewritten0555 success.

Remaining: actual short/long GDN qualification, relevant state/lifecycle/graph scope, unprofiled whole-model paired screening and three repeats, final official task smoke/full. Continuous30-minute utilization is UNMEASURED. No new whole-model benefit or task score is claimed here.

## Actual native baseline changes attribution, not historical verdicts

Actual067 physical6 smoke completed9 output/state raw rows with native dispatch,
mapped compensated solve and observed algorithm.blocks=20. Every candidate/native
output and state comparison passed the unchanged metrics; the single-token
three-step case is identical. Both arms nevertheless fail the old CPU64 absolute
gate on all9 rows. Native output Frobenius error spans0.0028578–0.0036218;
maximum candidate/native output Frobenius error is0.001813951. This proves a
native-baseline/test-contract issue exists in that synthetic domain, not that the
real model's failure is resolved. Owner0599 remains FAILED and the exact owned
CID was stopped/retained, Pid0/noExec/OOMfalse independently checked.

Actual DeltaLog B010 saved-raw diagnosis011 (Devices[], no NPU rerun) reproduces
the original failed peer metric0.003105590062111801. At dominant cell[9,9,15],
CPU64 reference=-0.005447388364538594, candidate=-0.005462646484375 and
native=-0.00543212890625; candidate is closer to that CPU64 value.
The boundary margin is only-6.692260938e-10, so reference rounding semantics
must be explicit. Another5-ULP near-zero difference has absolute error about
3.35e-10. Neither finding is a full lifecycle or task PASS.

A proposed independent forward-error contract was reviewed and rejected as a
sole gate after a real counterexample: truth1/output2 can pass an unbounded
gamma(n)*expanded_sumabs allowance. A simpler independent CPU64-final-BF16
reference with the original output/state limits is under preparation, not
activated qualification. It must specify direct versus double rounding and use
new unseen full lifecycle cases. Native-peer diagnostics and all old failures
remain. Same saved actual-model-frame replay019 is pending; standalone runtime
flags/adaptor identity must not be presumed equivalent to the worker.

New raw evidence, outside Git:
- Recovery016002 rank0 BRIDGE_RESULT.json:65353B,2c34b9b80b4653eb8344aefcf73f472fce8f6a30023b444dbc88f31698c96465.
- run-mxr-event-single6-owned-main-NEW48H_067_SMOKE_001/physical6/numeric/CONSUMED.json:26582B,d4bc2ddeb0eb0cad796fdb7c4db5dbd0c96e38fa8741bec0f355059b4715b858.
- run-dlB010-readout011-diagnostic-new48h-MAIN-20261015-001/native/result/DIAGNOSIS.json:24428B,4a4590c96a4f1ffe3b5c0eb816142c95142f9524f2166a98b84452e3b9097217.
All three are under /cache/cch/qwen36-paper-preparation-20261007/lowbit.
There is still no new whole-model throughput or final task-accuracy acceptance.
