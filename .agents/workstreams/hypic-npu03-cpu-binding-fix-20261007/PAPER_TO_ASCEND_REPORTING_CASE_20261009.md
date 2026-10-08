# Paper-to-Ascend reporting: HYPIC evidence-bound progress case

Status: **progress / partial-evidence**, reviewed 2026-10-09 against exact
`origin/main=ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`.
This is a real reporting audit, not a new NPU measurement or a final piercing
report. The exact-main `paper-to-ascend-reporting` Skill and its
`references/report-template.md` were read before classification. No foreign
container was touched and no NPU was used for this case.

## Step 0: identity and evidence categories

- Subject: HYPIC v0.8.5-derived C1/C2 text path on Qwen3.6-named hybrid
  checkpoint, official vLLM-Ascend image, chicaihong01 physical NPU0–3 TP4.
  The exact source, model/index, image, CPU/NUMA, guard and workload contracts
  are pinned in `PIERCING_REPORT.md`, `FINAL_EVIDENCE_DECISION.md` and
  `HOTPATH_CACHE10R12_TERMINAL_AUDIT.md`; the three experimental identities
  below must not be pooled.
- **Current measured r12:** 19 selected samples, three scored explicit-boundary
  max-2048 responses each, 57/57 scored, 52/57 four-worker hot proofs, 279
  clean physical-lane guard samples, exact owned resource release. Raw
  `hypic-evidence.jsonl` SHA256
  `4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60`.
- **Historical same-lane reference:** six-unit c16/32768-input/1024-fixed-output
  paired performance audit SHA256
  `de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1`.
  Three runs per arm, all 40/40; weighted TPOT median 77.5641 to 60.2237
  ms/token, relative change `(60.2237-77.5641)/77.5641 = -22.3562%`
  using full-precision audit values. This is not r12 performance.
- **Historical natural-task reference:** clean2 LongBench-v2 and GSM8K,
  max-2048 natural EOS, twelve valid units and paired input identity, but zero
  distinct worker-hot PIDs. Scope-audit SHA256
  `61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0`;
  `formal_acceptance_claim=false`. These descriptive scores are not r12
  explicit-boundary quality and cannot prove hot-path accuracy.
- **Paper claim:** no paper numeric result is used as a current measurement in
  this case. **Interpretation:** r12 demonstrates a strict activation miss,
  not a paired quality or performance verdict.

## Step 1–3: groups, commands and reporting gates

The historical performance G1/G2 pair differed by HYPIC enable flag within
its frozen identity. Clean2 reused its own paired natural-task identity but
did not activate the worker hot path. r12 is a separate HYPIC-only diagnostic,
not a G2 row to pair with either prior G1. The r12 frozen launch selector,
container mapping, workload and stop contract are in
`HOTPATH_CACHE10R12_STRESS_PLAN.md`; its independent read-only replay command
is `HYPIC_STRESS_AUDIT_CAMPAIGN=cache10r12 python3 -B
audit_cache10r11_stress.py` from this workstream directory. It returns exit 2
at the predeclared strict activation gate, not a successful quality verdict.
The measured r12 terminal receipt and clean lane guard are indexed in
`HOTPATH_CACHE10R12_TERMINAL_AUDIT.md`. Do not rerun unchanged r12.

The complete same-identity c8/max-2048/127 baseline-plus-treatment launch,
three-round performance, full paired quality, scorer reconciliation and final
profile/recovery commands are **not yet available as executed evidence**.
They cannot be invented from the older c16 performance or clean2 quality
commands. Freeze the future deployed-effect versus all-hot decision rule
before the next pair, then recover exact successful commands from its scripts
and receipts. The main reporting Skill's final-report completion gate is
therefore not met.

## Measured result and decision ledger

| Gate | Measured evidence | Decision allowed now |
| --- | --- | --- |
| Historical same-lane performance | 6 valid units; -22.3562% weighted TPOT median | bounded c16/1024 C1/C2 benefit only |
| Clean2 natural quality | 12 valid units; 0 worker-hot PIDs | descriptive natural-task comparison, not hot-path pass |
| r12 explicit mechanism | 57 scored; 52 four-worker hot; 5 cold | strict all-hot gate fails for r12 |
| r12 physical isolation/release | 279 clean samples; owned resources released | r12 lane validity only |
| Current same-identity quality A/B | no no-cache arm | not measured |
| Current repeated performance/profile | no matched c8/2048/127 pair | not measured |
| Adoption/full-paper C3 | C3 not implemented in this path | not established |

The five r12 cold scored requests are 77:1, 77:3, 81:3, 85:2 and 88:2.
Forensic replay identifies one initial prefill chunk shorter than the ready
reusable prefix and four scored producer/rematerialization cases; it does not
prove each exact eviction transition. Do not promote the r11-to-r12 hot-count
change (53/57 to 52/57) or the diagnostic score change (27/57 to 22/57) to a
source-regression or aggregate quality claim: concurrent scheduling changed,
long outputs vary within arms, and no matched no-cache control exists.

## Reporting behavior and gaps

`PIERCING_REPORT.md` is a retained historical progress snapshot. Its first
paragraph points to `FINAL_EVIDENCE_DECISION.md`, but several later paragraphs
still say clean2 is running; those paragraphs are not current terminal state.
`FINAL_EVIDENCE_DECISION.md` correctly closes the clean2 identity as hot-path
quality not passed. `HOTPATH_CACHE10R12_TERMINAL_AUDIT.md` separately closes
r12 as a negative strict-activation stress run. This case keeps current,
historical, paper and interpretation evidence in distinct categories and
marks missing results as not measured, never zero. It does **not** certify a
single final colleague-style report with all commands, repetitions, profile,
quality and recovery evidence; no such final artifact is claimed.

Allowed claim: the reporting Skill correctly forces an inconclusive/progress
status and exposes non-poolable denominators and missing gates on this real
HYPIC task. Forbidden: complete Paper-to-Ascend report, lossless quality,
HYPIC source-regression, production readiness, whole-paper reproduction or
29-Skill validation. Next reporting gate: after the prospectively frozen,
actually-idle NPU0–3 full pair, produce one final report with exact measured
commands and independent hash/row/formula/guard/release audit, then recheck
the exact-main Skill/template and rerun this case verifier. No credential or
AWMCP verification token belongs in a report.
