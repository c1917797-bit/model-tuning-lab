# T19: exact-T16 GDN terminal opportunity budget

Status: closed as a standalone TPOT candidate; retained only as a possible
stack component. No operator was generated and no NPU was used in this round.

## Question

Can fusing the existing GDN terminal chain
`_layer_norm_fwd_1pass_kernel_npu -> M=1 K1536 MatmulAllReduce` close the
remaining T16 c1 TPOT gap by itself?

The required c1 saving inherited from the exact T16 decision is
`6.098464807517281 ms/token`. The model executes 48 GDN terminal projections
per decode token.

## Method

`scripts/analyze_qwen35_gdn_terminal_budget.py` reads the four original
msprof `op_summary` CSVs under
`/cache/austinov/qwen35-t16-profile-raw-20260910T111524Z`. For every decode
`M=1, K=1536, N=5120` MMAR core it:

1. requires a same-stream GDN norm ending no more than 25 us before the core;
2. pairs the latest enclosing `MatmulAllReduceMc2AicpuKernel` interval using
   the established T16 25-us tail-slack rule;
3. measures norm-start to the later of the MMAR core/AICPU end;
4. reports a deliberately optimistic zero-cost upper bound.

The 25-us norm-gap guard is covered by a direct-assertion synthetic test and
prevents a norm from a previous layer being mispaired.

## Result

Evidence:
`/cache/austinov/qwen35-t19-gdn-terminal-admission-20260911/`
`T19_GDN_TERMINAL_BUDGET.json`.

Report SHA256:
`1d75bce433e9ff5c4a6aff5e92a37117bfae006c9c1a79d7ed78adaa0f78c2cb`.

Each rank contains 6,720 M=1 K1536 MMAR calls. Exactly 5,040 per rank pair
with the preceding GDN norm; the remaining 1,680 are the non-GDN K1536 route.
Median norm-start-to-envelope-end values are:

| Rank | Paired GDN calls | Median |
|---:|---:|---:|
| 0 | 5,040 | 63.00 us |
| 1 | 5,040 | 63.25 us |
| 2 | 5,040 | 62.50 us |
| 3 | 5,040 | 63.50 us |

Using the maximum rank median and assuming the entire interval becomes free,
the upper bound is `63.5 us * 48 = 3.048 ms/token`, only
`49.9798%` of the required c1 saving.

## Decision

`reject-as-standalone-retain-as-stack-component`.

Do not build or service-test GDN terminal fusion as the sole T16 successor.
Even an impossible zero-cost implementation cannot meet the c1 TPOT gate.
This does not say the fusion has no value; it may be composed only after an
independently gated dense-tail mechanism supplies the other half of the
conservative budget.

Next admission must target the exact dense
`gate_up -> SwiGLU -> K4352 MMAR` critical-path union. The T16 paired profile
places that union at about 237 us/layer across 64 dense MLP layers. A
dense-only treatment needs approximately 95.29 us/layer saving (about
1.67x whole-chain speedup), or a smaller independently measured requirement
when stacked with a separately passing GDN terminal component. Never add
overlapping AICPU, producer, and AI-core durations.

The external `/cache/efim/merge_pr` BuildKit/CANN compilation remained live
during this no-device analysis. It was not stopped or modified. Device
performance work must wait for an interference-free resource gate.
