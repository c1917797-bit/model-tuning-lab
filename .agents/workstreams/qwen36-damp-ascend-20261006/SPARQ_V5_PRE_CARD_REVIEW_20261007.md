# SparQ v5 pre-card review — 2026-10-07 20:05Z

## Scope and disposition

MAIN reviewed the real private v5-002 host, preflight, proof, producer, consumer,
model bridge and tests. No v5 Docker/CPU-Torch/NPU execution was admitted.
Disposition: preparation blocked by two source-proven cross-module mismatches,
not numerical rejection, paper-wide no-go or E2E/task evidence.

Private packet:
 /cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-token-native-v5-002
SOURCE_MANIFEST SHA256:
870ff13d8853c4037a56e84fbba4602b086569fc8b95965768c5ac194aeb6996
Actual preparation MA0f10: exit0, 69 stdlib tests; this does not close deployed ABI.
The earlier v4 MA0ef8 failed CPU ABI remains failed and frozen.

## Exact source mismatches

1. host.py SHA3de923e6b8048de76fc2f70e32c56b2c0c073b22776d1dfe1b8aec0ead14d8ca
   creates model-tuning-lab.owner=sparq-token-v5. The retained
   sparq_token_v4/proof.py SHA70eed04080d4a3e8c6a81871d3da81aa1bed6fcde3c06b32d0e04d37d89c539c
   requires sparq-token-v4. Its otherwise byte-exact historical proof module is
   incompatible with the new owner's actual inspect.
2. host.py calls preflight.py with --host-output-root <owned>/cpu-preflight.
   proof.py constructs an expected original CPU ABI argv without that pair.
   Both preflight.py and consume_numeric.py require the new complete argv.
   Exact-command validation would therefore reject the real child.

These are identified by source review, not an actual v5 failed native run.
The unchanged core/scalar oracle/model bridge are not implicated by this review.
No original numeric threshold, algorithm equation or failure receipt is changed.

## Next evidence-producing action

Sparse preparation owner is building a new independent frozen successor with
one exact source-bound owner and complete CPU ABI argv. Add cross-module tests
that feed host-generated inspect/argv into the real proof validator; a textual
assertion or mock-PASS packet does not suffice. Preserve old v5-002 bytes.
A new service successor must pin the new component source and independently
consume its real complete native result before TP4 admission. MAIN reviews and
applies the successor, then performs fresh resource admission after KVBuffer
releases its current serialized NPU lease.

KVBuffer warm MA0f29 is currently running on physical6 only. The snapshot at
19:58Z contains four completed B14 cases/640 steps and33 B11 eager steps.
This is progress, not completion of1280+1 or full11520/mixed/model/E2E/tasks.
Do not restart its live handle or edit its frozen144-source closure.
Memory authority is already fully spent:32GiB released, OVS intact; no further
HugeTLB release. Protected0–3 and fixed Oct8/Oct9 cutoffs remain unchanged.
