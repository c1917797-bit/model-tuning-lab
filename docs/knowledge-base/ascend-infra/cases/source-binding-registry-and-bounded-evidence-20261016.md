# Runtime-source binding, plugin lifecycle and bounded evidence (2026-10-16)

## Scope and current acceptance

Qwen3.6-27B at /cache/efim/Qwen3.6-27B, hybrid Qwen3_5, Ascend910B4,
vLLM-Ascend0.23/CANN9.1. The old48h window ended without final acceptance.
The separately authorized24h ends2026-10-17 07:02:13UTC. No result below proves
the >=10% three-pair model throughput or final task-quality requirement.

## Actual evidence and causal attribution

- DeltaLog061 actualNPU16 completed40records and63sidecars. The owner remained
  failed: the independent domain reader rejected two runtime-to-host mappings
  missing from its source readset. Preserve that failure, not a paper no-go.
- Recovery066 consumed the same saved raw in an owned same-image Devices[]
  container. Its SOURCE_MANIFEST was4943101bytes,
  db71c3a8e456e9e7fdbf611d3b260906e90edb6f916dfe2406d791d697ca69a9.
  DOMAIN066 was329005bytes,
  c77cb818b0c62fd1650cd28f5ae5a859fc0a8c80141216d3943b1b864e0a3e52.
  All40domain rows and63sidecars passed with no failures/missing evidence.
  The original strict failure and complete_proof=False remain unchanged.
  This is a successful independent diagnostic recovery, not a new160/model
  qualification or task-accuracy result. No NPU rerun was used for recovery.
- MXR065 actually passed its13 CPU tests and four tiny device canaries, then
  failed architecture inspection before model execution: load_general_plugins
  invoked the installer in a registry subprocess before native recurrent-op
  registration. Every created container was stopped/retained and released;
  the recorded cgroup OOM count was0.
- MXR067 implements full installation deferred to a real source-checked Qwen
  first-core instance, with explicit official-op and later48-instance evidence.
  Its full long experiment was NOT started: safety review rejected an allocation
  near227.5GiB on a filesystem with about228.5GiB free. Do not bypass this
  rejection. MXR068 is a separate129-token smoke with a complete3GiB cap and
  initial32GiB-free condition, not an indirect start of the rejected long run.
- Storage capture069's first actual attempt rejected a genuine completed
  failed-operation snapshot because it incorrectly required wrapper ok=True.
  The actual09c4 response had terminal=True/status=completed, exitCode=3,
  transport peer_direct/inner ok=True, but wrapper ok=False. Preserve the
  failed capture leaf; fix the precise terminal predicate in a successor,
  without changing the observed snapshot or declaring the old command passed.

## Reusable decisions

1. Regression-test the validator using actual producer/report shapes, including
   runtime path mappings, readset membership and cross-process source identity.
   A missing evidence field does not establish a tensor or algorithm failure.
2. Plugin registration runs in API/inspection/worker contexts. Execute a genuine
   cold entrypoint check; distinguish registration from real worker installation.
   Default-OFF, real first-instance dispatch and native operator identity remain
   independently verifiable. Do not fake a worker receipt in a registry child.
3. Read the actual producer and consumer predicates. Diagnostic False fields can
   deliberately preserve scope while permitting a later diagnostic stage;
   never infer readiness or permanent failure from a field name alone.
4. Design evidence coverage and retained bytes before dispatch. Full intermediate
   dumps are an experiment choice, not a universal paper requirement. A smaller
   preregistered smoke has its own scope; it does not inherit the old full-matrix
   certificate or lower the final performance/quality acceptance.
5. Distinguish completed process from successful computation using the actual
   operation contract and source-bound exit/owner evidence. Do not suppress
   missing/running/transport/identity failures to make a seal pass.
6. For verbatim source transport, preserve final newlines. Windows Get-Content
   output added a terminal blank line to one capture tool; deployed-byte hashing
   caught it before execution. Use exact text extraction and compare full bytes,
   not merely AST or patch success.

## Workload update and next gates

The user explicitly permits2K/16K inputs. Prepare distinct2048/16384-token
profiles, fixed1024 output, same dense/candidate stack/input/concurrency/common
policy, profilingOFF and separateTTFT/TPOT. Do not require32K/40K as a predecessor.
129 tokens is a correctness smoke only. C1 screening does not proveC16 behavior.

Next: finish the source/readset and bounded storage repair, then actual
same-source CPU/Meta ->16 ->160 for DeltaLog; actual first-core/48-layer smoke
for MXR; production-relevant2K/16K correctness and matched model performance;
promising three-pair performance and GSM8K/HumanEval/MMLU smoke->full,
thinkOFF/max2048/normalEOS. HistoricalHYPIC is not a new result.

## Subsequent actual gates (same day)

- MXR068 actual operation exec-0000000000000a2d exited1 after1.71s,
  before any container was created. The retained first error was
  unowned physical compute must be idle; contemporaneous SMI showed external
  kernel-eval processes on physical5. This is admission/resource failure,
  not a model numerical result. Its output001 remains unchanged.
- Storage069-repair1 capture002 really completed (operation0a31, exit0).
  EVIDENCE069.json is6070bytes,
  eab70137ec0763daa93dbd525f28a08b6ed4ac6ae83299c095c8c8162bbc82fc.
  It wrote5436230bytes under the50MiB capture cap without changing the ledger.
- The repair1 binder0a35 completed with SOURCE_MANIFEST52969bytes,
  b9cb456d960072d8e6730bb5307dcabfc83b3ad7bffd9d3476d9b92220048f21.
  Sourceaudit0a3c verified207 source dependencies. An earlier sourceaudit CLI
  attempt0a38 rejected a CPU-list string where this CLI requires an integer;
  it never created an experiment output. Corrected arguments were derived
  from run031.py/host.py, not from a guessed affinity convention.
