# Projection continuation v3: source preparation only

Status: **not frozen, not admitted, not executed on NPU**. The user explicitly
authorized continuation with “可以继续穿刺一直到成功”. The old result window still
closes at 2026-10-22 12:38:41 UTC. The new authority document and JSON preserve
that boundary and assign a separate finite internal diagnostic batch ending
2026-10-22 18:00:55 UTC. The six-hour internal cap is MAIN's execution limit,
not a statement that the user supplied a new six-hour result deadline.

## Exact new identities

Let `WS` denote the existing branch-local directory
`/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z`.

| Item | Assigned identity |
|---|---|
| Preparation | `WS/boundary_probe_prepare_v3_continuation_20261022T120055Z` |
| Frozen source, absent until reviewed builder runs | `WS/bound-boundary-ON-v3-continuation_20261022T120055Z` |
| Model output, must be absent | `/opt/host/vnf/austinov/run-bole-boundary-ON-v3-continuation_20261022T120055Z` |
| CPU output, must be absent | Model output plus `-CPU` |
| Preparation controls | `/opt/host/vnf/austinov/run-bole-boundary-source-controls-v3-continuation_20261022T120055Z` |
| Independent auditor source | `WS/boundary_source_audit_v4_continuation_20261022T120055Z/audit_boundary_source_v4.py` |
| Independent auditor output | `/opt/host/vnf/austinov/run-bole-boundary-source-audit-v4-continuation_20261022T120055Z` |
| Batch | `MAIN-BOLE-BOUNDARY-CONTINUATION-20261022T120055Z-ON-V3` |

Deploy `audit_boundary_source_v4.py` into its separate assigned auditor
directory. Other preparation files belong to the preparation directory. The
copied `audit_boundary_source.py` is retained historical source/readset input;
its old identity guard deliberately prevents use as the continuation auditor.
Only the separately reviewed v4 auditor is the new source-admission entry.

## What changes from the reviewed v2 draft

`boundary_probe_v1.py`, `projection_probe_v1.py`, `boundary_delta.py`, both
observer test modules, `metadata_envelope.py`, and all five installed-source
snapshots retain their complete original bytes. There is no new model math,
state update, numerical tolerance, raw tensor dump, GEMM, collective, tracing
scope, D2H allowance, or lifecycle policy.

The continuation changes only these preparation/authority boundaries:

1. New preparation, source, output, batch, and auditor identities; a separately
   pinned authorization JSON and its exact Markdown document.
2. Six original runtime clock files continue to be generated from the same
   fixed qualified ancestor by the original `clock` renderer. Their finite
   3600-second phase and 180-second cleanup remain unchanged.
3. The current ON software coordinator has **three additional cutoff literals**
   outside those six files. The entire current 5440-byte source is pinned to
   SHA `b862faa3ac7763c34af4055e48fef2c3d1140eea023e10de71d73770d13f05cd`;
   only those three literals change. Replacing the new cutoff back yields the
   exact original file. The builder and child validator both enforce this.
4. The old complete `performance_validate.py` retains its exact functions,
   twenty-test enumeration, mathematical/source/runtime checks and command
   closure. Its renderer changes exactly one authority predicate's start and
   cutoff, while adding the existing exact helper/child-lineage hook. The
   inverse control restores the entire original 6933-byte validator.
5. Only `fixed_cutoff` changes inside each of `performance_software_scope` and
   `service_software_scope`. Both entire dictionaries must equal their old
   value with that single substitution. Original test allocations, 300-second
   aggregate software budget, 3600-second owner phase and 180-second cleanup
   remain exact.
6. The new `SHORT_AUTHORITY.json` retains its original schema. Its allowed
   changes are `user_authorization_ref`, `historical_authority_ref`,
   `start_epoch`, `cutoff_epoch`, `cutoff_iso`, `batch_id` and `scope`. The
   historical link is the immutable completed ON-v2 short authority, rather
   than a rewritten copy. Every other field must remain identical.

The original `GOAL_24H_20261021.md`, ON/OFF results, old authority, old source
bundles and all prior failures remain inputs. Their dates and hashes do not
change. See `DEPENDENCY_LEDGER.json` for local old/new source identities and
the remotely verified producer operands supplied by MAIN.

## Review and execution sequence

MAIN must review exact deployed bytes, this authority, the helper source
identities, meaningful preparation controls and immutable parent references
before supplying a new review record. The required review schema is
`bole.boundary-probe-main-source-review/v2-continuation`; it must additionally
contain `continuation_authorization` equal to the exact Ref in
`boundary_integration.AUTHORIZATION_REF`. Existing required helper and control
references remain present. File/hash membership does not automatically prove
that referenced control results passed; MAIN must check their semantics.

The preparation-control runner retains four stages: eleven boundary controls,
eight integration controls, sixteen projection controls and the metadata
capacity calculation. The eight integration controls retain the prior inverse
and complete-source checks and add explicit continuation predicate/coordinator
inversion and malformed-ticket rejections. It keeps each child cap of 30
seconds, whole cap of 120 seconds, address-space cap of 512 MiB and existing
output limits. A local source-only execution of the eight integration controls
passed; that is not host or same-image execution evidence.

The preparation `inputs.files` descriptor must include the four exact immutable
ON-v2 inputs read by the integration controls: `short_binding_delta.py`,
`performance_validate.py`, `performance_software_stages.py` and
`SHORT_AUTHORITY.json`. `run_boundary_controls.OLD_CONTROL_INPUTS` supplies their
fixed complete Refs. The runner requires those exact entries before creating
its output; they participate in the same whole-byte before/after check as the
current preparation files. Omitting these old operands does not qualify as a
complete control readset.

After actual preparation controls and independent MAIN source review, the
builder may create the new source once, if the unchanged full 3780-second
allowance fits. Then run the exact independent v4 auditor and separately bind
its complete source Ref. Fresh same-image **twenty** controls are mandatory on
the new frozen source. An old twenty-control PASS, local eight-control PASS, or
unchanged sixteen-control helper history cannot substitute for that run.

No `MAIN_REVIEW`, `BUILD_RECORD`, `SOURCE_TEMPLATE`, `SOURCE_BOUND`, `COMMANDS`,
CPU pass, NPU pass, or resource admission was created by this preparation.

## Additional downstream dependencies, not supplied by this source draft

MAIN must version the resource-admission configuration and outer launcher for
the new source/output/ticket and 18:00:55 cutoff, retaining all original phase,
cleanup, memory, CPU, device, process-identity and owner-release checks. The
previous admission configuration's 12:38:41 cutoff is historical and cannot
serve as a current admission. The read-only closeout snapshot grants no owner.

The independent result reader likewise needs a new exact source/output/auditor
binding and authority closure. The separate reader-preparation agent owns that
change. The original reader's old cutoff and unbound pins must not be bypassed.

Before dispatch, re-prove physical NPU 4–7 mappings and actual owners,
containers, process start identities, RAM, disk, unused output roots, the MAIN
serialization lock, and prior termination/release. Do not affect physical
NPU 0–3. Only MAIN dispatches a qualified bounded node. Any failure gets its
own retained evidence and cause-specific successor version.

Completing this diagnostic cannot pass the failed ON/OFF state gate or prove
whole-model accuracy. Performance remains blocked until the true-NPU numeric,
multistep, lifecycle, and low-observation path gates pass. Formal acceptance
still requires the original same-configuration fixed-1024 dense/candidate
pairs with at least 10% throughput improvement, separate TTFT/TPOT, and final
GSM8K/HumanEval/MMLU under the prescribed thinking/EOS/output/accuracy protocol.
