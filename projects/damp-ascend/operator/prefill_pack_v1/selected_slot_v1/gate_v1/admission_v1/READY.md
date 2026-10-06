# Selected-prefill strict component admission v1

Status: source preparation only; default OFF; no Torch/import/load/build/Docker/NPU/Git
performed by this packet. Existing frozen gate11, compiled kernels and actual
receipts are unchanged.

## API

`validate_complete(isolated_run, native_run, read_bytes, *, source_manifest, enabled=False)`
in `contract.py` returns a frozen `ComponentAuthority`, or raises `Pending`.
`read_bytes(absolute_path)->bytes` must read original actual bytes; validator checks
SHA itself and rejects duplicate JSON keys/nonfinite JSON. `source_manifest` is
a MAIN-issued `Ref(path, sha256)` to this packet's frozen SOURCE_MANIFEST, not a
report-supplied self-authorization. No code signs receipts or authenticates JSON.

`RunAuthority` has stage, report/child Refs, a TerminalAuthority, exact child
command/args tuple/cwd, MAIN's actual container ID/card, owner-proof Ref and
controller-sources tuple[Ref]. TerminalAuthority has original receipt Ref,
expected peer/operation ID/command/args tuple/cwd. It is MAIN's external expected
authority, **not a cryptographic signature**. It must be constructed from MAIN's
actual controller/operation result, never from software fixtures or report status.

Both stages are mandatory: isolated P1/P16 × adjacent/guard-gap arena, 20
same-buffer changing calls + 8 reset calls + PAD/range/duplicate + numeric errors
+ 57 host negatives; and eight native P1/P16 × layouts × fresh/continuation
cases, each actual native chunk → selected pack → 160 own-feedback steps.
Existing source-pinned status parser, compiler receipts and six independently
anchored native/reference traces are reused. Tolerances remain state 1e-5,
output .00303. Packed bitwise fields in feedback are diagnostic, not a new
acceptance threshold. All complete/selected state, immutable inputs, pointers,
ND, untouched raw arena and per-step metrics are checked.

The descriptor contains exact source/runtime/report/child/terminal/SO/native
anchor/controller identities and physical cards. It has batches=(1,16),
feedback_steps=160, plan_index=None. serving_ready,
performance_measurement_admitted, graph_supported, all_prefill_batches_supported
and full_model_cache_supported are always false. This standalone operation-chain
evidence is NOT calibrated 192 plans, actual 48 receivers/TP4 allocator, real
mixed scheduling/FA read-write/zero lifecycle, full P2–15 native continuation,
graph, task accuracy, E2E performance or C16 delivery.

## Future actual child producer contract (NOT a historical receipt)

The MAIN dispatcher does not exist yet. Missing original terminal or any child
field keeps admission pending. No actual pass receipt is created by this packet.

Schema `damp-selected-prefill-child/v1`:

- stage: isolated or native_feedback; report:{path,sha256}.
- execution: actual command, args (JSON list), cwd, state, returncode, error,
  cancelled, timed_out, stdout, stderr, started_ns, completed_ns, duration_ms.
  The producer must derive these from the actual subprocess return/timeout/
  cancellation/error branches. No unconditional success/false flags or defaults
  are permitted; an interrupted run does not produce success authority.
- container:{id (actual full 64-hex), image_id, physical_npu_ids:[4|5|6|7],
  logical_to_physical:{"0":card}, privileged:false}. Bind actual owned container
  inspect and fail-closed resource proof, not a requested Docker configuration.
- owner_proof:{path,sha256} (same original bytes as report bindings). Fresh at
  actual acquisition/start, <=30 minutes, nonfuture; retrospective admission does
  not pretend a historical preflight is fresh now.
- controller_sources:{absolute_source_path:sha256}. MAIN expects exactly the
  original parent/child shim source bytes; actual outer argv must execute one.
- runtime_manifest:{path,sha256}; runtime:{soc:"Ascend910B4",
  torch:"2.10.0+cpu", torch_npu:"2.10.0.post4", opp_version_info_sha256:...}.
  This is actual process observation, not the compiler's dav-2201 target.
