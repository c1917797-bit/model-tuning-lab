# When Good Enough Is Optimal — Qwen3.6 Ascend Piercing

## Terminal decision — no-go for the frozen service objective

Closed at `2026-09-19T22:23:26Z`. The method matches the model mechanism, but
the target path has insufficient opportunity. Applying the paper's best
reported `5.2x` inversion speedup to the measured Qwen3.6/Ascend inversion
share gives only `1.02421x-1.02447x` prefill-NPU speedup. Perfect inversion
deletion gives only `1.03015x-1.03047x`, before full-service dilution, and the
method has zero decode coverage. Reaching `1.10x` would require an affected
share of `11.255%`; observed is `2.927%-2.957%`.

Artifact:
`/cache/cch/good-enough-inversion-qwen36-ascend-20260920/opportunity-gate-v1/opportunity-audit.json`,
SHA256 `ab3f8ca82219b4262d3680bd0b3a33c58335b3adf0db412601e4a050555f0ef0`.
Three focused tests passed. This is an opportunity bound using prior real-NPU
correctness and timing evidence, not an E2E or quality result. The approximate
algorithm was not implemented; NPU4-7 were not consumed after the bound failed.

## Scientific question

Can the paper's masked low-order Neumann expansion plus parallel residual
correction produce at least 10% end-to-end throughput improvement for the
frozen Qwen3.6-27B workload on Ascend, without final quality regression?
Activated `2026-09-19T22:20:31Z`; deadline
`2026-09-20T22:20:31Z`.

The paper replaces chunkwise triangular inversion, using chunk-size-dependent
Neumann order, a structural diagonal mask, and residual correction. Its
default reported setting is chunk 64, order 3 and residual span 8. The method
is approximate and therefore has a separate correctness/quality identity from
the exact MXR campaign. INT quantization is outside the current scope.

## First gate

Do not repeat an isolated inversion microbenchmark. The preceding MXR work
already measured the same Qwen3.6 TP4-local inversion seam on physical
NPU4-7: incumbent inversion is only `2.9267%-2.9568%` of prefill NPU interval
and does not execute in decode. Apply the paper's best reported `5.2x` local
speedup and perfect deletion to that target share. If either bound is below
`1.10x`, approximation implementation and quality testing are not admitted.

Physical NPU4-7 remain the exclusive portfolio set. Fresh-check real NPU
processes, HBM, mappings and ownership before any run; stop only an exact new
external workload that really overlaps4-7, and never touch0-3.
