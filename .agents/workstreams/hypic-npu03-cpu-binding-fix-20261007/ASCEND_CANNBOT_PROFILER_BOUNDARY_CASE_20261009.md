# Ascend Cannbot Profiler routing and readiness case

Date: 2026-10-09

## Real task

Decide whether the completed HYPIC campaign justifies widening the investigation
from the vLLM-Ascend scheduler/cache seam into CANN, operator, kernel, or HCCL
profiling, and re-prove the expert-source locations before any low-level claim.

## Observed target state

The Skill's historical guidance pointed at `/home/mtuser/cch`. Fresh direct
inspection of `chicaihong01/ma` proved that directory absent. The four source
workspaces are currently under `/cache/cch`:

| Workspace | HEAD |
| --- | --- |
| `cannbot-skills` | `d5e0d44b7a1d2e90c5f0b9fb62970fb3bac89ec3` |
| `vllm-ascend` | `222677fc719c7014879b161ed1dd3ed3276d7a5d` |
| `ops-transformer` | `0684247214bae5abb5cb6dc7d90b34a6ad401cdd` |
| `cann-recipes-infer` | `3ed968171bd42d57874bd96bc242c5868b0e6d59` |

Git's safe-directory protection rejected ordinary worktree queries because of
ownership. Read-only commit identity was obtained through each repository's
explicit `.git` directory; no global Git configuration was changed.

The consulted expert contract was:
`/cache/cch/cannbot-skills/model/model-infer-profiling/SKILL.md`.
It requires routing between framework-integrated and injected collection,
`Level1 + PipeUtilization`, compile/JIT warmup outside the capture window,
separate Prefill/Decode selection, at least ten steady Decode steps by default,
and immediate output validation.

## Routing decision

The HYPIC source-map evidence identifies the current mechanism at the
vLLM-Ascend scheduler/cache materialization seam and explicitly says not to
widen to `ops-transformer`, CANN, HCCL, or physical-card configuration
without profiler evidence. The frozen six-phase performance campaign itself
states that no profiler was used.

Therefore this pass correctly stops at profiler readiness and does not claim a
kernel, operator, communication, or device root cause. Starting a new profiler
capture solely to make the Skill matrix green would change the experiment
scope and add NPU cost without a current unresolved low-level symptom.

## Acceptance boundary

This case validates target re-orientation, expert-source consultation, and a
bounded decision not to over-attribute or over-profile. It does not validate an
actual NPU profiler capture, Prefill/Decode artifact completeness, 47-column
`kernel_details.csv`, HCCL attribution, or a profiler-driven code change.
The Skill remains `partial-evidence` until a real low-level symptom triggers a
fresh bounded capture and artifact audit.

## Subsequent HYPIC profiler diagnostic

The unresolved HYPIC quality regression supplied that concrete symptom later
on 2026-10-09. `HYPIC_PROFILER_PREREGISTRATION_20261009.md` froze a separate
Prefill/Decode diagnostic using the accepted retry21 HYPIC-only service
identity. This does not change the earlier routing decision or the frozen
quality/performance verdicts.

The retry2 Prefill phase completed on physical NPU0-3 with four TP workers,
two warmups outside the capture, 88 clean continuous guard samples, 281
nonempty raw profiler files, and exact owned-resource release. A CPU-only
offline parser in the same pinned image generated complete output for each
rank. The independent replay in `verify_hypic_profiler_prefill.py` passed;
see `HYPIC_PROFILER_PREFILL_AUDIT_20261009.md` for paths and hashes.

The parsed `kernel_details.csv` is 46 columns in torch_npu 2.10.0.post4 /
CANN 9.1.0, with Level1/PipeUtilization config and the detailed pipeline
fields present. The preregistered exact `>=47` column check therefore missed
by one. Its failure is retained. The branch-local maintainer Skill now uses
semantic field checks for future cases, while this case remains partial.

Decode remains unverified. Retry2 and retry4 guards caught the pre-existing
`Maxon4ick_vllm` container briefly entering physical NPU0 before capture;
retry3 failed its preflight before creating a container. None is a valid
Decode profile or a technical failure of HYPIC. See the retry amendments and
their immutable raw roots. The next profiling action is a new-root Decode
attempt only after actual NPU0-3 and port 8223 idleness is proved.
