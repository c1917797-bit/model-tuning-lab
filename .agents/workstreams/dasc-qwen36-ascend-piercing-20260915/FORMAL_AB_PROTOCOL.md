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

Before either arm starts, create its deterministic runtime manifest. Hash the
model config, safetensors weight index, tokenizer files, Docker image
inspection, host driver/CANN metadata, pinned HYPIC benchmark, quality
evaluator, and both datasets. Include each raw manifest and its file SHA256 in
the normalized evidence. The independent decision rejects either an unbound
manifest hash or any cross-arm byte drift.

## Frozen resource budget

Both arms use exactly 9,663,676,416 cache bytes per TP rank (9 GiB), a
128-token block, `max_model_len=44032`, `max_num_seqs=32`, and the same
model-native bfloat16 cache dtype. The static audit derives the Dense TP4 page
from the immutable Qwen3.6 config: 16 full-attention layers contribute
2,097,152 bytes and 48 GDN layers contribute 19,611,648 bytes, for a
21,708,800-byte aggregate page. The fixed budget therefore admits 445 blocks
or 56,960 tokens. The longest audited request consumes 344 blocks, leaving 101
blocks, so the Dense arm can serve it without truncation.

Run `audit_formal_resource_budget.py` before launch and preserve its JSON and
SHA256. This is a preflight estimate, not runtime proof: each arm must emit and
independently reconcile its actual page sizes, allocated block count, cache
dtype, and cache bytes. A mismatch rejects the arm. The benchmark may queue
requests when all concurrency cannot be resident; such scheduling pressure is
part of the fixed-budget capacity comparison and must not be hidden by giving
the arms different cache budgets.

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

The Qwen3.6 tokenizer audit at the hash pinned in the v13 experiment found that
the 96-line neutral prefix adds exactly 2592 tokens. The largest LongBench-v2
prompt becomes 42234 input tokens and needs 43258 tokens with the fixed 1024
output budget. Both arms therefore use max_model_len=44032. A service configured
below that bound is inadmissible; silent truncation is not allowed.

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
The first context audit incorrectly measured the two fields of a dict-like
tokenizer result as two tokens. That artifact is hash-preserved as rejected
evidence and must never be used for sizing.

## Decision

The mechanism result, performance result, and quality result are independent
gates. Report negative evidence honestly. A candidate can be performance
positive only if all three repetitions improve cache-hit TTFT and derived input
throughput in the same direction. It can be accepted only if each dataset's
median quality loss is no worse than the larger of one percentage point and
the measured dense baseline run-to-run range.

The controller must normalize the complete per-request performance rows,
quality-detail rows, metric snapshots, and arm identities with
`build_formal_evidence.py` into `dasc-formal-v13-normalized/v1`. Run
`verify_formal_decision.py` over that
self-contained evidence. It recomputes completeness, cache-hit deltas,
accuracies, paired per-run direction, the Dense run-to-run tolerance, and the
one-switch identity. It also rejects candidate evidence unless the physical
cache, TP geometry, and dispatch events cover the same four workers. Its exit
code is authoritative for the formal decision;
a hand-written summary cannot override a rejection.
