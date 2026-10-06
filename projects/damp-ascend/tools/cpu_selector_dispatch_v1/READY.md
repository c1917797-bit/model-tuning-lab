# Source-bound CPU dispatch preparation; NOT execution admission

MAIN source review added this pure-stdlib packet while real TP4 reference capture
was active. It never calls Docker, creates a directory, imports Torch, runs fitting,
touches NPU, signs SOURCE_LOCK, or changes the frozen selector.

Run default plan.py and test_plan.py with /usr/bin/python3 -B. Default selector
argv is null until both actual successful parent RESULT and SOURCE_LOCK byte
hashes are supplied. Even then launchable remains false: MAIN must separately
inspect the exact new container, no-device/image/mount identity, actual canary
receipt, fresh ordinary RAM/disk/cgroup and source bindings. Docker create/start
arrays are templates, not receipts.

The canary has a distinct retained container name. It imports actual image Torch
on CPU and runs only the source-bound parent's default read-only CLI. Do not
restart this exited canary as a fitting worker. After successful parent finalize,
MAIN creates the distinct selector container with the actual two hashes and
explicit DAMP_POST_REFERENCE_CPU_EXECUTE=1. No fitting is allowed from partial
capture or smoke, no source-lock issuance here, and no automatic retry.

Ordinary RAM admission is >=12GiB: 4GiB capped no-swap selector plus 8GiB host
reserve, monitored during execution by MAIN. Eight CPU threads. Fresh all-result
children are nested read-only so the only intended writable output is a new
direct child calibration-plans-v1; never overwrite existing evidence. Reject
symlink/nonordinary/overlarge mount lists and inspect actual mount flags before
starting. The parent validates source pins and full native OFF/ON parity before
fitting. Its eight-hour timeout is a bound, NOT a predicted duration or license
to consume the remaining DAMP validation/E2E/quality window.

Use first three actual plan completion times and real cgroup memory current/peak
for a measured stage estimate. Stop only the exact owned worker if remaining time
cannot cover final numerical/shared-cache/prefill/service, paired fixed1024
performance and normal-EOS2048 task checks. Retain all partial/failed outputs,
which are neither plans admitted for service nor a paper-level no-go verdict.

Actual final192 plans, native NPU/graph, default-OFF monkeypatch service dispatch,
same dense budget, E2E throughput/TTFT/TPOT and task quality are not proven by this
preparation or CPU fitting.

Before any real Docker create MAIN checks fresh mount headroom, image/name and
all HostConfig.Devices/DeviceRequests/privileged fields, not only two device-node
assertions. The installed image Torch source was read: it supports
TORCH_DEVICE_BACKEND_AUTOLOAD=0. CPU fitting/canary use that explicit switch to
avoid importing torch_npu; this does not alter any NPU model/candidate environment.
The canary also independently checks all five actual POST source hashes plus
their frozen dependencies before running the default CLI.

Read-only bind mounts do not freeze host-side source. MAIN rechecks actual POST
five-file hashes/module origins before/after each run. Re-list result children
after reference finalize; the early list is not future filesystem isolation.
RESULTS root remains RW plus nested existing children RO, not an assertion that
only plans are filesystem-writable. If CPU fitting overlaps four allT shards,
fresh joint ordinary RAM admission is at least44GiB=32+4+8, not two independent
40/12GiB gates.

Actual preflight v1 MA04e8 failed at Docker create, before any container or
NPU execution: Docker reported only7 available CPUs and rejected quota8.
The unchanged failure is retained at cpu-selector-preflight-v1/RESULT.json
SHA034dc921b976f4902c86c1227cb9ebde18da02ed4a0c45368401b7298e6af342.
This source-supported correction uses quota2 (not8) and a NEW canary name v2;
the frozen fitting algorithm still uses8 Torch threads, which is not a claim
of8 available CPUs. MAIN observes actual Docker NCPU and budgets concurrent
CPU quotas; formal model performance remains exclusive of fitting/gates.
