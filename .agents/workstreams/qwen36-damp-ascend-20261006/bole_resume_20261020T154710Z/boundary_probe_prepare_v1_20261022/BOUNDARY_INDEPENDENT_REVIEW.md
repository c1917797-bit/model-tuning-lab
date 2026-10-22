# Boundary observer independent source review

## Scope and disposition

Reviewer: `/root/lowobs_readiness_review`, 2026-10-22 UTC. This is a **source-only independent review** of the local frozen candidate and MAIN's preparation scripts. This reviewer did not run a remote command, create an owner/container, import Torch, execute a model, run the proposed source-control suite, or modify any reviewed source. Reading and hashing local files are the only verification performed for this report.

No remaining deterministic blocker was found in the final helper/delta for the declared, bounded **ON-only diagnostic**. The retirement serialization issue and the missing final accounting boundary identified during review are closed in the pinned versions below. The three orchestration scripts preserve the complete original validator and require an exact host readset. A resource-boundary omission in the standalone prepare/audit executables was reported to MAIN; MAIN accepted an outer bounded launcher without changing these three source files. That launcher's remote execution receipt has not been independently observed by this reviewer.

This disposition is not numerical qualification, lifecycle qualification, ON/OFF equivalence, performance admission, or task-accuracy admission. The previous short ON/OFF pair's actual failure remains unresolved by this review. All such qualification flags remain false.

## Reviewed byte identities

All paths in this table are relative to `/workspace/scratch/e65c435145b1/`. SHA-256 and byte counts were independently reopened from the local files when this report was written.

| Local file | Bytes | SHA-256 |
|---|---:|---|
| `boundary_probe_draft/boundary_probe_v1.py` | 30245 | `24f12bae4c583d076d264e435578138de37ffddbf98e8175314b684ae420657b` |
| `boundary_probe_draft/boundary_delta.py` | 9525 | `17b95c2ed565f3aead8a4a6ac783f5ce9a6c66c99e168449c0d1e293fe9abf3c` |
| `boundary_probe_draft/rendered_v3/performance_host.py` | 6958 | `4ddb6f48220423577aaeaf232bb1fb05ecf94d4199bf816d271a81f3b5171b8b` |
| `boundary_probe_draft/METADATA_ENVELOPE.json` | 894 | `50234aeecd7e06b46b82be267d6724415606af7f2bd2105ade54609b767d6edc` |
| `boundary_integration_draft/boundary_integration.py` | 5271 | `00a7fc7a806d558cbbb9c0672608a02c423e3d6351038aa98c1f105e39f5fc4a` |
| `boundary_integration_draft/boundary_validation.py` | 10201 | `12e86c9e82a5238f6556dd7110adeee34da2057dc1579d5e0bb319a9e5f0b429` |
| `boundary_prepare_draft/prepare_boundary.py` | 11609 | `efcc7f00d433c78b690441e5947eb43e3aeb6f733b1b6668332fbe00e04f2452` |
| `boundary_prepare_draft/run_boundary_controls.py` | 7703 | `011a4ab26d8e0bc3498b27de5f3209cb3b3d0774844bbce5723345d4113d7380` |
| `boundary_prepare_draft/audit_boundary_source.py` | 4631 | `318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533` |
| `probe_builder_input/performance_validate.py` | 6933 | `c45e114ab03fd35a47c85c8dd6f70bb71bbc406fa08be151222d082d8d57d824` |
| `probe_builder_input/host_service.py` | 16263 | `c47ab542ad0691c3358378a043fbb85380b772b23c7e3a707e34c9eccb78bd4c` |
| `old_runtime_review/evidence/gdn.py` | 21887 | `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816` |
| `old_runtime_review/evidence/service_runtime/qwen_patch.py` | 8743 | `21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3` |

The exact retained ON parent required by the preparation and integration is:

`/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json`

Its required Ref is 1503149 bytes, SHA-256 `a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f`. This report checks the local scripts' binding to that identity; it does not claim a new remote read of that parent.

## Helper and delta findings

### Actual API, shapes, and return preservation

The helper's layer-0 core shape is `(131, 12, 128)` and its gated-normalization shape is `(1572, 128)`. Projection, post-normalization hidden/residual, and MLP logical shapes are `(131, 5120)`; mixed QKV is `(131, 2560)` and the two gate inputs are `(131, 12)` (`boundary_probe_v1.py`, lines 18–27). These agree with the retained GDN implementation's core allocation, flatten/norm/reshape/projection sequence (`gdn.py`, lines 119–145), and the retained decoder's two-value post-normalization result and single MLP output (`qwen_patch.py`, lines 136–148).

Each observation hook returns `None`, validates the actual module identity, and compares the complete output object's tensor/container signature before and after observation (`boundary_probe_v1.py`, lines 355–389). The native core wrapper calls its existing `_old(...)` and returns the same `result` (`boundary_delta.py`, lines 62–76). The delta adds no replacement mathematical function or new NPU state write. The observer does blocking D2H copies followed by CPU finite checks and hashes; it does not claim to be scheduling-neutral.

