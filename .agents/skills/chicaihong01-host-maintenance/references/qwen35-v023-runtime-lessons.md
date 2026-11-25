# Qwen3.5 v0.23 runtime lessons

Read this reference when maintaining Qwen3.x BF16 serving work that uses the
official vLLM-Ascend v0.23 runtime family. The September delivery campaign and
the November 25 projection and host recovery checks provide evidence for
candidate admission, diagnosis, and reuse. Read live resource state and final
acceptance from the active workstream.

## What worked

- A read-only, removable Python monkeypatch in the unchanged official image
  can be proven active in every TP worker without rebuilding the image or
  overlaying framework source.
- The bounded-prefill treatment completed 32/32 requests with zero errors and
  natural EOS. Against its fresh identity-matched control, c1 TTFT P95 fell
  from 6310.576 ms to 808.224 ms, an 87.193% reduction. Retain this only as a
  TTFT component: TPOT improved just 2.835%, below the 20% gate.
- A separate stabilization pass exposed unseen-shape compilation and prevented
  warmup latency from being reported as steady performance. Use a distinct
  cache identity for the measured pass.
- The no-prefetch ablation also completed 32/32 with zero errors and natural
  EOS. Its differences from the prefetch-on run were only +1.77% TTFT and
  +0.087% TPOT. Removing both prefetch hooks is therefore a successful
  simplification, not a failed optimization.
- Existing immutable evidence from the same image, dtype, real weights, TP
  degree, and exact shapes can close a candidate without consuming another NPU
  lease. Revalidate all identity fields before reusing it.
- Retained raw profiles can close source-level shape ambiguity only after the
  service identity is proven. The official Control four-rank capture has
  5,040 exact `1x5120 @ 4096x5120` QKVZ calls and 5,040 separate
  `1x5120 @ 24x5120` BA calls per rank. T34 instead has 5,040
  `1x5120 @ 4120x5120` calls because its six-way GDN projection monkeypatch
  was active in all TP workers. A padded 4,128-wide buffer is a third,
  implementation-only shape. Do not transfer timing or correctness claims
  between these three identities.
- A pinned-image, network-disabled source/ABI audit can close an impossible
  lifecycle hypothesis without allocating NPUs. For the v0.23 image, the
  public CANN 9.1 HCCL header was sufficient to prove the supported A2 flow is
  init, prepare, commit/wait, and finalize; preserve the image digest and exact
  header path with that conclusion.
- The real-client harness became a reusable success: OpenAI-compatible streaming
  requests measure request-to-first-token TTFT and first-to-last-token TPOT,
  require unique cache salts, natural EOS, zero errors, and keep raw per-request
  evidence. Operator timers and server logs are diagnostic evidence only.
- A custom recurrent-GDN operator package exposed a same-name ACLNN ABI
  collision. Giving custom entry points unique names and pinning SHA256 for the
  extension, kernel, op-api library, and OPP tree fixed packaging ambiguity.
  This is a delivery-correctness repair, not a performance contribution.
- Four independent exact-shape oracles on physical NPU0-3 are useful before a
  TP4 service run. Parallelize seeds, dtypes, and shapes only after physical
  mapping and leases are proved; a four-way oracle pass does not replace the
  single TP4/HCCL end-to-end gate.

## What failed and why

- The upstream experimental `SwigluGatedMlp` package matched the installed
  CANN tag and built unchanged, but its shared library had an unresolved
  internal matmul symbol. Stop before device execution. Do not hide an
  upstream ABI defect with copied local matmul code or an unrelated runtime
  library.
- Upstream presence is not a quality certificate. Inspect commit history,
  tests, support matrices, PR review, release ancestry, and removal reasons.
  Unknown non-promotion rationale is a risk signal; it does not authorize a
  parallel reimplementation.
- Later upstream source is reference material until its code is deliberately
  adapted and validated. Inspecting a v0.24 commit does not mean the official
  v0.23 runtime or image was upgraded.
- Weight prefetch was later removed upstream as underused/low-value, and its
  target-stack ablation showed no material value. Do not revive it unchanged.
  A deleted or deprecated graph/operator path remains closed unless a new
  supported implementation changes the premise.
- A later upstream GDN-gating route was rejected by opportunity math before
  device testing. The measured operator accounted for at most about 3.67% of
  the required c1 TPOT gap even under an impossible zero-cost assumption.
  Reject candidates whose complete recoverable critical-path budget cannot
  meet the declared gate.
