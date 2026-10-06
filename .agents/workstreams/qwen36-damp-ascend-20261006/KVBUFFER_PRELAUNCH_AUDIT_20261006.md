# KVBuffer FP32 parallel-fold: next-stage prelaunch audit

Status: SOURCE/READINESS AUDIT ONLY, not launch-ready, no new NPU result.
Preparation does not activate KVBuffer or begin its formal24h clock. It does not
change DAMP's2026-10-07T08:48:03Z cutoff or the portfolio's2026-10-09T11:17:31Z
cutoff. MAIN alone may admit/dispatch; current MA06a0 four-card DAMP correctness
work remains exclusive. No Torch import, Docker/build/load/NPU/Git operation or
KVBuffer/DAMP frozen source change was made in this audit. The only write is
this NEW document, commit:false. MAIN full review is still required.

## Read point and actual evidence

Canonical root: /opt/host/vnf/austinov/model-tuning-lab.
Branch: work/qwen36-damp-ascend-20261006.
Fresh prepatch HEAD8161a70c6ddc361ea405b687bdada16b0cbab9ab.
Root AGENTS, current branch HANDOFF/SCHEDULING, host/orientation/loop/benchmark/
paper-to-Ascend skills and migration references were read. No project-specific
AGENTS exists under the inspected projects/kvbuffer-parallel-ascend tree.

AWMCP MB direct route, read-only/source-only receipts:
- exec03fa inventoried actual project paths, not guessed historical paths.
- exec03fd:10/10 split REPO_PINS match; actual build/meta/SO bytes match.
- exec0400 and0401: actual host stdlib --help for split run and service launch,
  both completed/exit0/error:null/no timeout/cancellation. These are NOT
  same-image full CLI/plugin preflight, imports or device proof.
- exec0403: this new path absent/non-symlink, parent exists.
- exec0404: fresh37-file KVBuffer source snapshot and corrected static cost ledger.
These MB handles are not MAIN MA handles and must not be polled through MA.

Existing actual immutable image:
sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
Existing build receipt:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/build-receipt.json
 SHA25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4.
Existing SO:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so
 SHA0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b.
Existing Meta report:
 /cache/cch/qwen36-kvbuffer-parallel-20261006/meta-p1-v1/report.json
 SHA2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727.
They prove no-device compilation/load/schema/positive B1/B16 Meta only.
Meta negative validation is absent.25 old software tests are not NPU PASS and
were not rerun here. Do not rebuild or overwrite these completed roots.

Important current sources, relative to canonical root:
- projects/kvbuffer-parallel-ascend/tools/native_oracle_probe.py
  caa65dd94506edbd68a5600e9f813d93711ba162a8a2fc0565e7e00ede4414dd
- projects/kvbuffer-parallel-ascend/tools/split_gate_v1/run.py
  f5e3c4a66b007b9d2db34d0e72d2f5543127d2ee34c78efdf7ae472b35b020f1
- projects/kvbuffer-parallel-ascend/tools/split_gate_v1/contract.py
  32dd50050a28de0038aa847f55068e58efba98be07d15229b2e1f36eef4ae880
- projects/kvbuffer-parallel-ascend/tools/split_gate_v1/PACKET.json
  00816f440a883202c9f5bb79672e8ff2ee1d63fde4cb8b19f8fa14d80f0a775e
- projects/kvbuffer-parallel-ascend/plugin/kvbuffer_parallel/patch.py
  71be0c99af19d66bc5f44ebb983b748cd56e2e776d567b0b4df0789ca0d89e2d
- projects/kvbuffer-parallel-ascend/operator/op_kernel/qwen36_gdn_kvbuffer_parallel.h
  8fde339a17c32d853de9d05bdfb69dd2e6ab4e023f1de8c3dc7abc9c7e153674
All37 sources are independently snapshotted in exec0404; after-write verification
must check they stayed unchanged. REPO_PINS10 and NATIVE_PINS4 are declared
bindings, not proof of every transitive imported module/current loaded native SO.

## Actual entrypoint and preserved full matrix

Use the NEW split driver, NOT the old physical4-only main:
 /usr/local/python3.12.13/bin/python3 -B
 /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_gate_v1/run.py
 --batch 1 --physical-device 5
 --identity /kvbuffer-results/split-p1-b1-phys5-v1.identity.json
 --output-dir /kvbuffer-results/split-p1-b1-phys5-v1
PACKET.json contains exact argv arrays. Second job uses
--batch 16 --physical-device 6 and split-p1-b16-phys6-v1 paths. Their defaults
bind the existing library/build/meta under /kvbuffer-results. Preserve exact
image CANN paths; canonical repo/build/meta RO, only fresh results RW.