### Actual ownership, generations, and lifecycle

Worker, runner, model, current request, CPU batch row, actual tensor object, storage pointer/size, data pointer, offset, shape and stride are observed from runtime objects (`boundary_probe_v1.py`, lines 251–285). Generation entry requires the previous request to have retired and retains distinct actual request objects and IDs. The observer requires 48 ordered native GDN returns, all nine selected raw stages, 64 real bindings, and joins native objects/metadata/physical slots to the registered request and arenas (`391–465`). The five registered capture phases are checked in order (`470–494`).

The existing request retirement implementation, tree execution, request restorers, bridge restoration, prefill rearming and final restoration are retained. `boundary_delta.py` adds callbacks around those existing transitions; it does not replace `bole_performance_lifecycle.py`. Creation remains at the original first capture installation point after existing source checks. The added own-hook restorer is included in existing restoration handling (`boundary_delta.py`, lines 23–59; rendered `service_runner.py`, lines 304–309 and 709–720).

The first identified serialization defect is closed: the actual retirement record can contain the original Owner dataclass. The final helper uses the already source-pinned `PERF.metadata_value` to normalize it, hashes the normalized record, and emits only bounded primitive retirement fields (`boundary_probe_v1.py`, lines 194–203 and 522–540). It does not mutate or copy the full original record into the metadata envelope.

Uninstall verifies each handle is still the actual installed observer before removal; it does not remove a foreign replacement. Successful repeated uninstall is empty/idempotent (`559–566`). `COMPLETE.hooks_removed` proves removal of this observer's hooks only. Whole-model native restoration and cleanup still depend on the original retirement, barrier, final snapshots and cleanup proofs.

### Explicit default OFF

The disabled `select`/factory paths return before source reads, tensor work, hook installation or output creation; no declaration is allowed when the flag is absent, empty or `0` (`57–65`, `170–175`). Enabled selection requires both exact declaration bytes and `BOLE_NATIVE_BOUNDARY_PROBE_ENABLE=1`. The integration independently checks this disabled factory and retains `default_enabled=False` (`boundary_validation.py`, lines 59–70).

## Resource accounting and final boundary

| Quantity | Source-bound value | Meaning |
|---|---:|---|
| Cumulative additional D2H per rank | cap 536870912 B | Incremental boundary-observer copies across both generations, not all historical ON instrumentation |
| Calculated maximum additional D2H | 515220032 B | Source-only arithmetic; margin 21650880 B |
| Retained raw slices per rank | 836352 B, 18 files | Exactly two generations of the nine final-eight-token slices |
| Probe metadata cap | 524288 B | Runtime cumulative writer cap |
| Fabricated metadata envelope | 501961 B | Capacity calculation only; margin 22327 B |
| Largest calculated metadata file | 51151 B | Below per-file cap 131072 B |
| Calculated file count | 148 | Below direct-file cap 160 |
| Original `other` / metadata / raw caps | 3 MiB / 64 MiB / 1 GiB | Not increased by this delta |

The D2H upper bound derives from two generations, six observations of all 48 selected GDN state/conv slots at maximum convolution width 16, nine complete logical raw-stage reads per generation, and the additional native-layer-0 projected-input reads:

`2*6*48*(12*128*128*4 + 16*2560*2) + 836352*131/8 + 2*(131*2560*2 + 2*131*12*2) = 515220032`.

The runtime counter is incremented for every logical D2H read before copying and is bounded cumulatively; no per-generation reset exists (`boundary_probe_v1.py`, lines 214 and 276–285). Actual BF16 raw slices and full FP32 state slots are read without converting their native numeric encoding.

The writer uses exclusive single-copy files. It checks the original real budget before and after each write and deliberately retains partial files on failure. Directory accounting includes every direct ordinary boundary file, even incomplete writes (`68–78`, `119–164`, `233–241`). The `g3_budget.py` delta includes probe raw and metadata in the existing `other` bucket, plus MTP-load and worker-snapshot staging forms. Sets avoid repeat charges for overlapping patterns within that bucket. Short state digests are included in aggregate metadata accounting. No original cap is expanded (`boundary_delta.py`, lines 92–108; rendered `g3_budget.py`, lines 27–70).

The source-only envelope's `original_other_actual_max=1668008` and calculated `3071857 <= 3145728` are retained inputs/calculations from the supplied envelope, not independently re-observed new-run measurements. They cannot replace runtime accounting.

The second identified gap is closed: observer `COMPLETE` precedes later performance metadata and final worker snapshots. `terminal_accounting` now runs after the actual final four-worker snapshots and before the existing consumer. It pins its actual helper/budget/contract source, reopens the actual bound source, recomputes all four ranks with `B.actual`, checks unchanged 3 MiB/64 MiB/1 GiB caps and summary headroom, and joins rank/source/generation-2 COMPLETE records with own hooks removed (`boundary_probe_v1.py`, lines 81–116; rendered `performance_host.py`, lines 109–123). The independent post-run reader still needs to verify the actual final evidence. This is source closure, not proof that a future run fits.

## Preparation and validator preservation

