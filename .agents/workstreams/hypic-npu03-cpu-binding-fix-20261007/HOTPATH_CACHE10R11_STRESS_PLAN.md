# Prospective r11 request-local stress gate (diagnostic, not a quality verdict)

Frozen 2026-10-08 after r10 terminal audit. Scientific question: does the
separate HYPIC plugin source `62b0d4a89234ffaa69855427e0c0dad0ba3e9e41`
restore all four-worker scored-request hot-path proofs under c8 cache turnover,
and, if not, which request-local Prefill filter or planning state rejected
the route? The only primary treatment from pinned r10 `4429e351` is resetting
successful materialization retry state after the cache accepted material;
request-local diagnostics and null-safe evidence emission are instrumentation.
Their timing is not an optimization result.

## Frozen identity and ruler

- Own one new root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r11-stress-hypic`.
  Never overwrite/rerun r10 or this root; use a distinct new root if a
  documented successor is necessary.
- Source: clean read-only mount
  `/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008` at the exact
  commit above. Preserve image digest, real Qwen3.6-27B BF16 model index,
  frozen evaluator/dataset hashes, CPU-binding-off setting, context 41,984,
  GPU utilization 0.85, material cache 3,584 MiB and ten segments from r10.
  Physical NPU0–3 only, TP4, cpuset 112–191, port 8223. Native prefix cache
  disabled as in r10. NPU4–7 and foreign containers are out of scope.
- Use existing `hotpath_quality_full.py` with new `cache10r11` / `hypic-only`
  / `stress` configuration. Selected LongBench-v2 indexes are 75 through 91
  inclusive, then 107 and 111: 19 distinct eligible prompts, exceeding the
  ten-segment material-cache capacity. Include known r10 misses at 75:3,
  77:2–3, 86:1–3, 91:3, 107:2–3 and 111:3 plus nearby controls.
- Each sample has two one-token observations then three scored requests with
  its frozen explicit segment ends. Per-sample tasks run at concurrency eight,
  natural EOS, max output 2,048, temperature/seed zero, thinking off. The
  first sample is serialized as the four-worker activation sentinel. Frozen
  expected cardinalities are 19 samples and 57 scored responses; no failures
  or silent retries are accepted. Sample 86's three misses must be diagnosed
  at the request ID level, not by aggregate counters.
- This is a targeted fail-fast stress/canary, **not** a matched baseline,
  full LongBench quality ruler, or performance claim. No-cache quality and
  six-phase performance are deferred until a future source passes the
  original full 127×3 activation and independent quality gates. Do not reuse
  the historical 0.9 baseline against this 0.85 source identity.

## Entry, stop and decision

Before launch, run offline source/tests/parity checks, verify the new root
does not exist, resolve the target AWMCP peer afresh, confirm actual physical
NPU0–3 and port 8223 are idle, and check no other controller is live. Passive
Docker mapping alone is not use. Launch only the exact owned service and keep
the 10-second foreign-process guard active; on intrusion, preserve evidence,
attribute the PID/cgroup if observable and release only the owned service.
The r10 observed rate projects about 20–30 minutes including model load for
19 samples; allow a 60-minute controller window plus audit/release margin.
If the controller handle remains live at an observation timeout, poll the
same handle, never restart from a status file.

After terminal, independently require: exact source/image/weight and physical
PID mapping; 19 unique sample indexes, 57 unique scored IDs and frozen payload
hashes; all 57 IDs uniquely boundary-joined with positive skipped tokens and
post-repair proof from four workers; no missing/failed plan, worker, or request;
zero guard foreign/probe errors; exact container/PID/port release; and raw
contract/evidence/rows/guard/stop SHA256. A pass only admits the **next full
candidate arm**. A fail is a bounded negative result: retain diagnostic
reason(s), root and source hashes, do not reclassify r10, and choose a
materially different source hypothesis before another attempt.