- runtime_image_sources: exact 23 pinned image sources for native_feedback;
  {} for isolated. A source-bound actual child shim must measure them.
- loaded_libraries:{actually_mapped_absolute_path:sha256}; selected only for
  isolated, plus actual allbatch/reference/native for native_feedback.
  Files merely existing on disk do not qualify. A child shim in the SAME process
  can run the frozen gate and then inspect its actual /proc/self/maps and file
  bytes; the parent's post-exit file SHA alone cannot observe mapped libraries.
- artifacts:[{path,sha256}]: exact preserved negative artifact set; no missing
  copy errors, arbitrary extra files or substituted output roots. Validator
  checks original bytes without unpickling .pt.

Expected child args bind frozen run.py, --execute, --stage, physical card,
owner proof, exact runtime/source/SO/build, output directory and explicit
--batches 1 16 (or 16 1). Native args additionally bind reference/decode/anchor.
A MAIN source-bound shim may receive run.py as an argument and call its public
main; do not monkeypatch torch.ops or bypass original protocol.

After writing the actual child receipt, the actual outer controller stdout must
contain exactly one line:

`MAIN_SELECTED_PREFILL_CHILD {"child":{"path":"...","sha256":"..."},"report":{"path":"...","sha256":"..."},"stage":"..."}`

MAIN saves the **original operation_get structuredContent bytes**, hashes them
and supplies its expected operation ID. Validator checks schema agentweb.operation/v1,
kind exec, terminal/completed/succeeded, direct peer
lgw_a6109c51076a4a2c9d2674ca5a8704a0, original command/args/cwd, return exitCode0,
no cancellation/timeout/error, and that raw stdout marker binds both actual
receipt/report hashes. This binds related artifacts under MAIN trust; it does
not prove that arbitrary JSON cannot be forged.

## Evidence limits which cannot be upgraded by this validator

Positive gate reports serialize twelve-P status rows, all guard checks and raw
arena SHA, not the complete guarded positive status tensor payload. Frozen
pack_once checks the full status guards before recording rows. This validator
does not fabricate missing positive raw tensor bytes. Per-step feedback reports
have full numerical/guard rows but no per-step input/output/state content hashes;
they cannot become bitwise graph replay or crash-recovery evidence.

CPU BEFORE snapshots in gate11 are held in memory; negative/failure artifacts
are saved later. There is no durable pre-dispatch disk journal, no process-kill
recovery proof, and a partial numeric write must retire the entire selected
call/slot set permanently with no retry. This admission checks all 12P status
rows and exact 12 numeric-retirement records; successful feedback has no
poisoned dispatch/D2H/pointer record. Expected synchronous host TORCH_CHECK
exceptions are retained negatives, not treated as an NPU numerical failure.

The runtime closure is own gate9 + declared repo50 + actual-image23 and immutable
image/binaries, not a complete third-party framework/driver source audit. Actual
OPP version.info supports OPP9.1 identity, not every CANN SDK package.

## Software verification command

From canonical repository, MAIN may run (no Torch or devices):

`python3 -B -m unittest discover -s projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/gate_v1/admission_v1/tests -p test_admission.py -v`

Behavior fixtures are explicitly SYNTHETIC in-memory JSON/artifact bytes; real
frozen source/build/anchor bytes are reused to test identities. Software tests
cannot authenticate AWMCP origin, create actual NPU receipts or serve authority.
On a source-only host the actual image-native .so path is unavailable; the full
validator must stay Pending rather than synthesize native bytes or waive SHA.
The isolated complete path and individual native matrix/metric/status/poison/
scope rejection paths are exercised independently; MAIN may run the same
stdlib tests in its immutable no-device image to exercise complete binary reads.
This packet contains no NPU execution command or dispatcher; MAIN writes and
reviews the actual future producer, performs fresh preflight, executes the two
existing gate commands, and only then passes genuine evidence here.
