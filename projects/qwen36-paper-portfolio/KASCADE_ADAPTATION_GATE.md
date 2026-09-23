# Kascade: Qwen3.6 Ascend cross-layer mechanism gate

Started 2026-09-23 16:15 UTC; decide or pivot within 24 hours. The
experiment record is `.agents/experiments/exp-20260923-qwen36-kascade-cross-layer.yaml`.

## Source and scope

Paper: https://arxiv.org/html/2512.16391v2. Official MIT source:
`microsoft/kascade` branch `vllm_integration` at
`de249edf9f2b10f436e2bf6d9e70e29247a671c9`. The source has
`src/vllm_backends/kascade_attn.py` and paged decode recompute/reuse kernels.
The backend says `supported_dtypes=[torch.float16]` and requires an NVIDIA
device capability; those kernels are not drop-in BF16 Ascend operators.

Kascade's relevant mechanism is exact full QK/softmax in selected anchor
layers, Top-K selection on probabilities pooled over the GQA query heads for
each KV head, then reuse of selected token indices in subsequent layers.
The official backend stores `topk_indices` as `[batch, num_kv_heads, topk]`,
loads a model-specific head mapping, and uses dense prefill in its vLLM path.
Its published 10% and 20% results were not measured on this checkpoint or
the current Ascend stack.

The installed Qwen3.6-27B has full-attention layers every fourth block and
TP4 places one KV head with six Q heads on each worker. Thus the official
per-KV-head selection is locally representable, but its cross-KV-head remap
would require communication across ranks. The first probe tests same-head
reuse within each rank, not an unverified global remap; this distinction is
critical to interpretation.

The existing four-rank decode profile identifies native FIA as 27.40025%
of summed operator time, not a critical-path or end-to-end bound. A new
custom CANN operator is justified only if the real-model cross-layer support
holds, the native paged ABI cannot express the needed token indices, and
the algorithm-specific gap can plausibly reach the 10% E2E objective.

The first NPU test is non-mutating: compare anchor/reuse probability mass
and selected output error at 10/20/30% token budgets on real decode Q/K/V
from pairs 3->7, 31->35 and 59->63. Same-layer KV-pooled and per-Q-head
exact Top-K provide upper bounds. Full-support FP32 math must first agree
with native BF16 dense FIA. A useful result advances to selected-token
operator ABI, eager/graph/multistep correctness and matched dense E2E;
an unfavorable result is scoped to the tested pairs, prompt and budget.

No Kascade performance, TTFT/TPOT or task-accuracy result exists yet.

## First live NPU diagnostic: scoped partial evidence

The first non-mutating request on physical NPU4-7 used one 20,718-token
repetitive prompt in the exact v0.23/CANN 9.1 BF16 TP4 container. Worker
dispatch and the attention source hash were proven. It produced 22 valid
layer/rank samples and two failure events; the service request did **not**
complete. The first two pairs completed on all four ranks. At the 20%
token budget, cross-layer mass was min/mean 20.735%/73.577% for 3->7,
versus 75.078%/94.605% for 31->35. Same-layer KV-pooled Top-K at the
target layers retained 62.449%/92.342% and 83.360%/96.916%, respectively.
The large early-layer drop shows that blindly reusing indices in every
successive attention layer is not suitable for this prompt, while the
mid-layer transfer merits a broader adaptive-anchor check.

At rank1 layer59, the full-support FP32 mathematical oracle differed from
native BF16 FIA by max-abs 0.120853, above the predeclared 0.1 gate; it
was not used to interpret sparsity. Layer63 then lacked that anchor and
failed. The threshold was not relaxed and this is **not** a Kascade quality
failure at that pair. The owned container was stopped but retained; its
request process exited 137 from that stop, not an observed OOM diagnosis.
NPU4-7 returned to process-free baseline. No precision or E2E claim follows.

Immutable evidence outside Git:

- `/cache/cch/kascade-qwen36-crosslayer-v1/audit.jsonl` SHA256
  `85935543b8004fce5f426ece1f414cbff1eb62f9618766abc623f493494ec811`.
- `/cache/cch/kascade-qwen36-crosslayer-v1/admission.json` SHA256
  `b61631654d9f1542513f4cc71ea047ac95dee3cfa464ccb378568f9f115d6c2d`.

The next *distinct* experiment is an all-full-attention-layer transition
map with a new immutable root. It will skip only a transition whose
full-support oracle fails and record the skip explicitly; it will not weaken
the 0.1 gate. The aim is to determine whether an adaptive anchor/reuse plan
can touch enough actual layers to justify a targeted Ascend operator.

