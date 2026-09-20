# Qwen3.6 GDN decode mega-op

## Status

- Stage: v13 exact hybrid candidate rejected by one-shot end-to-end screen;
  evidence checkpoint ready.
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

The original target chain was:

`static conv-weight transpose -> causal conv/state update -> packed QKV
rearrangement -> gating -> Q/K L2 normalization -> recurrent state update`.

The implemented v13 boundary is deliberately smaller:

`native causal conv -> native Q/K l2norm -> custom async gating+recurrent`.

The boundary was reduced after exact failing-input diagnostics proved that the
custom K-normalization path changed BF16 values. It is not valid to relax that
error merely because the formulas are algebraically equivalent.

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

## Candidate numerical result

The queue-safe v13 operator is independently named, explicit opt-in, and
delivered only through this plugin project. It preserves the deployed native
`l2norm_fwd` boundary and fuses gating plus recurrent state update.

- Operator library SHA256:
  `feaf6a4297dc2b688dc41cc5c49851188c7de8d156b2aa9583f4b4b38e38ed69`.
- Gate report:
  `/cache/cch/qwen36-gdn-decode-megaop-20260920/candidate-core-gate-v13-hybrid-v1/report.json`.
- Gate report SHA256:
  `e0477146e3e89ef888b8aaec12074b55b5cc88f60b6ea3d58437b7ba1c299a9f`.
- Physical NPU4: 32 queue-order iterations, batch 1 and batch 16 with eight
  stateful steps each, eager and NPUGraph all passed.
- Output, complete recurrent state, successor clones, indices, unselected
  slots, storage pointers, and metadata were exact; maximum absolute and
  relative-L2 error were both `0.0`.

This proves the implemented operator boundary, not service performance.

## End-to-end result and decision

The TP4 service ran on physical NPU4-7. A real request recorded 48
`candidate_dispatch` events on each of the four workers. The fixed screen used
40 requests, concurrency 16, input 32768, shared prefix 16384, and exactly 1024
output tokens per request with profiler disabled.

| Metric | frozen dense | v8 sync candidate | v13 exact hybrid | v13 vs dense |
| --- | ---: | ---: | ---: | ---: |
| output throughput (tok/s) | 125.819134 | 115.069990 | 118.455179 | -5.852810% |
| mean TTFT (ms) | 38,456.890 | 47,521.586 | 43,965.658 | +14.324528% |
| weighted TPOT (ms) | 73.628823 | 77.060475 | 76.399910 | +3.763590% |

All 40 requests completed 1024 tokens and all finish reasons were `length`.
The v13 queue-safe route recovered 2.941853% throughput over v8, but remained
slower than dense and far below the required 138.401047 tok/s (+10%) target.

- Performance report:
  `/cache/cch/qwen36-gdn-decode-megaop-20260920/service-candidate-v13-hybrid-v1/performance.screen.run1.json`.
- Report SHA256:
  `0ddd8ed4973ea5ead95d488944415eba51e4ec7797bcbd7ee4cc0cc584e95954`.

Decision: reject this implemented fusion boundary for service acceptance. Do
not spend LongBench-v2 or GSM8K time on a performance-negative candidate.
This is not a blanket rejection of every paper mechanism; it is evidence that
the exact boundary available after preserving native BF16 normalization does
not provide a useful end-to-end gain in this stack.

## Immediate next action

Checkpoint and push this negative result, release the owned service without
deleting its evidence, then open the next bounded Paper-to-Ascend loop for
DeltaLog. DeltaLog must first prove a distinct deferred-state materialization
seam in the real v0.23 Qwen3.6 decode path before implementation.
