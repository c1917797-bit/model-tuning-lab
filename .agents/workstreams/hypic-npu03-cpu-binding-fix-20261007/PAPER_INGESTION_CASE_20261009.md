# HYPIC paper ingestion: bounded hypothesis and source identity

Status: **partial-evidence**, reviewed 2026-10-09 against exact
`origin/main=ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`.
This retrospectively ingests the paper for an experiment already under way;
it cannot convert an omitted pre-implementation applicability review into a
historical pass. No NPU was used and no unchanged benchmark was rerun.

## Identity and source boundary

- Research paper: *Hypic: Accelerating Hybrid-Attention LLM Serving with
  Position-Independent Caching*, arXiv:2607.01299v2, 2026-07-12,
  https://arxiv.org/html/2607.01299v2 (versioned paper, reviewed 2026-10-09).
- Public project page reviewed on 2026-10-09:
  https://github.com/redai-studio/HYPIC . Its README presents the same paper
  and an Apache-2.0 repository license. Its install example still names
  `redai-infra/HYPIC`, which currently redirects to `redai-studio/HYPIC`;
  this is a repository move, not evidence of two distinct source projects.
  The lack of a fixed upstream Git commit means this case does **not** prove
  byte-for-byte paper-to-code identity or redistribution rights for every
  downloaded artifact. The
  retrospective architecture audit records a ten-file upstream-source
  aggregate SHA256 `9ed7595aee682d7461fa2058156d625962ac6b5fa82e9cedba80521fb06f02de`;
  that is a snapshot hash, not a Git revision.
- Target is a different vLLM-Ascend derivative: local plugin Git
  `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`, not the authors' SGLang
  runtime. Its later experimental source `c12060c` is yet another pinned
  derivative revision and must not be conflated with the author project.

## Mechanism translated into implementation hypotheses

| Paper part | Inputs and changed state/dataflow | Target decision |
| --- | --- | --- |
| C1, linear attention | Cache each independent segment's zero-start end-state plus cumulative transition; compose with incoming recurrent state instead of replaying every segment token. Dense GDN transition storage and first-prefill accumulation add work and HBM cost. | Candidate single-instance text hot-reuse path, conditional on actual segment boundaries and cache residency. |
| C2, full attention | Relocate segment KV and recompute a small beginning/seam window through the hybrid stack to repair cross-segment context. Extra recompute and boundary bookkeeping are costs. | Candidate only with observed seam/worker activation and paired quality. |
| C3, cold prefill | Router sends independent cold segments to multiple **model replicas**, transfers caches and combines them; LPT scheduling and transfer overlap address tail TTFT. | Not implemented/tested by one TP4 replica on NPU0–3; TP4 ranks are not four replicas. |

The paper's SGLang/Triton/NIXL/GPUDirect transport and distributed router
are paper-specific implementation assumptions, not automatically portable
Ascend components. Its author-reported speedups and quality gap are paper
claims against their baselines, not local measurements or acceptance targets.
The local one-switch hypothesis is `VLLM_ASCEND_HYPIC_ENABLE=0/1` with the
same model, image, TP4, physical cards, CPU-binding repair, request payloads,
cache budget, evaluator and stop protocol in both arms. It predicts a
reused-segment Prefill/TTFT benefit and may incur transition storage,
first-prefill, seam-recompute and cache-miss overhead. Decode and quality
must be measured independently; one benchmark percentage is not transferable
to another workload or lane.

## Target prerequisites and evidence

- Current `/cache/efim/Qwen3.6-27B/config.json` SHA256
  `69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c`
  reports `Qwen3_5ForConditionalGeneration` / `qwen3_5`, 64 text layers:
  48 linear and 16 full attention, text dtype `bfloat16`. The directory name
  is not proof of a distinct Qwen3.6 architecture. Model index SHA256 is
  `a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`.
- C1/C2 require exact tokenized segment boundaries, cache residency,
  compatible GDN/attention layout and scheduler-to-worker proof. C1/C2 do not
  require checkpoint retraining for this tested text path. The existing
  `PAPER_ARCHITECTURE_FIT.md` separately documents passing bounded source
  audits and expected full-scope C3 failures; source-symbol checks alone do
  not prove NPU behavior.
- Natural clean2 evaluation had valid rows but zero worker-hot activations
  because ordinary chat requests lacked explicit segment boundaries. The
  current r12 explicit-boundary stress got 52/57 scored four-worker proofs,
  not 57/57. These are different experiment identities and do not form a
  final accuracy pair. C3, multimodal, MTP, native-prefix coexistence and
  cross-host communications remain untested for this derivative.

## Applicability decision and next checks

The first bounded hypothesis is **fit for testing**, not accepted for
deployment: C1/C2 on this hybrid text checkpoint in one TP4 instance can be
investigated with a same-identity no-cache/HYPIC pair and explicit segment
boundaries. The full paper is **not** fit-now because distributed C3 is absent.
The main Skill's paper-ingestion workflow is exercised on a real paper and
model, but exact author-code revision, paper-to-code mapping, complete
request-level activation, matched max-2048 quality and current performance
remain open. The branch Skill has extra bounded/full-scope and retrospective
instructions that are absent from exact main; this case does not attribute
those branch-only instructions to main.

Before any final acceptance: pin and review the upstream code revision and
license scope; freeze the claim rule and same-identity c8/2048/127 protocol;
run only on actually idle physical NPU0–3 with continuous foreign-PID guard;
audit complete paired quality, repeated performance, mechanism, capacity and
resource release. Keep C3 a separate multi-replica research workstream with
new authority/resources rather than relabeling TP ranks as replicas.