- Actual same-image Devices[] CPU gate0a40 completed in112.245s, exit0.
  Host owner1386bytes/54e38927342aa9c4e443cbde798768e46a421afc3fb1ba7c8e220aa3842ed3cd;
  stage5231bytes/cdc6cc7b89e5720176fc7f6274f7d411958549cb408ee565839cb8c9268d780f.
  Both actual051 production/debug libraries loaded; Meta covered13/14
  arguments and batch1/16. Primary/secondary errors are empty and the
  no-device container is stopped/retained. This does not grant NPU correctness.
- NPU16 operation0a49 has been dispatched after a fresh physical5 idle check.
  Its terminal and numerical outcome are pending at this checkpoint; do not
  infer success from dispatch or an operation being live.

External-process handling retained no-action refusals when the exact PID/start
departed or scope validation failed. No external signal or container stop has
been proved successful here. Recheck fresh ownership; never target stale PIDs.

## Actual numerical and bootstrap attribution (later checkpoint)

The earlier pending NPU16 observation is now terminal: operation0a49 passed the
diagnostic40-row/63-sidecar domain. It does not grant model or performance
qualification. The subsequent NPU160 operation0a58 failed at B1/eager mixed
step90: whole-state relative L2=8.515666478e-7 exceeded its frozen7.92e-7.
Keep that failure; no paper-wide conclusion follows.

CPU074 repair2 independently consumed the original91 retained frames in the
same immutable image, Devices[], with no NPU rerun. Operation0a9b exited0;
DIAGNOSIS074.json is231657bytes,
c01e2993a59805703a7cc98b67d11df89fb84656c9ad89d3984901db76c8ff1d.
At step90 the decode candidate/native state difference was4.56e-8, whereas
the prefill state difference was1.219e-6. Candidate and native cumulative
CPU64 error norms were both about.00212. Similar norms do not prove identical
error vectors, nor a wrong native implementation. The CPU64 ledger uses saved
candidate post-convolution operands; it is not an independently captured
native-input trajectory or the exact BF16 working DAG. Next intervention:
reopen the step89->90 slot/flush join and compare native prefill from both
actual initial states, with common-input and deterministic replay controls.
Do not tune the old threshold to fit the observed failure.

The 2K model preparation exposed real deployment defects, not paper failures:
a guessed historical source directory, an omitted own IPC leaf, and an
environment method initialized only in the later guest role. Retain073R1-R3
failures and test the actual aggregate and subprocess paths.

073R4 then demonstrated a phase-contract error: real GDN plugin registration
imports the Ascend Triton driver and queries architecture. Devices[] cannot
satisfy that runtime dependency. 073R5 kept CPU source/argv/static checks,
explicitly marked real registration pending, and moved the unchanged real
registration into admitted N1 after four actual tiny canaries and before model
weights. The host must consume the real child receipt; pending is not PASS.

073R5's four tiny computations passed, but its isolated registry subprocess
failed to import acl. Python -I ignores environment PYTHONPATH and a fresh
subprocess does not inherit its parent's sys.path. 073R6 reuses the original
source-pinned guest installed_cann helper inside that child: fixed CANN root,
ENV and extension identities, direct and active spec equality, explicit
sys.path insertion. No image edit, pip install or fake ACL module is needed.
Operation0ab1 has passed actual N1 registration/parser and started the service;
full2K/48-layer/nine-decode numerical and E2E results remain pending.

CPU074R1 also failed before creating output because host512MiB soft address
space propagated into Go Docker. Actual read-only probe0a8f reproduced
Docker exit2 (failed to reserve page summary memory); the exact Docker-only
prlimit --as=unlimited wrapper exited0. Repair2 applies that wrapper to all
Docker metadata/create/attach/stop clients, keeps the host and container RAM
budgets unchanged, and retains actual argv/exit/stdout/stderr. A parent virtual
address cap is not a total Docker-client RSS budget.

The maintainer already required genuine aggregate checks and correct
static/device phase separation. These failures are compliance/implementation
gaps, not a reason to add another scheduling framework or claim that more
rules alone fixed execution. Reuse the native bootstrap sequence and verify
it in every real interpreter context. Exact refs, terminals and CURRENT/NEXT
are in CURRENT_STAGE_20261016_1030UTC.json in the active workstream.

## Real 2K model and same-initial native interventions (11:00UTC checkpoint)

073R6 operation0ab1 is now terminal FAILED after actual TP4 model execution,
not another registry failure. Rank0 consumed48 prefill and432 decode rows:
all48 solves passed; five prefill states failed (layers0/21/37/53/56), and34
native decode outputs failed the uncast CPU64 comparator. Other-rank raw is
retained but those consumers were not run. Never promote a local solve PASS
to complete GDN correctness or blame an unmodified decode on MXR automatically.

Saved-raw Devices[] diagnostic082 consumed all34 failed decode rows under the
unchanged original metrics, separately reporting exact integer binary64-to-BF16
RNE. Of52224 output cells only4 differed from that reference; maximum relative
actual-to-RNE error was2.758e-5. The original uncast comparison includes a BF16
rounding floor up to.0034022. This proves a relevant ABI/reference-domain issue;
it does not retroactively pass073R6, fix its five prefill failures, qualify unseen
inputs or establish task accuracy. A corrected contract must be independently
frozen with negative controls and affected complete coverage.

