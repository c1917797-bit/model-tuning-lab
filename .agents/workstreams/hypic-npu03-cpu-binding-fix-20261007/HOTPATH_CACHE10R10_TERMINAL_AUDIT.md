# cache10r10 full HYPIC terminal audit — failed activation, complete response set

At 2026-10-08 20:04:15 UTC, sole controller
`exec-00000000000016af` terminated with exit 1 and
`candidate scored boundary/hot coverage incomplete`. Its immutable attempt
root is `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r10-full-hypic`.
Do not restart or relabel this root. Plugin source was frozen at
`4429e35177979c874bf053ab29789e4773f39b22`; the separate diagnostic
source at `62b0d4a` was not mounted and has no r10 NPU result.

## Frozen scope and observed outcome

- Physical NPU0–3, TP4, cpuset 112–191, 0.85 GPU utilization, 3,584 MiB
  material cache, at most ten materialized segments. Native prefix cache
  coexistence was disabled. LongBench-v2 c8, 127 samples, two one-token
  observations plus three scored requests per sample, natural EOS,
  temperature/seed zero, thinking off, maximum output 2,048.
- All 127 sample files and 381 scored responses persisted. The controller
  recorded `quality_pass_claim=false`. Independent frozen-input, payload,
  response-hash and scorer replay via `hotpath_quality_partial_audit.py`
  with explicit `--root` passed: 635 distinct request IDs, 381 scored rows,
  214 correct. Per-repeat correct counts were 72, 70 and 72; this is a
  **single failed candidate arm**, not a paired accuracy or paper verdict.
- The terminal request-level gate `verify_hotpath_request_coverage.py`
  exited 2: 366/381 scored requests had all four namespace workers' positive
  skipped-token, post-repair proof; 15/381 did not. Gap repetitions were
  first: 1, second: 4, third: 10. Missing pairs (sample:repetition):
  6:3, 18:2, 18:3, 28:3, 30:3, 75:3, 77:2, 77:3,
  86:1, 86:2, 86:3, 91:3, 107:2, 107:3, 111:3.
  Each missing scheduler request has an explicit segment boundary and
  independent-segment observation but no request-local plan or worker proof
  in the pinned source's evidence stream. Sample 86 misses all three scored
  repetitions, refuting a repeats-only explanation. An eviction/retry cause
  is plausible from source inspection, but **not established for these IDs**:
  this source did not emit per-request planner reasons or eviction hashes.
- The lane guard collected 1,077 samples with no foreign process or probe
  error. The exact owned container `7146ab8743674109e6a4d4058ed14e3fb371d6bcfee366e7b52b24077ea2dc86`
  was removed; stop receipt asserts owned NPUs and port 8223 released.
  A post-terminal `npu-smi info` and `ss -lntp` independently found no
  NPU0–3 processes or listener on 8223. This is not another person's
  interference verdict.

## Raw evidence identity

- `contract.json`: SHA256 `2c35791ee9f7e0db7f4efcff330296906ef7fa3c185d5c1e4f3ea3a0ac93afa1`
- `arm-result.json`: SHA256 `272b6d1b7b6f3cdc572c1b4dfbb46a29e65bad1a5a949e5159abdee5a857c608`
- `hypic-only/hypic-evidence.jsonl`: SHA256 `c630a6662153856c3abd0c0981f15d013c5f05253472f09fa68ab27c74a3a7b9`
- `hypic-only/lane-guard.json`: SHA256 `8af3e8dec5dfd384efb8a6b8dbb7ce63bda220d540833f8a0242967bb9b2bebb`
- `hypic-only/service-stop.json`: SHA256 `c318acca1b150c24792563303a8f00e773eb3aca1ef6b8d5eabc24be7aa3e368`
- Ordered sample manifest SHA256 `9855ab4c7e82bd59ed29c23f7c1c738b9e8ff5eb5b3776b752670d58366a9804`,
  computed by feeding each sorted sample filename, NUL, file SHA256 hex,
  and newline to SHA256. Raw responses, weights and datasets stay off Git.

## Decision and next test boundary

r10 is a valid isolated **negative activation result** for its frozen
single-service source and protocol, despite a complete response set. It is
not a HYPIC quality pass, not a matched baseline comparison, and not an
algorithm-wide failure. Do not run or pair a same-source no-cache baseline
merely to rescue this failed activation arm. Investigate a prospective
candidate with request-local fallback telemetry and a distinct source/root;
first use a diagnostic stress/canary that exercises the failing c8 class,
then rerun the original full ruler if the path is proven. Only when actual
physical NPU0–3 and port 8223 are free, with no foreign task, may another
device attempt start. Never use NPU4–7 or alter foreign containers.
