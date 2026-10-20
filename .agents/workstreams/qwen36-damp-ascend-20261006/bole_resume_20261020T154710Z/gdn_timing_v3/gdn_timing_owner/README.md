# Prepared only: finite GDN component timing owner

Nothing in this packet has run on the host, in the target image, or on an NPU.
It is a local advisory packet for MAIN to review and separately admit after its
priority G1 TP4 unit releases resources. The frozen candidate, replay-v2 and
timing files are unchanged. Component timing cannot establish model, task,
whole-service, fixed1024 E2E or >=10% E2E success.

## Sources and prerequisites

`timing_owner.py` adapts the supplied exact actual replay-v2 controller
`gdn_owned_v2_controller.py` (12517 bytes,
SHA256 `18ce957ef0a8130e64d73f7c73a99536e19f283ea68e09620c6b328fd089a195`).
The supplied actual audit `GDN_REPLAY_V2_AUDIT.json` is pinned by its exact
2942 bytes/SHA256. That audit names the independently successful actual
192-frame x2-layout replay; it is a component prerequisite rather than timing
evidence. Every launch reopens its actual owner, independent report, producer,
release, prior admissions/raw inspections, all original captures, all replay
indexes/blobs and all relevant executable sources. Failure of any source or
chain check prevents admission.

The installed runtime paths below were supplied by MAIN after its actual
Devices[] scan. The timing manifest uses these installed absolute paths. Host
evidence copies are separate Ref3 objects with matching bytes/SHA256 and must
have different paths.

| Runtime key | Installed container path | Bytes |
|---|---|---:|
| triton_jit | /usr/local/python3.12.13/lib/python3.12/site-packages/triton/runtime/jit.py | 36630 |
| triton_compiled | /usr/local/python3.12.13/lib/python3.12/site-packages/triton/compiler/compiler.py | 18714 |
| ascend_compiler | /usr/local/python3.12.13/lib/python3.12/site-packages/triton/backends/ascend/compiler.py | 53431 |

`timing_owner_common.py` pins these three exact hashes and both frozen timing
source hashes. It checks host copies before Docker, then actual installed files
in the bounded boot and the Devices[] statistics reader. No Torch or Triton is
imported by any source in this new packet, including execution paths. The
frozen timing CLI imports its tensor runtime only after the complete real
post-inspection admission gate.

## Preparation and review interface

`INPUTS_TEMPLATE.json` is a non-executable sketch. Null Ref3 placeholders must
be filled from actual files; it is not an admission or a successful execution.
`build_inputs.py` is the executable source preparation path. MAIN copies this
packet into a **new immutable source leaf**, retaining the frozen timing leaf,
actual replay-v2 leaf, original r23 source/captures and host runtime evidence.
The generator accepts explicit paths and exact existing refs; it validates the
entire successful prior chain before writing a new `INPUTS.json` with
`admission:null`.

Generator flags are `--execute --source-dir ABS --timing-dir ABS --baseline-ref
REF3_JSON --audit-ref REF3_JSON --runtime-host-evidence JSON_MAP --name
UNIQUE_NAME --reader-name UNIQUE_READER_NAME --output NEW_ABSOLUTE_INPUTS_FILE`.
Both names must start with `bole-gdn3-timing-`; the reader name additionally
starts with `bole-gdn3-timing-reader-`. `--source-dir` must be the generator's
own new directory. The runtime map has the three keys in the table and Ref3
values pointing to **host copies**. The returned `inputs` Ref3 is passed intact
to the owner.

MAIN must review exact bytes, perform its actual same-image Devices[] cold
default/help/source checks, observe admission/resource availability, and assign
a new output leaf before launch. This packet does not contain an actual
same-image software-pass receipt. All four entrypoints default OFF and support
`--help` without importing tensor packages.

The explicit owner CLI is:

```text
BOLE_GDN3_TIMING_OWNER_ENABLE=1 /usr/local/python3.12.13/bin/python3 -I -B timing_owner.py \
  --execute --inputs-ref REF3_JSON --output NEW_ABSOLUTE_OUTPUT_LEAF
```

This is an interface description; no command has been submitted by this agent.

## Finite lifecycle and ownership

The whole source-precheck/timing/reader phase has an inherited 1800-second
deadline and a separate 120-second cleanup window. The bounded post-inspect
handoff waits at most 60 seconds after its full prior-chain check. All retained
unit evidence/logs have a 192MiB monitored aggregate cap; actual timing exports
retain their own frozen 64MiB cap, each child log has an 8MiB cap, and independent
statistics output has an 8MiB cap. A timeout/cap failure remains a failure.

