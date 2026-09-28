# Faster Flash Decoding: Qwen3.6/Ascend applicability gate

Status: official-source and output-preserving real-Q/K/V NPU investment gate.
No Ascend FFD operator, selected-output serving run, paired throughput, or
task-accuracy result exists. Do not count this as a completed paper piercing.
The formally started paper-specific loop must be decided within 24 hours.

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
  V is fetched only when a block is retained by any query head in its KV group.
  The released paged wrapper defaults `SBS=BS=128` unless explicitly
  overridden; the inner subblock loop is not evidence of 16-token selection.
  This is not Quest page min/max,
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

## Second real-model request and selector-semantics correction

The shape-fixed v2 probe added a unit test for `[head, block, token]` scan
layout. The owned `qwen36_ffd_realprobe_v2_20260928` service again mapped only
physical NPU4-7 to logical 0-3. Its four worker audits bound the live v0.23
attention source to SHA256
`80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390`.
One immutable, deliberately repetitive 20,718-input/4-output request returned
HTTP 200. All four ranks sampled layers 3, 31, and 63 once: 12 real decode
Q/K/V samples, each with 161 full 128-token blocks and a 111-token tail.
The full-support BF16-rounded math/native relative RMS was 0.000188-0.000873,
below the predeclared 0.005 diagnostic ceiling.

Across these 12 samples the six-head *union* full-block keep fractions were:

| Threshold interpretation | delta=5 | delta=7 |
| --- | ---: | ---: |
| Released author log2 units | 0.919255 | 0.995342 |
| Paper natural-log units | 0.996894 | 1.000000 |

These are one-prompt traffic-investment proxies, not measured NPU bandwidth,
critical-path latency, task accuracy, or speedup. The v2 audit also computed
selected-output error using each query head's private keep mask. Source review
after the run showed that the released paged kernel's `need_keep` is the OR
over the KV group's heads, followed by residual/V loads and online-softmax
updates for **all** heads. Thus v2's `selected_math_vs_native_*` fields are
only a hypothetical per-head-implementation diagnostic; they do **not**
measure the released kernel's group-union output error. Do not use those fields
as a correctness no-go. The kernel supports a subblock loop, but its released
wrapper defaults `SBS=BS`; no 16-token claim is justified by that loop.

The next unique v3 probe must calculate the union token mask, exact dense mass
retained under that mask, and BF16-rounded union-support output versus native
on the same live Q/K/V. Keep the per-head diagnostic separately labeled. It
still must not replace the dense output or become a throughput claim. Only
after that correction can the one-prompt operator-investment gate be decided.

The v2 service was stopped without deletion and NPU4-7 returned to idle HBM
with no process. External immutable artifacts:
`/cache/cch/ffd-qwen36-realprobe-v2-20260928/`.
Admission SHA256:
`7cf2e2412e21fec02da74d33c9fe92217f5dc2247e392d73065630c9130747f4`.
Request SHA256:
`030f639d22331d240d20b747f9832b854c1a80cc6f2cc20904a20b49f5130395`.
TP0/1/2/3 audit SHA256:
`5e24e202fb5bd1bf3fd83ad46ee04b7af4966e873137f4d141a641d94d652ab2`,
`87d0f82c16f7e0591ecd53cc45ffeb98c3ab0eff4ad10a71a0a9147f9457b91d`,
`c9863f1d7e96590bdaaa241ceb7cb1a394b76e6ac77da0d19156d081b6cff4d9`,
`fd9c4c9b55e406060b95ed3e6a631226c670142084864a711eae87f7350aedae`.

## Third real-model request: official KV-group union scope

The distinct v3 probe kept the same 20,718 input token IDs, native dense
return path, model/image/TP4/NPU4-7 mapping and three sampled layers. Its
unit test freezes the difference between a private query-head mask and the
author's KV-group OR mask. All four worker hooks installed, the single request
returned HTTP 200 with four output tokens, and 12 real decode samples were
recorded. Full-support BF16-rounded math/native relative RMS was at most
0.000888, again below the frozen 0.005 *oracle* ceiling. The v3 mask model
still uses exact K/V for retained blocks, so it is an optimistic selector
diagnostic, not Q2+FP8-kernel numerical parity.

Across the 12 samples (means unless noted):

| Threshold | Union blocks kept | Exact dense mass kept across heads | Union output/native relative RMS |
| --- | ---: | ---: | ---: |
| author log2, delta=5 | 0.940994 | 0.987379 (min 0.924660) | 0.002081 (max 0.007216) |
| author log2, delta=7 | 0.997930 | 0.999748 (min 0.996220) | 0.000530 (max 0.000975) |
| paper natural, delta=5 | 0.998447 | 0.999846 (min 0.997851) | 0.000522 (max 0.000888) |
| paper natural, delta=7 | 1.000000 | 1.000000 | 0.000503 (max 0.000888) |

These intermediate output differences are **not** LongBench-v2/GSM8K accuracy
deltas or a candidate correctness pass. The source-default delta=5 leaves
only about 5.9% of full blocks without residual-K/V access in this prompt.
Under an intentionally optimistic byte-only model (native BF16 K+V:
1024 bytes/token; FFD Q2 K: 64 bytes/token always; FP8 residual K plus BF16
V: 768 bytes/token on kept blocks), the observed 0.940994 union fraction
implies a 0.7682 traffic ratio and at most 1.30x attention-local speed from
those bytes alone. The diagnostic 27.40025% attention operator-time share
would require about 1.50x local speed for +10% E2E under an equally
optimistic serial Amdahl model, or an ideal union keep fraction <=0.8076
with zero new overhead. Neither model is a measured critical path or a proof
that a fused Ascend kernel cannot improve other costs.

