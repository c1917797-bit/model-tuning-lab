# KVBuffer P1 split runner packet — PREPARED / NPU-UNVERIFIED

MAIN-owned execution only; no container, NPU, Torch load, build or Git action was
performed by the preparer. DAMP remains the mainline, deadline2026-10-09T11:17:31Z.
Independent correctness jobs may use physical5 and6 in parallel ONLY after
MAIN's fresh device/namespace admission. Formal TP4 performance is exclusive.

## Existing CLI gap and exact reuse

Frozen tools/native_oracle_probe.py SHA
caa65dd94506edbd68a5600e9f813d93711ba162a8a2fc0565e7e00ede4414dd
accepts only --library/--identity/--output-dir, requires physical4 and loops
B1+B16. Its unchanged run_case accepts a single batch and supplies160step
closed-loop feedback, complete and per-head logical state, all slots/logs,
untouched/no-write/guard/input/pointer gates, capacity16 flush, resets64/112,
and three independent changed-input graph trials. This NEW driver imports and
calls that exact function; no operator, original gate or threshold is edited.

B1 maps physical5→logical0; B16 maps physical6→logical0. Each executes eager1
plus graph3 (four160step cases), slots=B+3. B16 graph active lengths repeat
[0,1,3,7,12,15,16,16]; native dummy slot0 must not write and output must be zero.
Thresholds remain output normalized maximum0.00303 and complete AND per-head
state relativeL2 2e-6. These are not the1% task-accuracy allowance.

## Frozen artifact binding

Existing actual NO-device build receipt SHA
25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4.
Existing positive load/Meta report SHA
2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727.
Library SHA
0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b.
contract.REPO_PINS locks seven compiled sources plus unchanged probe/contract/
patch. NATIVE_PINS locks the four actual runtime files. Neither build nor Meta
is numerical, physical ND, graph or lifecycle proof. No build/Meta repeat here.

## MAIN admission and command packet (not executed)

Create only fresh exact names from PACKET.json; stop if output, identity,
container or log exists. Fresh read-only source inspection observed all four
proposed host output/identity paths absent in LGW02f8; recheck at actual launch.
Host result base:
/cache/cch/qwen36-kvbuffer-parallel-20261006
Container mount target: /kvbuffer-results.
Canonical repository at same absolute path READ-ONLY; existing build-p1-v1 and
meta-p1-v1 nested READ-ONLY; new results RW. Preserve exact-image CANN/LD_LIBRARY/
PYTHONPATH environment. Use ONLY the job's physical card plus source-verified
Ascend control devices; nonprivileged, private device namespace, exactly8GiB
memory AND swap cap, e.g. --memory8g --memory-swap8g; sufficient disk/ordinaryRAM.
No model/port/network service is involved. Do not join another workload's namespace.

MAIN independently creates schema kvbp.split-launch-identity/v1 with:
image_id; physical_devices [5] or[6]; logical_to_physical {"0":5} or{"0":6};
fresh_idle_verified, nonprivileged, source_canary_passed all true;
memory_cgroup_bytes8589934592; library/build/meta receipt hashes;
repo_sources=contract.REPO_PINS; native_sources=contract.NATIVE_PINS;
driver_sources=all five NEW files' final SHA map; protocol=contract.protocol(B,P);
fresh preflight_utc≤600s; independent device/mapping/canary/resource/source
evidence refs. The runner cannot issue this identity or self-sign a PASS.
It also reads actual memory.max/v1 limit and rejects unlimited/wrong8GiB.
MAIN must record actual PID→physical-card proof while each owned job executes.

One foreground command each (arguments also exactly in PACKET.json):
ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1
/usr/local/python3.12.13/bin/python3
/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_gate_v1/run.py
--batch 1 --physical-device 5
--identity /kvbuffer-results/split-p1-b1-phys5-v1.identity.json
--output-dir /kvbuffer-results/split-p1-b1-phys5-v1

Second command is --batch 16 --physical-device 6 with
/kvbuffer-results/split-p1-b16-phys6-v1.identity.json and
/kvbuffer-results/split-p1-b16-phys6-v1. CLI arguments use normal spaces:
--batch 1, --physical-device 5 (see PACKET.json exact argv).
Both use existing /kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so.
No automatic retry. Each owned container stop-and-retain belongs in MAIN's
finally; never broad kill/remove. Keep per-job outer stdout/stderr log/receipt.

## Failure evidence and exclusions

The frozen oracle saves each synchronized before/after/native/full inputs/
raw outputs/guards/pointers before numerical analysis; failed raw steps remain.
Only the present passed step's individually hash-checked temporary raw may be
removed by the frozen oracle. Existing results are never removed.
Dispatch/poisoned-context failures before a raw snapshot can complete remain
failures with unavailable tensor evidence; keep full original traceback/log,
never invent tensor availability or treat this harness failure as paper no-go.
The split report marks only its one batch; joining two independent PASS reports
requires MAIN's source/identity review. No new pass is asserted by this packet.

48-layer model lifecycle, mixed prefill/scheduler paths, allocator budget,
formal matched E2E, task accuracy and cross-environment portability remain
separate. Graph kernel PASS would not prove model graph integration.
Software fixtures below are CPU protocol tests only:
python3 -B -m unittest discover -s projects/kvbuffer-parallel-ascend/tools/split_gate_v1 -p test_contract.py -v
