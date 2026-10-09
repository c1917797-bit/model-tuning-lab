# HYPIC r14 — prospective c1 response-variability diagnostic

Frozen before any r14 device action on 2026-10-09. This is a discriminating
diagnostic prompted by the read-only r13 response analysis, not a repeat of
the complete 127×3 c8 quality ruler and not a revision of its decision.

## Question and fixed denominator

Does the greater HYPIC-only within-arm answer variability observed in r13
persist when the same service is exercised by one request at a time? This
can test whether c8 concurrent scheduling is *necessary* for that observed
variability on this selected subset; it cannot establish a population
quality verdict or identify the numerical/cache/CANN/HCCL root cause.

- Same pinned official image `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
  Qwen3.6-27B BF16 TP4, plugin checkout
  `/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008` at
  `c12060cd47e7575ead059983d7a8bb4704165c98`, context 41984,
  GPU memory utilization 0.85, material cache 3584 MiB / 10 segments,
  CPU set 112–191, physical NPU0–3 only. The only serving-arm switch is
  HYPIC on/off, plus its evidence path. No NPU4–7 mapping.
- LongBench-v2 dataset/evaluator and frozen chat template, prompt construction,
  seed 0, temperature 0, thinking disabled, natural EOS and 2048 output cap
  match r13. Client concurrency is **1**, unlike r13's 8, in *both* arms.
- Three samples were selected by length before inspecting their r13 answers:
  index 0 (24,616 prompt tokens), shortest index 55 (10,352), and longest
  index 48 (39,642). Selection order is `[0,55,48]`. Each arm has two
  one-token warmups then three scored max-2048 requests per sample, nine
  scored requests total. Segment ends are derived identically by the frozen
  controller and verified before launch. No additional samples are admitted.
- Run no-cache first, then HYPIC-only, each in a distinct immutable root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r14-variability-baseline`
  and the same prefix ending `-hypic`. Neither root may preexist. Do not
  reuse r13 or any earlier root.

## Admission and fail-closed execution

Before each arm, freshly resolve `chicaihong01/ma` by AWMCP, load
`host-development`, prove force-direct target identity, source Git cleanliness
and exact commit, root absence, real physical NPU0–3 process emptiness, and
port 8223 freedom. A passive container device declaration is not a process.
Do not stop or modify any external workload. The existing controller's
continuous physical-process guard must remain clean throughout each arm,
including long in-flight requests. On any foreign PID/probe error, preserve
that arm as environmental failure, stop and remove only its exact owned
service, and do not pair it with another arm. Poll the same asynchronous
controller handle; timeout or slow output is not permission to restart.

Use `r14_variability_adapter.py` with `HYPIC_R14_ARM=no-cache` first and
`HYPIC_R14_ARM=hypic-only` second. The adapter verifies the historical
`hotpath_quality_full.py` and `binding_off_quality.py` SHA256 values before
import, then sets the r14 campaign, mode, roots, c1 concurrency, and selected
cases only in Python memory. The historical source files stay byte-identical
to their earlier evidence and the plugin source values above remain pinned.
The adapter, independent auditor and focused offline selection test must be
committed and pushed before device launch. No runtime source edits are
allowed after the baseline starts.

## Independent audit and interpretation

`audit_cache10r14_variability.py` independently verifies both exact source
attestations, matching service fingerprint except HYPIC, all nine paired
request hashes/scores per arm, four physical workers, continuous isolation,
and exact owned release. Candidate activation requires 9/9 *per-request*
four-worker post-repair hot proof; baseline must emit no HYPIC hot event.
It reports raw correct counts only as descriptive diagnostics. Primary
variability observations are exact text equality, extracted-answer agreement,
correctness agreement, and median common-text prefix across each sample's
three within-arm repetition pairs; matched cross-arm results are also
reported. Three pairs from one sample are correlated. No p-value or full
quality pass is inferred from nine scored responses per arm.

After the baseline terminates, run
`audit_cache10r14_variability.py --baseline-only` and require its independent
read-only receipt before admitting the candidate. The final paired audit
emits one external immutable report only after both arms pass.

If the candidate's c1 variability still exceeds the matched baseline,
c8 concurrency is not sufficient as a sole explanation on these samples.
If it does not, concurrency/capacity becomes a stronger hypothesis but is
not proven causal without a controlled follow-up. Either outcome leaves
r13 `REJECT_OR_QUALIFY`, its 368/381 strict quality hot failure, the
Prefill `>=47`-column preregistration miss, and C3's unimplemented state
unchanged. Do not repeat the full baseline or assert paper/deployment success.
