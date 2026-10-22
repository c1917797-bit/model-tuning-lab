# Exact supported inner entry for a future reviewed v4 launcher

These are **argv templates**, not approval to execute this unfrozen draft. MAIN must use the actual final frozen `launcher_ref.path`, serialized immutable config Ref and serialized genuine MAIN resource-review Ref. Do not put authentication/verification values in any argument or file.

For a non-dispatch check, the exact argument sequence is:

```text
/usr/bin/env
DENSE090_EXTERNAL_OUTPUT_ENABLE=1
/usr/bin/python3
-I
-B
<launcher_ref.path>
--check-only
--config-ref
<one complete JSON Ref argument for the immutable config>
--review-ref
<one complete JSON Ref argument for the genuine MAIN resource review>
```

For an actual reviewed dispatch, the exact argument sequence is:

```text
/usr/bin/env
DENSE090_EXTERNAL_OUTPUT_ENABLE=1
BOLE_CONTINUATION_MAIN_ENABLE=1
/usr/bin/python3
-I
-B
<launcher_ref.path>
--execute
--config-ref
<one complete JSON Ref argument for the immutable config>
--review-ref
<one complete JSON Ref argument for the genuine MAIN resource review>
```

Pass each displayed line as one argv item through a structured process/unit interface. The Ref arguments are whole JSON objects serialized into a single argument, without shell interpolation. The `DENSE090_EXTERNAL_OUTPUT_ENABLE=1` value is required in both modes because current source loading precedes any later `COMMANDS.model` exec. The second opt-in is required only for actual dispatch. The source's model argv is separately validated and executed in full, including all six of its source-defined opt-in assignments; the launcher does not rebuild it from these templates.

## Host process and systemd preconditions

- Use a new bounded one-shot unit and a fresh host Python process. MAIN must read the actual old unit's terminal configuration before choosing outer unit parameters. This document does not invent a new unit name, timeout, cgroup resource budget or cleanup policy.
- Pin the host to CPU166, as in the original owner. The launcher independently sets and verifies that affinity, then retains the original CPU quota/ancestor/cpuset admission.
- `RLIMIT_CPU` **soft and hard must already both be unlimited**, and `RLIMIT_FSIZE` **soft and hard must already both be unlimited**. The launcher refuses a short-auditor inheritance. It never raises a finite limit.
- `RLIMIT_AS` hard must already be unlimited. The launcher sets soft to exactly512MiB and verifies soft512MiB/hard unlimited before checks and again before exec. This preserves the existing Docker/Go wrapper; guest limits remain owned by the source controller and its cgroups.
- Preserve the original host budget, full phase3600, shared cleanup180 and complete preparation admission3780. An outer unit or process timeout must not replace or prematurely cut off those original budgets. The separately authorized absolute cutoff remains18:00:55UTC; the old12:38:41 report deadline was not extended.
- Use the existing shared MAIN lock. The launcher acquires it before final current checks, checks its actual inode/device again, verifies the FD is inheritable, cancels its predispatch-only alarm and execs the exact source command. The same host PID/FD owns the lock after exec; the original source controls every subsequent create and cleanup.
- Obtain a new successful complete snapshot only after the final source/helper bindings and review preparation are ready. It must be no more than180 seconds old both when consumed and at final dispatch. No historical or failed snapshot grants resources.

The saved source/audit PASS_SOURCE_ONLY, this entry contract and the local control results do not by themselves admit a resource owner. Current real six-chain verification, live resource checks, immutable final config and genuine MAIN review remain necessary.
