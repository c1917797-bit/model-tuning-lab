# r13 sixth performance phase: complete attempt inventory

This is a retrospective inventory of the original attempt and retry1–21 only.
It does not rerun any service, overwrite raw evidence, or change the six-phase
performance/quality decisions. Source: each original root under
/cache/cch/hypic-npu03-cpu-binding-fix-20261007.
The accompanying HYPIC_R13_REPEAT3_ATTEMPTS_20261012.json records exact paths,
SHA256 (or explicit absence), raw errors, response counts and release fields.

## What the raw files establish

- 22 roots:19 explicitly invalid arm-result receipts,2 missing arm-result
  receipts (retry5/6),1 valid receipt (retry21).
- 20 attempts contain foreign-process observations; retry6 has no saved guard
  receipt, while retry21 has a clean guard.
- Only retry4 and retry21 have performance.json. retry4 retained40 rows:
  16 marked ok,24 not ok; only15 ok rows have1024 output tokens. All40 rows
  are excluded because isolation failed. "16/40" is not16 valid fixed-output
  benchmark requests.
- retry21 has40/40 ok,1024-token rows and is the sole admitted final phase.
  The existing independent six-phase audit remains the authority for its
  request/rank/source identity and numerical effect.
- Absence of performance.json on other attempts means no retained benchmark
  rows in this inventory, not independently proven zero network activity.

## Release-proof boundary

18 pre-health failures retain container_removed=true but
worker_release_proven=false; these receipts do not establish a full
worker/port release proof. retry5/6 have no release receipt in these roots.
retry4 and retry21 have complete service-stop fields for container removal,
owned-NPU release and port release. Do not extend their proof to other roots.
This is historical evidence absence, not evidence of current leaked resources.
No current container action is justified by this inventory.

The old terminal report's selected incidents and handoff summaries are not a
substitute for these per-attempt fields. Any stronger historical cleanup claim
needs its independent contemporaneous receipt; do not manufacture it now.
Likewise, retry6's20-second controller-timeout account is retained in the older
report, but the raw root itself has only contract.json, not a terminal receipt.

## Consequence for efficient reproduction

The attempts are predominantly isolation failures, not21 independent HYPIC
algorithm failures. Repeating costly startups between intermittent foreign
bursts produced no valid extra samples. Future runs should use a confirmed
usable window and continuous isolation, while preserving the user's rule that
passive device mapping alone does not block work. Never stop foreign jobs.

This closes the inventory gap for this phase, not historical Prefill-controller
byte provenance or all profiler failures. No reporting Skill promotion follows.
Review missing historical receipts only if they change the final claim; do not
rerun successful measurements to reconstruct old metadata.

## Read-only replay

From this workstream directory:
python3 -B verify_r13_repeat3_attempt_inventory.py

The replay checks all22 root identities, present/missing receipt hashes, raw
result decisions, response counts, foreign observations and release facts.
No new NPU work; no source/threshold/raw edits; no main/remote synchronization.
