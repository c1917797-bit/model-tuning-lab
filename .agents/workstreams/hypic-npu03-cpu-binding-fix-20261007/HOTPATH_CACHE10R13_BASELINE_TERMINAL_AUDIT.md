# r13 full no-cache arm: independent terminal audit

- Date: 2026-10-09 UTC. Frozen campaign: cache10r13, physical NPU0–3 only.
- Controller `exec-0000000000001a76` terminated successfully with exit 0.
- Immutable raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r13-full-baseline`.
- Contract SHA256 `79ef620ab90a1f5925e6155b03b30de3c396ba1cb2e379108ec593f3a4661d23`; arm-result SHA256 `d348af20d07dab5d34dfa3b2fbf68d310f716f1a9e6aecf91e1d467ad63a5449`.
- Independent `hotpath_quality_audit.frozen_cases`, `frozen_pair_seam` and `audit_arm(..., require_source_attestation=True)` passed: 127 exact LongBench-v2 samples, 381 scored responses (3 each), 230 correct, 48 responses stopped at the 2048-token length limit. These are baseline counts, not a paired quality verdict.
- Source attestation SHA256 `7cc0946d1dff61f7ea04ef592277557ff2d3288b512b6501e0af51f7fa5d1f88`: frozen plugin commit `c12060cd47e7575ead059983d7a8bb4704165c98`, exact image and Python source bytes validated against service binds and import path.
- Lane guard recorded 998 clean probes, no foreign NPU0–3 process or probe error. Exact owned container `7bafc149c7982753958371304735222c2f663db6cda6df4550bbeb726e807490` was removed, its NPU processes released and port 8223 freed. No HYPIC worker-hot events occurred in no-cache arm.
- Before candidate launch, `npu-smi info` showed no running processes on physical NPU0–3, `ss` showed port 8223 unbound, candidate root absent, and branch worktree clean at `18ae2718734f65885059cccdedd229f4459f2a41`. Mapping-only containers were not modified.
- HYPIC-only full candidate was then launched as controller `exec-0000000000001bb1`. Until it terminates and both-arm audit passes, the r13 paper-level HYPIC conclusion, strict hot-path conclusion and performance conclusion remain open.
