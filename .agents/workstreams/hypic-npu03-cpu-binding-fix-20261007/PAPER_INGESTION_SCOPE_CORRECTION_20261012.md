# Paper ingestion: current evidence and scope correction

Recorded 2026-10-12; retrospective supplement to PAPER_INGESTION_CASE_20261009.md.

## What is already complete

The October 9 note and its observed fields are historical snapshots, not a
current launch queue. HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md and task.json
record the independent replay of 8,676 scored responses: both LongBench arms
(127 x 3 each) and both GSM8K arms (1,319 x 3 each). The r19 source is
4429e35177979c874bf053ab29789e4773f39b22. LongBench remains REJECT_OR_QUALIFY,
227/381 versus 219/381. GSM8K off-path safety is a distinct result.
No new NPU run is needed to establish that these paired tests completed.

The historical ingestion note binds derivative 3ad0967; current measured 4429e35
is its descendant with a pending-materialization guard and request proof changes.
Do not relabel these two sources as byte-identical or attach r13 speed to r19.

## Exact ingestion obligation versus downstream adoption

The exact-main paper-ingestion workflow identifies paper/version/source,
mechanism, prerequisites, portable/nonportable assumptions, single-variable
hypotheses and unknowns. A source-backed selection also pins author code,
reference tests and license. These are the ingestion acceptance obligations.

Full paired quality and repeated performance belong to downstream experimental
acceptance, not a reason to keep reopening ingestion. C3 absence must be recorded
as a limit of the C1/C2 single-service derivative. Building C3 or acquiring a
multi-replica lane is not required to truthfully ingest this bounded hypothesis.
No retrospective note can prove a pre-implementation gate happened historically.

This corrects the stale case next_gate; it does not change any frozen experiment
gate, quality verdict, original task scope, exact-main Skill bytes or acceptance
count. The case stays partial-evidence pending its source and obligation review.

## Remaining source work

The author reference snapshot is outside Git at:
 /cache/cch/hypic-npu03-cpu-binding-fix-20261007/author-hypic-98147c0-20261012.git

Fixed author revision: 98147c01909004e66d98bcb18b886927d41b0ee5.
Read-only source retrieval exec0183 ended at its 180-second timeout with no
comparison output. No repeated network fetch was attempted. Local-object-only
audit exec0188 then completed in 104ms: three cached reference files match the
historical derivative manifest exactly (picache.py, scatter_xfer.py, segmenter.py);
seven blobs are absent locally and remain unverified, not mismatches.
PAPER_AUTHOR_REFERENCE_PIN_20261012.json records Git object IDs and SHA256s.
The local replay reads only previously enumerated objects and cannot lazy-fetch.

This pins a current author reference, not the unique historical origin revision,
whole-repository equivalence, author GPU test execution or full-paper Ascend
reproduction. License review of the author root does not by itself establish
the derivative's redistribution status. Remaining source review is offline
ingestion work, not authorization for further device experiments.

## Next action and boundaries

Finish fixed-source comparison/reference-license mapping when available, then
review ingestion obligations against the actual note. Preserve current r19
negative results and the original incomplete pre-implementation sequence.
Do not repeat r16/r19/r22 quality, add observers, or launch C3 for this case.
Current-source performance remains a separate pending prospective choice.
29 cases exist: 8 bounded verified, 21 partial. No promotion in this supplement.
Deadline remains 2026-10-13T08:47:14Z. Remote authentication is unchanged;
this is branch-local evidence, not main/remote integration.
