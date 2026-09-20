# Qwen3.6 GDN decode mega-op

## Status

- Stage: native reference verified; candidate implementation not started.
- Branch: `work/qwen36-gdn-decode-megaop-20260920`.
- Base: portfolio synthesis checkpoint `a4a9def`.
- Hardware lane: physical NPU4-7 only.
- Delivery boundary: independent, explicit opt-in, fail-closed vLLM-Ascend
  plugin/monkeypatch. Do not modify upstream vLLM, vLLM-Ascend,
  `ops-transformer`, CANN, or the original image.

## Why this loop exists

The fresh dense TP4 profile isolated one shape-filtered GDN decode call chain
covering 14.15340% of decode operator time. Under the diagnostic Amdahl model,
the affected route needs at least 2.79680x local speedup before a 10% decode
phase gain is plausible. This is an opportunity gate, not an end-to-end result.

The target chain is:

`static conv-weight transpose -> causal conv/state update -> packed QKV
rearrangement -> gating -> Q/K L2 normalization -> recurrent state update`.

## CannBot provenance

The preceding portfolio stage did not generate an operator. This workstream
must distinguish:

1. upstream vLLM-Ascend operators;
2. paper-author implementations;
3. CannBot-generated specification/scaffolding;
4. project-authored adaptations and kernels.

The first implementation checkpoint is allowed only after:

- the actual arch22 schemas, shapes, dtypes, layouts, aliasing, and state
  mutation contracts are recorded;
- CannBot `ops-spec-gen` produces the initial spec skeleton;
- all manually completed L0 fields pass the 11-stage strict validator;
- the design does not invent an unsupported CANN API or primitive.

The CannBot-generated-and-audited L0 specification now exists at
`projects/qwen36-gdn-decode-megaop/operators/qwen36_gdn_decode_megaop/spec.yaml`.
Strict validation passes stages 1-4, 6-8, and 11. Stage 5 remains an explicit
CannBot v1 tooling limitation because it incorrectly places heterogeneous
activation, weight, state, and metadata inputs in one broadcast group; stages
9-10 are skipped because no upstream single-call mega-op oracle exists.

## Native golden gate

The project-local probe
`projects/qwen36-gdn-decode-megaop/tools/gdn_decode_golden_probe.py` ran once
in the immutable v0.23.0 image on container logical NPU0 mapped only to
physical NPU4. It exercised the current native causal-conv, gating, Q/K
normalization, and recurrent operators for batch 1 and batch 16 over eight
stateful steps with changing slot indices.

- Result: `native_gdn_decode_golden_gate_pass`.
- All 16 case/step combinations passed.
- Eager and NPUGraph outputs, convolution states, and recurrent states were
  bitwise identical at every step.
- Unselected slots and all tracked tensor metadata/storage pointers remained
  unchanged.
- Maximum output absolute error versus the independent formulation was
  `9.5367431640625e-07`.
- Maximum FP32 recurrent-state absolute error was
  `1.2959353625774384e-05`.
- External report:
  `/cache/cch/qwen36-gdn-decode-megaop-20260920/native-golden-v1/report.json`.
- Report SHA256:
  `5df8a431b892cf82bc2be986cd4e6d7b62e06a69d558b86094e8c4822cddaf19`.

This proves the reference chain and oracle protocol, not a candidate operator
or a performance gain.

## Fail-closed gates

1. Preserve FP32 recurrent state and the actual runtime state-index semantics.
2. Preserve in-place causal-conv and recurrent-state updates, including
   multi-slot indexing.
3. Prove eager and graph-replay determinism on real NPU over multiple stateful
   steps before any performance claim.
4. Compare candidate output and complete mutated states with the unmodified
   Ascend reference path; non-finite values or an unexplained mismatch fail.
5. Reject before end-to-end work if a credible implementation cannot cover the
   measured seam or cannot plausibly reach the 2.79680x local-route gate.
6. Apply generic runtime optimizations to dense and candidate equally.
7. Only repeated profiler-off output-1024 service measurements may establish
   throughput, TTFT, or TPOT gain.
8. Final acceptance still requires paired LongBench-v2 and GSM8K with thinking
   disabled, max_tokens=2048, normal EOS, and no accuracy decrease.

## Portability rules

- Detect operator availability, framework ABI, shapes, dtypes, and NPU
  architecture at runtime; do not key correctness to one filesystem path.
- Keep v0.23 integration behind a thin adapter so later vLLM-Ascend releases
  replace the adapter rather than the operator semantics.
- Use arch22 as the current verified implementation target; keep architecture
  selection explicit and fail closed on unvalidated architectures.
- Never infer support from an image tag or model name.

## Immediate next action

Create the independently named direct-invoke AscendC candidate scaffold in the
plugin project. First fuse packed-QKV rearrangement, gating, Q/K normalization,
and recurrent update while reusing the audited recurrent algorithm; then run
the candidate against the frozen native golden probe. Only a passing candidate
may absorb causal conv and proceed to the `2.79680x` affected-route gate.