Before create, MAIN observes NPU4, /proc PID/cgroups and physical4 FD holders,
requires it unoccupied, and observes the actual original r23 container stopped
on the same exact image. It never selects physical0..3 or stops foreign
processes. The owned singleton maps **physical4 -> guest /dev/davinci0**, with
the same three control devices and read-only Ascend driver mount. Bounds stay
8GiB memory+swap, CPUs0,1,2,3, 512 PIDs, network none, read-only root, caps ALL
dropped, no-new-privileges, private `/tmp:rw,exec,size=1073741824`, shm1GiB.
All relevant source/prior-evidence parent mounts are read-only; only the new
output is writable. Runtime caches/logs go to private tmpfs. HF32 is OFF in
the admission and frozen timing entry.

The owner starts the waiting boot, saves the complete raw actual Running Docker
inspection, validates identity/image/resources/mapping, then writes the real
`ADMISSION.json` and final `MANIFEST.json`. Only then does it atomically publish
`MANIFEST-REF.json`. The boot independently reopens source/prior/runtime and
admission/current-cgroup/environment/mount protections before exec of the
unchanged timing CLI. No fabricated admission is used. Existing real frozen
timing config remains 4 warmup pairs, 20 sample pairs, 4 iterations/batch,
all192 frames x2 layouts, alternating AB/BA, actual r23 terminal, symmetric
host perf_counter_ns + NPU synchronization. No candidate-only precomputation or
guard-in-measurement modification is introduced here.

After actual child exit0, the owner stops and retains the exact singleton,
records raw stopped inspect and `RELEASE.json`, observes no remaining physical4
FD holder, checks source/evidence immutability, then writes `NPU-OWNER.json`.
That receipt is the completed finite NPU phase; it deliberately precedes the
independent reader to avoid a final-owner/consumer hash cycle.

A separate same-image Devices[] reader uses CPU145, 1GiB memory+swap, 128 PIDs,
private exec tmpfs64MiB, shm64MiB, network none, no numbered/control device
mapping and no driver mount. Its actual created raw inspect is written before
start. The reader verifies this exact identity/cgroup, Devices[], environments,
resources and read-only evidence mounts. The final owner `RESULT.json` links
the reader report and both exact owned identities. All owned containers are
stopped and retained in `finally`; cleanup rechecks full CID/image/exact label,
never globally kills/resets/removes anything, and retains primary and secondary
failures separately.

## Independent arithmetic scope

`consume_timing.py` reopens successful prior replay/source/runtime files,
actual timing admission, raw Running/stopped inspections, zero-exit child/log
refs, NPU owner before/after source inventory, every original raw Ref3, all four
`TIMING-RANK` JSON files and every `.npubin` byte. Binary inventory must exactly
equal the union of all frame proofs. It joins all192 layers/ranks and both
layouts to the original saved request/selected terminal, checks saved untimed
calibration/bitwise hashes and checks finite original112 metric evidence.
It does **not** pretend to recompute tensor math from timing JSON. Independent
numerical qualification remains the already successful actual replay chain.

For every one of 384 frame/layout records it reads all20 ordered sample pairs,
checks exactly10 AB +10 BA, positive integer durations, full warmup schedule
and no missing/duplicate/reordered frame. It independently recomputes per-role
mean/median/min/max using all20 raw batches, per-order10-pair statistics,
paired ratio/difference descriptive statistics and both full aggregates, then
checks the producer aggregate for exact arithmetic equality. Its own rank
reports retain all7,680 raw pairs (15,360 batch durations). No sample/frame or
outlier is removed and no favorable-order or winning-frame group is selected.
AB and BA aggregates are reported separately alongside the total. No speed
threshold, model qualification or E2E success is inferred.

## Local validation and remaining actual work

`test_pure.py` exercises only local stdlib controls. Its JSON fixtures are
explicitly synthetic unit fixtures and are never passed to a device owner or
claimed to be actual admission. Tests check default/help/opt-in failures,
source AST/import restrictions, known sample arithmetic and omitted/order/
duration/summary mutations, runtime path-vs-copy distinction, Ref3/duplicate
JSON guards, exact singleton/Devices[] mappings and resource/tmpfs mutations.

MAIN still must review and copy this new packet, materialize actual source refs
using `build_inputs.py`, run actual same-image cold/software checks, wait for
its priority G1 unit to release resources, create a distinct admission, execute
the bounded timing, independently consume it and inspect final cleanup.
1800 seconds is a preregistered finite limit, not a prediction that actual
compile/timing will finish within it. Any runtime/API/numeric/source failure
remains a failure with retained evidence. No optional timing/config alteration
or hidden fallback has been added to the frozen timing code.
