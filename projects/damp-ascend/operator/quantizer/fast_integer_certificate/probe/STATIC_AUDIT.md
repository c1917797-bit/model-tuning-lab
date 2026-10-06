# Source-only audit record (not an NPU pass)

## Actual runs
Unique software operation exec-00000000000002a5: completed, exit0, 73203ms;
stderr empty. Exact stdout is retained in audit/software-v1.json.
It checked 387096 endpoint rows, 221676 proposal rows and 40316 labeled
fixtures with 28244 certificate acceptances and zero unsafe acceptances.
This is mathematical/source-contract evidence only; ASC/CXX not compiled
and NPU not executed by this subagent.

sync_audit.py operation exec-00000000000002a8: completed, exit0, stderr empty.
All raw JSON is retained verbatim in audit/sync-audit-v1.json, including
101 syntactic events and all SIX findings:
- SYNC-09 EndpointFloor45 barriers (frozen helper line26).
- SYNC-09 frozen helper90 lexical barriers (line26).
- SYNC-09 probe Run7 barriers (line60).
- SYNC-09 probe file7 barriers (line60).
- SYNC-11 output EnQue->DeQue without further computation (line96).
- SYNC-09 Certify45 lexical barriers (frozen helper line132).

All findings have scanner severity 性能; none has been removed or relabeled
as a numeric/device pass. The output queue also carries the intended V->MTE3
handshake, so its performance finding is retained pending real compiler/NPU
evidence; no scanner-driven fence deletion was applied.
The call-expanded arithmetic is135 certificate vector/fence calls plus90
additional EndpointFloor calls and7 export fences in this diagnostic. These
are API counts, NOT measured instructions, cycles, bandwidth or E2E benefit.

ascendc_flow_analyzer.py operation exec-00000000000002aa: completed, exit0, stderr empty.
Verbatim JSON is audit/flow-audit-v1.json. It parsed only THREE DataCopy
operations, THREE accesses and FOUR explicit sync edges. Buffer dependencies
and synchronization coverages are empty; findings are empty.
The scanner did not resolve the loop-indexed arrays and inlined tensor
arithmetic. Consequently, empty findings do NOT prove synchronization safety.

Both scanners were inspected for side effects first. PYTHONDONTWRITEBYTECODE=1
was used; existing Cannbot cases DB was opened read-only, no missing DB needed
creation, and the original Cannbot repository was not edited. Scanner inputs
were the five project headers, not a proof over all SDK implementations.

## Manual producer/consumer mapping
| Producer -> consumer | Current mechanism | Remaining evidence |
| --- | --- | --- |
| GM/MTE2 inputs and fixedLUT -> V helper | VECIN DataCopy, EnQue/DeQue | Real compiler and NPU values |
| Dependent INT32 limb operations -> next V op | Frozen PIPE_V fences | ISA support and actual execution |
| V certificate/endpoint exports -> scalar GetValue | Explicit FetchEventID/SetFlag/WaitFlag V_S | Actual values on N64/896 |
| Scalar domain/code writes -> output queue | Explicit S_V then VECOUT EnQue/DeQue | Actual ordering and complete returns |
| UB output -> GM | Sole AIV, full32B DMA, offset8 INT32 guard | Raw before/after guards on NPU |

Explicit94,208B UB accounting is source-level. Compiler stack/internal
allocation is unknown until parent build; no actual UB allocator pass claimed.
Prepare stream(true) is only outside-launch initialization synchronization.
The actual ASC-compiled RunOpApi queued kernel uses current stream(false).
Never infer graph support from Meta; actual proposal D2H admission is
intentionally blocking and not suitable for capture or production performance.

## Admission/data evidence
Range checks on actual INT32 proposal occur before kernel/Gather, not merely
as post-computation masking. Exported domains include BOTH original positive
normal finite scale and endpoint exponent validity. Invalid x/scale fallback
returns code0/valid0. Safe floor placeholders when domain0 have no threshold
authority. Full backing storage intervals must be disjoint.
Seven complete fresh outputs include each8-INT32 guard. The runner saves all
raw outputs and input-after before numerical assertions. Unexpected cold or
cached prepare failure likewise saves its before/after/error artifact.

## Unfinished gates
No ASC/CXX build or actual schema/Meta load has been performed for this NEW
target by this subagent. No NPU test, GatherMask compaction, graph, production
packed recurrence, cache manager, paired E2E, or GSM8K/LongBench result exists.
Physical non-ND and cross-NPU negative runtime cases are not generated in this
single-card runner; hard guards are present but those cases remain untested.
The parent must verify and run them as appropriate without unauthorized cards.

The original v1 seven compiled-source files plus2 external headers were sent
to MAIN at MA02b3. V1 failed in the host-pass architecture include boundary.
The original raw audit results above remain unchanged as historical evidence.
V2 changed ONLY the new kernel.asc include boundary; original archived source
hash0c845... and currente623... are recorded in V2_CHANGES.md.
MAIN MA02dc actual CXX/ASC/link v2 PASS is separately proved by its build
receipt, not by these static outputs. Nothing here proves NPU correctness.
DAMP24h deadline remains2026-10-07T08:48:03Z, portfolio cutoff unchanged.