DeltaLog CPU076 verified the actual89->90 slot/flush/input/returned-state joins.
Then same-image Devices[]083 verified the exact native079 source and raw extract
before device admission. Actual physical5 intervention081/079 made six calls to
the original native chunk with identical captured operands and two actual FP32
initial states. Same-initial repeats and clones were bitwise deterministic.
SC reproduced the old candidate output/state bitwise; SN reproduced the old
native final state bitwise. Only changing initial state changed19 actual BF16
gmH cells and reproduced the original1.219032779e-6 prefill state discrepancy.
The independent CPU64 two-initial propagation predicted only2.217e-11 here.

This isolates native working-boundary sensitivity for this saved turn; it is not
a complete ideal-FP64 theorem, a binary-source proof or a full trajectory PASS.
Original baseline transformed operands were not independently captured, so keep
that limitation explicit even though its final state was reproduced exactly.
Do not enlarge7.92e-7 to fit the failure. Choose a source-justified adaptation
repair or a separately preregistered component-operational contract, preserving
independent changed-decode/flush checks and all old failures. Neither path may
skip new state/lifecycle/graph holdout, matched performance or task acceptance.

The completed intervention was stopped and retained with independently reopened
exit0/Pid0/noExecIDs/noOOM. No protected0-3 workload was changed. This stage
reused saved inputs and established causal device evidence without reloading the
model or manufacturing occupancy. Exact references and next entries are in
NUMERIC_BOUNDARY_CAUSAL_CHECKPOINT_20261016_1100UTC.json in the active workstream.


## Actual three-arm MXR attribution and executable packet checks (11:37UTC)

086 failed while observing its own compiler child535517. The first actual
snapshot was present/R with stable parent/start, root-only cgroups, empty
cmdline and zero virtual/RSS values; it was not a proved zombie or an external
protected-card occupier.092 only adds an at-most2s, whole-deadline-clipped wait
for that source-owned original-tree departure. Final two complete missing
reads, fresh Docker-top absence and a last missing read remain mandatory.
Foreign/unknown ownership, PID reuse, protected/bound/init identities and
persistent presence still refuse. Same-image CPU controls and saved-frame
extraction actually passed before the new NPU run.

Actual092/084 physical5 three-arm execution completed in87.98s, preserving the
old candidate output/state bitwise anchor. Independent Devices[] consumption
finished successfully. All arms have identical actual A/G. On this real2K
rank0/layer0 frame, candidate-versus-native final-state relative L2 is
0.00211012898911623, while native-versus-CPU64cast is2.9498510855650152e-5.
The actual B change precedes W/U and accumulated H-entry differences. This
is evidence of a candidate readout/propagation issue, not solely an oracle
false-negative. One frame is neither a complete correctness gate nor a paper
rejection. Save X0/X1 and a single additional FP32 residual correction for a
new discriminating experiment; do not blindly iterate or increase epsilon.
The CPU64cast arm is an operational Torch cast, not a proved direct integer
RNE theorem. Intermediate FP32 H-end is not exposed by the native API.

Two source-preparation defects in dense090 were caught before NPU: Windows
Path string serialization created a non-POSIX output, and Path division plus
string addition raised TypeError in the actual client command builder. New
R2 freezes Linux strings and tests both actual client builders as well as
server/OFF/negative entry paths. MAIN deployment also initially dropped two
trailing newlines in five copied source files. Preserve the failed SHA audit;
restore byte-exact reviewed contents and rehash every payload before running.
Transport success, helper tests and authored command lists are not readiness.

Exact source recovery archive and actual terminal/attribution references:
MXR_THREE_ARM_ACTUAL_20261016_1137UTC.json in the active workstream. Native-only
2K/16K fixed1024 opportunity measurement is a separate pending diagnostic,
not candidate performance or task acceptance. Continuous utilization remains
unmeasured; do not claim four-card no-gap use from job snapshots.

## Decode-graph gate and deployment-layout regression (12:19UTC)

Actual095 completed B1/B16 with16 changing-input decode graph replays each.
Independent CPU consumption passed all32 rows, maximum state relative L2
9.486863797469401e-8 against unchanged7.92e-7. All six recurrent storage fields,
output/debug equality and slot/metadata invariants were checked. Full mixed
prefill/flush graph,160-step trajectory, whole-model performance and task
accuracy remain unqualified. Source archive and exact receipts are recorded
in GRAPH_STORAGE_AND_PREFLIGHT_20261016_1219UTC.json.

Actual093 closure sealed the existing six completed phase trees into immutable
storage ledger8. It did not enlarge the80GiB authorization or100GiB free reserve,
and it did not grant mathematical correctness. A successor must consume the
existing seal; it must not invoke the historical seal creator again.

097 same-image CPU preflight then caught a real preparation defect before NPU:
two interface tests assumed the preparer's flat local directory, while the
deployed guest and owner roots are separate. Fifteen guard controls passed;
two of eight math/interface controls raised FileNotFoundError. Keep the failed
owner and stderr.097-repair1 consumes the already verified owned.files Ref3s,
with actual disjoint-directory CPU-entry regression and missing/hash-negative
controls. Compute guest, numerical consumer and two-residual arithmetic bytes
are unchanged. Actual same-image/NPU repair results remain pending here.

The maintainer already required real aggregate and deployed-source closure
checks. This was an implementation/compliance gap, not missing permission or
proof that adding more rules makes the code correct. Test the actual delivered
layout, exact isolated-interpreter flags, producer/consumer schemas and argument
builders before a resource lease. A local helper PASS cannot certify a different
filesystem layout or a later live stage. Preserve failures and repair only the
proved seam; never lower arithmetic thresholds to compensate.

