# Independent HYPIC Paper-to-Ascend

Human direction: reconstruct the paper independently, then implement and test
the algorithm/operator/runtime chain on chicaihong01 physical NPU0–3.
Use only the selected27B model, including the C3 feasibility check.
The task is active; no device experiment has started.

## Implementation provenance
The paper revision is2607.01299v2. Implement new references, primitives,
cache/router and monkeypatch in separately named source paths. Existing
hypic_vllm_ascend trees and their algorithms, kernels and runner patches must
not be copied, imported, mounted or editable-installed. Ordinary official
framework operations and the maintained generic plugin template are allowed.
Prior discussion of old source means this is an independent reimplementation,
not a claim of blind clean-room authorship. Record derivation and file origins.

## Requirements before code
- Establish paper revision/digest and model/runtime/operator identities.
- Record each method stage and backend adaptation before editing.
- Run a native-only two-instance capacity smoke first. TP2 instances must map
  only physical0–1 and2–3, with actual process/rank proof and owned cleanup.
- Preserve native source and official image. New inference logic is opt-in,
  separately packaged and removable.
- Record no hidden threshold changes; freeze numerical and task tolerances
  after reference/official baseline measurements and before candidate execution.

## Paper mechanism ledger
| Stage | Paper location | Independent target | Evidence required |
|---|---|---|---|
| Segment identity | §5 | Explicit token boundaries and stable identity | Token/hash reproducibility |
| C1 | §4.2, equations2/6 | Affine state tuple and ordered composition | Independent recurrence oracle, actual-shape NPU comparison |
| Conv boundary | §4.2 | Carry trailing conv state and recompute boundary tokens | Boundary-length and consecutive reuse tests |
| C2 | §4.3, equation8 | Per-request KV relocation and seam propagation | State/slot/position checks; seam-width ablation |
| Cache ownership | §4.1/4.2 | Public material and private request state with leases | Eviction, generation and concurrent reuse tests |
| PDC coexistence | §4.2 | Native prefix capability plus independent PIC | Orthogonal native/PIC controls |
| C3 | §4.4 | Two27B instances; cold-only LPT scatter, actual transfer, combine | Two-instance capacity and real transfer/compute timeline |
| Numerical ladder | §§4.2/6.3 | Same-input oracle separated from deep-layer approximation | Eager, graph, slots and TP service correctness |
| Evaluation | §6 | Target27B paper-style workloads and dedicated Skill tests | Independently frozen request/scoring/measurement contracts |

The original four models, H20 topology and unavailable private production trace
cannot be relabeled as reproduced on this target. All three mechanisms remain
required. A C3 resource limit must be an explicit incomplete gate, not silently
dropped.

## Efficient execution
M0 paper/contract -> M1 native dual-TP2 capacity -> M2 equation/NPU primitives
-> M3 integratedC1/C2 canary -> M4 realC3 -> M5 performance -> M6 quality
-> M7 rollback/audit/Skill acceptance/published handoff.
Cache one successful unit with exact identities; rerun only after a material
change. Multiple Skills share this evidence chain. A correct negative technical
result can validate a workflow Skill; failed implementation does not imply the
paper is invalid.

## Evaluation design to freeze before runs
Use Full Recompute, native Prefix Cache, Naive Addition and the independent
method as separate groups; add C1/C2/C3 ablations. Measure warm hits, cold misses,
eviction/concurrency and PDC coexistence without pooling their denominators.
Paper-style public QA/summarization workloads need frozen provenance and
appropriate F1/ROUGE-L scoring. LongBench-v2/GSM8K are additional repository
quality checks, not substitutes for all paper tasks. Private Prod-RAG remains
unavailable unless supplied.
Performance uses fixed1024 output and repeated matching inputs. Quality uses
natural EOS, non-thinking1024 by the user's policy; thinking2048 if selected.
Capture actual retries and every request identity. Do not impose token equality
on a paper approximation; define exact local math tests separately from task
quality envelopes before candidate measurement.

## Current evidence
- Source0154: host/config/resource inspection succeeded; Git fetch timed out.
- Source0156:15 weight shards exist; index total55,562,855,904 bytes.
- Native dual-instance capacity is unproven. Weight lower bound25.873GiB/rank
  under TP2, private32k KV1GiB/rank, recurrent state0.0703GiB/request/rank.
  Public cache, graph, workspace and actual partitioning still need measurement.
- Remote start publication is required before product implementation.
- No NPU kernel, service request or performance/quality result exists for this task.
