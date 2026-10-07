# Authorized free HugeTLB release — 2026-10-07

## Outcome and authority

The human explicitly authorized a completed hugepage safety audit followed by at
most 32 GiB of free hugepage release, preserving OVS and its required capacity.
One runtime operation released exactly 32 free 1 GiB pages from NUMA0 at
2026-10-07T16:04:21–16:04:28Z. No further release is authorized by this spent
32 GiB allowance. No service was stopped, no mount/file was deleted, and no
permanent boot/sysctl/OVS configuration was modified.

Ordinary MemAvailable was 58.04511260986328 GiB immediately before and
90.04466247558594 GiB after. Independent live readback at 16:05:55Z saw
89.65732192993164 GiB (other workloads can change available RAM). This removes
the previously measured ordinary-memory shortfall against the unchanged
72.25 GiB full-model admission floor; it is not a resource lease or permission
to skip fresh admission. It is not paper, NPU numerical, performance or task
accuracy evidence.

| NUMA | Before nr/free (1 GiB pages) | After nr/free |
|---|---|---|
| 0 | 471 / 471 | 439 / 439 |
| 1 | 485 / 485 | 485 / 485 |
| 2 | 486 / 486 | 486 / 486 |
| 3 | 474 / 450 | 474 / 450 |

Global nr/free: 1916/1892 -> 1884/1860. Global reservations and all surplus
counts were zero. Only observed hugepage consumer was ovs-vswitchd PID27118,
with 24 GiB entirely on NUMA3. The entire NUMA3 474 GiB pool, including 450 GiB
free, remained unchanged. DPDK reported one 24 GiB heap on NUMA3, with about
13.6 GiB free within its heap at the initial audit. All three OVS interfaces
were admin/link up with empty error fields, and the management gateway ping
passed before and after. OVS PID/start_ticks/cgroup/argv, ovsdb identity,
DPDK heap capacity and permanent configuration hashes remained unchanged.

Independent post-readback npu-smi showed the same physical NPU0–3 worker PIDs
3176115–3176118 and no physical NPU4–7 processes. This is snapshot evidence,
not a future lease or a claim to have run the next paper numerical experiment.

## Evidence and narrow implementation

Remote repository:
`/opt/host/vnf/austinov/model-tuning-lab`, branch
`work/qwen36-damp-ascend-20261006`, pre-change HEAD
`c9b8d98d5cf8f476c61e7a4b58af340a2ca36a07`.

One-shot implementation at execution:
`.agents/workstreams/qwen36-damp-ascend-20261006/hugepage_release32_20261007.py`,
SHA256 `e274b196e7ec6150864728d59c9650e1ffc600aeb7e7546834922bf1a9139d6e`.
It is default OFF, refuses an existing result directory and unexpected
NUMA0 count, and only writes the exact NUMA0 1 GiB nr_hugepages attribute.
The byte-exact executed source was preserved as `source-executed-v1.py` in the
raw result directory below, independently verified against that SHA256.
The repository copy was subsequently normalized by removing one surplus EOF
blank line after staged diff-check caught it; no executable line was changed.
This formatting-only successor is not the byte-exact execution authority.
The source is an experiment artifact, not an approved general-purpose
hugepage maintenance skill. Do not rerun or rewrite the frozen executed v1.

Actual AWMCP target was chicaihong01/ma:
`lgw_a6109c51076a4a2c9d2674ca5a8704a0`, force_direct/tpc,
with actual peer_direct and matching target identity. No session value is
stored in source or this record.

Actual operations, each exit0:
- `exec-0000000000000d64`: consumer/all-NUMA/reservation/service audit.
- `exec-0000000000000d76`: actual startup units, OVS argv/config, boot pool,
  control-command inventory and hugetlbfs file ownership.
- `exec-0000000000000d79`: DPDK heap/mempool and gateway check. One optional
  virtio status query returned port-type error because fst-ovs is virtio_user;
  that failure was retained, not used as a successful health check.
