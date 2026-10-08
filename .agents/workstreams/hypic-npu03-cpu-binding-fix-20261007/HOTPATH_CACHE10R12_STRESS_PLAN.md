# Prospective r12 NPU validation of eviction-directory rebuild

Frozen before launch. This is one material-source successor to r11, not a
repeat of the same bytes. Plugin source is clean commit
`c12060cd47e7575ead059983d7a8bb4704165c98`; the controller changes only
the campaign/root selector. Earlier r11 source `62b0d4a` remains immutable.

- Scientific question: on physical NPU0–3, does the new scheduler-directory
  rebuild restore the r11 79:2→79:3 worker-ready-after-eviction failure chain
  under the exact r11 19-prompt c8 stress schedule? Other cache-eviction cold
  fallbacks may remain; the fix is not assumed to solve all four misses.
- New external root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r12-stress-hypic`.
  Do not overwrite or resume r11 or r12 roots.
- Keep r11's frozen Qwen3.6-27B BF16 model/index, image, evaluator, dataset,
  context 41984, max output 2048, seed/temperature zero, natural EOS,
  explicit ends, two one-token observations, three scored answers, 19 sample
  indexes (75–91, 107, 111), c8, TP4, 0.85 utilization, 3584 MiB/10-segment
  material cache, native prefix cache off, CPU binding off, cpuset 112–191,
  and port 8223. Only the pinned plugin commit changes from r11.
- Device boundary: only actual-idle physical NPU0–3. Docker mapping alone is
  not occupancy. Check PIDs and port immediately before start, then keep the
  ten-second physical-process guard active. If another PID appears, invalidate
  this attempt, capture provenance, and release only the exact owned service.
  Never touch 4–7 or foreign containers.
- Offline gate: plugin focused red/green regression, focused tests, compile,
  source/topology audits; controller selection regression and repository MST
  validation. Refuse dirty/drifted plugin commit or existing root.
- Acceptance for this diagnostic is 19 unique samples, 57 unique scored
  responses, exact payload/score/hash and isolation audit, with per-request
  four-worker proof. Report any remaining cold fallback IDs and specifically
  compare the 79:2→79:3 failure phase. A 57/57 proof would admit a separately
  predeclared full paired experiment; this stress itself cannot establish
  quality or performance gain. A shortfall is bounded negative evidence, not
  an algorithm-wide conclusion. The eventual full-pair all-hot versus
  deployed-effect analysis rule is not decided by this diagnostic.
- Controller call uses `HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10r12`,
  `HYPIC_HOTPATH_QUALITY_ARM=hypic-only`,
  `HYPIC_HOTPATH_QUALITY_MODE=stress`,
  `HYPIC_QUALITY_PLUGIN_REPO=/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008`,
  and `HYPIC_QUALITY_PLUGIN_COMMIT=c12060cd47e7575ead059983d7a8bb4704165c98`.
  Execute `python3 -B hotpath_quality_full.py` from this workstream directory
  as an asynchronous AWMCP exec; retain its operation ID, poll the same handle,
  independently audit terminal raw artifacts, then record hashes and cleanup.
