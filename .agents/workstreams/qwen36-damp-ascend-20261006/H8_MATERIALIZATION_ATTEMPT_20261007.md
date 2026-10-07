# KVBuffer H8 targeted materialization attempt — 2026-10-07

## Alignment and scope
This targets the actual native incoming-state intervention: the previous
sixteen-step reconstruction reached a BF16 midpoint while native state lay just
above it. It is not a complete cause proof. Change only materialization16->8;
retain log storage16, the four-level TreeFold, UB/DMA/native current-step order.
Independent default-OFF namespace qwen36_kvbuffer_short_horizon_v3. No native
runtime/source/image modification. No tensor gate relaxation, output bias,
fine-tuning, speculative decoding or unrelated operator optimization.

Original KVBuffer cutoff2026-10-08 08:29:54Z and portfolio
cutoff2026-10-09 11:17:31Z unchanged. Final objective remains non-HYPIC Qwen3.6
plugin, real complete NPU correctness, paired fixed1024 E2E >=10%, TTFT/TPOT,
then official max2048 thinking-OFF task gates. None is newly achieved here.

## Actual source/software/build evidence
- Seven actual operator source hashes plus PLAN were independently read:
  MA0cbd/MA0cc7. Name-normalized six sources unchanged; kernel.h only interval8,
  length>=8 refusal and length+1==8 merge. Storage16 and TreeFold parity unchanged.
- MAIN actual source closure/AST MA0ce4 exit0; V3 manifest7292ebd16430ac945fa8d9ebff842b11875643e5e09ec5cd1083e9163fca3c37 binds79sources.
- Actual nine focused software checks MA0ce6 exit0; original0.00303 output,
  complete/per-head state2e-6 and160steps/reset64,112 unchanged. This is software,
  not a numerical PASS.
- Actual MST MA0cea exit0 (20skills), tracked diffcheck MA0ce8 exit0.
- Actual no-device build+dlopen/schema/Meta MA0cf0 exit0. Independent
  readback MA0d04 exit0. Image660ce23...; no compute devices/no backend autoload.
  Library3f7cc32eda77c68ce306bf1bb952886a332683e74a860430d01a1ead68f98e77;
  build926cf3472116c4ddbf63c0d607b65a588bf1dd73121e3dbcd96107403a5c9239;
  Meta9c07aafc47a2ef865f21238cf9a0a1c25edb4b00bebfe548bfa1159cc9c94d03.
  Defined ASC host export typeT. Actual MetaT1/16 output[T,12,128],BF16,
  nonalias,prepareNone,actual mapped candidate hash. No NPU claim.
- Exact own CID3c9358befa7d9c2ede2fbe109172d9d612b13070a425f8ae0377ed788e0e76f9
  stopped/retained/Pid0/noExec/noOOM. Container sleep exit137 is NOT the
  compiler/Meta child exit: actual children0 retained separately. No rm.

External build root:
/cache/cch/qwen36-kvbuffer-parallel-20261006/build-short-horizon-v3-20261007-1500

## Discovered observer seam, not a numerical failure
V3 contract inherited the frozen16-step validate_cases flush-count replay.
Source review found lengths==15, so it cannot correctly consume an H8 trajectory.
V3 files/manifest/results remain unchanged. New H8 observer v4 copies the full
replay with only flush boundary7, preserving output/full-state/per-head gates,
all logs/slots/raw checkpoints/modes/guard/input/pointer/reset/maximum checks.
Actual six software tests MA0d05 exit0 reject H16 replay and bad thresholds/
finite/padding; synthetic software rows are never a device receipt.
No NPU was spent knowingly executing this observer mismatch.
Actual V3 seven compiler inputs/SO/schema/Meta are reused as those identities
are unchanged, never as old numerical evidence. New controller/source manifest
closure pending at this checkpoint.

## Resource and queue truth
MA0cca: ordinary MemAvailable58.104GiB; fixed1GiB HugeTLB1916 total1892free,
actual observed OVS24GiB. Protected0–3 HYPIC RSS16.672GiB. No other process
or hugepage pool was changed. Full-model72.25GiB is conservative cap+reserve,
not measured minimum. Numerical8GiB+reserve remains separately legal.
MA0ccb briefly observed actual NPU4 PID3532158; MA0cce showed it exited.
Do not copy that observation as a later device lease.

DeltaLog frozenv5 passed31software tests but MAIN/source cross-review found:
declared-only devices wrongly blocked; resumed receipt mount used new instead
of original path; help timeout could block numerics; cleanup could mask primary;
effectiveCPU budget lacked cgroup closure. V6 owner is repairing these proved
seams with actual no-device load/Meta prerequisites, not lowering numerical gates.
W4A16 independent packet has31actual software tests, but no native/full-model
PASS. Preparation names and CLI/matrix counts do not establish readiness.

