# all-T single-card dispatch preparation v1

This is a pure-stdlib argv generator, not a controller and not NPU admission.
It never executes Docker, Torch, Git, canaries or gates and never creates outputs.
MAIN alone owns resource checks, launches and retained first failures.
The live TP4 collection operation is exec-0000000000000455; do not overlap it.

## Actual dependencies, not placeholders

The generator rechecks the frozen all_batch_gate_v1 contract (9 compiled /20
runtime sources), actual v3 SO/build receipt and exact full-runner Meta report
(32 positive /46 negative NO-device calls). Exact SHA constants live in plan.py.
It also reuses the actual graph native-source-manifest.json (SHA6eb9c6d5...)
and source-verified v0.23 reference header. The actual image SO/GDN/load paths
must still pass native_bindings and loaded-library checks during the real gate.
A missing/drifted native identity yields waiting_native_identity; it is not
silently fabricated or replaced.

Physical4/5/6/7 each map to logical0, with actualT1-4/5-8/9-12/13-16 respectively.
Each new nonprivileged container has one compute node and only the necessary
davinci_manager/devmm_svm/hisi_hdc control nodes. Repo, build, native reference,
manifest and driver are RO bind mounts; only its new per-card result/control
directory is RW. Container rootfs is not asserted read-only: CANN cache behavior
has not been validated for that additional change. No host network/privileged/
auto-remove/background controller is emitted.

Each shard has an8GiB memory and memory-swap cap; four simultaneous shards
require fresh MAIN ordinary MemAvailable >=40GiB (32GiB caps +8GiB reserve).
This is a conservative admission policy, not a measured RSS bound.
Each numerical shard has1 CPU quota, four together4; optional CPU selector
quota2 makes joint6. MAIN must supply fresh actual Docker info JSON with NCPU>=6,
not os.cpu_count or a stale7-CPU assumption. This is quota feasibility, not proof
of free CPU capacity: inspect competing work. Formal performance never overlaps
these numerical shards or CPU fitting. The CPU selector stays independently
capped4GiB; if it overlaps, MAIN aggregate RAM policy is32+4+8=44GiB, not the
four-shard-only40GiB. Torch selector threads8 are not changed by quota2.
Fresh free disk >=8GiB is also an admission policy. Do not reclaim HugeTLB or
protected0-3 to satisfy it.

## Source-only commands

From /opt/host/vnf/austinov/model-tuning-lab:

    /usr/bin/python3 -B projects/damp-ascend/tools/allT_dispatch_plan_v1/test_plan_contract.py
    /usr/bin/python3 -B projects/damp-ascend/tools/allT_dispatch_plan_v1/plan.py --run-id v1

JSON is printed to stdout only. Initially status is waiting_MAIN_live_admission;
docker_create_argv, docker_start_argv and docker_canary_exec_argv contain real
source paths/hashes. gate_argv_source_bound_incomplete lacks only the actual
device-proof path/hash. Executable gate_argv remains null: no pass is generated.

The expected new external root is
/cache/cch/qwen36-damp-20261006/allT-dispatch-v1.
It must not exist for initial planning. MAIN creates only new root/physical4..7
control directories after admission; each nested gate directory stays absent.
Use a different safe --run-id for a genuinely new evidence-supported experiment,
not to repeat an unchanged failure.

## MAIN launch sequence

1. Observe collection terminal/released, fresh process/HBM/device-node holders,
   physical scope, protected0-3, aggregate RAM/disk, image/source identities and
   absent planned names in actual docker ps -a. Do not equate device declarations
   with usage. Only after these checks create the new per-card control directories
   and execute emitted create/start argv, without changing their contents.
2. Execute each emitted tiny canary. Save its actual JSON as physicalN/canary.json,
   retain actual stdout/stderr/exception, and independently save actual
   physicalN/device-proof.json from inspect/process/card observations.
   The canary checks real logical0 arithmetic/SoC; its expected_physical_card
   argument is not physical-device measurement. Actual mapping is MAIN authority.
3. Record an actual admission JSON with schema
   damp_allT_MAIN_live_admission_v1. It requires:
   observed_at_unix_ns; capture_operation_id; capture_terminal;
   owned_TP4_lease_released; physical_npu_ids=[4,5,6,7];
   exclusive_resource_check_passed; protected_NPU0_3_unchanged;
   ordinary_mem_available_bytes; per_card_cgroup_limit_bytes; free_disk_bytes;
   docker_cpu_capacity with observed_at_unix_ns, actual info_path/info_sha256
   (raw Docker info JSON NCPU), per_numeric_shard_cpu_quota=1,
   numeric_shards_cpu_quota=4, optional_selector_cpu_quota=2, joint_cpu_quota=6,
   formal_performance_exclusive=true; cards keyed4,5,6,7. Each card requires actual container_name/64hex container_id/
   container_image_id/create_argv_sha256/fresh_created_from_this_plan/
   inspect_single_card_scope_passed/device_proof/device_proof_sha256/canary/
   canary_sha256. Exact paths/argv SHA are printed by the initial plan.
   Central resource observation and actual canaries must be <=5min old.
   Device proof also satisfies the unchanged gate's mapping/freshness contract.
   Never save the tests' in-memory simulated admissions as actual evidence.
4. Regenerate with --admission-file /absolute/actual-admission.json.
   Status complete_gate_argv_for_MAIN_final_recheck_only means source/hashes and
   those supplied real records were checked; it does not independently observe
   host truth. Fresh final recheck precedes MAIN execution of only the four
   docker_gate_exec_argv commands. If preparation takes longer, obtain fresh
   actual records rather than extending freshness or numerical thresholds.

The gate itself creates its new output and retains first raw-before, nullable
after/copy errors and full failure. No unchanged retry, overwrite, automatic
cleanup or container deletion. Observe terminal exit and stop only identified
owned idle containers while preserving their files/logs.

Scope remains synthetic restricted SR1/power2 all-T shared-arena/eager/graph
correctness. Final192 general-SR plans, prefill import, service/lifecycle,
paired throughput/TTFT/TPOT and GSM8K/LongBench-v2 are separate obligations.
Deadline remains2026-10-07T08:48:03Z. These software checks do not claim any new
NPU, graph, service, performance or task result.

## Evidence-supported CPU quota correction

MAIN actual CPU-canary create MA04e8 was refused before creating any container:
"Range of CPUs is from 0.01 to 7.00, as there are only 7 CPUs available".
Its original v1 failure is retained by MAIN. No all-T NPU shard was launched.
This preparation now uses one quota CPU per numerical shard, plus an optional
two-quota CPU selector, and requires fresh capability/aggregate budget evidence.
It does not reinterpret a failed Docker create as an NPU/algorithm failure, reset
the deadline, change frozen selector thread count, or relax numerical/RAM gates.
