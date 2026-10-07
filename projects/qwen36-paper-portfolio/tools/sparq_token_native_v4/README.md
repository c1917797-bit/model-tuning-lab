# SparQ token numerical v2 — NOT NPU/service ready
An independent new packet based on old SparQ preparation patch
SHA0c045a0d3101b4652fa2797b27c1f866010207fd586774a1823e5110524900f5.
Old v1 is untouched. Algorithm2312.04985v6 GQA support remains approximate
per-head probabilities summed within one local KV group, rank32 channels then
128 full selected tokens/local1/native PA. Mean correction is explicit off/on;
author ANN logits variant is named separately and not admitted by runner.
Official source revision554ea6db219405becbdc0a126984a19f181bdc69; no source copied.

Changes fix actual preparation gaps, not claim algorithm performance:
- independent original BF16-input CPU-FP64 unsplit-history/support golden;
- each request/head RMS/cosine, never six-head mean or native-derived oracle;
- exact full native cache/input/workspace/mean prefix-suffix guards, offsets/backings/pointers;
- all logical/offset/PA table/budget/batch topology and input readonly checks;
- fixed preallocated corrected output, guard bytes charged as extra backing;
- actual case/step SHA Refs, producer stdout marker, full child CLI/source/
  proof/report SHA consumer linkage, not substring docker exec;
- B1..16/eager1 + graph3/mean off/on/160 own-query-feedback=128cases20480steps.

The unchanged native KV remains fully allocated; selected scratch/logits/mean/
guards are additional capacity, NOT saved HBM. Numeric mean payload18576bytes,
actual guarded backing20112bytes. Original relativeRMS.005/cosine.99998 are
unchanged, now EVERY head must pass. Both paused mean leases/full KV including
guard page persist, reset/reuse80 and batch-row rotations are exercised.
Actual numeric cache/prefill/reuse is not a real vLLM model scheduler or allocator.

Pending BEFORE any actual dispatch: MAIN must build a fresh complete owned
source-bound canonical device proof + full safe host producer/observer/cleanup,
actual source/import/PA ABI. The typed proof/CLI/source sentinel SHA checks do
not become optional. This packet provides no controller that fabricates proof.
A whole-device shared host gate must protect0–3 and stop-retain exact CID;
standalone component consumer explicitly returns hardware/retention false.

Pending after numerical component: empty/inactive and actual mixed prefill-decode
model scheduler, TP4/all64layers16FA48GDN, real common allocator scratch/mean
deduction, wholemodel graph, B17..32 quality, frozen matched C16 dense1024 and
final2048 normalEOS/no-thinking tasks. No model/E2E/task/Paper24h authority.

V3 includes original full host/CPU-only ABI/consumer and actual-source eager model seam; see READY.md. Preparation is software-only, never NPU/model readiness.

## v4 independent correction (v3 retained, not admitted)

The CPU-FP64 golden now promotes original BF16 V to FP64, including selected V
and direct historical mean, and asserts every CPU matmul/mixture/result dtype.
No real Torch golden or NPU run happened during preparation.

Candidate-feedback q support is compared with its independent same-query oracle.
Reference-feedback rq keeps its own prior mathematical output. Their support
divergence is retained explicitly and the original rollout numerical thresholds
still apply. Rank32/budget128 checks approximate SparQ implementation, NOT dense
attention or final task equivalence.

Model mode is diagnostic by default. Formal mode removes candidate-only guard
.item synchronization and per-layer JSON/selected/channel .cpu tracing; it uses
the identical core/parameters/source/numeric authority and additionally requires
an actual same-source TP4 diagnostic consumer authority. Original native input/
metadata CPU copies intrinsic to this adapter remain part of measured cost.
No formal TP4 diagnostic authority currently exists.

The consumer directly reads full raw original operation_get structuredContent,
operation.route/target/result.record, and outer operationId. It also preserves
original direct a_exec compatibility; no flattened success file is generated.
Tests use the actual read-only original MA0e85 (Git/software operation, NOT NPU
PASS) and actual MA0e7f not-found envelope; mutated negatives are not authorities.
