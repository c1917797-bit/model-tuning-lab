# Model-quality Skill case: r10 terminal request coverage

This is a subsequent terminal observation for the bounded
`ascend-model-quality-evaluation` case. It does not rewrite the earlier r9
checkpoint. The frozen r10 source, raw artifact hashes, exact root and
release receipts are recorded in `HOTPATH_CACHE10R10_TERMINAL_AUDIT.md`.

The original-protocol physical NPU0-3 TP4 candidate persisted 127 sample
files and 381 scored 2048-cap responses. Independent scorer/input/response
replay passed; 214/381 answers were correct in this *single candidate arm*.
The strict scored-request gate rejected the arm: only 366/381 scored
requests had positive post-repair skipped-token evidence on all four
namespace-mapped workers. The remaining 15 requests had boundary and
independent-segment observations but no request-local plan/worker proof.
Sample 86 failed on all three scored repetitions, so the gap is not limited
to repeat reuse. The pinned source did not record per-request planner
failure reasons; a cache eviction or retry explanation remains a hypothesis.

The lane guard and exact owned-container/port cleanup passed. This makes
r10 a valid isolated *negative activation* result for its frozen source,
not a paired quality verdict, HYPIC paper-effect verdict, or proof of a
foreign-card interference root cause. The request-level Skill gate made
the correct rejection; the main Skill remains `partial-evidence` because
its per-request wording is not integrated and the full paired quality
workflow has not passed.

Next gate: use the separately pinned diagnostic source in the predeclared
r11 c8 stress selection, only on actually idle physical NPU0-3. Audit
every scored request and the new request-local fallback reasons. A passing
r11 would admit a fresh original-protocol full candidate; it would not by
itself establish quality or performance. Do not rerun r10 or pair an
activation-invalid arm with a no-cache baseline merely to produce a gap.
