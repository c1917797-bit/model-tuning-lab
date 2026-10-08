# cache10r9: asynchronous material-cache eviction race

Status: failed candidate arm; no paired HYPIC accuracy/performance conclusion.
Scope: original full LongBench-v2 127 × 3, 2048-token natural-EOS candidate,
physical NPU0–3 only, GPU utilization 0.85, HYPIC material cache 3584 MiB /
10 segments. Raw root:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r9-full-hypic`.

## Observed failure

- Controller operation `exec-000000000000158e` ended exit 1. It retained 93/127
  complete sample files, then sample 98 received HTTP 500. Its exact owned
  service was released at 2026-10-08 18:14:21 UTC. Do not resume/mix this root.
- Four TP workers reported `HYPIC PI hit lacks GDN (conv,S,T)` for
  `language_model.model.layers.0.linear_attn`; this is a missing worker-local
  public material read, not a numerical-quality score or NPU topology error.
- Evidence JSONL contains 100 producer plans with 100 distinct material hashes,
  100 ready publications and 90 evictions under the 10-segment cap. The final
  producer (`cb6455c5c27bbd4164c65f857af4775f`) was dispatched at
  `179148325219...` ns. The scheduler issued the next batch with one hot hit
  at `1791483252203754540` ns, before the producer report at
  `1791483254822779520` ns announced one eviction. The dumped next batch
  referenced an older hot material (`9c2e2247211dceec24218d2343eef636`).
  The worker then failed to find GDN material. The report records eviction
  count, not victim hash; the exact victim identity is not independently
  logged. The scheduling-before-report ordering and failure mechanism are
  directly observed; victim identity remains an inference.

## Repair candidate and proof boundary

In a separate plugin worktree, local commit
`4429e35177979c874bf053ab29789e4773f39b22`:

1. Holds queued prefills while any materialization report is pending, allowing
   already-running native decodes to proceed. This prevents scheduling a hit
   against an LRU entry whose eviction the scheduler has not learned yet.
2. Emits `worker_hot_request_verified` with the scheduler request ID only
   after the worker validates complete hybrid repair; the model-tuning-lab
   request-coverage gate can join every scored API ID to all four workers.

Six focused CPU tests and compile/diff checks pass. The single-instance and
paper-core source audits pass; the upstream-complete audit correctly remains
FAIL for known C3 scatter/router/transfer and other missing capabilities.
The host default Python 3.9 cannot collect the full suite (`itertools.pairwise`);
a device-free container Python 3.12 run hit its pre-existing Torch library
registration failure. These environment failures are not test passes.

The plugin commit is local only, not pushed to the third-party Gitee remote.
No repaired NPU run has passed yet. Next use a fresh `cache10r10` root with
the pinned read-only plugin worktree, and start only when physical NPU0–3 have
no processes and port 8223 is free. Review its gate and isolation first; run
a new same-fingerprint no-cache arm only if the candidate passes. The prior
0.9-utilization baseline cannot pair with this 0.85 candidate.