- `exec-0000000000000d86`: ten software safety/negative cases only.
- `exec-0000000000000d8c`: the complete actual live safety gate, read-only.
- `exec-0000000000000d8d`: the single authorized runtime release, 6329 ms.
- `exec-0000000000000d8f`: independent full-node artifact consumer plus fresh
  OVS/DPDK/network/SMI readback, 2547 ms, read-only.

New-only raw result directory:
`/cache/cch/qwen36-paper-preparation-20261007/hugepage32-release-20261007-1605-v1`.

SHA256:
- before.json: `bc38600c4d3327c4b9f4b554bae104c62d364319c4cffb20527869cdb2be1a9e`
- prewrite.json: `a192ae2471d21354fcbd16b596a7be7d0661daf1a5ef6d0856ee4399ea2c3b51`
- after.json: `0e2b59e7203d068f97ce2d8ad700999ed290cd406d7c8901a53c716a0bf66819`
- RESULT.json: `069cae7b82a614fd377dea7498c084286db1bd80425cb32efb3e9d98382bac58`

Independent consumer explicitly compared complete nr/free/surplus dictionaries
for NUMA1/2/3 across before/prewrite/after and fresh live state. NUMA0 and global
nr/free decreased exactly 32; Hugetlb decreased exactly 33554432 KiB. It checked
identical hugepage consumers/config hashes, preserved DPDK heap, zero reservations
and successful gateway checks. The final consumer was a new operation rather
than merely trusting the release tool's PASS flag.

## Review limitations and reusable lessons

A parallel source reviewer delivered two valid strengthening requests while
the already-dispatched six-second operation was completing. Preserve this
ordering; do not claim that its recommendations preceded execution.

1. v1 gathers pool counts at the start of each full snapshot, then performs
   health probes, and immediately before the write rechecks only nr_hugepages.
   A future successor must collect and save a narrow final nr/free/resv/surplus
   check immediately before the write and abort any drift. Userspace cannot
   atomically exclude every new reservation; a current allocation/maintenance
   exclusivity check is also needed. This run's snapshots and independent
   readback demonstrate observed success, not absence of all transient races.
2. v1's main guard did not fix NUMA1/2 free counts or consume a complete
   non-target-node equality assertion. The independent consumer subsequently
   checked the actual full dictionaries and found no changes. A successor
   must enforce this inside the execution gate and add negative tests.
3. A skipped rollback due to unexpected current count must say skipped,
   not attempted. v1 did not need or attempt rollback in this successful run.
4. Never infer ordinary free RAM from free HugeTLB pages or cache/RSS totals.
   Page-cache can already contribute to MemAvailable; deleting stopped
   containers frees disk, not process RAM.
5. Preserve the active OVS heap AND its NUMA-local spare pool. Do not stop OVS,
   delete hugetlbfs backing files, or release an anonymous global pool.
6. Kernel HugeTLB regrowth depends on contiguous memory; a restore attempt is
   not guaranteed. v1's failure recovery was one conditionally exact restore
   to 471 on NUMA0, with actual readback. No recovery was executed.
7. Record operational observer failures separately from paper failures:
   the earlier H8 canary aborted on a protected0–3 identity comparison before
   a numerical report, and its owned container was stopped/retained. Releasing
   RAM does not convert that attempt into a numerical PASS or justify an
   unchanged retry.

Primary semantics reference:
[Linux HugeTLB documentation](https://docs.kernel.org/admin-guide/mm/hugetlbpage.html).
The project maintenance Runbook §9 requires consumer, OVS/DPDK dependency,
free-page, health, per-NUMA and rollback evidence before release.

Next: resolve the H8 protected-identity observation with retained raw evidence,
and fresh-admit a real NPU numerical candidate on physical4–7. Keep paper
cutoffs and all numerical/model/performance/task gates unchanged. No new
non-HYPIC jointly accepted method or performance/accuracy result is claimed.
Normal Git push remains subject to the already documented credential-helper
blocker; do not retry an unchanged credential failure or claim a remote update.
