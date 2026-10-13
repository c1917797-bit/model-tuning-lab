# Existing HYPIC host-event / exported-kernel-gap association

2026-10-13; offline only; operation exec-0000000000000014 on ma.
Source c12060cd47e7575ead059983d7a8bb4704165c98, not current4429e35.
The six same-source performance phases and r19 quality remain unchanged.

## Method and identity

correlate_hypic_host_gaps.py reads existing four-rank Prefill r2 and Decode
r6-manager copies. Kernel CSV hashes must match the immutable prior timeline
audit90385d77afe877b66758529d9272d0674b7d89d3798349577fd19b96b372bddd;
all eight recomputed largest-gap durations matched. Trace hashes, exact
nanosecond coordinates and top-event indexes are in
HYPIC_HOST_GAP_ASSOCIATION_20261013.json.

Only X events in metadata-labeled Python/CANN process lanes count as host
events. Synthetic Overlap Analysis/Free and Ascend Hardware lanes are excluded.
Clip to the gap and merge overlaps instead of summing nested API durations.
Decimal timestamps prevent epoch rounding. Six tests passed: synthetic-lane
exclusion, nested union, edge clipping, touching intervals, missing host lanes
and negative durations. These tests are not independent device validation.

## Observations

Milliseconds; no exported kernel is not proof of actual device idleness.

| Phase/rank | Largest gap | Host-event union within gap | No exported host event |
| --- | ---: | ---: | ---: |
| prefill/0 | 3666.746480 | 0.262300 | 3666.484180 |
| prefill/1 | 3861.327020 | 0.217940 | 3861.109080 |
| prefill/2 | 3836.966940 | 0.188660 | 3836.778280 |
| prefill/3 | 3810.703900 | 0.239725 | 3810.464175 |
| decode/0 | 3.515520 | 3.151025 | 0.364495 |
| decode/1 | 3.443460 | 3.141265 | 0.302195 |
| decode/2 | 3.955400 | 3.639615 | 0.315785 |
| decode/3 | 3.577560 | 3.380540 | 0.197020 |

Decode's largest overlapping host event is AscendCL@aclmdlRIExecuteAsync on
all four ranks, overlapping respectively2.954700/2.987540/3.512670/3.309080ms.
This is a temporal association in exported profiler coordinates, not proof
that this API causes the gap or an opportunity fully removable by a patch.
The Prefill gaps have only0.189–0.262ms of exported host coverage. The trace
therefore does not explain the remaining roughly3.7–3.9 seconds; absence of
events is not proof that Python, scheduler or CPU was idle.

No causal dependency join, external clock calibration, individual Decode-step
identity, CPU/NUMA placement or paired baseline/treatment profile is established.
Do not diagnose HCCL or propose a low-level change from these observations.
The original46-vs47-column contract miss remains; no threshold is rewritten.

## Decision and continuation

The existing-trace host-association check is now complete; do not repeat it
for a higher Skill count. The exact-main profiler case stays partial-evidence.
New capture or a causal treatment needs a separately justified authorized task;
no NPU, container, service, clock or runtime setting was changed.
No quality pass, deployment acceptance or main/remote integration is claimed.

Replay from the workstream: python3 -B correlate_hypic_host_gaps.py
Tests: python3 -B -m unittest discover -s . -p test_hypic_host_gaps.py
