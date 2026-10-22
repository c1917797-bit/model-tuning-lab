# Independent audit v2 source review

Date: 2026-10-22 UTC. Reviewer: `/root/lowobs_readiness_review`.

**Disposition: no deterministic source blocker found for the new, bounded source-only audit.** This review read the complete v2 source, computed its SHA-256, and compared the complete unified diff against the retained v1. It did not execute v2, a remote command, a container, Torch, or any NPU/model operation. It does not establish numerical, lifecycle, pair, performance or accuracy qualification.

## Exact reviewed identities

| File | Bytes | SHA-256 |
|---|---:|---|
| `/workspace/scratch/e65c435145b1/boundary_audit_v2_draft/audit_boundary_source_v2.py` | 6904 | `50bf41cf7e0069e374631cf7672210f923d52e76f466aca41c8509cee5d3d1e7` |
| `/workspace/scratch/e65c435145b1/boundary_prepare_draft/audit_boundary_source.py` | 4631 | `318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533` |

The v2 assigned remote program is:

`/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/boundary_source_audit_v2_20261022/audit_boundary_source_v2.py`

The new output is `/opt/host/vnf/austinov/run-bole-boundary-source-audit-v2-20261022T080000Z`. The audited runtime root remains the already frozen `bound-boundary-ON-v1-20261022T080000Z`.

## Causal scope

MAIN reported that read-only remote evidence `exec06a9` isolated the v1 audit failure to the serialized `--source-ref` dictionary key order: all three Ref fields were equal, and preserving the literal operand from immutable COMMANDS made all model/CPU/bind argv strictly equal. This reviewer did not independently reopen that remote receipt.

The retained `probe_builder_input/command_contract.py`, lines 7–17 and 28–30, independently supports the mechanism: `expected()` uses `json.dumps(sr)` without sorted keys and then requires whole argv string equality. Therefore the repair must preserve the exact recorded caller operand. Replacing strict equality with parsed-object equality would weaken this contract; v2 does not do that.

## Actual diff assessment

1. **Caller adaptation only.** Lines 36–40 retain the raw `--source-ref` string and parse that same string. Lines 71–79 require model/CPU command values to be lists, each with exactly one `--source-ref`, require both recorded parameter strings to equal the raw CLI string, and require the bound Ref fields to equal the parsed Ref. The original full `V.validate(args.source_ref)` follows at line 80. No original command comparison is bypassed, sorted, normalized or weakened.

2. **Independent auditor identity.** Lines 37 and 41–51 require a complete Ref with exactly path/bytes/sha256, the assigned v2 path, an ordinary file without symlink ancestry, a bounded source size and exact whole bytes before validation. Line 66 rechecks the actual loaded auditor through the bound source reader; line 97 rechecks the full Ref after validation. SOURCE_AUDIT records this Ref and its unchanged flag at lines 102–103. This separate auditor is not inserted into the existing host runtime readset.

3. **Original closure retained.** Lines 67–70 require the exact old 4631-byte v1 auditor Ref to remain in the original manifest dependencies and reopen it. The unchanged complete validator, unique proof readset checks and exact actual host readset equality remain at lines 80–96. The proof is not enlarged by v2's independent program Ref and no original runtime dependency is removed or replaced.

4. **New evidence identity.** v2 has a new assigned program directory and fresh output directory. The absent-output check and all exclusive `xb` writes remain. It cannot rerun into the failed v1 output or overwrite frozen runtime files. Source mutation is absent from the executable.

5. **Original limits and false flags preserved.** The exact cutoff `1792672721` / 2026-10-22 12:38:41 UTC, full-phase-fit check, 512 MiB address-space limit, CPU150s, FSIZE16MiB, CORE0 and elapsed check are unchanged. The same complete validator proof must retain the original twenty controls and false NPU/test-executed qualification flags. SOURCE_AUDIT keeps its original schema and fields and only adds independent auditor provenance and the recorded operand. Pair, numerical, performance and formal-performance flags remain false.

## Execution and reader conditions

The existing elapsed check is still post-return validation, not a proactive wall timer. MAIN's previously accepted outer launcher remains necessary: new process, AS512MiB/CPU150s/FSIZE16MiB/CORE0, `alarm(180)`, `execv` of the exact `/usr/bin/python3 -I -B` program and arguments, and AWMCP timeout190. This review does not claim that the actual remote bounded operation has occurred.

The CLI source argument must be copied literally from the frozen COMMANDS operand, without a tool round-trip that serializes the dictionary again. The new `--audit-program-ref` must be the reviewed program's complete expected remote Ref.

MAIN stated that the successor independent reader will explicitly pin this new audit program's complete Ref. That reader must check the Ref itself and the preserved original v1 dependency rather than accepting `audit_program_unchanged=true` alone. Its implementation is outside this v2 auditor diff review.

The existing `BOUNDARY_INDEPENDENT_REVIEW.md` is preserved unchanged. This new note does not revise prior experiment results or convert the failed ON/OFF pair, a source audit or host controls into real-NPU qualification.

`source_only_review_complete=true; remote_execution_verified=false; numerical_qualified=false; paired_gate_pass=false; performance_admitted=false; task_accuracy=false`.