Native-only090R2 separately reached a real server, but its client requested one
warmup while the canonical benchmark parser requires at least two.090R3 tests
the actual parser and command builder with two warmups, retains child exit and
stderr before a generic barrier failure, and passed actual sourceaudit. Its
model diagnostic was running at this snapshot, not a performance gain.


## Same-frame repair PASS and a caught identity defect (13:29UTC)

097-repair1 actually passed same-image preflight, NPU0b8e and independent
Devices[] consumption0b94. All384 trace anchors were consumed. The original
working, native-peer and CPU64cast-peer gates passed without threshold changes;
native-peer final-state relative L2 fell from0.00211012898911623 in092 to
3.9299860606595066e-5. This proves a targeted repair on the saved rank0/layer0
2K frame, not full-model or task qualification. The archived source leaves and
exact report Ref3 are in MXR_REPAIR_AND_BOLE_20261016_1329UTC.json.

098R1 then refused fresh physical5 foreign computation before creating any
container. This is a resource admission failure, not failed MXR mathematics.
The immutable R2 source bound and audited961 references/33 registered deltas.
However, MAIN's actual host entry review found DEPLOY still used a split
LOW/'...repair1' literal and the generated owner's DEPLOY replacement also
pointed to repair1. HERE!=DEPLOY would deterministically reject execution.
R2 was not executed. Its source and audit are retained; R3 must correct only
that identity seam and test actual loaded globals plus generated-owner globals.
A whole-byte inverse proves what changed, not that the new values are correct.
An absolute-string-only renamer misses path fragments and dynamically emitted
code. Sourceaudit PASS therefore cannot substitute for the execute predicate.

DeltaLog088R2 actualN16 completed its new preregistered same-initial-native
operational domain. Original independent strict FAIL, pass_gate=False and
complete_proof=False remain unchanged. New diagnostic160 is running as0bef;
it is not a model/performance certificate. Actual decode-graph095 remains a
separate bounded PASS. Never union scopes merely because both jobs exited0.

The human explicitly added BOLE2608.01651v1 for parallel preparation. Paper
integration into SGLang is not proof of public upstream support. Actual660
source shows Qwen MTP config/registry/loader infrastructure, but the existing
Ascend proposer remains linear and the tree FA/conv/GDN/sampling/commit seams
need adaptation. Dense-loader skipping mtp.* is normal separate-loader behavior,
not evidence of an unsupported MTP checkpoint. Ordinary MTP is a necessary
control, not BOLE success. Public-author implementation parity remains unverified.

No final performance or task acceptance was achieved at this checkpoint.
Continuous four-card utilization is unmeasured; a real single-card diagnostic
and parallel CPU preparation do not prove four-card no-gap operation.
## Mapping closure and retained resource failures (14:38UTC checkpoint)

098R3 actually failed a same-image aggregate because an old test08 still pinned
repair1. R4 repaired that test and ran all26 actual controls, then loaded TP4
and answered HTTP200. A separately restarted cannbench_align subsequently
used physical5; R4 terminated with a foreign-process/UDA conflict and no
complete FRAME/DECODE files. Its owned container was independently reopened
stopped/Pid0/noExec/noOOM. This is resource failure, not failed mathematics.
R5 is an identity-only new output/source experiment; actual deployed globals,
966-ref source audit, Linux26 and same-image26 passed. Actual four tiny
canaries, registry and parser passed; whole-model numerical result is pending
in operation exec-0000000000000c61 at this checkpoint.

BOLE112 first failed the actual CPU aggregate: prepared_template was absent
from its readonly guest closure. R1 added only that exact Ref; actual same-image
CPU10 and24 Meta cases then passed and the container was independently released.
Its numeric entry failed before creating a container: the new owner declared
physical4 but reused a physical5-only scoped_cards adapter. Keep operation0c52
and its primary error; no NPU math ran. R2 preparation now supplies a separately
source-bound physical4 adapter and actual donor-inspect mapping controls.
Actual R2 same-image/NPU results are still pending.

Reusable lesson: trace a relocated physical device through source-bound scope
selection, actual create argv, actual donor inspect, host SMI/PID/namespace join,
and guest ARM; changing only the outer physical variable is insufficient.
Test the inherited real scope/inspect functions, including wrong-device
rejection, before admission. Preserve protected0-3 guards and numerical
contracts. A byte inverse proves the delta, not mapping compatibility.

An automatic approval-review quota failure explicitly left one BOLE deployment
unexecuted. MAIN retained that fact and performed only unaffected work; after
the human reported recovery, the normal reviewed route succeeded. Never
switch routes to evade an uncompleted approval check or count an unexecuted
call as a running experiment. Later transport timeout on the large R5 patch
was reconciled by reading all actual target hashes: all files had committed,
so the mutation was not blindly repeated.

## 2026-10-16 checkpoint: numerical scope, transport bytes, and typed dependencies

BOLE tree-GDN112R4 completed its actual full eager component gate: 72/72 rows
passed independent CPU-double comparison, max output relative-L2
1.2513252618498079e-7 and state relative-L2 9.058046145669613e-8.
This does not qualify a complete BOLE model, tree attention, convolution,
scheduler acceptance, joint cache commit, graph, performance, or task scores.
The exact evidence and subsequent failures are indexed in
`.agents/workstreams/qwen36-damp-ascend-20261006/VALIDATION_PROGRESS_20261016_1605UTC.json`.

MXR098R5 remains a failed full-model working-state gate (25/192 failures).
120R2 replayed three saved actual frames through candidate, original native
inverse, and independent CPU64-inverse-cast paths; independent Devices[]
consumption proved the candidate B/output/state bitwise anchor. Both failure
frames also fail the unchanged working-state reference for native and
CPU64-cast. Therefore an inverse-only cause is insufficiently supported.
The candidate can still have additional error. Do not infer that the reference
is invalid, that native is mathematical truth, or that more inverse iterations
will repair the state. Compare actual versus reconstructed A/G, inverse
residuals, B rounding cells, and W/U/H propagation; preserve old failures and
require independent evidence plus held-out NPU validation for any corrected
reference contract. Original R5 solve/output/decode success is not full-model
state success.

