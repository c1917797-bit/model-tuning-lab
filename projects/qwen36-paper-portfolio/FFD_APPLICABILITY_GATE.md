# Faster Flash Decoding: Qwen3.6/Ascend applicability gate

Status: source-level investment gate only. No official-code checkout, Ascend
operator, NPU numerical run, paired throughput, or task-accuracy result exists.
Do not count this as a completed paper piercing. If formally started, the
paper-specific loop must be decided within 24 hours.

## Mechanism and provenance

- Paper: https://arxiv.org/html/2609.00097v1
- Author code: https://github.com/qluoluo/faster-flash-decoding
- Pinned author checkout (read-only):
  `/cache/cch/faster-flash-decoding-official-ca09458`, commit
  `ca09458ab1536328e5f46502b27891412733cd6d` (clean after clone).
  `quantized_cache.py` SHA256
  `02033493c18a3c00072b60c2e38234eacf932e6ea9d922d74c3600498fc27a89`;
  `paged_decode_kernel.py` SHA256
  `a9b634ab6b9000fa03bae98e3da2f044f1bada38dcd916e2eeda21628c8e4173`.
  The checkout is CUDA/Triton for Llama/HuggingFace; its README names RTX
  4090/H100 and CUDA 12.8. Source pin is not numerical author parity.
- The paper's distinctive decode mechanism is a 2-bit mid-rise K thumbnail,
  8-bit residual K, sink/local pseudo-max, and top-delta block threshold.
  The selected block uses quantized-scan scores plus residual refinement;
  V is fetched only when a block is retained. This is not Quest page min/max,
  SparQ query-coordinate Top-K, or v0.23 C8 static-per-channel INT8 K/V.
- Author `fast_decode_kernel.py` groups query heads sharing a KV head and
  loads V when **any** head in the group keeps the block. Its cache code
  quantizes full blocks and keeps the incomplete block unquantized. Preserve
  these semantics when adapting to vLLM's paged cache and request lifecycle.
- There is a source-versus-paper delta-unit question: the paper defines
  `score >= pseudo_max - delta` with natural-log softmax scores. Both observed
  author kernels multiply scores by `1/ln(2)` for `exp2`, then subtract the
  unconverted public `delta` parameter. If no other conversion intervenes,
  a code delta of 5 means a natural-log gap of `5*ln(2)`, not the paper's 5.
  The wrapper passes delta through unchanged. Treat this as a fidelity
  discrepancy to reproduce and report, not as proof of a paper error before
  an exact author-code parity check.

## Target fit and main falsification

The frozen Qwen3.6-27B TP4 trace has 16 full-attention layers, local Q/KV
head counts 6/1 and D=256; decode native FIA accounts for 27.40025% of
summed operator time at concurrency 16. That is not a measured critical-path
share. Even treating it optimistically as a serial share, +10% E2E would
require about 1.50x attention-local acceleration with no new overhead.
The official H100/4090 gains and Llama/Qwen2.5 accuracy do not establish
either gain or final LongBench-v2/GSM8K accuracy here.

The first real-model question is not whether a two-bit kernel is fast in
isolation. It is whether top-delta at useful settings keeps enough *exact*
attention mass while the six-head union still avoids enough V/K-residual
traffic to leave a credible >=1.50x native-attention opportunity. A head-wise
keep percentage alone cannot answer the union-I/O question.

The first probe uses an unpacked PyTorch replay of the released cache's Q2
formula on live BF16 K, not the released Triton kernel's FP16 query/scale
rounding, packing, FP8 residual refinement, or fused reduction. It returns
the unchanged native output. Its keep/mass numbers are an investment
diagnostic, not author-code parity or candidate numerical correctness. A
full-support math/native relative RMS above 0.005 fails that sample before
interpreting selection; this diagnostic ceiling is separate from final task
accuracy and does not license an approximate service implementation.

## Ordered, non-overwriting gates

1. Pin the official source and independently reproduce its 2-bit mid-rise
   quantization, block scaling, residual and top-delta decisions on identical
   small inputs. Audit the deployed paged FIA/cache ABI and existing CANN
   low-bit primitives before designing a new kernel.
