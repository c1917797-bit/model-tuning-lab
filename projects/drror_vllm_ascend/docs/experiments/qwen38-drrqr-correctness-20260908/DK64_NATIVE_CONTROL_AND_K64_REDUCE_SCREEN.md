# Dk64 native control and K64 reduction screen

Status: the exact-path recurrent control passed its target-NPU numerical gate.
The isolated K64 reduction replacement also passed numerical parity but was
rejected by its graph-path performance screen. Neither result is endpoint or
accuracy evidence.

## Numerical evidence

- Shape: TP4-local H_QK=4, H_V=12, D_V=128, D_K=64.
- State and Q/K/V/beta: BF16; g: FP32.
- Cases: batch 1 and 16, eight changing-input and state-index steps.
- Comparisons: frozen native eager versus plugin eager and plugin NPUGraph.
- Criterion: bitwise output and full mutable-state equality, finite values,
  intact guards, untouched slots, stable metadata and storage pointers.
- Control report SHA256:
  `9b843c5cf86625ce265f4a5fc51a33447280d616bf5da507ef377285d48fe04c`.
- K64 candidate report SHA256:
  `86ae8e0c26e9c4510e49c92511b55e70950998eb746cef4525fff1effe9d2101`.
- Candidate opapi SHA256:
  `242a8bd802b4a7ed0e957816a7c315bb5c688e5a1ab65b97bddfb13a145c4ebe`.

This proves only the tested operator arithmetic/state/graph behavior on
physical NPU4. It does not prove vLLM cache integration, endpoint throughput,
task accuracy or cross-environment speedup.

## Order-balanced micro screen

Six fresh processes were run in ABCCBA order: native, exact plugin control,
K64 candidate, K64 candidate, exact plugin control, native. Each case used 20
warmups, seven blocks and 100 calls per block. Medians below pool the 14 device
event samples for each two-run implementation.

| Batch | Path | Control ms | Candidate ms | Candidate change |
|---:|---|---:|---:|---:|
| 1 | eager | 0.164594 | 0.155658 | -5.429347% |
| 16 | eager | 0.164464 | 0.159654 | -2.924780% |
| 1 | NPUGraph replay | 0.014125 | 0.014431 | +2.164909% |
| 16 | NPUGraph replay | 0.041170 | 0.044512 | +8.116835% |

Positive change means slower. The graph path is the admission signal for the
intended serving route, so this candidate is rejected despite its eager-only
improvement. Raw report SHA256 values:

- 01 native: `dd4198c0ecd7ba18ef76d86d3f3cbfa7e2355ee74dd018b45842bb71152c3b1d`
- 02 control: `e67d4e38d680a934f103ecacfea0a165c6e3ebed0d8cfeb8bd12ce6493ecc64f`
- 03 candidate: `b874efc9d83ffd72a524680ea872d72771ffab743708db96c6b1c82c5807a2c8`
- 04 candidate: `91f8c2783adc3180f4702b6e8fc0611b41843de2007e47a8966c1585b9f7e262`
- 05 control: `6a09cf48d1e7b11cbd3a39f9f20b7a8e61919a842870fc0653d5a6980a9a4df4`
- 06 native: `28b8401415ce5118e1973afc08253e73d7be26c4b7c81bfec4d631a2a6704e01`

## Decision

Do not integrate the K64 WholeReduceSum replacement or run a model endpoint
for it. The next bounded DRRQR-specific direction is to audit and, only if
semantically feasible, fuse the real Ascend decode Q/K normalization with the
recurrent update to remove materialization and launch overhead. The unchanged
native composition remains the portability fallback.