The120R2 NPU parent remained FAIL: its already-bound own init exited between
Docker inspect and Docker top, and the protected-ownership observer rejected
retiring init. Its complete raw child and a separately released independent
consumer support numerical diagnosis only. Child exit0 or later stopped CID
does not retrospectively fill the missing observation or turn parent FAIL into
PASS. Report scientific results and operational parent status separately.

Two BOLE preparation defects had distinct proved causes.116R1's patch used
the Windows default cp1252 decoder on UTF8 text containing NBSP; emitted bytes
did not match the frozen manifest.116R2's actual installed header hash was
correct, but CANN's include directory was a symlink. Reusable controls:
explicit UTF8 throughout; reconstruct every patch payload and verify exact
bytes/SHA before deployment; independently inspect installed alias and canonical
path; bind the measured ordinary canonical path and retain no-symlink checks.
A copied display header with an extra LF is not the installed header identity.

DeltaLog119 sealed retained historical storage without numerical promotion.
The original088R3 recursive Ref walker traversed20,135 provenance objects,
including historical supersedes/inverses and guest-only installed paths.
Thirteen missing host paths and eleven relative inventories were not evidence
that the current runtime lacked required inputs. The replacement readset follows
the unchanged119/093/069 validators' actual helper, evidence-phase, receipt, tree,
authority and ledger reads;79 actual required host references passed byte/hash
checking. Historical/guest provenance remains whole-file hash-bound metadata,
not guessed host mounts. Unknown required schemas, missing required fields,
relative required paths, and changed container hashes still fail. Avoid replacing
a typed dependency graph with either arbitrary recursive traversal or broad
ignore/allowmissing rules.

The new same-source088R4 CPU/Meta stage completed, but its16/160 NPU gates and
downstream model/performance/task status require actual new results. A storage
seal, source audit, or Meta registration never lends numerical qualification.

Existing BOLE CPU and DeltaLog controllers both inspect all running
qwen36.owner labels; independent output locks are not a joint resource lease.
Do not start them together by relabelling or deleting guards. Compatible
concurrency requires explicit summed RAM/CPU/device/output budgets and mutually
compatible admission/continuous guards. A single idle/busy snapshot does not
prove a30-minute utilization window; no four-card no-gap claim is made.

Large control calls may time out after a mutation began. Reconcile actual
target bytes/existing operation handles before retrying. A wrapper syntax or
CPU-affinity error before owner admission is an orchestration failure, not a
paper numerical failure; prefer reviewed exact stage argv and let the owner
assign its own host/guest affinity. Preserve each failed operation.
## 2026-10-16 16:43 UTC: exact namespace joins and real source-context controls

BOLE116R6 completed actual CPU ABI, typed ticket, physical NPU4 six-call FIA
matrix and an independent Devices[] consumer. All6 rows passed both unchanged
FP32 and FP64 comparisons; mask modes0/1 are supported only on this tested
matrix. Combined with112R4's72/72 tree-GDN component result, this advances
component correctness, not packed paged-KV, convolution, joint commit, TP4 model,
E2E throughput or task acceptance. Exact results are indexed in
VALIDATION_PROGRESS_20261016_1643UTC.json; no new technique is accepted yet.

Three concrete preparation faults were repaired without changing algorithm gates.
An unrelated conv-ABI collector imported GDN and queried HAL inside Devices[],
so that hardware-dependent dependency was kept pending outside FIA CPU admission.
A later ticket compared guest /adakv-results with host paths as though Ref.path
were namespace-independent. Resolve only the exact advertised file through the
actual stopped container's sole RW bind, same CID/source/image, exit0/noExec,
Devices[] and exact bytes/SHA. Do not broadly replace path prefixes or accept
arbitrary filenames. The broad startswith discriminator then misclassified unit
fixtures under the real guest TMPDIR; the final regression exercises the exact
absolute alias and nearby TMPDIR paths plus real isolated ticket entrypoints.
Windows mock success cannot establish Linux container path semantics.

MXR120-analysis1 produced a complete4,323,534-byte three-case diagnostic, but its
parent rejected the same guest/host Ref join. A separate source-bound recovery
verified all seven original records, exact original create flags/RW alias,
child exit0,22 controls and all3x384 tileheads. It references the original report
without copying or rewriting it; the old parent remains FAILED. Numerical
qualification and reference validity remain unresolved. Save valid completed
child evidence and repair the demonstrated consumer predicate rather than
rerunning NPU data or reclassifying the failed parent as PASS.

DeltaLog088R4's16-step capture was interrupted by actual foreign physical5
processes; no complete producer remained. This is a resource execution failure,
not a numerical or paper no-go.121 independently sealed all11 retained phases
at ledger15 while preserving original exit137 and cleanup-false evidence, under
unchanged80GiB total/100GiB free limits. The new source must still pass its own
CPU/16/160 gates. Pre-admission command and metadata export also checks all
cross-platform Ref paths explicitly as POSIX; never serialize host Path objects
as target-host paths. Neither storage release nor transport recovery lends
numerical, performance or task qualification.

## 2026-10-16 17:45 UTC: first-fault timing, actual registration, reference interventions

