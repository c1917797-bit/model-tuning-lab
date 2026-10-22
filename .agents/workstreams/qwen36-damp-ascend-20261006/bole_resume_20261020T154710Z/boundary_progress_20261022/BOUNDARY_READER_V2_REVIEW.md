# Boundary reader v2 and one-shot runner: independent source review

Date: 2026-10-22 UTC. Reviewer: `/root/lowobs_readiness_review`.

## Disposition and scope

**No deterministic blocker was found in the reviewed v1-to-v2 delta and complete runner for the two declared read-only modes, with MAIN's specified outer guard.** Controls mode may execute only its thirteen CPU controls. Actual mode additionally requires the three complete, actual source/result/audit Refs. Neither mode grants permission for another model run or changes the failed original ON/OFF pair's status.

This review independently read the complete supplied diff, recomputed that diff from all three v1/v2 file pairs and confirmed exact equality, read the complete 469-line runner, and checked the added reader gate and surrounding original source/readset/finalization calls. It read the unchanged thirteen-test source to verify the declared controls-only scope. It did not repeat the completed analysis of the entire original reader, execute controls/the reader, perform a remote operation, import Torch, or use an NPU. Only this new review note was written.

## Exact local source identities

Paths are relative to `/workspace/scratch/e65c435145b1/`.

| File | Bytes | SHA-256 |
|---|---:|---|
| `boundary_reader_v2_draft/read_boundary_result_v2.py` | 64411 | `99cba03e1777cff4432a034a10801a5acb5fb7dc6546d12289bc47619f713d00` |
| `boundary_reader_v2_draft/run_boundary_reader_once_v2.py` | 26795 | `052fa4c4c02654d2e3c62966dd707557407ab1feb006849db5a9cde6b88f7086` |
| `boundary_reader_v2_draft/test_boundary_reader_v2.py` | 9374 | `70a82bdd6b48a41857cf46a81d251d9beec3814cd1ab61d0e436c30124fdda24` |
| `boundary_reader_v2_draft/V1_TO_V2.diff` | 8473 | `b591a2001c4a601d8d3cf77dcc985e783a932075623a526282b11d7a47f9c19b` |
| `boundary_reader_draft/read_boundary_result_v1.py` | 62075 | `3a278075f3d33bfea8ef39f266bd04a23a2c49b66cd3a645806512fb05c71089` |
| `boundary_reader_v2_draft/V2_LOCAL_LINEAGE_CHECKS.json` | 799 | `9f8cc04403d9ef62f4f6ff92106d1430639cf3312533cb6a4ea98b1673824ba5` |

The supplied local lineage-check record describes synthetic predicate inputs only, explicitly says no actual source/result read and no remote/NPU execution, and is not treated here as a new run or as tests independently rerun by this reviewer.

## Added v2 auditor gate and unchanged host closure

The reader fixes the new audit output path to `/opt/host/vnf/austinov/run-bole-boundary-source-audit-v2-20261022T080000Z/SOURCE_AUDIT.json`. It fixes the complete auditor program Ref to the assigned workstream path `boundary_source_audit_v2_20261022/audit_boundary_source_v2.py`, **6904 B / `50bf41cf7e0069e374631cf7672210f923d52e76f466aca41c8509cee5d3d1e7`**. The original v1 auditor remains fixed at **4631 B / `318abb0246fce440ba877c8428cbcc1dd90caea7846be76a884c5e26cb4b5533`** (`read_boundary_result_v2.py`, lines 23–27).

The new `independent_audit_lineage` requires these exact Refs in the audit's provenance, requires the original auditor in both manifest dependencies and the original audited set, and performs full reads of both programs (`229–240`). Those reads enter the common final reader input reread. The new program is not inserted into or substituted for the host's original audited set.

The audit's `recorded_source_argument` must parse through strict JSON to the exact source Ref and equal the unique `--source-ref` operand in each model/CPU command from the audited COMMANDS Ref (`241–252`). This preserves the earlier caller repair without weakening whole-string equality. Re-encoding the reader's separate Ref arguments does not replace this independently checked recorded command string.

The original source/audit schema, complete original twenty-control declaration, fixed cutoff and false qualification predicates remain (`255–274`). The host result's `source_before` and `source_after` must still equal exactly the SHA map of the original source-audit readset, followed by complete reads and checks of every source-owned file and dependency (`275–287`). The added reader-only auditor provenance is kept separate from that map. Full input hashes and file identities are reread by the unchanged `Readset.finish` before result writing (`187–194`, `939`).

MAIN supplied the now-completed audit's actual identity as **1417609 B / `0280671e14430dbe314ea90754db33a42dc60b648a553285d0f355f4cedc3ca2`**. The runner accepts the full audit Ref as a CLI operand and checks the exact fixed path and actual complete bytes; that result hash is not hardcoded into the reader. MAIN must supply this actual Ref. This reviewer has not independently reopened the remote audit result or its execution receipt.

## Independent outputs and mode boundaries

The package is fixed to the assigned workstream `boundary_result_reader_v2_20261022`. The two fresh outputs are:

- Controls only: `/opt/host/vnf/austinov/run-bole-boundary-reader-controls-v2-20261022T080000Z`.
- Actual evidence reading: `/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z`.

