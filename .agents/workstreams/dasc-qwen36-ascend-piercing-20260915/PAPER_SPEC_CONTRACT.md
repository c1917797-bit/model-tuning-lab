# DASC paper-spec contract for the Ascend piercing

Status date: 2026-09-16

Authoritative paper: arXiv:2608.30386v1, especially Sections 3.3, 4.1-4.3,
5.1, and Appendices B-C.

This contract separates paper-specified behavior from the independent
vLLM-Ascend implementation. The paper page does not link first-party source
code, so passing this contract establishes specification parity only; it does
not establish official-code parity.

## Algorithm identity

For Qwen GDN, the persistent temporal-state unit is one complete GDN head.
Using representative gate input `a=-0.3` and `epsilon=1e-3`, the static
log-decay and retention horizon are

```text
g = -exp(A_log) * softplus(a + dt_bias)
H_s = log(epsilon) / g
```

A head is retained when `H_s > W_max`. The mask is derived from weights only;
runtime prompts do not construct or calibrate it. Full-attention KV is never
compressed by DASC.

On cache-hit Load, DASC-NR restores retained heads and initializes omitted
heads to zero. The zero-fill is a Load-boundary operation, not a per-token or
per-forward reset. Omitted heads then evolve normally for the lifetime of the
active request. DASC-WR is a separate policy that replays a bounded suffix; it
must remain labeled unimplemented until suffix inputs, replay length, local
head copyback, and added latency are all verified.

## Dense-identity gate

The paper's dense denominator uses the same recurrent-state checkpoint path
with `W_max=0`, retaining the complete mixed-precision checkpoint. Therefore
two controls answer different questions:

1. A plugin-disabled dense service proves the underlying model, prefix cache,
   and Ascend runtime can be deterministic.
2. An all-head DASC-path control proves the adapted checkpoint Store/Load path
   is an identity transformation when compression is disabled.

The first control cannot substitute for the second. Performance, capacity, or
quality experiments are inadmissible until the all-head control produces the
same first resumed token and stable repeated continuation as the dense path.
This is why the mixed-cache lifecycle correction following v12r17 remains on
the critical path even though it does not itself compress state.

## Physical layout and accounting

The paper's ragged GDN temporal pool has logical shape

```text
[slots, sum(retained_heads_per_layer), d_v, d_k]
```

with per-layer offsets. A padded or per-layer physical adaptation is allowed
only when its additional bytes are reported as an adaptation tax and are not
described as paper-equivalent ragged storage.

Capacity accounting must include both FP32 temporal state and the unchanged
BF16 convolution state. For TP serving, usable checkpoint capacity is limited
by the largest per-rank payload, not by the mean or aggregate compression
ratio. Full-attention KV must remain byte-for-byte and allocation-for-allocation
unchanged across arms.

The current TP4 MAX-padded layout therefore remains an Ascend derivative. Its
measured W64 counts (1728 threshold-retained heads versus 2084 physically
stored heads) are evidence of a capacity tax, not evidence against DASC. The
paper-equivalent variable-split Store/Load and the whole-GQA-group permutation
bound remain distinct successor designs.

## Performance contract

DASC is a persistent prefix-checkpoint capacity mechanism, not a steady-state
decode-compute optimization. A no-reuse decode benchmark cannot validate or
reject it.

A formal performance comparison must hold constant model, weights, tokenizer,
prompt IDs, request order, seeds, TP degree, software image, compilation mode,
full-attention KV allocation, and total recurrent-state HBM budget. Dense and
candidate must use the same checkpoint lifecycle and differ only in the DASC
selection/storage policy.

The workload must cross the dense checkpoint-capacity boundary, then replay
prefixes with measured cache-hit tokens. Report at least TTFT and input
throughput; report TPOT separately to reveal any unintended decode regression.
The paper's Hopper/SGLang results are motivation, not an Ascend performance
baseline and not a transferable percentage target.

## Quality contract

Correctness is layered:

1. all-head identity on the first resumed token and repeated continuation;
2. finite, stable multi-step recurrent state under real Ascend execution;
3. compressed DASC-NR cache-hit behavior on controlled long-prefix probes;
4. paired end-to-end quality with the cache-hit path actually exercised.

Single-needle retrieval is insufficient because the paper reports it can
saturate even when recurrent checkpoints are heavily ablated. The final local
gate must use the predeclared paired end-to-end suite and tolerance, preserve
raw generations and cache-hit telemetry, and must not infer task quality from
an intermediate tensor-error threshold.

## Current decision boundary

The next NPU experiment remains the one-time all-head mixed-lifecycle control.
It tests dense identity of the adapted Store/Load path; it does not test DASC
compression benefit. If it passes, reintroduce the physical bridge with all
heads before W64 pruning. If it fails, localize mixed-group checkpoint
materialization and aligned boundary handling before changing the selector,
operator, benchmark, or quality protocol.
