# Text-only boundary diagnostic successor: local review draft

This directory contains a source-only draft for a fresh ON boundary/projection
diagnostic. It does not contain a frozen SOURCE_BOUND, a resource owner, a new
native parser result, a same-image software result, or an NPU result. The two
authorization documents were copied byte for byte from MAIN's locally frozen
documents and bound by their actual complete Refs. They have not been deployed
by this child agent.

## Minimal semantic change

The existing command builder adds exactly one native option:
`--language-model-only`. Its source manifest, the actual argv, the actual native
parser and the actual `AsyncEngineArgs` must agree on:

| Field | Required value |
| --- | --- |
| `language_model_only` | Python `True` |
| `skip_mm_profiling` | Python `False` |
| `enable_mm_embeds` | Python `False` |
| `limit_mm_per_prompt` | An empty Python `dict` |

`contract090.source()` checks the source field. The existing
`cache_memory_config(argv, m, args=args, engine=engine)` joins those fields with
the actual native parser and EngineArgs. Missing attributes, integer values in
place of booleans, duplicate flags, alternate boolean forms, MM embeddings,
modality-limit overrides and skip-profiling are rejected. No missing attribute
is supplied a passing default. The old cache-memory function still returns
exactly its original three-field dictionary and retains every old assertion.

The actual retained `preflight114.py` has been read in full. It invokes the real
API parser, validates parsed serve arguments, constructs
`AsyncEngineArgs.from_cli_args(args)`, and passes both actual objects to the
existing cache-memory function. This file stays byte-identical in the child;
the new lineage gate also pins its byte count and digest to the actual retained
file. A future CPU PASS from this entry is required. The synthetic Namespace
objects in the local source controls test the guard's rejection behavior only.
They are not evidence that the native parser accepts the configuration.

The exact old command contract is transformed after the existing
`B.bind_outputs(...)` call in both the source assembler and the original full
validator. The new renderer has three exact source substitutions and one pure
configuration function append. Its explicit inverse restores every old byte.
The full old validator body is preserved after removing the helper-pin/lineage
hook, replacing the declared authority predicate, and removing the single new
contract-render line. The original full-file runtime comparisons remain active.

The only new manifest fields are `text_only_config` and
`text_only_preparation_evidence`. Every evidence Ref is included in the host
dependency set, opened with the original complete-Ref reader, checked by the
new lineage gate, and covered by the unchanged before/after host readset.
The evidence field contains the actual failed-startup RESULT, the actual CPU
parser caller, two native-source read receipts, and twelve complete native
source snapshots mapped by their installed guest paths.

## What stays unchanged

The previous `boundary_probe_v1.py`, `projection_probe_v1.py`,
`boundary_delta.py`, both observer test files, metadata calculation, historical
auditor, and five projection source snapshots remain byte for byte unchanged.
The five-helper runtime closure is unchanged. Model mathematics, numerical
thresholds, TP4, physical NPU 4–7, 131 input tokens, two eight-token requests,
retirement barrier, all worker-state requirements, and the existing lifecycle
code are retained. The phase remains 3600 seconds, cleanup 180 seconds, and
whole admission 3780 seconds.

The current same-image software suite remains exactly the original 20 cases in
`test_short_state_digest.py`, `test_digest_reader.py`, and
`test_short_dependency_contract.py`. The full coordinator and exact-control
entry were reviewed: they reopen the historical 381-case proof, mark it as not
freshly executed, and execute only the current 20 cases. The historical
`test_cache_budget131r16.py` uses three-field Namespace fixtures; it would not
satisfy the new strict four-field join if separately invoked. It is outside the
current suite and is not altered, skipped, or represented as a fresh PASS here.
No required current test or assertion has been removed.

## Exact new identities

`WS` is the existing workstream:
`/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z`.

| Purpose | New identity |
| --- | --- |
| Preparation | `WS/boundary_probe_prepare_v4_textonly_20261022T171000Z` |
| Bound source | `WS/bound-boundary-ON-v4-textonly_20261022T171000Z` |
| Model output | `/opt/host/vnf/austinov/run-bole-boundary-ON-v4-textonly_20261022T171000Z` |
| CPU output | Model output plus `-CPU` |
| Host source controls | `/opt/host/vnf/austinov/run-bole-boundary-source-controls-v4-textonly_20261022T171000Z` |
| Independent auditor preparation | `WS/boundary_source_audit_v5_textonly_20261022T171000Z` |
| Independent auditor | `audit_boundary_source_v5.py` |
| Independent auditor output | `/opt/host/vnf/austinov/run-bole-boundary-source-audit-v5-textonly_20261022T171000Z` |
| Batch | `MAIN-BOLE-BOUNDARY-TEXTONLY-20261022T171000Z-ON-V4` |
| Internal batch clock | 2026-10-22 17:10:00–23:10:00 UTC, epochs 1792689000–1792710600 |

