# Qwen3.6 Linear/Hybrid Attention Piercing Lessons

Read this reference when selecting, implementing, or reviewing a Qwen3.6-27B
linear/hybrid-attention paper on Ascend. It records reusable decision rules and
the bounded conclusions available as of 2026-09-22. Refresh live environment
facts and branch-local evidence before acting.

## North-star alignment

The long-term outcome is a reproducible and transferable vLLM-Ascend
plugin/monkeypatch with at least 10% end-to-end output-throughput gain, separate
TTFT and TPOT reporting, and no final LongBench-v2 or GSM8K loss.

The medium-term obligation is the complete evidence chain:

`paper/source fidelity -> runtime-path proof -> NPU numerical correctness ->
graph correctness -> TP service dispatch -> paired dense performance -> final
task accuracy`.

Every short loop must remove the newest proven blocker in that chain. At the
start and end of a loop, state which long- and medium-term requirement the work
advances. CPU-only work, a kernel microbenchmark, documentation, or an
unpaired service run may prepare the next gate but cannot close it.

## One-day paper protocol

From formal start, spend at most 24 wall-clock hours on one paper. Predeclare
the stop time and the next queued paper; a failed gate closes the current scope
and advances the queue unless new evidence changes the gate.

1. **Freeze provenance.** Record paper revision, official implementation URL
   and commit, license, equations, checkpoint identity, and which parts are
   faithful ports versus project adaptations. If official code is absent, say
   so and build an independently testable reference instead of claiming an
   official reproduction.
2. **Prove the runtime seam.** Trace the running service from Python dispatch
   through the registered operator to the actually loaded shared object and
   binary. Hash the decisive source and loaded artifacts.
3. **Apply the opportunity gate.** Let `f` be the measured fraction of the
   critical path affected by the proposal and `s` its optimistic local
   speedup. The optimistic service speedup is
   `1 / ((1 - f) + f / s)`; perfect deletion is `1 / (1 - f)`. Reject the
   standalone 10% claim when even the optimistic bound is below 1.10. Continue
   only when an explicit composition plan names an independent bottleneck and
   budgets the new overhead.
4. **Pre-register the comparison.** Freeze input/output lengths, request count,
   concurrency, prompt/token transport, warmup, EOS behavior, seed,
   temperature, graph mode, parallelism, physical devices, ports, model and
   tokenizer hashes, runtime versions, and output directories. Apply common
   optimizations to both dense and candidate.
5. **Pass the correctness ladder.**
   - equation/reference agreement;
   - real NPU eager output and mutable-state agreement across multiple steps;
   - alias, pointer, guard, finite-value, shape, stride, padding, and state-index
     checks;
   - NPUGraph capture and replay with explicit synchronization before host-side
     comparison;
   - TP service worker dispatch and loaded-binary proof;
   - a small service canary before the fixed performance run;
   - final task accuracy after performance screening by default; a separately
     authorized quality study may proceed after regression without changing
     the negative speed decision.
6. **Measure the service.** For the current formal performance contract use
   fixed 1024 output tokens and report throughput, TTFT, and TPOT. Profiling is
   diagnostic and must be disabled for the formal comparison. Kernel-duration
   sums do not establish end-to-end gain.
7. **Decide and move.** A valid negative screen is a result. Preserve the
   implementation and evidence in history, remove or disable failed code from
   the safe tree, record the no-go scope, and move to the next paper rather than
   rerunning a deterministic failure.

## Runtime and stateful-operator traps

- Eager correctness does not imply graph correctness. Asynchronous NPU kernels
  can make an unsynchronized replay check look nondeterministic.
- Graph correctness does not imply scheduler correctness. Test changing state
  indices, mixed prefill/decode batches, slot reuse, and multiple decode steps.
- A decode-only fast path can be destroyed by a mixed-batch fallback. Instrument
  branch reasons and count full-state copies/materializations per layer, rank,
  request, and step.
- Check storage contracts, not only values: state layout, alignment, padding,
  aliasing, stable data pointers, arena guards, and view offsets are part of the
  ABI.
- Record the physical-to-container device mapping. Container device 0 is not
  evidence that physical NPU0 is in use.
- Keep custom operators independently named and explicitly enabled. A plugin may
  register and dispatch them, but must fail closed when version, shape, dtype,
  graph, or ABI capabilities do not match.