Controls mode rejects any of the three actual Ref operands. Actual mode requires all three and checks exact source, host-result and audit paths. The wrapper validates ordinary ancestry and its exact assigned executable path, then creates its output exclusively with `mkdir` and a private TMPDIR (`run_boundary_reader_once_v2.py`, lines 336–359). Existing outputs are not resumed, deleted or reused. Metadata, traceback and stdout/stderr use exclusive creation. The reader's final output is also exclusive and outside original source/evidence roots.

Controls mode launches exactly the thirteen existing tests through a small runtime-origin wrapper; the only test-source change from v1 is the imported reader basename. It requires the exact runtime-origin stdout, a single terminal `Ran 13 tests` record and final `OK`, and prohibits an actual diagnostic output (`290–306`). This is not a replacement for the original twenty same-image software controls or a model-state gate.

Actual mode launches only the immutable reader, checks the returned diagnostic file's complete Ref against stdout, checks source/result/audit/reader identities, and requires the retained integrity and original input-preservation predicates (`309–333`). Failure or partial retained output is explicitly distinguished in EXECUTION. It does not create an owner, launch a container/model, or perform device work.

## Host Python, module provenance and input preservation

The wrapper requires observed host Python **3.9.9**, `/usr/bin/python3`, isolated mode, bytecode disabled and site enabled. It intentionally uses `-I -B`, not `-S`, because the existing host runtime supplies the missing unittest through its pre-existing site directory (`367–386`). No installation or site mutation is attempted.

Both wrapper inputs and the actual controls child check these exact files:

| Actual import origin | Bytes | SHA-256 |
|---|---:|---|
| `/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/__init__.py` | 3761 | `07bdf1fff20e4121ba61cfb64ea3c404d54ac56b053475a3a105907f48685210` |
| `/usr/local/lib/qwen35-pytest-8.4.2-py39/site-packages/unittest/mock.py` | 99215 | `883176927e3c64d328716635b294523a9be16bbe3ac0f5792947897535f34844` |

The child checks each imported module's actual `__file__`, ordinary non-symlink ancestry, complete bytes/SHA and stable identity before running the tests (`45–70`). These checks are stronger than merely hashing the named files while importing a different module. The parent's before/after set includes the pinned reader/test files, both unittest sources, its own observed source Ref, actual executable and, in actual mode, all three actual operand Refs (`372–395`, `424–435`). The Python executable hash is correctly labeled an observed value, not a previously reviewed binary pin. MAIN must independently pin the runner's final SHA in its external invocation, as the runner's header requires.

## Budgets, process ownership and MAIN's outer guard

The runner applies and checks hard/soft address-space **512 MiB**, CPU **180 s**, file **64 MiB**, core **0** limits before reading the full input closure; its child inherits those limits (`168–180`, `367`). Individual source/metadata/JSON/file reads and output sizes are separately bounded. Whole-file reading verifies file and ancestor identities and complete byte counts/SHA; it does not accept a prefix digest (`94–165`).

The normal runner budget is **240 s**, with **12 s reserved for cleanup**. Its only child starts a new session and process group. The runner records the process's actual start ticks and checks PID/PGID/SID ownership before signaling. It polls against the shared deadline, sends owned-group SIGTERM if needed, waits at most 3 seconds, then owned-group SIGKILL and another 3-second reap wait. Cleanup failures are recorded, and success requires the child reaped and its group absent (`193–287`, `411–415`). It does not sweep or signal unrelated groups if absence checks fail.

The source alone actively enforces the child's wait budget; the parent before/after file operations and final reporting are not governed by an internal active global alarm. Its `within_wall` result is a monotonic check, not an independent timer. This was reported to MAIN.

MAIN accepted this separate, unchanged-source invocation: launch `/usr/bin/python3 -I -B -c`; verify the runner's fixed complete Ref; install a SIGALRM handler that raises `TimeoutError`; arm `alarm(252)`; set the exact runner argv; and call `runpy.run_path` in that same process. AWMCP receives timeout **270 s**. Using runpy rather than exec preserves the handler. An alarm while inside the runner enters its existing BaseException/finally cleanup path, including owned-child cleanup when active. The outer 252-second guard and 270-second operation timeout do not extend the runner's original 240-second successful-result condition. MAIN states that actual mode will use the same guard with its real operands.

No new blocker is introduced by this specific outer design. The actual invocation and operation receipt remain MAIN's responsibility and have not been executed or independently verified by this reviewer. A source-reviewed cleanup path is not a claim that a future timed-out child has already been released.

## Qualification and interpretation

The runner requires and emits false NPU-executed, model-ready, numerical-qualified, paired-gate-pass, performance-admitted, formal-performance, task-accuracy and technology-success flags. The actual reader additionally retains false causality, algorithm-numerical-qualification and original-pair-replacement flags. Its successful result means complete read-only integrity and within-ON diagnostic comparisons only; it does not prove identical incoming request state, causal origin, alias exclusion, or numerical acceptability. No numeric threshold is introduced by the v2 delta.

This review leaves the original hard report cutoff **2026-10-22 12:38:41 UTC** and all unresolved original ON/OFF, low-observation, fixed-1024 whole-model performance and final accuracy requirements unchanged.

`source_only_review_complete=true; controls_executed_by_reviewer=false; actual_reader_executed_by_reviewer=false; remote_execution_verified=false; numerical_qualified=false; paired_gate_pass=false; performance_admitted=false; task_accuracy=false`.
