# DASC Formal A/B Protocol

## Entry gate

Do not start the formal A/B merely because unit tests pass or compact tensors
exist. Experiment v12 must first prove that the order-fixed physical cache:

1. starts on physical NPU4-7 as TP4;
2. emits geometry, worker-dispatch, and compact-page evidence from the same
   exact set of four workers;
3. binds pages smaller than the dense representation with positive admitted
   blocks;
4. completes a byte-exact short response with a normal stop finish reason;
5. completes three deterministic shared-prefix reuses with a positive cache-hit
   counter delta.

Any v12 failure is preserved under its immutable artifact root and classified
before a superseding experiment is created.

After the controller is terminal, run verify_physical_v12.py against the
immutable root. It must independently recompute the raw activation cohort,
exact responses, cache-hit delta, source commit, and every nested SHA256
manifest. A controller-authored ok field is not acceptance evidence by itself.

## One-switch arms

Both arms use the same Qwen3.6-27B bytes, image digest, CANN/driver stack,
physical NPU4-7 to container NPU0-3 mapping, HCCL TP4, CPU set, port policy,
prefix caching, cache budget, graph mode, maximum lengths, request order, and
random seed.

- Dense: Ascend plugin only; native dense recurrent checkpoints.
- Candidate: Ascend plus dasc_vllm_ascend, physical-cache-eager, W_max=64.

The DASC switch is the only treatment difference. A run with prefix caching
disabled is not a DASC denominator.

## Performance ruler

Reuse the HYPIC-proven dependency-free shared-prefix benchmark at the pinned
SHA256 in the v13 experiment file. Each arm has three unique measured runs:

- input tokens: 32768;
- shared prefix tokens: 16384;
- fixed output tokens: 1024 with ignore_eos enabled;
- requests: 40;
- concurrency: 16;
- warmups: 2, excluded from aggregates.

Store every per-request result. Validate 40/40 success, zero failure, exact
fixed output length, positive cache-hit deltas, and candidate hot-path evidence.
Report TTFT mean/P95, TPOT mean/P95, request duration, output throughput, and
derived input-token throughput. DASC is a checkpoint-capacity/reuse method, so
decode-only throughput is secondary and cannot substitute for cache-hit TTFT.

## Quality ruler

Reuse the validated HYPIC/AIS Bench LongBench-v2 and GSM8K parsers and scorers,
but adapt request construction so the DASC restore path is actually exercised.
Both arms must prepend the same hash-bound, semantically neutral shared prefix.
The evaluator must snapshot prefix-cache counters before and after each run and
reject a run with no positive hit delta.

Run all 127 LongBench-v2 and 1319 GSM8K samples three times per arm with
temperature 0, seed 0, thinking disabled, and the same output budget. Preserve
one JSONL row per sample, unique complete indexes, response hashes, dataset and
prompt hashes, scorer identity, and summary-to-detail hashes. Recompute every
summary independently.

The thin shared-prefix adapter is implemented in dasc_quality_eval.py. It
verifies the validated HYPIC evaluator SHA before importing its unchanged
dataset loaders, prompts, and scorers; prepends a deterministic neutral prefix;
captures cache metrics; and augments the summary with all relevant hashes. It
must be invoked with --require-cache-hit. Its offline self-test is necessary but
not sufficient: only a live positive hit delta makes a quality run admissible.

## Decision

The mechanism result, performance result, and quality result are independent
gates. Report negative evidence honestly. A candidate can be performance
positive only if all three repetitions improve cache-hit TTFT and derived input
throughput in the same direction. It can be accepted only if each dataset's
median quality loss is no worse than the larger of one percentage point and
the measured dense baseline run-to-run range.
