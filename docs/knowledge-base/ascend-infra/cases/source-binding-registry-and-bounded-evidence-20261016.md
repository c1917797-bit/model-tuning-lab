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
