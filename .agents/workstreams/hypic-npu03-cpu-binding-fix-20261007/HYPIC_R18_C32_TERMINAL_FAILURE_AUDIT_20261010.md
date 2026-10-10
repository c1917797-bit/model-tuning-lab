# r18 c32/max-2048 terminal failure — original monkeypatch

No paired quality verdict exists. Preserve both immutable roots; do not resume the failed root.

The no-cache arm completed 127/127 LongBench samples and 381/381 scored responses (223 correct), with source and isolation audit passed. Its arm-result SHA256 is `7d17df0e23319ff55f2a798e2cc2a1e63f99504b23ad6fe5fb75936c0a4a3464`.

HYPIC-only controller `exec-0000000000000247` terminated at 2026-10-10 10:10:30 UTC after 33/127 complete sample files. Independent read-only partial-row audit passed 99 scored rows, 165 distinct request IDs, and 54 correct among those partial rows only. HTTP 500 followed all four TP workers raising `HYPIC PI hit lacks GDN (conv,S,T)` at `language_model.model.layers.0.linear_attn` (`patches/gdn.py:894`). This is runtime failure, not a quality score.

A materialization batch was planned at `1791627021827960410` ns. A distinct hot-hit batch was planned 21.7 ms later, before the materialization report at `1791627024518618140` ns announced ready=1, evicted=1. The crashed scheduler dump referenced hot hash `ec05bf95ffcf8a42e56007a24ca4cfba`. The report omits victim hash, so exact victim identity is not directly proven. This matches the r9 asynchronous eviction failure (`HOTPATH_CACHE10R9_EVICTION_RACE_ROOT_CAUSE.md`). Original source `3ad0967` lacks the pending-materialization prefill guard in direct descendant `4429e3`.

The guard recorded 400 physical NPU0–3 samples, zero foreign PIDs and zero probe errors. Exact owned container `21a5e6845b73639d2160027405eb8e084cc781cf6d2ea57ee34ef5ed7cab710f` was removed, with owned NPU workers and port 8223 released. Historical release is not current lane admission.

Immutable root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r18-c32-full-hypic`.

| Artifact | SHA256 |
| --- | --- |
| arm-result.json | `8041f87fbc56579e387bd0e80b362b752306e60a2ddb2445865ccc34f1345588` |
| contract.json | `451ca7ac54f5cddaf54e7f43550c15e73916477a81adcf7ccfa78b1980a3ee12` |
| progress.json | `f390ec122752eaed84bf017815a0c5919d780f495ac0b857abb3f0904aa0958b` |
| hypic-evidence.jsonl | `6715ea5c960569f363f7e2d5ebcc59dd857461f577703dbc669ca80a69611977` |
| service log | `19ffc96cfab43d9a0ef546b827fdbf71142e23b5ab4d6ffe6ec3347d62ae9979` |
| lane-guard.json | `0fd536c75a0d8a7db7944924fcd19603ef570439730e202a8d374be541ba28d8` |
| service-stop.json | `b4dd60d592ee9a59ce0a972b9e3769ead30d7b37a2f736e12bbd9480d655d80c` |

Next: reuse the existing `4429e3` repair as a bounded candidate, first validating its focused CPU race tests and disabled-control seam. Freeze new source identity and immutable quality roots. Reuse the r18 baseline only if the quality contract independently proves disabled-path/source equivalence; otherwise obtain a new matched control. No isolated operator detour or automatic repetition of valid original-source performance.
