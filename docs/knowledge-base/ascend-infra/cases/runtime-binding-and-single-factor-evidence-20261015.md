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

## 11:45 UTC update: real frames do not inherit synthetic PASS

This section supersedes the earlier pending019/simple-readout statements above.
Source020 completed all9 actual NPU raw captures (three selected real model-layer
frames, three repeats) with actual mapping and teardown. Its separate Devices[]
consumer failed before arithmetic because visibility was incorrectly set to0.
CPU-only recovery022 then ran the unchanged original consumer successfully:
owner2807B/3fa8d9a960403516595cb98e503d2fc809d11a62f1fd348b84f3b91fdde8fed8;
ATTRIBUTION31236B/67c8ffb46c9f448bfd1a679184370f9cd76ffd4eddf927f3065c37c79c0d55a6
under run-mxr-saved020-recovery022-new48h-MAIN-20261015-001.

The real result is NOT all-peer-PASS. Layer0 candidate/native state Frobenius
difference0.002706 fails the original0.002 bound. Layer1 native CPU64 state
error0.001974 passes while candidate0.002052 fails. Layer56 peer output error
0.004238 fails. Both solve input matrices match the saved matrix; candidate
output/state reproduce the original model capture bitwise on all three repeats.
Native repeated metrics agree; independent native cross-repeat bitwise equality
was not checked by022. Thus baseline error does not excuse extra candidate error.
The proposed native-preserving021/023 route is blocked by its own real peer
prerequisite, not promoted using synthetic067. Current evidence localizes the
substitution chain but does not distinguish inverse rounding from layout/tiling
or downstream WY sensitivity: native solve B/WY were not saved in020. A new025
diagnostic adds those actual intermediates and a CPU64-to-real-dtype operational
cast arm; it does not repeat an unchanged failure or grant model qualification.

DeltaLog013 used a newly frozen unseen seed and direct integer binary64-to-BF16
RNE, not an FP32 intermediate. Actual independent consumption completed smoke4,
fullB1x160 and fullB16 through step137, then rejected step137 output
0.0030864197530864196 above0.00303; worst-slot state8.6386e-8 passes7.92e-7.
Original013 owner remains FAILED:
1622B/7e01715e8f88b93ce095055c740d93ea137999641d00cc156b0a472df4f33812,
independent302-record result180066B/5a4819baa1c797104e66e8f618e11e70f672b0d1602009f06ddb666fe8b4f084.
No full324-row lifecycle qualification or model/performance admission follows.

Actual014 CPU-only reconstruction of138 steps confirms only6 of24576 output
cells differ from direct-RNE ideal output (five1-ULP, one2-ULP), while aggregate
state relative L2 is8.2144e-8. Dominant cell truth is only4.3983e-10 beyond the
candidate BF16 rounding-cell boundary. CPU alternative reductions suggest a
possible FP32 midpoint crossing, but actual CANN pre-cast output was NOT captured.
The014 diagnosis17868B/32491a61b2d9e8bb365b402640c4cf6b185fcf0d68ecd69dfa35402d1f5c6f56
is not a new PASS. Quantization-cell distance is a minimum required perturbation,
not an upper bound on actual pre-cast error. Capture the actual FP32 value before
deciding an explicitly new numerical contract; never silently widen the old
point-reference gate or infer task accuracy from a tensor metric.

## Integration and transport failures are separate from numeric failures

The actual frozen controller passes Path(e['service']) to environment(), not a
boolean or None sentinel. Fixing this with a guessed truthiness test repeats the
bug. Bind exact output leaf to e['physical'] in create and reuse that binding in
inspect. New025 calls the real original create_argv AND inspect_owned in cold
positive/negative tests; software tests alone still do not prove actual NPU math.

