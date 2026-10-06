# KIVI-4 to Ascend: bounded real-model investment gate

Formal loop start: 2026-09-28 15:03 UTC; decide this first KIVI loop by
2026-09-29 15:03 UTC. This is a new paper-specific loop, not a continuation
of the closed FFD or Ada-KV implementations.

## Provenance and mechanism

The [KIVI paper](https://arxiv.org/html/2402.02750) and
[MIT author code](https://github.com/jy-yuan/KIVI) describe asymmetric low-bit
KV quantization with Key quantized per channel over token groups and Value
quantized per token over channel groups. The source HEAD observed at loop
start is `876b4d2d08e3b1d5f70d0969c299d8c7c42ddfb6`; the pinned
`quant/new_pack.py` and `models/llama_kivi.py` are the equation/lifecycle
references. This target uses their supported 4-bit setting, group size 32,
and residual length 128. The author code targets Llama/Mistral and CUDA,
not Qwen3.6-27B/vLLM-Ascend; use an independently implemented plugin.

For Key, quantize complete 128-token groups and leave the current modulo-128
tail unquantized. For Value, retain the most recent 128 tokens unquantized;
its 32-element quantization groups run along channels within each older
token. The group min/max equation uses `(max-min)/15` and round/clamp codes.
Constant groups use a scale of one to avoid NaNs while reconstructing their
constant exactly; the probe reports their count. Its unpacked math is not
bitwise CUDA-kernel parity.

The deployed `torch_npu.npu_fused_infer_attention_score` wrapper exposes
INT4 K/V, `key_antiquant_mode=0`, `value_antiquant_mode=1`, separate scales
and optional softmax LSE. Those modes have *one* Key channel scale and a
whole-head Value scale per token; they cannot directly express KIVI's
32-token Key-group and 32-channel Value-group scales. The separate BF16
residual windows add another lifecycle seam. Therefore a direct native call
is not a faithful KIVI port. We test its static-scale **derivative** only as
an explicit comparator, never under the paper's name.

## Frozen opportunity and one-shot probe

The prior physical-NPU4-7 dense profile at TP4, batch 16 and long context
shows local Q/KV heads 6/1, D=256, with FIA 27.40025% of summed decode
operator time. A representative rank-0 FIA call was roughly 0.75 ms and
MTE2-heavy. These are diagnostic signs of KV traffic, not a measured
critical-path share or KIVI end-to-end gain. The frozen target remains
same-stack dense/candidate, fixed 1024 output tokens, at least +10% output
throughput, separately reported TTFT/TPOT, and final paired task quality.

The opt-in plugin reads actual paged Q/K/V after the unchanged native decode
on one 20,718-token repetitive input, sampled at full-attention layers
3/31/63 on all four TP workers. It returns the native output unchanged.
For every sample it records: full-support FP32/BF16-rounded math versus
native; author-equation KIVI-4 output; and native-mode-compatible static
derivative output. The only hard diagnostic gate is finite tensors and
full-support math/native relative RMS <=0.005. The quantized-output errors
are investment data, **not** an E2E task-accuracy verdict or a native INT4
kernel pass. The small-shape formula tests passed before this one-shot load.

If the derivative is much worse than author KIVI, do not relabel it as KIVI
or build service integration on that shortcut. If author KIVI is numerically
promising, the next step is a plugin-owned grouped-scale and residual-tail
implementation using existing CANN/ops-transformer primitives where their
semantics match. Before any service speed claim, require physical-NPU
quantization/attention and graph correctness, then a profiler-off matched
dense/candidate fixed-1024 screen. A tensor microbenchmark alone is never
the +10% result. Stop this first loop at its deadline with an explicit
scope if those gates cannot be reached; do not fabricate success.

Immutable result root for the first request:
`/cache/cch/kivi-qwen36-realprobe-v1-20260928/`. Only physical NPU4-7
are mapped into its non-privileged container as logical 0-3. The result
directory and container name were absent before launch. This paragraph is
pre-registration, not a claim that the request or output has passed.

## First-loop result and scoped decision (audited 2026-10-06)

The one-shot output-preserving request completed with HTTP 200: 20,718 prompt
tokens and four generated tokens. All four TP ranks recorded the three planned
full-attention layers, for 12 real-Q/K/V decode samples. The uncompressed
FP32/BF16-rounded full-support oracle differed from native FIA by
0.000369–0.001168 relative RMS, below the predeclared 0.005 diagnostic gate.
No sample reported a non-finite value or a probe failure.

Across those same 12 samples, the *unpacked FP32-scale KIVI-4 equation*
differed from native output by 0.011307–0.054832 relative RMS. The static
FIA-mode derivative differed by 0.034362–0.120483 relative RMS and was worse
than the grouped equation in every sample. These are single-layer output
measurements, **not** a LongBench-v2/GSM8K accuracy loss, deployed INT4-cache
numerical result, or throughput measurement. The probe's scale arithmetic is
FP32 and does not establish bitwise parity with the author's dtype and packing.

Decision at the pre-registered one-day gate: **no-go for substituting the
existing static FIA antiquant modes for KIVI; inconclusive for a faithful
grouped-scale KIVI implementation.** The first loop ended without packed K/V
storage, residual-tail cache lifecycle, NPUGraph correctness, matched dense
end-to-end performance, or task accuracy. Its deadline was 2026-09-29 15:03
UTC and has passed; do not silently extend or rerun this first probe. Preserve
the files and select the next paper-specific route using a fresh opportunity
gate. Any later KIVI attempt needs a separately bounded hypothesis that
isolates K-only/V-only and author-dtype arithmetic before commissioning a
grouped-scale attention operator; this first loop neither proves nor disproves
the paper's final task quality or serving benefit.

Immutable evidence (SHA256):

- `request-summary.json`: `4cd2aee0dde32b8c30de2854a01a3a36c373c92044556e99c03574d4e8b78b1f`
- TP rank 0 `audit.jsonl.126.jsonl`: `92b213e3acdbaf13f8ac85745088705409281120538909bdafbe974a3b395469`
- TP rank 1 `audit.jsonl.127.jsonl`: `bdf552de48f48114bb01f4d591cc2c6fd272dbeeb98b2e10bdfb56bcb2495ea1`
- TP rank 2 `audit.jsonl.128.jsonl`: `43d62918be02647bd898c827120fc946b02ba1bdfaa183f44ad8d0bc670edfd6`
- TP rank 3 `audit.jsonl.129.jsonl`: `89a10b40fd1fd533221970dc0f43c5f709d35bd101c3e96b50a6a382ea6adf56`

All paths above are under
`/cache/cch/kivi-qwen36-realprobe-v1-20260928/`; raw outputs stay outside Git.
