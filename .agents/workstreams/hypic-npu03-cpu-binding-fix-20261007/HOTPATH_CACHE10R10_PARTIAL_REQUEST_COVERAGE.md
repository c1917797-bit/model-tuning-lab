# cache10r10 request coverage checkpoint (non-terminal)

At 2026-10-08 18:54:53 UTC, the sole active full HYPIC controller was
`exec-00000000000016af`. Its immutable raw attempt root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r10-full-hypic`.
The pinned clean plugin commit is `4429e35177979c874bf053ab29789e4773f39b22`;
the service uses physical NPU0–3, TP4, 0.85 GPU utilization and the frozen
127-sample / three-repeat / c8 / maximum-2048-token quality contract.

The host-PID / container-PID namespace mapping is validated by
`hypic-only/worker-namespace-map.json`. With that map, 56 of the first 57
completed scored requests had four-worker `worker_hot_request_verified`
events with positive skipped tokens and post-repair validation. This is a
partial observation, not a final acceptance count.

The first exception is sample index 6, repetition 3, API ID
`chatcmpl-8e084fc989213aec`, uniquely joined to scheduler ID
`chatcmpl-8e084fc989213aec-a883a075`. The evidence file has
`explicit_segment_boundary_active` and `independent_segment_observation`
for that request, but no `position_independent_batch` plan attributable
to it and no per-request worker proof. It returned HTTP 200, finish reason
`stop`, duration 106.274 seconds. Therefore this is an actual native
fallback for one scored request, not the earlier PID-namespace audit error.

The c8 controller runs each sample's three repetitions sequentially inside
its own thread while other sample threads run concurrently. The sample-6
scored request events are widely interleaved with other requests. The
materialization log showed an eviction before this exception and 10 cached
segments around the admission, but it does not record the victim identity
or a rejection reason for ordinary non-producer requests. Concurrent cache
turnover is a plausible hypothesis, not a proven root cause. Do not silently
relax the predeclared per-scored-request activation gate after seeing scores.
Preserve the full original ruler as runtime-enabled safety evidence and,
if needed, prospectively freeze a separate matched in-path ruler. The
running r10 operation and raw root must not be restarted, mixed, or erased.

The current controller may still complete full quality, but request-level
strict hot-path acceptance for r10 is already false unless the frozen gate
is changed prospectively for a new attempt. Baseline/performance work must
not treat r10 as an accepted treatment arm merely because aggregate hot
event counters exceed scored-row counts.

At 19:01 UTC, sample 18 provided a second independent counterexample:
its repetition 1 had four-worker proof, but repetitions 2 and 3 (API IDs
`chatcmpl-9042a6e198dfa80a` and `chatcmpl-b0b94139d9729751`)
had boundary observations and no worker proof. Its first scored response
lasted 243 seconds while c8 sample threads interleaved; later repetitions
lasted 139 and 194 seconds. Cache evictions occurred during this interval,
but victim hashes and ordinary plan rejection reasons were not emitted,
so the exact reason remains open. The branch-local read-only diagnostic
`diagnose_partial_hotpath_coverage.py` reports these per-request gaps
without labeling partial samples as accepted.

At 19:54 UTC, 105/127 samples were complete. The read-only partial
diagnostic joined 315 scored request IDs to the frozen event stream:
303 had four-worker post-repair proof, while twelve did not. The gaps are
request-level, not a verdict on whether the complete response text is
correct. The new diagnostic includes a `request_local_diagnostics` field
that can correlate future per-request Prefill filter misses and planner
unavailability. It reports no such event for r10's legacy pinned source,
and deliberately leaves the cause `unresolved_without_matched_state_audit`.
The separate source at `62b0d4a` is a candidate for a prospective test,
not a retrospective explanation of these twelve gaps.