CPU-only tokenizer isolation must distinguish optional-package import from
device execution. Actual008 traceback shows AutoTokenizer importing generation,
torch._dynamo and optional Triton detection. A ValueError denial escapes the real
has_triton_package() except ImportError path. New009 prepares explicit optional
Triton denial via ModuleNotFoundError while retaining hard NPU-backend/device/FD/
runtime-map prohibitions and the unchanged tokenizer/template. This is neither a
fake backend module nor an NPU result; actual sameimage rendering remains pending.

For byte-exact delivery, encode EACH text chunk as a JSON string before transport.
Never trimEnd arbitrary chunk contents: a boundary can contain genuine spaces.
MAIN's014 transfer lost three manifest spaces; the source gate rejected it before
execution, and exact sealed bytes were restored before the successful CPU run.
Derive the remote directory from the sealed source Ref and manifest.root, not a
similar-looking local directory name. Validate bytes/hash at the destination
before dispatch. Retain transport failures without calling them algorithm failures.

There is still no new whole-model paired throughput or official task score.

## 13:12 UTC update: actual precast evidence and production-bridge code gaps

Actual015 debug DSO built successfully (2347032B,
0d3400929262a16f6485cebc3fcf7e683fbff335af193df4754875091b915e2c).
It exposes the real FP32 value immediately before the unchanged BF16 cast;
production B010 DSO remains2332672B/298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7.
The new016 contract was frozen before the new unseen324-record run: per-request
FP32 peak<=0.00303, relativeL2<=2^-13, original state bound7.92e-7,
direct integer BF16 RNE and production/debug output/full-state byte agreement.
It is empirical tested-domain evidence, not a universal CANN Exp theorem.
Original013 remains FAILED; neither task-level1% nor a larger fitted epsilon
was substituted for its gate.

016 run001 failed on a genuinely observed extra physical5 process; its
historical owner departed before identity collection. Do not invent ownership
from a later idle snapshot. New run002 produced324+original137 records but its
CPU consumer failed at its final Meta read because the required original CPU
result directory was absent from the consumer's RO mounts. Keep that owner
FAILED. Actual019 recovered the unchanged raw data in Devices[]:
owner1349B/d2bf4e12a7b8b57414ed7bf26d3adbe75349b109fbff00e6e78c6aad70e45301,
independent numerical650163B/035e81b8b950094811b043db9f0dbc83d82e48b818e7f0ea5cf88cd9edf4aae3,
strict audit288856B/f5a78e6e1beca9b56f0604ea2cd6cdb47e479804a201f0ba267cf17784245b9c.
All324 strict records and325 numerical records pass. Overall strict qualification
is still FALSE: original137 did not save redzones or four pointer receipts.
A source-pinned physical4 successor020 supplies only this missing same-input
frame; its actual CPU Meta passed and NPU operation068f is running as of this
update. No future PASS is inferred. Physical5 has an actual external
kernel_eval task, not merely a container declaration; it was not stopped.

Independent review reproduced a real017 plugin bug in _flush_slots:
dead U/K payload NaNs still enter einsum, so zero coefficients do not prevent
state poisoning. Local021 masks dead payloads before arithmetic and refuses
non-finite live materialization before any writeback. MAIN reran six controls
including an independent FP64 explicit head/log loop and the actual helper's
prefill-boundary fixture; PASS is CPU-only. Actual NPU native prefill/mixed and
request-slot lifecycle qualification is still required. The old two-token
service smoke cannot reach the eighth-step merge and cannot discharge this gate.

Source review also caught per-layer/per-token D2H metadata reads in017. Prepared
018-rev2 uses the actual scheduler CPU block-table and pinned-snapshot H2D helper,
plus request generation, epoch, group, layer and arena identities. Invalidate
dummy receipts before buffer writes; actual pointers identify views, not data
contents. Pure-prefill must not dereference absent decode metadata. Actual
48-layer provider/runtime wiring023 and source-aware CPU recovery admission022
remain in preparation, not model/performance qualification.

