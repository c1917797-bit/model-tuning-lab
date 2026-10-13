# HYPIC historical profiler provenance review — 2026-10-13

This supplements, rather than rewrites, the r13 report and its frozen verdict.
It is a reporting/evidence review, not a new profiler experiment or causal claim.

## Seven retained phase attempts, not six successful runs

| Root / phase | Retained outcome | Capture | Exact release receipt |
|---|---|---|---|
| r1 / prefill | Foreign physical NPU0 process invalidated isolation | None | Present, all three flags true |
| r2 / prefill | Device capture valid | 281 raw files, 4 ranks | Present, all three flags true |
| r2 / decode | Foreign physical NPU0 process invalidated isolation | None | Present, all three flags true |
| r3 / decode | Admission rejected: physical NPU0–3 running process | None | Not available; result.release=null |
| r4 / decode | Foreign physical NPU0 process invalidated isolation | None | Present, all three flags true |
| r5 / decode | Foreign physical NPU0 process invalidated isolation | None | Present, all three flags true |
| r6 / decode | Device capture valid | 441 raw files, 4 ranks | Present, all three flags true |

The old r13 failure table grouped r1/r2/r4/r5 and omitted r3.
The r3 receipt is a preflight rejection, not an algorithm/profile measurement.
No release is invented for r3: absence of launch files is not proof of exact
runtime ownership or cleanup. Nothing in this review stops a current process.
No observation from these failures enters the accepted performance denominator.

The two successful captures retain their separate parser decisions:
Prefill exported46 columns and missed its original47-column gate.
Decode's first offline parse had internal exporter failures despite process
exit0; the management-node copy parsed successfully. Those existing conclusions
are unchanged. Parser-controller transcripts were not found at the inspected
top level of the retained offline parse copies; this is a bounded search,
not a claim that no possible external archive exists.

## Controller bytes versus plugin bytes

Every inspected contract records source_commit c12060c for the HYPIC plugin.
None contains controller_sha256, controller_git_blob or controller_commit.
That plugin revision must not be relabelled as the controller identity.

The tracked history of hypic_profiler_capture.py starts at820ee0c2
(committer timestamp2026-10-09T17:34:16Z), with root r4 and blob
9f181ebb075ec458cc08e8450a0979f5c64946eb.
r2 Prefill's terminal receipt is2026-10-09T16:56:20.248527Z.
Later retained versions are r5 at788e2091 and r6 at30eba46d.
Their exact blob/SHA identities are in the companion JSON and rechecked from Git.

These facts prove a retained r4/r5/r6 source history, not the exact r2 executed
bytes. Editing r4's path back to r2 would be a reconstruction, not recovered
authority. Source text and timestamps alone do not attest actual execution.
Mark r2 executed-controller byte identity unavailable in the retained receipts;
do not repeatedly search the same files or rerun a capture to backfill it.

## Replay and remaining boundary

From this workstream:
~~~bash
python3 -B verify_hypic_profiler_history.py
python3 -B -m unittest test_hypic_profiler_history.py
~~~

The JSON pins all available contract/result/capture/inventory/release and guard
receipts for these seven phases. Existing full raw-profile verifiers separately
own the281/441-file integrity checks and four-rank parsed-output checks.
No new profiling, parsing container, NPU work or root write is required.

Experience destination: verification case for paper-to-ascend-reporting.
Trigger: finalizing a report after retries and mutable controller edits.
Required change: enumerate every retained attempt and distinguish runtime
plugin identity, checked-in controller versions and executed-controller proof.
Verification: readonly receipt replay and negative controls reject omitted r3,
invented cleanup, controller-proof promotion and environmental/algorithm mixing.

This closes the retained device-attempt inventory review for r1–r6 and classifies
the Prefill source gap; it does not manufacture missing parser transcripts,
historical launch attestation, matched baseline profiles or a quality root cause.
Full reporting/Profiler Skill acceptance stays partial. Other historical
quality/performance command obligations remain separate from this supplement.
