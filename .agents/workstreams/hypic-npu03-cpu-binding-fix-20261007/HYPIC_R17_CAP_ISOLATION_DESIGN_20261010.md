# r17 output-cap isolation design — not yet admitted to devices

Purpose: resolve a *ruler sensitivity* question inside the HYPIC E2E
workflow, not repeat r13–r16 or run an isolated GDN operator. The
2026-09-06 accepted Qwen3.6/TP4 experiment used max-1024/c32 quality
and both LongBench-v2 and GSM8K. r16 used the original `3ad0967`
source on NPU0–3 at max-2048/c8: the full LongBench-v2 pair was
224/381→210/381, `REJECT_OR_QUALIFY` under its stricter frozen gate.
That 3.6745 pp fall is nevertheless below its baseline three-run
range of 5.5118 pp. Of 30 regressed paired responses, 16 became
newly length-limited and 14 did not. Neither a specific numerical
defect nor historical full acceptance follows.

## One-variable successor

Use the same pinned Qwen3.6-27B weights, official image, original
HYPIC commit `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`, TP4,
physical NPU0–3, CPU112–191, source attestation, context41984,
memory fraction0.85, material cache3584MiB/10 segments, native
prefix cache disabled, the same 127 LongBench-v2 IDs/prompts/scorer,
explicit segment boundaries, temperature/seed0, thinking off, natural
EOS, c8, two one-token warmups and three scored requests per sample.
Change **only** the scored request output cap from 2048 to 1024.
Run a fresh no-cache arm and a fresh HYPIC-only arm, serially, with
new immutable roots and distinct owned containers; only the HYPIC
enable switch differs within the pair. Never reuse the r16 2048
baseline as the 1024 denominator.

Before device admission, record exact source/model/image/dataset/
evaluator/controller hashes, new root/container/port IDs, response
limits, baseline and candidate order, the complete audit script and
its no-side-effect tests. Prove root absence, direct `chicaihong01/ma`
route, actual NPU0–3 and port idleness. Controller must continuously
guard physical processes and release only exact owned resources.
Handle retryable gateway timeouts by recovering the same idempotency
key/operation, never launching a second controller. NPU4–7 and
foreign work remain untouched.

Independently audit 127×3 hashed and rescored responses per arm,
request-ID/boundary coverage, source/service identity, guard samples
and exact release. Report all-request correct counts, paired flips,
three-run variation, difficulty/length strata, finish reasons and
HYPIC activation evidence separately. Use the **same frozen r16
floor/category/length-limit gate** for the primary r17 current-skill
decision, and also show the historical baseline-range comparison as
a clearly labeled descriptive lens; do not alter either old verdict.
The original source lacks per-scored-request four-worker proof, so
aggregate hot coverage and serialized sentinel must not be promoted
to universal in-path evidence. Do not borrow r13 performance.

If r17 is better than r16, that is a cap-sensitivity signal, not a
causal estimate across different service lifecycles. A further
prospective cap crossover or direct numerical-path proof is needed
before assigning cause; c8→c32 and cache residency are separate
variables. GSM8K, deterministic canary and matched performance remain
separate gates before full Skill/paper acceptance. A rejected quality
gate blocks performance *adoption* claims but does not erase valid
mechanistic diagnostics.

Admission status: **design only**. No r17 controller, root or NPU job
exists by virtue of this note. The r16 full pair took roughly three
hours, so this cannot finish before the earlier 04:42:44Z milestone;
report that schedule miss plainly rather than abbreviating the full
suite or reusing mismatched evidence. Obtain exact script/offline
preflight results before any run.