- The installed Python schema and prose for `torch_npu.npu_ffn` appeared to
  allow BF16 SwiGLU, but the executable `aclnnFFNV2` kernel rejected the
  no-expert-token BF16 path for M=1/5/8/16. Runtime execution evidence
  outranks wrapper signatures and documentation. Do not cast to FP16 when BF16
  fidelity is part of the contract.
- A local FFN or GEMM win is not a TP service win. If a candidate breaks the
  existing Matmul-AllReduce boundary, benchmark the complete replacement
  chain, including the standalone collective, against the fused control.
- The existing decode SwiGLU median was about 4.39 us per layer, below the
  installed guidance's roughly 30-us vector threshold. Do not optimize a small
  named operator merely because a replacement exists.
- Six-way GDN projection fusion produced promising local latency but failed
  semantic regression, including a 26-case concurrency set, and remained
  unstable even when narrowed to single-row decode. It is closed unchanged;
  performance never compensates for wrong model behavior.
- Conv-weight prepacking reduced repeated layout work in theory, but did not
  earn admission with complete accuracy and end-to-end evidence. Do not combine
  it into a release candidate merely because the preprocessing idea is sound.
- `fused prefill`, `FusedGdnDecode`, and `fused_gdn_prepare` are upstream
  vLLM-Ascend/CANN capabilities or upstream-derived paths. They may be baseline
  B or reused components, but must never be reported as local invention.
  Known accuracy/support defects remain upstream risks until the exact pinned
  version is repaired and independently gated.
- Adaptive M<=8 projection, weight-prefetch variants, row padding, MMAR/LCCL/
  AIV experiments, FlashComm1, NUMA cpuset, and PCI-local CPU-affinity did not
  establish a repeatable full-matrix gain. Treat their recorded terminal
  decisions as closed; do not create a new trial number or recombine them
  without a concrete changed premise.
- The r20 RGDR output-boundary fusion showed large exact-shape microbenchmark
  reductions for M=1/4/8, but M=16 had a BF16 mismatch and service-level
  startup/performance were unproven. A fast partial boundary is not a release
  candidate when the task requires the complete GDN preprocessing-to-recurrent
  or projection/collective critical path.
- Persistent cross-layer Matmul-AllReduce lifecycle reuse is closed for the
  pinned public interface. The CANN 9.1 A2 API exposes no public reuse, reset,
  imported-handle, or cross-invocation resume primitive. `repeat` repeats one
  collective over continuous memory inside one lifecycle; it cannot span
  dependent model layers with different weights and buffers. A private ABI or
  monolithic multi-layer kernel would no longer be the requested removable
  monkeypatch.
- Do not confuse a large diagnostic envelope with removable latency. The T34
  rejected-treatment MMAR outer-minus-core envelope was about 16.016 ms/token, while the
  required conservative admission threshold was 4.626 ms/token, but no public
  mechanism could remove that envelope across invocations. The previously
  tested InitV2 substitution saved only about 0.009854 ms/token in the weighted
  exact-shape result and is terminally rejected.
- Partial-path opportunity math closed the old GDN routes: the T34
  preprocessing-to-recurrent zero-cost upper bound was about 2.796 ms/token
  and its terminal norm-to-MMAR envelope was about 3.108 ms/token. Both are
  below the 4.626 ms/token admission threshold. A separate official-Control
  full block profile pairs QKVZ, BA, conv, gating, both L2 norms, recurrent,
  output norm, and MMAR for all 5,040 calls per rank; its zero-cost ceiling is
  9.804 ms/token. That only permits source-design investigation. It does not
  revive the rejected six-way fusion or prove any implementable saving.
- Later official vLLM-Ascend release notes removed the Matmul-AllReduce and
  Matmul-AllReduce-RMSNorm fusions after they had already been marked ready for
  deprecation. Treat that removal as corroborating maintenance evidence, not as
  proof that newer source is active in the frozen v0.23 image and not as a
  local contribution.
- A same-family patch release is not automatically a performance candidate.
  The inspected `v0.23.0.post1` release carried KV-cache/MTP correctness,
  dependency, CI, and documentation changes but no relevant A2 BF16 TP4
  Qwen3.5 critical-path optimization. Record the audit result and keep the
  frozen official baseline unchanged instead of upgrading by version number
  alone.
- Large graph-node or microbenchmark reductions must be translated into a
  conservative, non-overlapping end-to-end critical-path budget before they
  earn device time. Record which enclosing path remains untouched; otherwise a
  partial fusion can look larger than the maximum service-level gain it can
  actually deliver.

## Trust and quality gates

- Performance and model quality are independent mandatory gates. A latency win
  never offsets an accuracy regression.
- A workload with empty reference answers can prove latency, completion,
  natural EOS, and paired-output stability, but cannot prove accuracy.
