# Outer unit allowance for the reviewed continuation launcher

This is a local reconciliation of the actual old-unit settings reported by MAIN on 2026-10-22. This agent did not query systemd or create a unit. The full host receipt remains MAIN's evidence; these reported values are not a new live resource admission.

MAIN reported the terminal original unit as `Type=exec`, `RemainAfterExit=yes`, `RuntimeMaxUSec=1h5min` (3900 seconds), `TimeoutStopUSec=3min` (180 seconds), `MemoryMax=536870912`, `CPUAffinity=166`, unlimited `LimitCPU`, `LimitFSIZE` and `LimitAS`, `KillMode=control-group`, and append stdout/stderr. The unit had `MainPID=0`, `ControlPID=0`, `ActiveState=active`, `SubState=exited`. These observations must remain linked to MAIN's actual receipt and must not be treated as a fresh observation at a later launch.

The proposed new outer `RuntimeMaxSec=4080` is the original 3900-second outer allowance plus the new launcher's bounded 180-second predispatch check. It does not alter the original source's phase3600, shared cleanup180, source cutoff, controller cleanup ownership or guest resource budgets. `TimeoutStopSec=180` remains the original value. The source controller reserves cleanup within its phase; the launcher cancels only its own predispatch alarm immediately before executing the complete validated source command.

The old external `flock --nonblock --no-fork` must not be added around v4. V4 itself opens the existing shared MAIN lock, takes a nonblocking exclusive lock, validates its inode/device, marks the FD inheritable and keeps it through the exact owner exec. A second independently opened outer flock would contend with the inner lock rather than add useful protection.

Retain the actual old unit's host memory, CPU affinity, kill mode, resource-limit inheritance and stdout/stderr semantics. In particular, do not inherit short source-auditor CPU or file-size caps. The launcher requires both CPU/FSIZE soft and hard limits to be unlimited; it sets host AS soft512MiB with hard unlimited. The Docker/Go wrapper and source-owned guest cgroups remain unchanged.

MAIN must also ensure the selected actual launch time and outer stop allowance fit the separate 18:00:55 UTC continuation cutoff. A conservative unit-level check is `launch_epoch + 4080 + 180 < 1792692055`; the launcher and original source retain their own tighter phase/cutoff checks. This outer check must not be used to extend the authorization. The old report cutoff of 12:38:41 UTC remains unchanged.

No contradiction was found between this proposed outer allowance and the existing v4 source contract. This conclusion is limited to the above arithmetic and inheritance review. No new unit, owner, NPU workload, paired gate or performance result was created by this agent.
