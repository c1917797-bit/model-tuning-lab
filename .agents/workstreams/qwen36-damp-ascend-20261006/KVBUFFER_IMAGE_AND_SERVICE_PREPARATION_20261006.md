# KVBuffer: actual image preparation and NEW service handoff

Preparation checkpoint2026-10-06T20:50Z; not NPU/E2E acceptance.
Canonical repository /opt/host/vnf/austinov/model-tuning-lab; branch work/qwen36-damp-ascend-20261006.
Predecessor source7fd59c11121772afd7f691f4b64e22d567c89e09 was pushed normally
and exact remote-verified. Frozen service11/split5/bridge4/dispatcher5 and
49-source closure remain unchanged. MAIN alone owns Git, Docker and NPU launches.

## Actual same-image evidence, including the scoped failure

MA0729 used fresh Git-export source mounted RO, the recorded image660ce23a,
Python3.12.13, real CANN environment and no NPU devices. It was nonprivileged,
netnone, capdropall, 1CPU/2GiB with no swap; no SoC mock. All actual child
commands exited0:69 stdlib tests (17 service+17 split+14 bridge+21 dispatcher),
six frozen CLI --help commands, default-OFF bridge/dispatcher checks,49 source
pins/native-image identities and the real vLLM API-server --help. The latter
really ran70.61s and contained all13 required server flags. No model was loaded.

The whole parent exited1 because MAIN incorrectly required all six requested
plugin names to belong to vllm.general_plugins. This is a preparation predicate
bug, not a native numerical or algorithm failure. The actual groups are:

- vllm.platform_plugins: ascend -> vllm_ascend:register.
- vllm.general_plugins: ascend_kv_connector, ascend_model, ascend_model_loader,
  kvbuffer_parallel, kvbuffer_service.
- Existing profiling plugins were not added to the activation whitelist.

MA0734 performed a NEW narrow grouped-inventory check. It rehashed all original
streams/summaries, verified the actual69 test counts, original49 source pins and
native-image bytes, and checked each required group. It exited0 with no missing
platform/general names. It did NOT rerun69 tests or the70.61s API help, and did
NOT relabel the original MA0729 exit1. The original VLLM_PLUGINS string stays
byte-identical; platform registration is discovered in its own group.

Both exact-owned no-device containers were stopped and retained:
MA0729 d959bcce59fe69ad962d239cfdef4a6ee478f071713e432d964340f27d88054f exit1;
MA0734 4acec9f39b4cfa73cac63a70fd986f76ac9351d74013ba70440f1513f07ff8f2 exit0.

Original evidence outside Git:
- /cache/cch/qwen36-damp-20261006/kvbuffer-preflight-MA0729-terminal-original.json
  SHA256 f41aad29057b635b8ebd4b12389550bf85b9885bbe23f3df7f413806e217336e.
- /cache/cch/qwen36-kvbuffer-parallel-20261006/preflight-image-export-v1/results/SUMMARY.json
  SHA256 cbd40d9079c81ab474cdb4f595e2ad15d302f12fd0addafa79e10bb27588375f.
- /cache/cch/qwen36-kvbuffer-parallel-20261006/preflight-grouped-inventory-v1/results/GROUPED_INVENTORY_CORRECTION.json
  SHA256 23d42ea0ff5acbc61b7a6d27dc5610a142ee714ca68e92a94b4865f187dca6bd.
- /cache/cch/qwen36-damp-20261006/kvbuffer-preflight-MA0734-group-correction-terminal-original.json
  SHA256 da98e5b234a682cf62c3da8fe8fa8d98ea86a1c255347ff3ecd39f9106777539.
Both result paths above were checked against the original a_fs_read receipts.

## NEW report consumer and launcher, default OFF

MAIN read the complete four-file split_service_consumer_v1 draft and added only
NEW files; no frozen producer, bridge, old launcher or liveDAMP52 source changed.
Actual MAIN MA0747 exited0:11 synthetic producer-shaped regressions, byte hashes
of all four files, syntax, and actual default-OFF consumer/launcher/middle-driver
CLIs. Synthetic fixtures are not actual device identities or reports.
Original /cache/cch/qwen36-damp-20261006/kvbuffer-preflight-MA0747-new-source-host-check-original.json
SHA256 8c69b09039a2360a67063cb67f1a3c66c149c78312b337fae27644fbf07e3dc6.