- Byte-identical paired outputs pass directly. Every non-identical pair needs
  a row-level, hash-bound decision; a summary-only approval is insufficient.
- Run the expensive reference-backed accuracy suite only after fail-fast
  performance passes. Require fresh identity-matched control/candidate runs,
  complete repetitions, zero request failures, and candidate accuracy no lower
  than control in every repetition and in the median.
- Exact response hashes may drift even without a treatment. Do not confuse
  nondeterminism with either correctness or regression; use paired semantic
  evidence and reference-backed scoring.
- For the frozen 2026-09-22 Qwen3.5-27B campaign, the performance contract is
  official v0.23.0 BF16 TP4/HCCL on physical NPU0-3; c1/c5/c8/c16 each use 32
  fixed streaming requests, unique cache salts, three rounds, and the median of
  per-round P95. Every tier must reduce TTFT by at least 20% and TPOT by at
  least 8%, with 32/32 success, zero errors, and natural EOS. Do not inherit
  older 40%/20% or partial-tier gates from stale handoffs.
- The quality contract is a sensitive semantic set followed by GSM8K 1319
  questions, paired Control/Candidate for three rounds. Candidate accuracy must
  be no lower in every paired round and in the median. GSM8K is a quality gate,
  not a performance workload.

## Attribution and release-candidate discipline

- Use A/B/C attribution: A is the unchanged official image, B is the exact
  upstream vLLM-Ascend/CANN capability baseline, and C is B plus the smallest
  local original increment. Only C-minus-B is local contribution.
- For this repository, "upstream" in contribution accounting means
  vLLM-Ascend and CANN/ops-transformer. Other sources can inspire design, but
  provenance and license still need recording.
- Do not start another device piercing run because a named operator looks fast.
  First use existing profiles and source to prove a non-overlapping complete
  critical-path budget. Use the latest maintainer-approved screening rule.
  For this campaign, require coverage of the formal gap plus a documented
  measurement margin. The September two-times floor and its recorded
  rejections are historical. The final performance and quality gates still
  apply to the exact delivery.
- A full-block profile analyzer must prove the ordered causal path, not merely
  pair a projection with a later recurrent or MMAR anchor. For GDN this means
  checking projection, causal convolution, gating, both L2-normalizations,
  recurrent state update, output normalization, and terminal projection/
  collective in the same bounded stream interval, with every expected
  layer-step call accounted for. Missing stages or unmatched calls make the
  budget inconclusive, not admissible.
- An analyzer must also bind the profile to the exact service treatment.
  Check the variant manifest, patch hash, worker activation log, and
  projection shapes before admitting a profile. T34 was labeled
  `candidate-fused-prefill` but also activated six-way projection; treating
  its 4,120-wide path as official Control would have produced a false
  candidate admission. Require separate 4,096-wide QKVZ and 24-wide BA
  calls for the pinned official Control profile.
- Keep three quantities separate in every admission report: the observed
  end-to-end TPOT gap, the required conservative admission floor, and the
  removable implementation budget. A zero-cost whole-envelope ceiling may
  eliminate an impossible route, but it cannot establish that a monkeypatch
  can realize the ceiling. Device time is earned only after a concrete public
  mechanism has a conservative removable budget above the floor.
- Accepted local performance modifications were still zero at the 2026-09-22
  checkpoint. Keep upstream wins, packaging repairs, harness improvements, and
  local microbench wins in their correct evidence categories; none alone is a
  validated release candidate.
- Candidate manifests and executable contract tests are one state machine.
  When a candidate moves from `pending` to terminal `rejected`, update the
  tests to require the rejection reason, missing gates, and concrete reopening
  premise. Never leave a test that treats `pending` as the only legal state or
  silently accepts both states without checking their different obligations.
- Once a candidate passes the offline budget, use the fixed order: exact
  layer/state oracle, sensitive semantics, c1 fail-fast, complete repeated
  performance matrix, then three paired GSM8K rounds. Only the all-green result
  becomes the removable monkeypatch delivery and PR.

## Reusable admission sequence

1. Pin model bytes, official image digest, framework/CANN versions, dtype, TP
   degree, workload hash, cache state, and physical device mapping.
2. Audit the accepted, unmerged, experimental, deprecated, and removed
   upstream routes before writing code.
3. Compute a non-overlapping critical-path upper bound. Close routes that
   cannot satisfy the end-to-end gate even at zero cost.
4. Reuse the exact upstream or built-in implementation. Add only the smallest
   removable runtime adapter needed to reach the real call path.