Actual DeltaLog088R5 N16 stopped before numerical capture. The retained child
failed its original ARM30 wait; the next host observation was blocked by the
unchanged full storage.check, measured39.261s (install53.524s). A later terminal
success fence hid this earlier exit in the parent message. Keep both first
child error and parent failure. R6 moves the same readonly predicate off the
ARM critical path, locks failures sticky, and retains final full verification;
it does not relax physical PID/namespace/SMI ownership or any numerical gate.
R6's actual Linux40 aggregate then failed four historical fixture-path reads,
not mathematics. R6repair1 declares the exact actual R2/R5 Ref dependencies,
retains original R1 content fingerprints as explicitly historical/nondeployed,
and passed all42 actual Linux controls. Operation0d81 captured the real R5
closed-phase overlay and bound a new source; no new CPU/NPU gate is implied.
A subsequent source audit found cleanup could permit a fresh39s background
scan after cleanup began. A minimal successor must request stop before cleanup
and join the current scan within the same original90s deadline; never extend
the clock, discard sticky failures or mutate the already bound source.

BOLE118 initially failed because normal GDN import did not register the custom
C extension. Actual installed utils.enable_custom_op performs the required
bootstrap and native/meta imports.118R1 reused that exact function after MAIN
ARM, recorded actual mapped extension/opapi bytes, captured the full dispatcher
overload family and passed its independent released consumer (0d65). This is
ABI/registration evidence only: no conv call or model qualification occurred.
The separate12-call SD chronology experiment0d85 was dispatched at this
checkpoint; its actual terminal and independent numerical outcome are pending.
Its prefault evidence does not prove complete kwargs or pointer-alias behavior.

MXR120A3's actual Devices[] report0d5e makes controlled actualA/G interventions
on three saved cases without changing the NPU candidate or old gate. ActualA
removes a common reconstruction discrepancy for layer4, while layer0 candidate
and native still fail the frozen state criteria. This neither repairs the
candidate nor proves an invalid reference in general. Positive-g/safe-exp clamp
differences are absent on these cases. Next localize first B/WU/H divergence
and separate common-reference and candidate error vectors under one denominator;
do not use sums of norms or repeated inverse corrections as causal proof.

Reusable rule: module import, dispatcher registration, actual kernel execution,
component correctness and whole-model acceptance are separate gates. A source
manifest or CPU test count never substitutes for the next gate. Preserve exact
frozen-source bytes in the recovery archive, including mixed vendor line endings.
Current DeltaLog production remains2048/C1; variable-length task prompts and
high-concurrency gains require real supported adapters and independent gates.
No new valid model pair or final task result exists at this checkpoint. Exact
Refs and CURRENT/NEXT are in RUNTIME_HANDSHAKE_20261016_1745UTC.json.

## 2026-10-16 18:30 UTC: actual convolution, operational domains and causal controls

BOLE118c completed12 actual native SD-convolution calls on physical4: B1/B16,
activation0/1, three changed-input steps, nonzero initial history and odd state
slots. The independent CPU-double chronology consumer passed all12 and full
state/inactive bits; maximum absolute output error was0.00011980218344632976.
All three exact owned guests were independently re-opened stopped/Pid0/noExec/
noOOM. This qualifies the tested convolution primitive, NOT BOLE tree attention,
accepted-path cache publication, a model or performance.118t is a separate eight
paged-TND case domain, now byte-verified and source-bound. Its host-only suite
probe failed because host Python lacks torch; preserve that wrong-interpreter
probe and run the declared same-image CPU stage, never install into the host or
claim that the source audit proves image/device readiness.

DeltaLog R6repair2 passed45 actual Linux controls and completed same-image CPU
and16-step capture/independent consumption, with actual released cleanup. Its
new domain PASS is explicitly local: CPU64 one-step recurrence from captured
before, actual FP32-to-BF16 RNE, guards, immutable inputs and production/debug
bits; flush has an independent CPU64 gate, while prefill repeats the untouched
native control from the same real materialized initial state. The original
strict first B1/step0 FAIL remains: decode BF16 versus uncast CPU64 peak
0.0030743712 exceeds0.00303; native-prefill ideal-CPU64 output/state also fail.
Whole candidate/native output matches, state peer error is4.2473e-8, and byte
checks pass. These facts do not establish a candidate-only decode defect or
prove that the BF16 discrepancy is exactly the rounding floor.

The independent cumulative-history metrics are reported but only checked finite,
not against a cumulative-error limit. Thus neither local-domain PASS nor the
fixed pass_gate/complete_proof=False receipt may be described as whole-history
mathematical correctness. Actual160 is still running on its original handle;
its complete operational matrix can at most admit the separately gated101
real-model diagnostic, not performance/task acceptance. Do not retrospectively
expand a tolerance or lend PASS from the old failed strict consumer.

MXR120A4 actually ran Devices[] on three immutable saved cases. CPU64cast equals
direct integer-RNE in the first layer0 chunk, disproving double rounding for
that specific divergence. Candidate and common-reference state errors strongly
cancel (cosine about-0.615); separate vector interventions, not sums of norms,
are needed. Layer4 is common-reconstruction dominated while layer1 control stays
bitwise aligned. X3 is a new bounded correction candidate, not an assumed fix.
Its unlaunched source metadata must honestly say four arms, originalX2 four
FP32 bmm/group versus X3 six; stale donor metadata is not a new algorithm fact.

Keep source binding, actual native execution, local operational correctness,
whole-history/model correctness, paired timing and task quality separate.
A declared command is not a ready resource-admitted node. Legacy owners still
reject any other owned guest, so disjoint-card declarations alone cannot prove
parallel admission or gapless utilization. Never bypass their guards or launch
dummy loads; prepare reviewed successors and improve actual shared budgeting.
Exact source/result/release Refs and CURRENT/NEXT are recorded in
NATIVE_CONV_OPERATIONAL_DOMAIN_AND_HANDOFF_20261016_1830UTC.json. No new E2E or
task acceptance exists.