Byte-exact source delivery must use UTF8 LF BEFORE hashes are frozen:
apply_patch normalized CRLF and rejected initial019 template identity before
execution. The corrected LF binder/audit succeeded. Cross-check every command
Ref3 against the final artifact; a stale byte count can invalidate a correct
source before any experiment. Preserve such failures as transport/contract
failures rather than paper negatives.

Actual MXR025/026 further narrow the inverse-input hypothesis. Candidate/native
B error is0.000851845; candidate versus BF16 inverse of rounded A16 is0.000288867,
whereas native versus BF16 inverse of original A32 is1.44617e-6. The current
half-input kernel has no original-A32 residual correction API. This supports
investigating that lost input precision; it does not alone qualify a replacement.
Both native and candidate full-GDN CPU64 floors and downstream WY sensitivity
remain separate. No new whole-model throughput or official task score exists.

Audit-only source snapshots015/016 are retained in
projects/qwen36-paper-portfolio/tools/new48h_deltalog_source_snapshots_20261015:
34 files matched actual executed-source bytes. They are not a relocatable
production release, and their recorded external dependencies remain explicit.

## Actual guard recovery and composed component gate — 2026-10-15

DL020 physical4 first failed before arithmetic with missing
REGRESSION_INPUTS.json. Repair1 restored the original input Ref before Torch,
then failed at the DEVICE/host-process visibility seam: its preserved host
observations had no selected-card process proof while the guest had published
its canary. Neither failure supports a paper-level negative result.

Repair2 waits only for an absent host proof inside the unchanged guest ARM
and owner deadlines; nonempty identity mismatches, wrong mapping/argv/plan,
foreign overlap and missing positive proof still reject. MAIN ran all17 local
tests, source audit208 and actual same-image CPU preflight. Actual06c3 then
completed exit0 in86.456s on physical4. Independent single-original137 checks
passed for all14 memory/byte/pointer predicates; per-request FP32 peak was
1.8947486603663784e-7, relativeL2 1.4421968111827604e-7 and stateL2
8.638618832272069e-8. Both exact owned containers stopped-retained with errors[].
Owner RESULT1636B SHA f1a4828f8abd3d91a789c3c4f262143cf0cb90b71899c4ea8e333e74d69f797f.
This is one-frame supplemental evidence, not a new324-frame run or model gate.

Actual controlled Devices[] composite02206d1 completed exit0 in7.663s:
it reopens the original guarded/unguarded/raw tensors, checks complete325
numerical evidence and composes strict324 with the new same-input137 guards.
CERTIFICATE44169B SHA 2a5a51ecd51727d86a574a05380e869cdb9fc12cc2974df5b7724d3ca432afd5.
Original019 strict_pass=false and original016 failed owner remain unchanged.
The new certificate explicitly has model/performance/task/graph/PDC=false.

Readiness review caught two023 source defects before weights: the actual Qwen
dispatcher uses core_attn_out= while the helper accepted core, and the prepared
022 API pin was stale. MAIN reran the corrected real-dispatch11 software
controls; this is wiring coverage only. The024 prefill/decode/copy bridge also
needs every source read by022's startup receipt, including its external019
scope adapter, mounted read-only. MAIN identified that closure gap before the
first024 CPU/device launch; repair2 is a new prepared identity, not a PASS.

Accuracy010's real HumanEval/0 prompt ends in one newline. The original7764B
checkpoint Jinja template trims the user-content boundary, so the old literal
substring check rejected a legitimate rendered frame. The actual first-row
reproduction and01122 controls validate complete official framing with only
template-defined outer trim; deleting words or internal code indentation still
fails. Actual full15525 rendering and all task scores remain unmeasured.

MXR027-LF1 is a separate bounded diagnostic: retain originalA32 and refine
the unchanged037 FP32 inverse using R=I-(I+A32)X0, X1=X0+X0R before BF16.
All arms share the actual HF32-off policy. The real same-image CPU preflight
passed; actual physical4 replay06db is pending, not a numerical or speed PASS.
The two extra matrix multiplies may erase benefit; kernel FLOPs are not E2E.