`boundary_integration.py` starts from the complete SHA-pinned old delta and old validator. It performs exact-one-occurrence composition, retains the old runtime transform, and adds only the reviewed helper pins and child-lineage hook to the validator (`43–53`, `71–101`). The old validator still derives the complete expected runtime source with `D.runtime`, compares whole-file text, closes the explicit delta ledger, retains the unchanged numeric/component/common fields, checks all source refs, enumerates the original 20 tests, and preserves the aggregate 300-second same-image software budget (`probe_builder_input/performance_validate.py`, lines 29–68).

The added `boundary_validation.py` checks actual loaded helper identities, complete new source membership, exact old-parent semantics, unchanged non-permitted files, original numerical lineage, exact authority and dependencies, and preservation of those 20 controls. It requires the same user cutoff **2026-10-22 12:38:41 UTC / 1792672721**, phase 3600 seconds, cleanup 180 seconds. Only the new diagnostic batch identity and narrower scope change (`101–153`). No new experiment authority is created.

`prepare_boundary.py` requires the precise review schema/parent/helper identities, whole-file Ref3 equality, a fresh source root and both model/CPU output identities, and original inputs rechecked before recording completion (`79–128`, `208–218`). Writes to copied files are assembly within the new unfrozen root. Frozen manifests, command records and build receipt use exclusive creation. A failed partially created root blocks reuse; it is not overwritten. This script assembles a source and does not itself qualify it.

`run_boundary_controls.py` uses a fresh output directory, exclusive raw stdout/stderr and result files, source inputs before/after, three owned child processes with individual 30-second limits, and a 120-second successful-result limit. The separate 11 observer and 8 integration controls plus one capacity calculation do not replace the original 20 same-image controls (`80–148`). MAIN stated that the input descriptor will pin the ten Python files and exact old delta/validator operands; that specific descriptor and remote result are not created or verified by this reviewer.

`audit_boundary_source.py` invokes the complete newly bound `V.validate`, requires false NPU/test-executed qualification flags and the original 20 test names, checks the proof's exact references, then reconstructs:

`bind_model.readset(source) + manifest.dependencies + command_contract.validate(...)`.

It requires equality of this exact actual host set and the validator proof set, followed by rechecking every reference (`45–75`). It is not a subset check. The formula agrees with the retained `host_service.py` actual entry readset. MAIN's review and the audit runner are included as preparation dependencies; the four helper hashes are also embedded in the new validator. Successful execution of this audit is still required to establish the assembled manifest's actual closure.

## Standalone time-bound gap and MAIN's accepted execution boundary

At the reviewed bytes, `prepare_boundary.py` has no internal address-space or proactive wall timer; its initial `now + 3780 < cutoff` check is an authority-fit check. `audit_boundary_source.py` sets 512 MiB address space and CPU/file/core limits, but checks its 180-second elapsed bound only after synchronous validation returns. CPU limits alone do not bound blocked file I/O. The controls runner installs limits and starts its 120-second clock after initial descriptor/input prechecks. These facts were reported to MAIN before source execution.

MAIN accepted the following separate command-level constraint while keeping the three reviewed files unchanged: a new Python launcher sets `RLIMIT_AS=512 MiB`, `RLIMIT_CPU=150 s`, `RLIMIT_FSIZE=16 MiB`, `RLIMIT_CORE=0`, calls `signal.alarm(180)`, and then `os.execv` of `/usr/bin/python3` with `-I -B` and the exact target script/arguments. An outer AWMCP execution timeout is 190 seconds. The alarm survives exec with default signal disposition; prepare/audit create no child processes. Controls retain their own 30-second process-group cleanup and 120-second result limit; the 180-second outer alarm is a fallback.

That design covers the reported execution-boundary gap without weakening source or runtime gates. MAIN must retain the actual operation receipt containing exact argv and timeout. This reviewer has not executed or independently reopened that remote receipt, so the report records the accepted design, not a completed remote bounded-run claim.

## Remaining interpretation limits and next gate

- A blocking observer can change execution scheduling. A mismatch that disappears under observation does not exclude a race.
- MTP inventory records real tensor/storage geometry. It does not establish active write extents or prove alias exclusion; shared allocation alone is not alias-bug evidence (`boundary_probe_v1.py`, lines 499–520).
- This proposed run has 131 input tokens and two eight-token requests. It is a diagnostic and cannot serve as formal fixed-1024 dense/candidate performance evidence.
- Old short-arm completion, these source controls, and a source audit cannot pass the failed ON/OFF pair, qualify the separate low-observation path, or admit performance. After any diagnostic evidence, the numerical, multistep and lifecycle requirements still apply to the actual candidate path before a same-configuration whole-model screen.
- No new >=10% whole-model throughput gain, TTFT/TPOT result, or final GSM8K/HumanEval/MMLU accuracy acceptance is established here. No authority beyond the user's fixed deadline is inferred.

Disposition: **SOURCE_ONLY_REVIEW_COMPLETE; remote_execution_verified=false; numerical_qualified=false; paired_gate_pass=false; performance_admitted=false; task_accuracy=false.**