This evidence motivates one bounded delta=3/4 sweep on the *same* real-model
geometry to determine whether a more aggressive threshold offers a useful
union-I/O versus exact-mass/output Pareto point. It does not authorize
claiming a gain, relaxing a numerical gate, or calling the paper invalid
based on one repetitive prompt. If no plausible point remains, close this
implementation/workload route within the 24-hour deadline and move on.

The v3 service was stopped without deletion; NPU4-7 returned to idle HBM
with no process. Immutable artifacts:
`/cache/cch/ffd-qwen36-realprobe-v3-20260928/`.
Admission SHA256
`698d5b03d2030cbb5266537a3b3220b17b00a5e87eb5084e4e58a579a11c1c5b`;
request SHA256
`f579c512bf0abe7a64d48340436cfb9ee7bd76fe29200bec989c037bc25bda97`.
TP0/1/2/3 audit SHA256:
`610854f49df91c03a28e463b25f71770cc1ee5393bf5dc67b1798ce5753bd233`,
`1e73f02f14d05e867852db13a0224e7d5f94ca6e75e56ce8e495c56728b55121`,
`d8b6ddba39bf1fe92210df0ed22fe31c8c51237157d7acb5b86b2e3600832e34`,
`e9685c6f3f2e3764da6d08d200255b9f38e9c7ebb6de06f587f8f9365dde0f19`.

Paired throughput, TTFT/TPOT, and task accuracy remain unmeasured.

## Fourth real-model request: threshold Pareto check

The unique v4 service mapped only physical NPU4-7 to logical 0-3 and reached
HTTP /health 200. Four live worker hooks reported the same pinned Ascend
attention-source SHA256 as v3. A single request with the same 20,718 input
token IDs returned HTTP 200 and four output tokens. Twelve real decode
Q/K/V samples covered layers 3, 31, and 63 on all four TP ranks; there were
no sample failures. The full-support BF16-rounded math/native relative RMS
was at most 0.000969, below the frozen 0.005 oracle ceiling.

The table reports 12-sample means, with 72 query-head probability-mass
observations. `RMS max` is the largest *intermediate attention output*
relative RMS versus the native path, **not** an E2E task-accuracy loss.

| Threshold | KV-group union blocks kept | Exact dense mass kept (minimum) | Output/native RMS max |
| --- | ---: | ---: | ---: |
| author log2, delta=3 | 0.746377 | 0.886294 (0.329833) | 0.126387 |
| author log2, delta=4 | 0.842133 | 0.943805 (0.673891) | 0.032415 |
| author log2, delta=5 | 0.930124 | 0.984780 (0.884318) | 0.010309 |
| author log2, delta=7 | 0.996377 | 0.999556 (0.994475) | 0.001231 |
| paper natural, delta=3 | 0.877329 | 0.961120 (0.782073) | 0.021170 |
| paper natural, delta=4 | 0.966356 | 0.994272 (0.937190) | 0.005850 |
| paper natural, delta=5 | 0.997930 | 0.999749 (0.996498) | 0.001217 |
| paper natural, delta=7 | 1.000000 | 1.000000 (1.000000) | 0.000969 |

The aggressive author-log2 delta=3 reaches the **optimistic** whole-block
traffic-only requirement of union fraction <=0.8076, but loses substantial
dense probability mass and has large intermediate output drift. Delta=4
has less drift but misses that optimistic traffic bound even before new
kernel overhead. No tested 128-token selection point on this one prompt
justifies building the compressed Ascend kernel or claiming a +10% E2E gain.
This does not reject the paper as a whole: the released kernel exposes an
`SBS` subblock parameter, whereas its public wrapper defaults `SBS=BS=128`.
The next bounded, algorithm-specific check is source-audited 16/32/64-token
subblock selection at safer thresholds on live Q/K/V, including the extra
subblock-loop cost in any later performance hypothesis. If no plausible
quality/traffic point survives, close this implementation/workload route
within the pre-registered 24-hour FFD gate (2026-09-29 10:07 UTC). Do not
mistake the user's permitted 1% *E2E GSM8K* loss for an intermediate RMS
threshold; only final paired task tests can determine that loss.

The v4 container was stopped, not deleted. Host NPU4-7 returned to
2868-2872 MB idle-baseline HBM with no running process; NPU0-3 were not
used. Immutable evidence root:
`/cache/cch/ffd-qwen36-realprobe-v4-20260928/`.
Admission SHA256
`1d65be4b918f6dcb5f2046b5eb77266a370fe97c8187021588fb196e08d4fca5`;
request SHA256
`acd89137abb21bbf067242876840d8f41773183cc31c4da19a8e384277c6e8c3`.
TP0/1/2/3 audit SHA256:
`1c67095f287de0932e3f6d5e6a7ee2a69f1e8054784f30ee2a3859363bb4b0f0`,
`86774e1caa635b833aa9cb0cfefc1772d69d610ee331d6271fd308291f048ee5`,
`c6cebbd399b852357966ad25e24581c9876a857bae721b49213e5c8d10729534`,
`134aebe01a607c9c3b3c05f604d81916e14b004855d5df26b0629c4bea52ddb6`.

Paired throughput, TTFT/TPOT, and LongBench-v2/GSM8K accuracy remain
unmeasured for FFD. This v4 experiment did not enable a candidate kernel.