## 2026-10-16: saved160 timeout recovery, paged layout and disproved X3 repair

The actual160 DeltaLog producer completed328 main records,351 sidecars and two
anchors; its original independent domain child timed out after585.6111058300012s.
The original failed owner, strict FAIL, logs and both stopped/released CIDs are
preserved. A source audit found960 extra full-anchor hydrations used only for
PID metadata. A new consumer caches only copied JSON PID metadata after the
complete original anchor verification; its body is exactly reversible to the
pinned7119-byte consumer. No tensor/blob cache, arithmetic, thresholds, row
coverage or timeout is changed. The actual target20-file byte check,17 host
controls, actual original-fault binding and full135520-Ref source audit passed.
Actual same-image recovery0dec is running at this checkpoint, not a claimed
mathematical PASS. Its new typed envelope cannot pretend the original160 owner
succeeded or pass unchanged101 admission; a reviewed recovery receiver remains
a separate edge. Reuse complete saved raw rather than spend NPU time recapturing
because a consumer failed. Record source-verification cost too: bind/sourceaudit
took222.208s and generated42.69MB of external metadata, not model throughput.

BOLE118t's eight native calls all failed the installed TND/D256 tiling domain
before independent mathematics. This is a concrete adapter boundary, not a
paper-wide negative.118tR1 changes only the actual layout to BNSD and PA
BnNBsD, retaining D256, the exact tree/path cases and independent references.
The full physical-page mask forbids padding; independent consumption rebuilds
every actual call operand from original CPU pages and checks shape/stride/dtype,
scalar arguments and before/after bytes. Master documentation is a candidate
support hypothesis, not proof of installed9.1 support. Actual59-file verification,
bind and source audit passed; its new same-image/NPU/consumer stages are queued,
not borrowed from the older contiguous attention or12-call convolution PASS.
Actual full-model BOLE binding still needs implementation.

MXR125R1 completed its new NPU experiment and independent four-arm diagnostic
on two saved failed cases and one passing control. X3 reduced BF16 inverse-cell
mismatches but made the working state errors worse: layer0 relative Frob
0.0014159344 ->0.0016425672, and layer4 0.0026266985 ->0.0026267698.
Both still fail; the control still passes. Native and direct-RNE common controls
also fail those two state gates. Per preregistration stop this X3 correction,
not blindly add X4. A better intermediate inverse is not proof of better
reconstructed state; native failure does not authorize relaxing the gate or
rejecting the paper. All three diagnostic guests were independently re-opened
stopped/Pid0/noExec/noOOM. No performance or task qualification follows.

Exact original/new source, failed owner, report and CURRENT/NEXT identities are
in RECOVERY_AND_LAYOUT_HANDOFF_20261016_1905UTC.json. Deadline and final model/
performance/task requirements are unchanged. Legacy global owned-CID exclusion
still prevents claiming disjoint admission or continuous four-card utilization;
CPU preparation and source deliveries are not NPU compute.

## 2026-10-16: repaired paged-tree NPU PASS and retained precreate RSS refusal

BOLE118tR1 now actually passed all eight new native BNSD+PA+D256 cases and
their released independent CPU consumer, followed by MAIN0e03 exact source/
owner/report re-opening and fresh three-CID stop verification. Maximum absolute
output error was0.0007012410050634965. Both sparse modes passed the independent
sequential ancestor paths, actual native operand bits/layout/kwargs, full padded
mask, accepted-path scatter, untouched cache and owner publication. This repairs
the proved installed TND-layout incompatibility; it does NOT supply BOLE model,
tree scheduler, TP4 publication, performance or task evidence. Missing model
integration is an engineering gap, not a paper-wide negative. Preserve old118t.

DeltaLog consumer-only127R2 actually failed before creating its guest:
aggregate actual host+child peak RSS exceeds256MiB, elapsed523.226s, no numerical
result and no cleanup secondary. The old681 raw artifacts remain unchanged.
Do not confuse a512MiB address-space reservation or8GiB guest cap with this
separate256MiB sampled aggregate host/CLI ceiling. Source binding expanded
135520 Ref entries into42.69MB and materialized them repeatedly; an actual
pre-refusal live host sample showed244680KiB RSS. The exact failing aggregate
sample was not retained, so do not invent a273MiB measurement. Only81 distinct
parents were observed, refuting a large-parent quadratic-frontier explanation.

Repair metadata representation, not the numeric limit: source-bound JSONL index,
bounded deduplication, small manifests and a repeatably streamable full readset.
Every required verification and full independent mathematics remains required.
A one-shot generator is not sufficient where closure, mount construction and
final verification iterate repeatedly. Test actual-scale metadata and real
host-plus-child peak cost before another experiment; do not repeat the same
failed source, increase budgets or blame the algorithm. The independentR3 and
new recovery-to-model receiver remain preparation, not recovered PASS.

Exact evidence, unchanged cutoff, actual BOLE scope, failed recovery and remaining
model/performance/task edges are in
PAGED_TREE_PASS_AND_RECOVERY_RSS_FIRSTFAULT_20261016_1920UTC.json.


## 2026-10-16: streamed readset fixes RSS, not mathematical timeout

Actual127R3 passed23 host controls and an actual-scale synthetic readset probe
with18,358,272-byte peak metadata RSS. Its actual38304-byte SOURCE binds135503
indexed Refs and82 parents; complete data SHA checks and all681 original raw inputs
remain required. The original R2 failure is retained. The new guest really started
under an observed237312KiB aggregate host+child peak, below256MiB. Synthetic
representation PASS is not numerical correctness or whole-model qualification.