The NEW consumer interprets two original MAIN RunAuthority records, actual
CHILD Python PID/start-ticks/NSpid/cgroup/argv separate from WAIT/canary, original
runtime-budget inputs, raw cleanup/release and source-after receipts. It accepts
the NEW split schema rather than fabricating an old combined8-case PASS.
The NEW launcher retains original eager/P1 dense/candidate argv/common flags and
72GiB model RAM floor, checks actual same-absolute-path RO evidence mounts and
platform/general plugin groups, and keeps diagnostic/execute opt-ins separate.
Matched E2E/task acceptance and true intermediate batches remain false/pending.

## Genuine T2–15 coverage, not PAD16 substitution

MAIN read actual MA0740 record.args[3] fully and added only
projects/kvbuffer-parallel-ascend/tools/middle_batch_gate_v1/run.py.
Final reviewed source SHA25616ed62857871e4576694802bd45afb2a3ec70d726f90f2687860689b92ef3a10.
An initial extra EOF blank line introduced while assembling the patch was
removed before source freeze; original MA0747 hash is retained as historical,
not silently reused as the current middle-driver hash.

The144-line driver calls frozen oracle.run_case directly, with unchanged
OUT .00303/full-state and per-head2e-6,160 feedback steps,1 eager+3 graph trials,
slots=T+3, selected/untouched/guard checks and reset64/112. Exact true-T shards:
physical4 [2,14,15];5 [7,11,13];6 [3,4,9,12];7 [5,6,8,10].
B1/B16 are owned by the existing separate prerequisite; NEW middle reports do
not impersonate their schema. MA0740 actual software-only14 checks passed,
including2240 frozen slot-admission/flush/reset turns; no NPU was executed.
Original /cache/cch/qwen36-damp-20261006/kvbuffer-middle-MA0740-draft-software-original.json
SHA256 7cad0b2d14fab53cd61ca3e3fd8e3627bca457e50f4ce05aeb0a6e242f857ef2.

After the EOF correction, MAIN MA074d read the actual landed driver file and
ran the same14 software checks with its exact reviewed hash; child exit0.
The wrapper's historical code_landed=false literal is not a filesystem claim.
Its second actual child validated the Maintainer Skill Tree (20 skills),exit0.
Original /cache/cch/qwen36-damp-20261006/kvbuffer-middle-MA074d-landed-software-mst-original.json
SHA25626c469d9c579c1e18a2efc4d74f034578b8faf14d72a372d057ae9d08df98bbf.
These remain software-only checks, not Meta, native numerics or a ready launch.

This is NOT a complete ready launch packet yet. Before new device dispatch:
finish the actual identity producer/summed budget/exact canary-to-child binding,
same-image no-device artifact/mount/Meta/CLI checks, terminal/raw report consumer
and predeclared timeout/cleanup. Old two-batch dispatcher cannot create this NEW
identity and must not be fooled with a changed owner label. MAIN will reuse its
audited helpers in a thin launch packet, not create a generic approval framework.
No KVBuffer formal24h start is inferred from software preparation.

## Live cards and queue: actual observation, not final PASS

MA0749 observed2026-10-06T20:46:19Z: MA070e selected_row_bal_v1 remains the ONLY
live numerical job. All four actual Python PIDs own physical4–7;24 completed
cases/3840 feedback steps and24 native anchors; zero failed recorded checks.
Full64-case aggregate/source-after/owned cleanup are still pending.
The snapshot helper reads the wrong pair_count key; its0 is NOT a failed
independent reference. Earlier originalMA070f proved192 bitwise pairs.
Protected0–3 PIDs174886/174890/174892/174896 remain unchanged.
Original /cache/cch/qwen36-damp-20261006/damp-selected-row-MA0749-live-original.json
SHA256 323d3262454d6d93533713c621dd2bdda5c406fa3d3c6beef461f559ab32c164.

Fresh MemAvailable57166256KiB remains below72GiB; no full-model admission.
The no-device preflight was separately admitted with summed current4x8GiB
jobs+2GiB preflight+8GiB reserve=42GiB and actual Docker7CPU. Actual DockerRoot
/cache/docker, not /var/lib/docker. A guessed /usr/bin/ss failed and is retained;
shutil.which proved /usr/sbin/ss before the bounded follow-up. These checks do
not authorize lowering model reserve or disturbing protected workloads.

Next: observe only MA070e through its existing bounded terminal/cleanup; prepare
the next real kernel and model handoffs in parallel. No dummy utilization,
uncontrolled retries, tensor tolerance relaxation or unsupported paper-wide
no-go. All fixed paper/portfolio cutoffs and final performance/task gates remain.
