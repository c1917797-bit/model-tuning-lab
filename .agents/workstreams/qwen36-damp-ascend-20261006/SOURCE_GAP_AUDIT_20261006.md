# Source-gap audit: eight previously unarchived papers

Audit date: 2026-10-06. Scope: primary-source and applicability review only.
Authoritative checkout: /opt/host/vnf/austinov/model-tuning-lab.
Creation base: work/qwen36-damp-ascend-20261006 at
7d60821a530d68541c1cf691e9141ed2cb93d869.

This supplement does not run a container, NPU experiment, model benchmark or
task-quality evaluation, and does not start a new paper's formal 24-hour timer.
It does not replace original failures or their measured scope. The active
DAMP -> prepared KVBuffer order and THREE_DAY_CLOSEOUT.md remain unchanged.
HYPIC is an earlier successful exemplar, not a new success of this audit.

## Evidence and governance boundary

Read for this audit: AGENTS.md, global and branch-local HANDOFF.md, the skill
registry, chicaihong01-host-maintenance, paper-to-ascend,
mst-experience-ingestion, PAPER_EVIDENCE_INVENTORY_20261006.md,
THREE_DAY_CLOSEOUT.md, SCHEDULING.md and the existing portfolio records.

The ID scan found these eight entries in the inventory's missing-archive
declaration, but no independent experiment archive supporting a completed
migration claim. That is an archival gap, not proof that no historical action
ever occurred. Seven primary-source titles/versions were verified; one remains
unresolved. None gains new NPU, E2E or task-accuracy evidence in this audit.

Code-verification wording below is deliberately layered:
paper link -> author-linked repository/commit -> inspected implementation or
pipeline -> reproduced build -> actual NPU -> matched service -> final quality.
A repository link is not full implementation fidelity, and source availability
is not an installed worker/binary dispatch proof.

## 1. 2608.20961v1 — TreeWY: Speculative Verification for Gated DeltaNet Hybrids