The actual independent child still timed out at585.6111058300012s. CHILD127 and
timestamped container logs prove this first fault; the later owner records1250.109s
and a reserve-clock/cleanup error. Preserve both. Fresh exact-CID inspection proved
exited1/Pid0/noExec/noOOM/Devices[]; it does not rewrite the old failed release flag.
No DOMAIN result or complete160-row mathematical verdict exists.

Read the executed callgraph before assigning causality. The original Lane class
is compiled into a namespace containing the current explicit cutoff: an old
calendar leak is not proved. Ordinary calls reserve180 of the720-second lease,
where the declared cleanup is90. Full pre/post source scans also cost real time.
Source shows repeated raw blob hash/read passes and671 sidecar hydration/audit
calls; these are hypotheses for runtime cost, not measured hotspot fractions.
Run a bounded same-image Devices[] actual-frame timing discriminator before a
minimal new codec/clock repair. Keep all math, frames, numerical thresholds,
source fences and original budgets; no unchanged full retry or cached PASS.

MAIN also attempted the model software suite with host Python3.9, which lacks
torch and the guest TMPDIR. Preserve that wrong-environment failure. It is not an
image regression and does not justify installing torch on the host. The genuine
source audit separately found16 missing original017 dependencies, now restored
missing-only with exact pinned bytes. Real same-image100-test plus IPC/EROFS
admission remains required. Prepared128/101 receivers cannot borrow a failed
127R3 result; a changed recovery needs its own explicit typed successor source.

The user conditionally authorized one24h extension. Its separate workstream
record is not activated: no new valid whole-model pair exists. Original clocks,
performance/task gates and all failed evidence remain unchanged.

## 2026-10-16 22:13 UTC: measured evidence cost and real-model source seams

Actual130R1 completed all27 retained sidecar measurements with no row/audit
errors in21.07076861s: hydration18.24487961s versus audit2.70203337s,
53,904 application blob opens and2,505,448,800 application read bytes. These
are application reads under uncontrolled filesystem cache, NOT physical disk
traffic. Main-record64-step math/cumulative ledger cost is not included.
Its parent FAILED because the complete final source/storage fence inherited
the container cleanup90 alarm; independent quiescence does not relabel that
parent. A successor separates cleanup from final verification inside the same
original500-second total. The unexecuted133R1 also fixes a proved nested-meter
reset/active-state error; inclusive parent and child timings must not be added.

Actual101R7 passed94 of95 Linux same-image controls, with one missing-file
error before NPU admission: INVERSE101R7.json existed on the preparer's machine
but was absent from the declared source and delivery. Both source-byte audits
and local95 tests had missed this implicit file. Preserve the failed owner
and its stopped retained CPU container.101R8 adds the exact inverse to source,
byte payload and RO mounts, then reconstructs and tests only declared files.
AST own-read analysis catches this resolved dependency but lists seven unresolved
dynamic read sites; it is NOT a general proof of every possible filesystem read.
Genuine same-image95, IPC/EROFS and actual model gates are still required.

A new explicitly typed16-to-nine-decode diagnostic edge may consume the actual
40-row/63-sidecar local16 domain to expose real2K/C1 worker seams. It is NOT a
replacement160 certificate, a promotion of the old strict FAIL, or production/
performance/task admission. The original numerical consumer/arithmetic/thresholds
remain unchanged; old106/122 consumers must reject this new diagnostic source.

Actual BOLE131 passed34 same-image controls, real native parser/MTP metadata,
and all four tiny NPU canaries. Real workers then rejected callable source
identity at worker_entry.discover -> code_source(obj.forward,qwen_next_ref),
before HTTP/tree execution. Preserve both native stderr and the parent's generic
startup failure. The specific callable ownership/wrapper cause is not yet proved;
inspect the actual installed method/decorator chain, never disable its identity
gate or blame the tree algorithm. All81 delivered files were verified before
and after the run. Both exact owned CIDs are stopped/Pid0/noExec/noOOM;
exit137 from stopping retained init is not an OOM or numerical verdict.

The next source-bound actual model diagnostic is101R8. BOLE requires a narrow
new source repair;133R1 and127R4 remain preparation with explicit missing
dependencies/budget evidence. No new model performance or task-quality result
exists, no30-minute utilization percentage is inferred, and the one conditional
24h extension remains unused. Exact source/results, CURRENT/NEXT/BACKUP and
source-only recovery archive are in
MODEL_DIAGNOSTICS_AND_DELIVERY_CLOSURE_20261016_2213UTC.json.

The subsequent actual101R8 gate passed all95 Linux controls, genuine AF_UNIX,
EROFS30 and four parser canaries, then FAILED before model construction in its
new real isolated entry. trace_plugin could not import qwen36_deltalog_service:
the parser probe had inserted the plugin path explicitly, while the actual
entry relied on PYTHONPATH ignored by Python-I. Keep the failed187.470s owner
and both released exact CIDs. Repair the source-pinned package bootstrap in
that real fresh interpreter and its actual children, not the numerical gate
or interpreter isolation. This repeats a known bootstrap lesson: test the
actual aggregate entry-to-first-import edge, not an already prepared process.

Readonly inspection of the immutable installed BOLE worker patch shows a real
Qwen3NextAttention.forward replacement in patch_qwen3_5.py. A successor must
bind that exact installed function and registration chain and record mismatch
operands; a generic model source or arbitrary inspect.unwrap is not proof.
The last two frontdoor failures are implementation defects, not evidence of
paper-wide performance impossibility. No current NPU job remains at this
checkpoint; two independent narrow repairs are being prepared.