## Durable experiment conclusions

### HYPIC

HYPIC is the prior successful piercing reference. Its benefit depends on
position-independent reuse and a matching segmented/RAG-style workload. Preserve
that workload contract when using it as a template; do not convert its success
into a claim for ordinary no-reuse decode.

Reusable pattern: identify the reuse identity, prove exact output restoration,
make the feature opt-in, compare against the same runtime with common
optimizations, and report the workload dependency explicitly.

### DRRQR state reduction

The best paired screen reached 141.564496 versus 135.142470 output tokens/s,
a 4.752041% gain. It was useful evidence but did not meet the 10% target.

The decisive correctness finding was a native decode state-row alignment
contract: non-16-aligned retained dimensions such as 104 and 88 were padded to
112 and 96, and the state copy-out crossed padding incorrectly. Retained
dimensions 128 and 64 avoided that specific defect. Prefill success, finite
values, and early token agreement did not validate the affected decode states.

The Dk64 LongBench-v2 preflight scored 50/127 (39.3700787%) at a 1024 output
limit, while the historical dense mean was 45.4068241%. Those runs were not a
same-stack 2048-token final pair, so they demonstrate risk rather than a final
accuracy verdict. Do not revive invalid Dk104/Dk88 results or treat an energy
top-k selector as the paper's exact StrongRRQR implementation.

Reusable pattern: verify every retained dimension against the native alignment
and copy-out ABI, distinguish selector variants honestly, and require paired
task accuracy before acceptance.

### DASC

The Ascend candidate failed deterministic cache-hit replay: with
`temperature=0`, `seed=0`, and thinking disabled, identical input produced
different outputs across three runs. This blocks performance and accuracy
claims. The user's 1% accuracy budget applies to end-to-end GSM8K accuracy, not
to an intermediate tensor tolerance.

Reusable pattern: compare candidate and baseline under the same eager/graph
mode, prove replay determinism before benchmarking, and never reinterpret an
intermediate numerical tolerance as the task-level accuracy allowance.

### DeltaLog

The v4c custom-operator candidate passed real-NPU eager and synchronized
NPUGraph multi-step state gates and reached TP4 service dispatch. This proved
the operator and graph path, not the paper's service benefit.

The fixed 32768-input/1024-output, 40-request, concurrency-16 screen produced:

- candidate throughput: 112.424603 output tokens/s;
- paired dense throughput: 125.819134 output tokens/s;
- throughput change: -10.646%;
- candidate TTFT: 159935.195 ms, 315.888% worse;
- candidate TPOT: 99.825471 ms, 35.581% worse.

Instrumentation found 2130 Python full-state materializations, all on the
`not_pure_decode` mixed-batch fallback, repeated across layers and TP ranks.
Deduplicating the K log saved about 298.6 MiB per TP worker across 48 layers but
did not remove the dominant fallback overhead. The candidate was rejected and
did not proceed to final accuracy.

Reusable pattern: after local state/log savings pass numerical gates, audit the
real scheduler batch composition and count fallback materializations before
expecting TPOT benefit. A correct decode primitive can still be the wrong
service integration.

### Opportunity-gated candidates

- Stable or approximate triangular inversion affected only about 2.96% of the
  measured path. Even a 5.2x local result implied only about 2.4% optimistic
  end-to-end gain, so it could not independently satisfy the 10% goal.
- KVBuffer's recurrent path occupied about 4.52-4.84% of the measured
  concurrency-16 NPU interval. The paper's 45.17% local latency reduction
  implied only about 2.1-2.3% optimistic end-to-end gain. Its larger
  speculative/MTP result is outside the current paper-only scope.
- Sparse Prefix Caching stopped at correctness; SSM tensor parallelism lacked a
  distinct candidate beyond the existing TP path; EPD-Serve failed the workload
  and deployment-scope gate; DUET required a hardware/package expression not
  deliverable as the current plugin.

These are scoped no-go results for the frozen target and protocol, not universal
claims that the papers have no value.

## Portfolio decision rule

Prefer mechanisms that affect a measured double-digit share of the current
service path, preserve exact model semantics, and expose a stable plugin seam.
When no single paper has enough headroom, compose only orthogonal candidates
whose measured affected shares and added overhead support a pre-registered
combined bound. Do not combine several individually weak ideas merely to make
their paper claims sum to 10%.
