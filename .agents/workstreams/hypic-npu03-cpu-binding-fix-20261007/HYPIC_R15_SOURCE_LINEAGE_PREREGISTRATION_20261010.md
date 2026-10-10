# r15: bounded HYPIC-on source-lineage E2E diagnostic

Frozen before device launch. This is **not** a repeat of r13, an acceptance suite, or a no-cache-versus-HYPIC quality verdict. It asks whether the behavioral source changes between the known-good historical `3ad0967` implementation and the current `c12060c` descendant change answers on selected r13 quality-flip cases under the *same current* max-2048/c8 environment.

## Arms and sole treatment

Both arms enable HYPIC and disable native prefix caching. Source order is original then current; the only declared change is the mounted plugin source commit. Use two clean, isolated checkouts:

- original `/cache/cch/hypic_vllm_ascend-r15-original`, `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`;
- current `/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008`, `c12060cd47e7575ead059983d7a8bb4704165c98`.

Keep Qwen3.6-27B BF16 TP4 weights/index, image SHA256 `660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`, physical NPU0–3, CPU 112–191, port 8223, context 41984, GPU-memory fraction 0.85, material limit 3584 MiB/10 segments, LongBench-v2/evaluator bytes, natural EOS, seed/temperature 0, thinking off, two one-token warmups per case, three scored max-2048 responses per case, and client c8 identical. Neither arm may use NPU4–7.

The 8 sample indexes in execution order are `[55,6,30,40,49,26,50,48]` with prompt-token counts `[10352,15683,11036,24608,16739,25585,27771,39642]`. From immutable r13 baseline/current scores respectively: neutral controls 55 `0/3→0/3`, 48 `3/3→3/3`; regressed 6 `3/3→1/3`, 30 `3/3→1/3`, 40 `2/3→0/3`, 49 `2/3→0/3`; improved controls 26 `0/3→2/3`, 50 `0/3→2/3`. This outcome-based selection is **diagnostic and biased**, never a population estimate.

The new immutable roots are `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r15-source-original` and the same prefix ending `-current`. Neither may preexist. The unchanged historical quality controller/service bytes are SHA256 `8ee34e61635731038df4312763ca2cac72b31578980a24539ca442fe7979c06d` / `714012b683142201fc4cf40d734f4d48f53210d7ade93479bf550e27020db0c4`; `r15_source_lineage_adapter.py` only changes selection, evidence root and source checkout in memory.

## Admission, stop and interpretation

Before **each** arm: freshly resolve `chicaihong01/ma` and prove direct route; load host-development; verify both exact source commits and clean checkouts, old r13 raw hashes, no live controller, root absence, physical NPU0–3 process/port 8223 availability, and source/service fingerprint. An outside process or guard error invalidates that arm; stop/remove only its exact owned container and retain the root. Keep the existing 10-second physical-process guard active during in-flight requests. Do not blindly restart after a control-plane timeout. Poll the same handle.

The historical controller requires first-sample hot-path evidence. If the original source cannot provide the *current* request-level telemetry, label that proof unavailable instead of equating an old aggregate counter with four-worker per-ID coverage. Preserve every completed response even if its controller exits nonzero at a proof-only gate. Require an independent raw-hash, sample-score, source-attestation, isolation and exact-release audit before interpreting any comparison.

Primary descriptive outputs: per-arm 24/24 valid responses, eight paired sample score counts, output/finish-reason changes, and same-source within-arm variability. A directional rescue concentrated in the four regressed cases makes source drift a stronger follow-up hypothesis; unchanged regression weakens it. Either outcome has sequential-order and post-hoc-selection limits and cannot assign a specific changed line as cause. Do not reinterpret r13's 230/381→219/381, promote a quality pass, or use favorable performance to cover quality. A source correction must subsequently pass a newly frozen full paired 2048 quality suite; reuse old baseline only after exact identity/hash equivalence.

Historical selector, not a license to reuse any old root:

```sh
HYPIC_R15_SOURCE=original python3 -B r15_source_lineage_adapter.py --check
HYPIC_R15_SOURCE=current python3 -B r15_source_lineage_adapter.py --check
HYPIC_R15_SOURCE=original python3 -B r15_source_lineage_adapter.py
HYPIC_R15_SOURCE=current python3 -B r15_source_lineage_adapter.py
```
