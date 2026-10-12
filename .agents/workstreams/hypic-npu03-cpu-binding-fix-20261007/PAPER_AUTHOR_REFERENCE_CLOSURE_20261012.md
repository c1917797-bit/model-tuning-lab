# HYPIC author reference: ten-file identity closure

Recorded 2026-10-12. Retrospective source review, not an Ascend benchmark.

## Identity result

Author project: https://github.com/redai-studio/HYPIC
Fixed revision: 98147c01909004e66d98bcb18b886927d41b0ee5
Paper linked by its README: arXiv:2607.01299; ingestion uses version v2.

Local-only audits0190/0191 checked all ten manifest reference files against
their fixed Git tree/blob identities and SHA256s. All10/10 match the historical
UPSTREAM_REFERENCE_HASHES in the Ascend derivative. The prior0188 partial3/10
receipt remains unchanged. This closes selected-reference-file identity only;
it does not uniquely identify the historical checkout commit or prove all
author-repository files were used.

Retrieval boundary: the lazy-fetch attempt0183 timed out. A bounded alternative
requested the seven fixed-revision public raw files with normal TLS verification,
importing only bytes whose SHA256 and Git blob identity both matched. Its
connector response timed out; no successful controller result is claimed.
Independent018f then found all10 objects locally and no matching curl process;
0191 replayed every object without network. No repeated clone or device run.

## Source mapping and reference tests

| Mechanism | Fixed author files | Target boundary |
| --- | --- | --- |
| Segmentation and position-independent lookup | segmenter.py, picache.py | Explicit boundaries; query not reusable material |
| Public/private state and convolution seam | pic_alloc.py, conv_tails.py | Existing single-service C1/C2 derivative |
| Linear-state transition and full-attention relocation | gdn_backend.py, hybrid_linear_attn_backend.py | Hybrid-specific state; not a generic Dense-only claim |
| Per-batch execution metadata | forward_batch_info.py | Must match actual serving/runtime layout |
| Distributed cold-prefill routing/transfer | scatter_xfer.py, pic.rs, pd_router.rs | C3 absent from target; TP ranks are not replicas |

The checked root LICENSE is Apache-2.0, SHA256
1495e1e757ef4d0925a2350563cf5754bb23c51701a8ec4fb3c5cdcbedae6747.
This identifies the author root license; it is not a complete dependency,
per-file notice or derivative redistribution review. No author source is added
to the model-tuning-lab Git tree.

The fixed test_seam_sink.py tests default8, ratio/count interpretation and
clipping to segment length. It is a scalar configuration unit test, not proof of
attention-state correctness. quick_test_offline.py describes six serving modes,
cache warmups and first-token checks. The distributed README compares a
single-GPU PIC transition baseline to a4-prefill/1-decode scatter arrangement;
it is not the local TP4 full-recompute comparison. None of those author tests
was executed or represented as NPU evidence.

README examples use SGLang0.5.14 and Qwen35B/122B or Ring model configurations.
They do not prove compatibility with the actual local64-layer BF16 checkpoint;
retain PAPER_ARCHITECTURE_FIT.md and its target source audits. Dtype/layout
portability is not established by a matching filename or author speedup.

## Consequences for this task

- Current measured Ascend source remains4429e35, not author SGLang code.
- Preserve all r19 quality results; this source audit does not explain the
  observed regression and does not admit a new candidate.
- No ingestion-driven quality rerun, C3 expansion, observer or GDN subtask.
- Original pre-implementation sequencing remains unproved retrospectively.
- Original-case obligation review below supports bounded verification of this
  ingestion task. Counts become9 bounded verified/20 partial; main/remote not updated.
- Same-source performance choice and deadline2026-10-13T08:47:14Z unchanged.

Replay: python3 -B
.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_ingestion_case.py
The replay checks the fixed author tree, all10 byte hashes and the five
license/README/test-reference hashes, using only locally present Git objects.

## Exact-main original-case acceptance audit

Reviewed exact-main Skill blob69edbce77685c9ae4cc20a22bbca403bbbd4e390
at ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2 (read operation0192).
The case task is unchanged: ingest HYPIC into bounded C1/C2/C3 hypotheses
for the actual hybrid checkpoint, distinguishing author code and local evidence.
It is not replaced with a smaller source-hash-only task.

| Main workflow obligation | Inspected evidence | Result |
| --- | --- | --- |
| 1 Paper identity/version/source | October9 note, versioned paper link, fixed README and ten-file revision | Proved for the reviewed sources |
| 2 Optimization target | Note identifies segment cache/recurrent state, full attention and router | Proved |
| 3 Mechanism/state/dataflow/cost | C1 transition composition, C2 relocated KV/seam, C3 scatter; storage/first-prefill/seam overhead recorded | Proved at ingestion scope |
| 4 Model/runtime/hardware prerequisites | Config/index hashes,64 layers48+16,BF16,TP4,exact boundaries/residency; no retraining | Proved for bounded text hypothesis; layout/runtime execution routed to architecture/source checks |
| 5 Portability and assumptions | SGLang/Triton/NIXL/GPUDirect and replicas distinguished from AscendTP ranks | Proved; C3 absence retained |
| 6 Single-variable hypothesis | Same-identity enable0/1; expected hot-prefill benefit and independent Decode/quality | Proved; no new experiment admitted |
| 7 Unknowns and routing | PAPER_ARCHITECTURE_FIT.md, missing C3/multimodal/MTP, unproved historical identity and current quality cause retained | Proved as explicit uncertainty, not erased |

Source-backed migration-selection guidance is also reviewed: this task is
reproduction of an existing Ascend derivative, not a new GPU migration.
Fixed author commit/core files/reference tests/root license are now verified.
Author benchmarks and distributed PIC denominators are not local full-recompute
baselines. Whole-project redistribution and full tensor-layout compatibility
are not authorized claims; the note explicitly limits what has been checked.

The exact-main boundary forbidding opening a tuning workstream before an
applicability gate was not followed historically. That historical sequencing
failure remains an explicit negative lesson. This retrospective ingestion does
not open a new workstream, execute a new hypothesis or backdate that gate.
The verified label applies to the original present-day ingestion task, not to
historical end-to-end compliance or all Paper-to-Ascend behavior.

Disposition: bounded verified for this original ingestion case, with linked
source, model, mechanism and uncertainty evidence. Not algorithm adoption,
C3 completion, NPU quality preservation, author test execution or main promotion.