run.py:10–17 imports the unchanged probe;78–81 calls its original run_case
once eager and three independently captured graph trials. Each job is640
closed-loop steps; aggregate is8cases/1280steps. This does not need DAMP full
calibration/SOURCE_LOCK or final192 plans. It needs genuine prior-job terminal,
exact stopped owners, fresh resources/mapping/canary and immutable identities.

Original oracle coverage:
- native_oracle_probe.py:82–86 uses genuine FP32 native recurrent state,
  four positional tensors, beta/scale/g/lengths/indices keyword-only.
- :144–189 keeps native and candidate independent feedback arenas; never
  resynchronizes candidate state from native. Graph inputs are copied to fixed
  buffers, synchronized before replay; prepare occurs outside capture.
- :169–174 covers capacity16 boundaries, changed slots, reset/reuse at64/112.
  B16 graph active schedule0/1/3/7/12/15/16/16 checks native dummy slot0.
- :190–208 saves complete raw tensors before logical reconstruction/metrics.
- :210–242 checks complete AND worst-head state relativeL2<=2e-6,
  output normalized max<=0.00303, untouched all slots/logs, nonflush base
  bitwise unchanged, metadata padding/old-U, state guards/pointers, all input
  immutability, finite values and dummy output zero.
- :262 requires flushes and two resets; no retry.

No actual eager/graph NPU PASS exists for this new parallel-fold implementation.
Graph captures here are operator-only, not scheduler/model graph admission.
Pointer gate :226 checks six state views only; native/static-input/output
pointers are recorded but not all asserted stable. Output and native-state
arenas are not sentinel-guarded. Malformed live metadata values are caller-
rejected by admit_lengths, not a tested device fail-closed matrix; kernel
:498/502 early returns may leave output uninitialized outside admitted contract.
Do not silently expand this evidence scope. T2–15 are NOT in the original
matrix although wrapper/plugin accept1<=T<=16.

## Fastest necessary prelaunch engineering gaps

1. **ONE joint resource/owner admission, not two independent promises.**
   split contract.py:40–60 checks per-job booleans/evidence dictionary/fresh
   timestamp/actual8GiB memory cap. PACKET has no CPU quota, reserve, summed RAM,
   timeout/cleanup/deadline, disk/IO or live paired-owner policy. A nonempty
   evidence dict is not verification of its referenced original bytes.
   Minimal MAIN preparation is a bounded two-job argv/admission record reusing
   existing safe canary/inspect/stop-retain primitives, not a large controller.
   Both monitors must recognize exactly the other new owned disjoint ID and
   reject genuine external workers; protect0–3 and the live TP4 job.
   Two8GiB caps require at least16GiB plus unchanged8GiB ordinary-RAM reserve,
   and summed actual CPU quotas against fresh engine/cgroup NCPU. Do not use
   Torch thread counts as quotas. If adopting1CPU per job, explicitly budget
   B16 CPU diagnostics and phase timeout first. Any additional fitting/correctness
   job adds its actual RAM/CPU/IO allowance to the SAME admission.

2. **Keep the primary exception when evidence saving fails.**
   native probe:264–266 and split run:84–86 unconditionally save in finally.
   IOError/JSON/save failure can replace the real native/candidate exception.
   Native/candidate dispatch :184–189 occurs before raw disk persistence;
   a dispatch/poisoned context/torch.save failure may have no durable tensor
   snapshot. Pre-mkdir identity/source errors in split :30–36 are outside
   report try. Minimal NEW outer/shim/save-callback guard must preserve original
   traceback/exit/stderr, independently report nullable snapshot/secondary-save
   errors and refuse PASS if evidence is incomplete. Do not rewrite frozen math.
   Test actual absent-output and injected-save failures before scarce cards.

3. **Bind actual image-loaded native ABI, not just source filenames.**
   run.py:58–63 records native schema but does not validate its keyword-only
   names;:64–71 only requires candidate SO hash in maps. The fresh MAIN process
   should strictly verify native schema/call boundary, actual native loaded SO,
   SoC/ND, deleted-map/inode constraints and complete image/runtime/source
   identity. The correct native call is already written; no algorithm change
   or new native operator is needed. Source-only host --help is not this gate.

4. **Bridge the real split reports to the old consumer lawfully.**
   split report schema kvbp.split-native-gate/v1/status
   single_batch_kernel_native_eager_graph_pass contains4cases.
   tools/service/contract.py:53–66 only accepts old
   kvbp-parallel-fp32-native-gate/v1/kernel_native_eager_graph_pass with8cases.
   Thus even two genuine split PASS reports are currently rejected.
   Add a tiny NEW source-bound aggregate authority plus explicit service bridge:
   original MAIN peer/opid/argv/cwd/terminal/stdout/stderr; both report/source/
   identity hashes; exact B1/5+B16/6 and8unique cases; full160step checks,
   finite/error/merges/reset/artifact conditions. Keep raw split schemas and
   failures unchanged. Never fabricate an old single-process PASS report.