## Second live NPU diagnostic: adjacent-layer map

The v2 probe used the same 20,718 prompt-token IDs and successfully returned
four native dense output tokens (HTTP 200). It recorded 63 valid samples
over 16 full-attention layers × four TP ranks. Rank1 layer59 again missed
the unchanged 0.1 full-support math/native gate (max-abs 0.112698); the
probe explicitly excluded that layer and its missing 59->63 transfer while
the service stayed healthy. All other valid samples had full-support
max-abs ≤0.06246.

The adjacent transfer map is heterogeneous. At 20% selected tokens,
3->7 retained min/mean exact mass 20.20%/73.43%, 31->35 retained
74.49%/94.36%, and 47->51 retained 57.94%/77.69%. The largest selected
output max-abs discrepancy at 39->43 was 3.17, far above ordinary native
vs full-math differences. These are intermediate diagnostics, not the user's
final task-accuracy percentage-point loss. Even a favorable middle pair
does not by itself cover enough layers to establish ≥10% E2E benefit.

The owned v2 container was stopped and retained after the request. Evidence:

- `/cache/cch/kascade-qwen36-crosslayer-v2/audit.jsonl` SHA256
  `35c2b8825a4d50c2cdce0e85cd384a7774b208c42f3f4adcfc10f87d417f01fb`.
- `/cache/cch/kascade-qwen36-crosslayer-v2/admission.json` SHA256
  `307b2b3818598a7dfaf4ffab5f7171ef370cebd90fe831f78ad919324354e97e`.
- `/cache/cch/kascade-qwen36-crosslayer-v2/request-summary.json` SHA256
  `7753ad81d7cdb9e8b0f39ae953c6fe7022c4619ade5cee47ee1aa61a35430cfd`.

The next distinct check will use all earlier local KV-head anchor selections
for each target layer and choose the best on this same token. This is an
optimistic *oracle* for the paper's dev-set anchor planning, not an online
free selection mechanism. If even it cannot support enough layers at useful
budgets, a new Ascend token-sparse kernel would be a poor investment.

## Third live NPU diagnostic: optimistic local-anchor bound and scoped decision

V3 completed a native dense request (HTTP 200, 20,718 prompt tokens and four
output tokens) on physical NPU4–7 with the same token IDs as v2. It tested
every earlier same-rank full-attention layer as an anchor for each target and
chose the best *after seeing this token*. This is more optimistic than a
deployable dev-set-fixed anchor plan, but it does not test the official
cross-rank KV-head remap. There were 63 valid layer/rank samples covering
354 local Q-head cases. Rank1 layer59 again failed the unchanged full-support
math/native gate: max-abs 0.124748 > 0.1. That sample was excluded, not
reclassified as a sparse-method failure.

At 10% selected tokens, the best-previous-anchor mass was min/mean
4.99%/72.30%; at 20%, 20.93%/86.30%; at 30%, 39.69%/91.73%.
The largest selected-output max-abs discrepancies from native dense were
4.31, 3.51 and 2.52, respectively. These are intermediate numerical
diagnostics, **not** LongBench-v2 or GSM8K accuracy loss. The probe returned
native dense output unchanged; there is no candidate throughput, TTFT, TPOT
or task-accuracy measurement.

Decision: **no-go for commissioning a new CANN token-sparse operator for this
Qwen3.6 BF16 TP4 same-rank local-anchor path at the tested budgets and
20K repetitive prompt**. Even the hindsight anchor upper bound leaves
low-mass query heads and large selected-output errors. This does not reject
Kascade as a whole, other workloads/budgets, cross-rank remapping, or future
Ascend implementations. It means the current algorithm-specific operator
investment lacks a credible numerical basis; profiling alone would not
rescue it. The owned v3 container was stopped and retained, and NPU4–7
returned to process-free idle baseline.

Immutable evidence outside Git:

- `/cache/cch/kascade-qwen36-crosslayer-v3/audit.jsonl` SHA256
  `d71e06e2b91a5bb60bac6a3f7d9c68aa9154cc06d81e33d81cb3e1074e9d63b0`.
- `/cache/cch/kascade-qwen36-crosslayer-v3/admission.json` SHA256
  `e644f6d99c2478aeda531992af1b953ce6f3f81ac3f01ee87ea5cf7617e078df`.
- `/cache/cch/kascade-qwen36-crosslayer-v3/request-summary.json` SHA256
  `a72280cc4b9ff0731291fcb69c20c4bc262b6f117fe02071f052bca5807df93a`.