Primary source: [arXiv v1](https://arxiv.org/html/2608.20961v1).

- Training/distillation: the verifier needs no new training when a compatible
  pretrained drafter exists, but speculation/MTP is an essential dependency.
- Fit and distinct mechanism: tree-WY verification reconstructs the accepted
  branch instead of storing a complete state for every draft node. It matches
  GDN, but addresses speculative snapshot capacity, not DAMP precision or
  ordinary DeltaLog/KVBuffer write deferral. Gains depend on memory pressure.
- Code level: an author-linked implementation commit is verified through the
  [author RFC](https://github.com/vllm-project/vllm/issues/54080) and
  [commit b073ed6](https://github.com/vllm-project/vllm/commit/b073ed6cacfa1cf5ae23111854729e662a72a6d1).
  Tree-WY reference/Triton, tree draft/verify and scheduling paths are present.
  This is not a completed source-fidelity audit, Ascend build or deployment.
- Reuse: GDN chunk/recurrent primitives and cache/scheduler scaffolds; the
  single-token native recurrent ABI alone cannot express tree verification.
- Minimum missing: permitted drafter/verify path, actual snapshot-memory
  pressure, Ascend WY/ancestor-mask implementation, atomic branch commit,
  rollback/migration/prefix identity and graph handling.
- Disposition: source verified; conditionally deferred speculative route.
  Not a measured failure and not a reason to introduce MTP into the current lane.

## 2. 2603.05931v1 — A Persistent-State Dataflow Accelerator for Memory-Bound Linear Attention Decode on FPGA

Primary source: [arXiv v1](https://arxiv.org/html/2603.05931v1).

- Training/distillation: no new training for the recurrence acceleration.
- Fit: Qwen3-Next/GDN is relevant, but full FP32 state residency in FPGA BRAM
  is a custom-hardware property. The published FPGA local result is not an
  Ascend model E2E result. Its GVA ratio differs from current HQ4/HV12 TP4.
- Code level: the inspected paper links a NVLabs baseline; an author FPGA
  implementation was not verified. Do not promote that into "no code exists".
- Reuse: native GDN update/readout and AscendC mathematical primitives, not
  an assumed persistent cross-launch BRAM contract.
- Distinct mechanism/minimum missing: after removing custom-silicon benefits,
  prove an incremental software state-traffic reduction beyond the current
  native fused update/readout and existing state-storage work. Any persistent
  Ascend design must establish capacity, ownership, lifecycle and graph safety.
- Disposition: direct hardware route outside fixed-Ascend plugin scope;
  software residual unproven. No current NPU implementation failure is claimed.

## 3. OpenReview c6TDOPEQ0e — title/version unresolved

Primary locations:
[forum](https://openreview.net/forum?id=c6TDOPEQ0e),
[PDF](https://openreview.net/pdf?id=c6TDOPEQ0e),
[official API2 note](https://api2.openreview.net/notes?id=c6TDOPEQ0e).

The forum/PDF returned a browser-verification challenge; the two official notes
API endpoints returned errors, and exact-ID search did not verify metadata.
Title, version, author, code, training requirements and mechanism remain
unknown. No applicability score or invented title is valid.

Minimum missing: an accessible primary PDF/metadata or author-hosted official
copy. Disposition: source unresolved, not a rejected algorithm.

## 4. 2509.19873v1 — SpecMamba: Accelerating Mamba Inference on FPGA with Speculative Decoding

Primary source: [arXiv v1](https://arxiv.org/html/2509.19873v1).

- Training/distillation: inference can use existing Mamba2 target/draft models
  without new training; a drafter and speculative workflow are still required.
- Fit and distinct mechanism: FIFO tree verification, mixed rollback and
  specialized FPGA pipelines target Mamba2. Its SSM transition does not establish
  equivalent GDN rank-one updates or the current Qwen serving semantics.
- Code level: an author FPGA repository was not verified from the inspected
  primary source. A search hit named speculative_mamba belonged to another
  paper, The Mamba in the Llama, and is not official SpecMamba provenance.
- Reuse: matmul/conv are only building blocks; they do not implement the custom
  hardware system, GDN tree verifier or rollback.
- Minimum missing: an in-scope target/drafter, GDN-equivalent derivation,
  tree/state rollback and capture, then actual Ascend physical implementation.
- Disposition: speculative, model and hardware scope mismatch for the selected
  non-speculative Qwen GDN lane; not a measured NPU rejection.

## 5. 2605.22416v1 — Asymmetric Virtual Memory Paging for Hybrid Mamba-Transformer Inference

Primary source: [arXiv v1](https://arxiv.org/html/2605.22416v1).

- Training/distillation: none required; this is allocator-level capacity
  management, not attention/matmul arithmetic.
- Mechanism: separate KV/SSM pools behind tagged handles. Unlike DAMP/DASC/HYPIC,
  it does not compress numerical values, restore approximate state or reuse
  arbitrary segments.
- Critical limitation: the evaluated allocator prototype has no direct model,
  kernel or request-scheduler integration. Baselines model allocator behavior.
  Both pools reserve maximum backing at initialization, approximately doubling
  backing memory; resize changes tables/counters without physical remapping.
  Allocator throughput is not model E2E throughput. Abstract and body counts
  differ; retain that discrepancy rather than choosing a favorable count.
- Code level: the paper links [CachePawl](https://github.com/codepawl/cachepawl);
  repository/README content was inaccessible in this session, so revision and
  implementation are not audited.
- Reuse/minimum missing: existing cache shapes, block tables and state indices;
  prove current fragmentation first, then real dual-pool allocation, address
  stability, reclaim/prefix/mixed/graph correctness without oversized sidecars,
  and memory-pressure matched E2E.
- Disposition: conditionally applicable allocator route, implementation and
  serving benefit unproven; not a measured failure.

## 6. 2606.16429v1 — Taylor-Calibrate: Principled Initialization for Hybrid Linear Attention Distillation

Primary source: [arXiv v1](https://arxiv.org/html/2606.16429v1).
Author source: [Taylor-Calibrate](https://github.com/FutureMLS-Lab/Taylor-Calibrate).

- Training/distillation: the full method explicitly includes gradient
  layer-alignment and global distillation after analytical initialization.
  Taylor-only is not the complete method.
- Fit: converts a softmax teacher into a hybrid GDN student. The current Qwen
  checkpoint already contains trained GDN; conversion is not a weight-preserving
  serving optimization or DAMP's inference calibration.
- Code level: author repository and its initialization -> hidden alignment ->
  distillation pipeline were inspected; no current-environment reproduction.
- Reuse: native GDN serving after a new converted checkpoint, not direct speed
  gains on unchanged Qwen weights.
- Minimum missing: training authorization, target checkpoint and quality
  evidence. Do not silently recast distillation as training-free calibration.
- Disposition: full method outside the current no-training/distillation scope;
  no NPU failure claimed.

## 7. 2604.19877v1 — Super Apriel: One Checkpoint, Many Speeds

Primary source: [arXiv v1](https://arxiv.org/html/2604.19877v1).
Linked framework: [Fast-LLM](https://github.com/ServiceNow/Fast-LLM).

- Training/distillation: the supernet is trained using stochastic distillation
  and SFT. Serving a released SuperApriel needs no additional training, but
  substitutes the checkpoint rather than equipping Qwen with missing mixers.
- Mechanism/fit: trained per-layer FA/SWA/KDA/GDN alternatives and placement
  choice; not D3's skipping of unchanged model layers.
- Code level: paper's framework/checkpoint links were verified. The framework
  README is not a complete serving-path audit; the placement toolkit was
  marked coming soon in the paper page, despite broader release wording.
- Reuse: FIA/GDN are partial primitives. Alternate mixer weights, KDA/SWA
  support and placement/runtime dispatch remain necessary.
- Minimum missing: trained Qwen-compatible alternatives or explicit model
  substitution, and an available faithful placement implementation.
- Disposition: target-checkpoint/training scope mismatch, not NPU failure.

## 8. 2503.08524v2 — Position-Aware Depth Decay Decoding (D3): Boosting Large Language Model Inference Efficiency

Primary sources:
[arXiv v2](https://arxiv.org/html/2503.08524v2),
[ACL publication](https://aclanthology.org/2025.findings-acl.154/).

- Training/distillation: genuinely training-free; strategy search does not
  update model weights.
- Mechanism: generated-position-dependent depth decay, retaining core layers
  while skipping flex layers. The paper's Llama/HuggingFace results are not
  evidence for Qwen's hybrid GDN/conv/KV lifecycle or Ascend performance.
- Code level: no author official-code entry was verified from the inspected
  primary pages; a future implementation must be labeled equation-derived.
- Reuse: decoder layer hooks and native FIA/GDN. It removes whole layer work,
  unlike DRRQR/DAMP state-channel or precision changes.
- Minimum missing: faithful strategy/core/flex mapping and per-request positions;
  skipped rows must not update recurrent/conv/KV state. Mixed batches, request
  reuse/new prefill and graph keys need independent lifecycle tests. Then
  fixed-1024 matched E2E and final task quality are required. A decay setting's
  layer/FLOP saving is not guaranteed >=10% service throughput.
- Disposition: training-free candidate, hybrid adaptation and NPU evidence
  insufficient; not a failed paper.

## Source interfaces observed in the current reference checkout

Read-only source identities (not deployed-library or worker identity):

- /cache/austinov/src/vllm-ascend/vllm_ascend/ops/gdn.py:
  SHA256 d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816.
  _forward_core, fused_gdn_gating and npu_recurrent_gated_delta_rule expose
  relevant recurrent/chunk seams.
- /cache/austinov/src/vllm-ascend/vllm_ascend/attention/attention_v1.py:
  SHA256 80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390.
  Cache shape/update, block tables, FIA and graph-parameter paths are present.
  Source extensions and source presence must not be assumed to identify the
  actually loaded native binary or upstream release capability.

## Reusable source-gap rules and follow-through

Trigger: auditing historical paper completion counts or selecting the next
training-free port. Destination: this narrow source/applicability verification
record; no global skill, portfolio or original experiment is overwritten.

1. An inaccessible source, missing archive or unimplemented adaptation is not
   an algorithm failure. Verify the primary title/version before scoring.
2. A verified author commit corrects a "no official code" assumption but does
   not prove fidelity/build/NPU/service success.
3. Allocator-only modeled throughput, oversized backing and custom FPGA
   properties do not meet fixed-Ascend E2E evidence requirements.
4. Separate trained-model substitution, speculation and changed numerical/
   lifecycle semantics from a weight-preserving inference adaptation.
5. Close only the supported decision scope; retain the smallest missing gate.

Verification for later integration: check all eight IDs and primary links are
present, unresolved metadata stays explicit, no new NPU/performance/accuracy
claim appears, and DAMP -> KVBuffer order remains intact. MAIN performs
validate-mst.sh, checkpoint/push and portfolio integration after review.
This single-file supplement itself does not certify those downstream checks.