The user's old report deadline remains 2026-10-22 12:38:41 UTC. This is a new
finite internal batch under the repeated continuation instruction. No old
source, authorization, output, result, or deadline is rewritten. The authority
documents identify their actual later recording checkpoint rather than claiming
17:10:00 is a verified user-message timestamp.

The independent auditor retains schema `bole.boundary-source-admission/v1` and
requires the literal source-ref operand recorded in immutable MODEL and CPU
commands. It does not reserialize that operand. The source assembler continues
using the existing command contract, so key order remains an actual immutable
argument property.

## Actual evidence and its limits

MAIN provided and this child read the retained failure and native-source
materials. The v3 model failed in startup before diagnostic requests, while the
host later recorded a health-probe timeout. Its result remains a failure. The
asynchronous AI Core stack in the MM encoder profile does not locate the first
failing kernel or establish an observer, BOLE, or hardware cause.

The native source path is consistent with a pure-text service: the registered
multimodal predicate returns false when every supported modality limit is zero
and MM embeddings are disabled; the runner then does not construct its MM
budget or enter its encoder profile. Qwen3.5's visual component is created under
`_mark_tower_model`, which uses meta initialization and `StageMissingLayer` for
zero limits, and `AutoWeightsLoader` skips that missing layer. These are source
findings. This draft does not claim the new actual worker took those branches,
that its measured encoder budget is zero, or that the former kernel failure is
fixed. Native ModelConfig construction and worker startup still require real
execution after independent admission.

The original corrected ON/OFF state comparison remains failed; this ON-only
diagnostic cannot pass that pair. It also cannot qualify the separate low
observation path, admit 1024-token whole-model performance, or establish the
final GSM8K/HumanEval/MMLU accuracy condition.

## Local validation completed

`local_validation/RESULT.json` contains raw stdout/stderr and before/after input
Refs. The eight existing integration-control methods passed after adding
focused assertions inside one existing method for the contract inverse, strict
field types, missing attributes, conflicting flags, and unchanged original
memory-checker AST. The full original validator and coordinator inverses passed.
The actual retained parent contract's complete bytes were independently read by
MAIN and are identical to the local 4301-byte control input. Every preserved
observer/helper whole file was compared. The new modules parsed successfully.
An unbound authorization Ref was explicitly rejected by the new frozen-input
guard. These results are source-only local checks, not the same-image 20-case
suite or a native parser run.

The identity-only whole-body preview of `owned_substrate.py` is 3579 bytes,
SHA256 `27a239407e8e1fcab40c9698cab12904772abacfdbca3a0e16e078c01f197df3`.
It changes only the cutoff epoch/ISO on the retained whole body. The preview has
not been frozen as a runtime source; MAIN must verify the actual generated child
file has this exact Ref before binding its lifecycle admission context.

## Remaining work owned by MAIN

1. Finish independent review of this draft and the separate lifecycle-admission
   draft, then materialize the specified new preparation files without altering
   any old inputs. Native read receipts and snapshots already have actual Refs;
   no required source file identified by this subtask is still missing.
2. Run the bounded host source controls with their complete input descriptor,
   including the old parent contract Ref. Freeze the new source only after
   review and matching actual controls. Run the new independent auditor using
   the exact command operand and auditor Ref.
3. Recheck complete live topology, devices, retained owner cleanup, processes,
   containers, RAM, actual Docker-root disk, exclusive outputs and serialization.
   Then run the original same-image 20 cases and the real Devices[] parser entry
   before any NPU model owner, using the existing admission/lifecycle machinery.
4. Only a newly admitted NPU diagnostic can supply the missing runtime evidence.
   Its result must be classified accurately, preserve the old failures, and
   retain all original numerical and state requirements.

## File routing

`DEPLOYMENT_FILES.json` names only the preparation files and the separately
routed v5 auditor. `make_draft.py`, `check_local_draft.py`, local control-input
copies, local result/preview files, this README, and the comparison diff are
review aids. They are not runtime helpers or command entrypoints and must not
be substituted for the original preparation/control/audit programs.
