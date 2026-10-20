"""Record a bounded failure diagnostic, then propagate the original guard.

The original observer, 16384-FD limit and every admission decision stay intact.
This module does not inspect FD targets, send signals or run Docker commands.
"""
import os
from pathlib import Path
import time

LIMIT = 16384


def capture(C, ctl, label, out):
    start = time.monotonic()
    deadline = start + 2.0
    pids = []
    process_inventory_capped = False
    with os.scandir('/proc') as entries:
        for entry in entries:
            if entry.name.isdigit():
                pids.append(int(entry.name))
                if len(pids) == 65536:
                    process_inventory_capped = True
                    break
    rows = []
    inspected = 0
    races = 0
    scan_complete = not process_inventory_capped
    # Recent processes include newly spawned workers; this is diagnostic only.
    for pid in sorted(pids, reverse=True):
        if time.monotonic() >= deadline or len(rows) >= 64:
            scan_complete = False
            break
        p = Path('/proc') / str(pid)
        try:
            count = 0
            with os.scandir(p / 'fd') as entries:
                for _ in entries:
                    count += 1
                    if count > LIMIT:
                        break
            inspected += 1
            if count > LIMIT:
                cgroup = (p / 'cgroup').read_text()
                status = (p / 'status').read_text().splitlines()
                rows.append(dict(
                    pid=pid, at_least_fds=count,
                    comm=(p / 'comm').read_text().strip(),
                    cgroup=cgroup,
                    NSpid=[s for s in status if s.startswith('NSpid:')],
                    belongs_to_current_owned_CID=bool(ctl.cid and ctl.cid in cgroup)))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            races += 1
    payload = dict(
        schema='bole.original-FD-limit-failure-diagnostic/v1',
        source=C.ref(__file__), label=label, owned_CID=ctl.cid,
        original_per_process_FD_limit=LIMIT,
        original_guard_rejection_propagated=True,
        original_safety_function_replaced=False,
        maximum_process_inventory=65536, maximum_overflow_rows=64,
        maximum_per_process_entries=LIMIT + 1,
        target_scan_budget_seconds=2.0,
        processes_inspected=inspected, process_races=races,
        process_inventory_capped=process_inventory_capped,
        diagnostic_scan_complete=scan_complete,
        oversized_processes=rows, elapsed=time.monotonic() - start,
        NPU_holder_coverage_or_admission_proof=False,
        NPU=False, formal_success=False)
    return C.write(Path(out) / ('FD-OVERFLOW-DIAGNOSTIC-%d.json' % time.time_ns()), payload)


def observe(C, ctl, label, summary, out):
    try:
        return ctl.observe(label)
    except ValueError as error:
        if str(error) == 'bounded actual FD inventory':
            try:
                summary.setdefault('FD_inventory_failure_diagnostics', []).append(
                    capture(C, ctl, label, out))
            except Exception as diagnostic_error:
                summary.setdefault('FD_inventory_diagnostic_errors', []).append(
                    repr(diagnostic_error)[:2000])
        raise
