# Main benchmark-evidence Skill: reject a nonmatching HYPIC baseline

Status: **partial long-term Skill evidence**, not a full benchmark or
HYPIC adoption decision. Reviewed 2026-10-08 against the live remote
`main=ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`;
`ascend-benchmark-evidence/SKILL.md` blob
`03ade79d697e974891410ea95f0ce54a8160b8c6`.

## Representative real task

Decide whether a completed historical physical-NPU0–3 LongBench-v2
no-cache quality arm can be reused as the denominator for the current
HYPIC candidate. The old arm has 127 unique samples ×3 scored rows,
clean continuous isolation and exact owned release. Its prompt,
generation, model, image and device identities otherwise match r9.
Re-running a baseline without cause wastes the shared lane; reusing a
materially different one fabricates a paired result. The correct gate
must inspect common serving flags as well as raw completeness.

## Observation and replay

`verify_hotpath_baseline_reuse.py` independently rehashes the old
contract, arm result, 127-sample manifest, guard, start and stop
receipts, and the live r9 contract. It compares frozen launch commands
and returns `old_control_complete=true` but
`old_control_reusable=false`: the old common
`--gpu-memory-utilization` is `0.9`, while both planned r9 arms use
`0.85`. The old contract omits this field, so matching only its
serialized fingerprint would miss the drift. HYPIC material-cache
1536/4 versus 3584/10 is treatment-specific and inactive in no-cache;
the common GPU budget is the decisive mismatch.

The current-main Skill's Comparability Gate correctly directs
re-baselining on material serving or cache-state drift. This real task
exercised that bounded negative decision. The branch has a more
explicit completed-baseline registry, raw-hash and reuse procedure,
but those additions are not in main. More importantly, r9's current
worker-hot telemetry cannot prove every scored request took the
optimized path: no new 0.85 control should start solely on a green
aggregate controller exit. The corrected baseline-reuse audit names
the strict prior candidate gate.

## Boundary and next gate

This proves one denominator-rejection behavior, not the Skill's
correctness-first, tail-percentile, cold/steady/boundary/lifecycle,
diagnostic-overhead or complete matched-performance behaviors. Keep
long-term acceptance `partial-evidence`; the campaign's bounded
benchmark row remains separate. Retain old complete control evidence
without relabeling it as r9. After a request-level-valid candidate,
only on actually idle physical NPU0–3 run its same-identity no-cache
control, then audit paired quality and performance. Revalidate this
case if main Skill bytes, source/image/model, common serving flags,
workload, scorer, raw hashes or physical-device identity change.