## Next evidence
Freeze/review new H8 controller and source manifest; fresh resources/physical6
mapping/protected0–3 proof; run B16 eager1+graph3/160changing feedback with
first-failure raw retention and own-only stop/retain. Then full B1..16/model
lifecycle and paired fixed1024 only if relevant numerical gates pass.
Final task runner/data identities still pending. No new throughput or GSM8K/
LongBench-v2 result. Normal push still has the previously recorded Git HTTPS
credential-helper blocker; no repeated unchanged push, force or main change.

## Actual H8 B16 numerical completion — 2026-10-07 16:37Z

The earlier sections are stage checkpoints, not the current queue state.
Observer/controller V4 is now frozen: manifest
1315160b24c51c89e02a75b81ca39562ed958590a2b15d12b9beb97639d67952,
84 transitive sources; host SHA
4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20.
Actual 37 software tests/default-OFF/source-audit MA0d4e passed before admission.

Original first attempt MA0d56 remains failed/parent-operation authority
unavailable, never promoted. Its canary watch observed a real additional
physical1 Python PID3970665/start31357057 in foreign cannbench_ds CIDefc5e45e...;
the original four protected workers did not change. The watcher compared true
PID/start/cgroup/argv identities, not HBM/RSS noise. Agent actual raw audits
MA0db1/0db4 and MAIN independent read support that attribution. Fresh MA0db5
proved this transient PID had exited and4–7 were idle; only that external-state
change authorized a new non-overwriting attempt. No outside job was stopped.

New attempt root:
/cache/cch/qwen36-kvbuffer-parallel-20261006/h8-b16-20261007-after-external-exit-v2

MAIN original MA0db7 actually exited0,594.022s; complete command/args, target
peer and peer_direct route were independently joined to the stdout-bound Ref.
It is an actual correctness-run duration, NOT a performance microbenchmark.
B16 eager1+graph3 completed640 changing feedback steps, all original guards,
inputs/pointers/untouched slots/log invariants and reset/flush replay passed.
Maximum output error0.0029411764705882353<=0.00303;
complete state L2 max1.2599801348389918e-7 and per-head max
2.5892022770307797e-7<=2e-6. No threshold or rounding bias changed.

- report SHA4abc87d561d2aabf41c5acec6af4948c6b860b64da6fcfd838dab379378d374d
- RESULT SHAcdf279bbe540261b132a8289c81ab0810e85d804cc9a99cf7188c0bff9dd9808
- matrix-child SHA44f4ebc3a23270d083b90929a0b0298ac818c5090070e3da7d3acbcaa8a15f70
- cleanup SHAcc4ad1840163ff691b73917186e4a7134f38ee1bf7a5cb1ee3b1e809f0624221

Independent MAIN consumer MA0dd3 exit0 consumed current84 source hashes,
actual library/build/Meta/native mappings, all640 rows and197 actual matrix
PID/start/cgroup/argv observation Refs. Algorithm PID138761/start31575074 on
physical6 is distinct from canary. Exact owned CID
fcc6335f2aa216f6e07663798f1c33b29514505e62fcba0f592193f806d15107
is stopped/retained/Pid0/noExec/noOOM;0–3 protected identities unchanged;
4–7 fresh idle and ordinary MemAvailable90.137GiB at the consumer.
First independent read MA0dd2 failed only because MAIN called an absent helper
symbol load_host instead of actual frozen; retain that exit1. Corrected read
MA0dd3 did not rerun NPU or change source/results. Child RESULT's original
MAIN authority flag remains false by design; MAIN joins the actual operation
separately instead of rewriting the raw result.

Decision: verified single-batch H8 kernel adaptation, NOT full-batch/model-ready,
E2E or task acceptance. H16 first numerical failure is retained unchanged.
H8 B1..16, cache/horizon identity,48-layer×4-rank mixed lifecycle, full service,
paired fixed1024 and final max2048 task evidence still pending. Recurrent
preparer now prioritizes those H8 closures while MAIN admits serial successors.

Memory admission changed for a separate authorized reason: MA0d8d released
exactly32GiB of NUMA0 free1GiB pages, with independent full-node/OVS health
checks. Ordinary RAM58.045->90.045GiB; NUMA3 pool/OVS24GiB unchanged. The
32GiB authority is spent. See HUGEPAGE_RELEASE_20261007.md; this is not speedup.