2. Use an opt-in, output-preserving real-model probe on physical NPU4-7 at
   the frozen long-context decode shape. For each of all four TP ranks and
   representative full-attention layers, record delta=5 and 7 under both the
   paper's natural-log rule and the observed author's log2-unit rule:
   pseudo-max versus exact max, quantized false negatives, per-head and six-head-union
   kept block fractions, exact dense probability mass retained, and selected
   output error. Compare with exact-logit top-delta on the same Q/K/V. Read
   the full K/V only for diagnosis, outside selector-cost timing. One prompt
   is an operator-investment gate, never E2E task accuracy.
3. Stop this implementation architecture if the six-head union or NPU scan
   cost eliminates a credible >=1.50x attention-local route. Do not save it
   by reusing dense K/V in a sidecar and calling that a bandwidth win. A
   failed first prompt scopes only that prompt and implementation, not the
   whole paper.
4. If the mechanism survives, implement the missing cache write/seal,
   fused scan/refine and selected-V read as independently named, explicit
   opt-in plugin code. Reuse vLLM-Ascend and ops-transformer primitives
   where their ABI/semantics actually match; use cannbot only for the measured
   paper-specific gap. Validate batch 1/16, multiple decode steps, slot
   recycling, mixed prefill/decode, four ranks and NPUGraph before E2E.
5. Run profiler-off, same-stack dense/candidate fixed-1024 paired screens,
   report TTFT/TPOT and repeats. Only a plausible >=10% candidate proceeds
   to fresh, same-protocol max_tokens=2048 LongBench-v2/GSM8K. The user's
   <=1% final task-loss allowance is not an intermediate tensor tolerance;
   report both percentage-point and relative-percent deltas.

## First bounded loop and preserved failed request

Formal loop start: 2026-09-28 10:07 UTC; decide by 2026-09-29 10:07 UTC.
The pinned author's `quantize_symmetric_blocks` produced bitwise-equal
packed Q2 codes and equal per-block scales against an independent small BF16
formula check at [1,256,1,256], block size 128, seed 19. This is a CPU source
parity check, not NPU selector or kernel parity. The full author package
could not import in the current v0.23 image because its Llama model uses an
older `check_model_inputs` decorator signature; loading only the pinned
`quantized_cache.py` file allowed the bounded check. An earlier no-driver
import also failed on missing `libascend_hal.so`. Neither error is an FFD
numerical failure.

The non-privileged physical-NPU4 canary mapped host 4 to container 0,
reported one Ascend910B4 device and computed an NPU tensor sum of 16.0.
The one-shot diagnostic container `qwen36_ffd_realprobe_v1_20260928`
mapped only physical 4-7 to logical 0-3, loaded four TP workers, and reached
HTTP /health 200. All four physical cards showed the expected worker PID/HBM
binding; 0-3 remained untouched. The plugin installed against attention
source SHA256 `80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390`.

The single 20718-token request returned HTTP 500 before a valid FFD sample.
The probe's einsum emitted [head, token, block] where the later selector
expected [head, block, token], so a 161-versus-128 dimension mismatch
occurred at the first sampled decode layer. This is a probe layout bug,
**not** evidence that FFD is numerically wrong or slow. The failed container
exited and was retained, and NPU4-7 returned to idle-baseline HBM. Do not
rerun that exact code or overwrite this directory. Correct the einsum, add
an explicit shape invariant and a small-shape test, then launch one uniquely
named v2 result after fresh resource checks.

Retained external evidence root:
`/cache/cch/ffd-qwen36-realprobe-v1-20260928/`.
Admission SHA256:
`092f37d51d4376c2b3bf3080cc0b5ccc20aeeaa4e8bf53b2b81ae625b81a2d6a`.
TP0/1/2/3 audit SHA256:
`4af957cff6c283f839f591f98607bc588407cb037371793eb9eba1912fb8dd1d`,
`f9dab16e12abb26c3f95057dd0596d611348482620b7978b31bf1407c8c80637`,
`d64055fafd0a92cb71fdc4fda069b56fec78bb7001b6c10be2c1e5c8c9723cff`,
`5de7b30089d96c75e9e700adc864445d4f8d50fbe9e849d95c61eeffcfc85d1d`.

The first real-model selection gate, paired throughput, and task accuracy
remain unmeasured.
