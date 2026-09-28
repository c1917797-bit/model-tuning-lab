# Faster Flash Decoding: Qwen3.6/Ascend applicability gate

Status: source-level investment gate only. No official-code checkout, Ascend
operator, NPU numerical run, paired throughput, or task-accuracy result exists.
Do not count this as a completed paper piercing. If formally started, the
paper-specific loop must be decided within 24 hours.

## Mechanism and provenance

- Paper: https://arxiv.org/html/2609.00097v1
- Author code: https://github.com/qluoluo/faster-flash-decoding
- Observed author code on 2026-09-28 is CUDA/Triton for Llama/HuggingFace;
  the repository README names RTX 4090/H100 and CUDA 12.8. A target-host
  `git ls-remote` timed out, so the author commit is **not pinned yet**. Pin
  and checksum the official sources before author-parity or NPU claims.
- The paper's distinctive decode mechanism is a 2-bit mid-rise K thumbnail,
  8-bit residual K, sink/local pseudo-max, and top-delta block threshold.
  The selected block uses quantized-scan scores plus residual refinement;
  V is fetched only when a block is retained. This is not Quest page min/max,
  SparQ query-coordinate Top-K, or v0.23 C8 static-per-channel INT8 K/V.
- Author `fast_decode_kernel.py` groups query heads sharing a KV head and
  loads V when **any** head in the group keeps the block. Its cache code
  quantizes full blocks and keeps the incomplete block unquantized. Preserve
  these semantics when adapting to vLLM's paged cache and request lifecycle.

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

## Ordered, non-overwriting gates

1. Pin the official source and independently reproduce its 2-bit mid-rise
   quantization, block scaling, residual and top-delta decisions on identical
   small inputs. Audit the deployed paged FIA/cache ABI and existing CANN
   low-bit primitives before designing a new kernel.
2. Use an opt-in, output-preserving real-model probe on physical NPU4-7 at
   the frozen long-context decode shape. For each of all four TP ranks and
   representative full-attention layers, record delta=5 and 7: pseudo-max
   versus exact max, quantized false negatives, per-head and six-head-union
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

The first two gates are not yet run. The next action is official-source pin
and a bounded real-model, output-preserving NPU probe, not a CUDA kernel port
or a claim that sparse attention already benefits this Ascend workload.