5. Gate ABI/loadability, exact-shape numerical behavior, repeated stress,
   whole-chain communication cost, and per-worker activation before service
   benchmarking.
6. Run smoke and the preregistered fail-fast cells. Expand to the repeated
   matrix and expensive quality gate only after both TTFT and TPOT pass.
7. Record `accepted`, `partial-component`, `rejected`, `failed`, or
   `inconclusive`, with the premise that would permit reopening. Remove
   rejected hooks from the safe runtime while preserving their evidence.
8. Stop multiplying trial labels. Continue the owning hypothesis ledger and
   convert each terminal result into a reusable admission or rejection rule.

Do not rerun a closed candidate unchanged. A retry needs a concrete changed
premise such as a new supported kernel release, repaired ABI, different
critical-path budget, or corrected evidence identity.

## November 25 reference capture and rejection

- Reuse a sealed official reference before spending more card time. On
  physical NPU0 the official BF16 projection captured repeatable outputs for
  four checkpoint TP shards at M=1. Each shard used learned weights and
  synthetic hidden input. Preserve the official post-load and callable
  identity, measured ND/NZ layout, exact input hash, scope and output hashes.
  Slice each logical Q/K/V/Z segment for its TP rank before joining the
  local shard. Sequential replay of four checkpoint ranks qualifies those
  component outputs. Live TP4/HCCL and whole-model acceptance require
  separate evidence.
- Reject the exact binary at the first confirmed numerical failure. The
  native rank0 replay at M=1 differed in 2 of 4,096 QKVZ BF16 values and 0
  of 24 BA values. Its arrival and protocol record counts were clean and
  the owned container and its PIDs were released. Keep that receipt and
  skip the remaining ranks for the unchanged binary. Compilation, clean
  protocol counters and static analysis cannot override the numerical gate.
  If a wider admitted design still needs the projection, localize the
  first arithmetic difference using the same reference. Keep the accepted
  tolerance and evidence scope fixed.
- Reuse the host's CANNBot and CANN tools before building another harness.
  Locate the actual `cannbot-skills` checkout and confirm its revision and
  target support. Use `ops-spec-gen` for the contract, the direct workflow
  for a focused kernel, and an existing 910B-compatible registration
  template when the operator needs registration. `ops-transformer` OpGen
  creates the project scaffold. The confirmed November actions were the
  OpGen CLI help and the CANNBot `ascendc-sync-audit` script against the
  sealed R2 source included by the failed binary. Its two informational
  `SYNC-12` entries did not resolve the mismatch. Record generated
  artifacts, compilation and device validation only when each actually
  occurs. An available agent image or documented workflow is capability
  inventory.
- Require the whole measured hotspot before generation. At the historical
  c1 TPOT of 28.909 ms/token, the 8% target costs about 2.31 ms/token.
  Removing BA alone had an optimistic ceiling of about 0.60 ms/token on
  the corresponding profile. Close that isolated route before generating
  or timing another kernel. Pin the full attributable boundary and separate
  the upstream baseline from the local increment.
- For an actual Prefill graph monkeypatch, snapshot graph counters after
  warmup in both paired roles. Require replay of existing entries in the
  measured client window on all four workers and inspect capture and
  fallback separately. A c1 screen can qualify a TTFT component only.
  A single-token natural EOS counts toward completed requests and TTFT,
  with no TPOT interval. Preserve that request and mark incomplete TPOT
  evidence accordingly.
- A host reconnect leaves device ownership to be rechecked. In this case,
  the restored route exposed an external privileged workload with a live
  PID on physical NPU0 and a UDA namespace covering NPU0–3. The TP4 run
  remained pending despite an available group lock. Apply the
  [host maintenance workflow](../SKILL.md) before admission.

Host evidence lives under `/opt/host/vnf/austinov/qwen35-diagnostics`:

| Evidence | Relative path | SHA-256 |
| --- | --- | --- |
| Official reference receipt | `official-projection-reference-npu0-m1-20261125T063553Z-a6d2/host-result.json` | `cbec2ec342592fae1731f202c42a5a050d34e7f3b6f82ac98a0f0c5659650c4b` |
| Staged fixture | `qwen35-official-projection-fixture-npu0-m1-20261125T063553Z-a6d2-stage/fixture-manifest.json` | `c444c21861307f98f33aebbfcc5f0da7e8c62fdfc39ebe33f1a510337736e408` |
| Native failure receipt | `native-projection-check-npu0-m1-rank0-20261125T064201Z-7bd3/output/oracle/fixture/result.json` | `ef76d71d00e77253c5ba7e70702a4842def2a467332d64aba5c96fdfc7b65ad9` |
