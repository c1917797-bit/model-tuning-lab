# Qwen3.5 Experience Ingestion

## 0. Status

- Execution: completed for the Qwen3.x knowledge extension; no NPU mutation.
- Integration: needs-revalidation; no main merge and no performance promotion.
- Branch: work/qwen35-experience-ingestion-20260909.
- Base: origin/main at 31c43a4c249c9d4c597372f47d989a7c10b2c9c4.
- Resume checkpoint: 88dc4f3e8568892de2d80f7ec503b61a0b14620c;
  its existing six-file lesson update was validated and pushed in this turn.
- Expanded-scope checkpoint ebd6383dd19c20edfd9432f3f2573e42d5b3fd08 was also
  pushed. The final content checkpoint is bound in integration-evidence.json;
  verify actual HEAD/upstream before continuing.
- Validated content checkpoint:
  `eb3279b23ae6c12c3bd9d8a5607c79181c74f6cc` (pushed).
  Content tree: `9bdf81f8f86605b5ad21af1a836be7fbfadcfee9`.
  The later receipt-only checkpoint does not waive final-source validation
  before integration; no main or performance merge is claimed.

## 1. North Star

Turn verified Qwen3.x Ascend optimization experience into reusable maintainer
rules without copying experiment-specific claims into generic skills.

## 2. Current Focus

The existing Qwen3.5 takeover packet remains unchanged. The current extension
adds cross-model Qwen3.8 lessons: model identity must distinguish checkpoint
provenance, architecture metadata, live loaded bytes and service alias; heavy
hashing/builds must not overlap latency measurement; long matrices require
per-cell resumable hashes; configuration changes are named candidates rather
than silent baseline mutation.

## 3. Recent Progress

- Created an isolated workstream from synchronized origin/main.
- Froze the maintainer contracts and declared exclusive knowledge claims.
- Validated and rescued the previously unpushed 88dc4f3 checkpoint.
- Recovered T14 r2: TTFT P95 840.460 ms, TPOT P95 28.969 ms, 32 successes
  and zero errors. It is a second control repetition, not a candidate win.
- Verified 12 evidence files and the 12 historical raw baseline files; the
  historical summary is P50-only and must not be read as P95.
- Privately preserved the performance worktree's 11 dirty tracked files and
  six untracked files, without modifying or staging that worktree.
- Confirmed direct absolute-shell execution and login-shell Git transport.
  Previous spawn/transport root causes remain unknown.
- Verified the Qwen3.8 lesson set is absorbed into this earlier exclusive
  knowledge owner; a duplicate later workstream was explicitly superseded.
- The Qwen3.8 quality evaluation remained out of scope and was not mutated by
  this workstream. A read-only follow-up observed it fail during partial MMLU
  collection after 2589 well-formed rows; the lesson records this as an
  incomplete lifecycle/operational result, not a model-quality conclusion.
- Preserved the completed Qwen3.8-27B BF16 TP8 full357 concurrency matrix as
  `.agents/experiments/exp-20260910-qwen38-tp8-full357-baseline.yaml`.
  All 12 performance cells completed with zero request errors. The record stays
  `inconclusive` for clean-baseline promotion because c1-r2 has known
  coincident audit/build load, full-window isolation was not proven, and the
  semantic-quality follow-up did not complete.

## 4. Current Action

The Qwen3.8 model-identity, benchmark-interference, long-matrix,
configuration-denominator, and partial-quality-population rules are implemented
and validated at content checkpoint `701cd9da47b975254fbcba3aa24a3f48fe6ad2b0`.
Leave serialized integration to the target owner after exact-source revalidation.

## 5. Next Actions

1. Before integration, fetch latest main, reconcile target-owned HANDOFF and
   knowledge proposals, and rerun gates on the exact final remote source.
2. Do not overwrite the dirty performance worktree. Its older branch-local
   HANDOFF has stale resume instructions; use the packet's corrections and
   re-prove owner, code identity, containers, ports and NPU leases first.
3. Resume T15 only as a registered independent-shape/JIT experiment, with
   matched cache states and held-out tests. TPOT is a separate unresolved gate.

## 6. Validation Commands

```sh
./scripts/validate-mst.sh
python3 scripts/validate_qwen35_handoff.py
python3 tests/test_qwen35_handoff.py
python3 scripts/validate_qwen35_handoff.py --verify-artifacts
python3 tests/test_qwen38_experience_ingestion.py
git diff --check
```

Last executed results before the content checkpoint: 26 skills passed; 12
lessons and 12 evidence references passed; 15 synthetic regression checks
passed; artifact/private-backup hashes and Python compilation passed. These
are maintainer checks, not NPU benchmarks or a substitute for integration review.

## 7. Do Not Do

- Do not claim the Qwen3.5 40%/20% target is achieved.
- Do not embed dataset contents, raw profiles, model paths, credentials, or peer IDs.
- Do not turn failed IPC collective bytes into a recommended implementation.

## 8. Recovery / Resume Commands

Run git status --short --branch, git log -8 --decorate --oneline, and inspect
this handoff and integration-evidence.json. Use the packet's absolute-path
AWMCP recovery entry; do not use an old concrete peer ID. For Git network
commands the login-shell invocation was verified; never disable TLS.
Private recovery inventory:
/cache/austinov/handoffs/qwen35-mtp-off-20260909T214308Z/preservation.json.
The original performance worktree is intentionally still dirty. Do not apply
the saved patch back onto it without an ownership and clean-recovery-tree check.