## Full-matrix CPU/D2H/IO budget risk: not NPU performance

Static tensor payload from raw save :196–207, with S=B+3:
 raw bytes/step =5195776*S +16544*B +5640.
This includes independent CPU clones of before/after state, both native states,
before/after full guard arenas, two copies of all inputs including T+1 lengths,
and actual/expected outputs. Pickle metadata/filesystem overhead is extra.
exec0404 is the corrected ledger; the initial exec03fd display omitted8B per
batch in its sequence-array calculation and is retained, not rewritten.

| Full shard | raw payload/step |640step payload writes | per-head rel calls |
| --- | ---: | ---: | ---: |
| B1/S4 |20,805,288B (19.84MiB) |13,315,384,320B (12.40GiB) |30,720 |
| B16/S19 |98,990,088B (94.40MiB) |63,353,656,320B (59.00GiB) |145,920 |

Every raw file is written, read again for SHA, then only its individually passed
step may be deleted (:253–261); failure stays. This is cumulative IO, NOT peak
required disk space or peak RSS. Temporary tensors/pagecache and worst failure
retention need actual cgroup/disk admission. :214–217 repeats rel per slot/head;
rel :88–90 separately performs two D2H copies and CPU FP64 reductions. This
adds61,440/291,840 per-head tensor transfers before other metrics, guards and
finite checks. logical(state) also launches NPU exp/einsum outside the candidate,
and check_logs loops/CPU reads plus repeated growing report JSON saves occur
each step. No torch.set_num_threads or CPU quota/timing breakdown is registered.

Both shards have640 genuine native calls, unlike DAMP's rowwise T calls, but
B16 raw/CPU work is about4.8x B1. Equal case counts therefore do not predict
equal elapsed time. No actual CPU benchmark or NPU timing was run here; no safe
3600s completion claim is made. Measure/log first admitted run's CPU fixture,
native/candidate, D2H/save/hash/metric/report segments without shortening its
matrix, and fit explicit bounded phase budgets+cleanup inside formal24h.
A small cost diagnostic is only budgeting, never substitutes full8cases or E2E.
If subsequently optimizing diagnostic metrics, do so in a separately reviewed
NEW source-bound harness with unchanged math/limits and behavioral equivalence,
not by omitting heads/raw evidence or tuning tolerance to pass.

## What operator PASS still cannot authorize

plugin/patch.py:330–435 admits real48 receivers/TP4/CPU scheduling/owners and
reserves full48 auxiliary bytes;:439–529 reuses native conv/gating/l2norm.
Its P1 service is eager-only. :455–462 mixed prefill materializes decode slots
via :146–193 Torch FP32 reconstruction and calls original native mixed core.
P2 mixed lane split is explicitly unimplemented (P2_MIXED_PLAN.md).
No persistent FP32 shadow is used, but actual allocator/typed SoA ND/offset,
shrinking trueT2–15, fresh prefill→mixed→pure decode, EOS/cancel/reuse and48×4
state/output noninterference remain untested for the new candidate.

service/bench.py:93–95 records output_ids_sha256. compare.py:95–117 does NOT
compare dense/candidate output IDs or numerical state. Its metadata observer
checks dispatch/storage/counts, not tensor correctness. It may validly label a
matched SCREEN after previous gates, but it cannot supply the README's missing
native-off/on output/state/cache lifecycle gate. Add that narrow genuine-model
gate before interpreting speed, retaining full failing outputs and source binds.

Existing service screen is40requests/C16/32768input/16384prefix/forced1024out,
profiler off, eager both arms, same total10,658,488,320B/rank:
dense native all; candidate native8,053,063,680 plus auxiliary2,605,424,640.
At119296B/layer/slot and48 layers candidate must<=455 slots before allocation.
Do not increase its budget or reuse historic108.996204tok/s as dense baseline.
Actual image CLI/plugins/imports, current48×4 lifecycle, total allocator budget,
then new contemporaneous paired screen remain pending. A hopeful screen needs
three balanced pairs and final nonthinking normal-EOS/max2048 GSM8K/LongBench-v2
quality, reporting pp/relative loss and TTFT/TPOT separately. User1% task-loss
allowance never replaces the2e-6/0.00303 tensor gates.

## Minimal next decision

Keep the current KVBuffer sources/SO/oracle and original8case matrix. First
repair the small admission/error/consumer seams and preflight actual entrypoints.
Then MAIN can activate the distinct FP32 parallel-fold hypothesis with its own
formal start and one fresh full split matrix after exact owner release. On a
numeric failure retain first raw input/state/exception and diagnose its specific
parallel contraction/fold before deciding. Old serial/v5 E2E negatives do not
reject this untested mechanism; build/Meta/software do not accept it.
