# r19 quality Skill obligation audit — 2026-10-12

Exact-main Skill303658f0a652ed392c875e58941c6b1d246552f7 and reference
a3d5ca9a98883ce651fc275f404a524b126f07c7 at
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2 were read in full (exec008b).
This is an audit of the real r19 task, not a new NPU test or an adoption pass.

| Main protocol obligation | Current evidence | Status |
| --- | --- | --- |
|1 Environment fingerprint | Four contracts record image digest, model-index hash, source4429e35, cpuset112-191, physical0-3, capacity; source attestations bind actual command/mount/import | Partial: separate historical tokenizer revision and host-driver identity not established in these receipts |
|2 Declare denominator/switch/ruler before candidate | r19 LongBench and GSM8K preregistrations, four contracts, actual one-switch source attestations; final report and0066 replay | Proven for the declared paired scopes |
|3 Freeze inputs/evaluator/retry policy | Dataset/evaluator hashes and request hashes replayed; generation c32/max2048/natural EOS/seed0/temp0; GSM8K retry budget2 recorded | Partial: tokenizer identity gap; actual attempt accounting is separate from configured policy |
|4 Short deterministic equality canary | r19-short-canary.json in both LongBench arm control directories, exact equality/within-arm checks in0066 | Proven for retained short-canary scope, not all HYPIC mechanisms |
|5 Three baseline repeats and per-run accounting |127x3 LongBench and1319x3 GSM8K with scores/finish lengths/dispersion;8676 paired rows rescored0066 | Three repeats and scores proven; actual HTTP retry/timeout attempt totals not retained by the final-row evidence |
|6 Separate matching candidate lifecycle | Four service-start/stop and source receipts, persistent isolation; actual treatment proof134/381 LongBench, GSM8K off-path | Lifecycle proven; strict all-request mechanism coverage fails, must not infer it for247 unproved requests |
|7 Paired/category/length statistics | Frozen paired auditors plus final r19 report, correct/length/run breakdowns and wins/losses | Proven for the reported quality scopes |
|8 Classify and retain negative results | LongBench REJECT_OR_QUALIFY; GSM8K off-path PASS; all roots retained | Proven; repairing algorithm is not this obligation |

Source files freshly inspected in0092/0094:
- Four root contract.json / arm-result.json.
- Baseline fingerprint and source-attestation key sets for both datasets.
- Baseline LongBench samples/082.json row schema.
- GSM8K baseline unit receipts and service status.
These targeted inspections do not prove that every unrelated historical file
was searched. The identity gaps mean "not established by inspected evidence",
not an assertion that recovery is impossible.

The required quality-after-performance ordering was not followed for4429e35:
r19 prospectively chose quality-first, and current-source performance is still
missing. The final report explicitly records that deviation. Do not rewrite
the main workflow or historical chronology. This affects exact-workflow
acceptance, not completeness of the stored quality responses or their scoped
negative result.

## What should and should not happen next

Do not rerun four complete arms to turn rejection into success or recreate
missing historical metadata. A current tokenizer/driver snapshot cannot prove
the2026-10-10 identity. Check an already retained authoritative receipt if one
is available; otherwise report the field as unavailable and retain partial
exact-main acceptance. A future independent quality task should retain the
required identity and every request-attempt outcome from the start.

The original quality result remains usable at its stated evidential scope.
No claim of universal losslessness, full hot-path quality, full main Skill
conformance, algorithm repair or main integration is made. Source-matched
performance remains a separate explicit goal gap and pending run decision.

Recovery: inspect HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md and its pinned
case evidence; verify hashes before reuse. The completed0066 rescoring need
not be repeated unless evidence changes. No NPU or foreign-resource action
is needed for this obligation audit.
