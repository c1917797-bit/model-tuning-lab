"""HOST-only compiler-order audit composed with the unchanged R27 canary audit.

The official compile monitor is info_once(local), so only TP0 completion is
required. Each worker's DEBUG compile start is checked against its own first
capture. No cross-rank completion barrier or per-token graph claim is invented.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
from host_audits import r27_graph_canary_audit as predecessor

ENTRY = "host_audits/r29_graph_compile_order.py"
PARENT = "host_audits/r27_graph_canary_audit.py"
_PREFIX = predecessor._PREFIX
_TIME = predecessor._TIME
_FINISH = re.compile(_PREFIX + r"INFO " + _TIME +
    r" \[compilation/monitor\.py:53\] torch\.compile took [0-9]+\.[0-9]+ s in total")


def parse_compile_order(log_bytes, workers, *, code_name="installed",
                        code_file="/probe/graph_candidate/entry_router.py"):
    if type(log_bytes) is not bytes or type(workers) is not dict:
        raise ValueError("original service bytes and independently joined workers required")
    owned = {int(r): p for r, p in workers.items()}
    if set(owned) != set(range(4)) or any(type(p) is not int or p <= 0 for p in owned.values()):
        raise ValueError("four real owned rank/PID mappings required")
    start = re.compile(_PREFIX + r"DEBUG " + _TIME +
        r" \[compilation/decorators\.py:593\] Start compiling function <code object " +
        re.escape(code_name) + r' at 0x[0-9a-fA-F]+, file "' + re.escape(code_file) +
        r'", line [1-9][0-9]*>')
    starts, captures, finishes = {}, {}, {}
    for number, raw in enumerate(log_bytes.decode("utf-8").splitlines(), 1):
        line = predecessor._ANSI.sub("", raw)
        for pattern, rows in ((start, starts), (predecessor._CAPTURE, captures), (_FINISH, finishes)):
            match = pattern.fullmatch(line)
            if match is None:
                continue
            rank, pid = int(match[1]), int(match[2])
            if owned.get(rank) != pid:
                raise ValueError("compile/capture line PID differs from independent physical owner")
            rows.setdefault(rank, []).append(number)
    if set(starts) != set(range(4)) or set(captures) != set(range(4)) or 0 not in finishes:
        raise ValueError("source-owned first compilation/capture or local-first completion missing")
    for rank in range(4):
        if min(starts[rank]) >= min(captures[rank]):
            raise ValueError("first native compilation occurred within/after first capture")
    if not min(starts[0]) < min(finishes[0]) < min(captures[0]):
        raise ValueError("local-first successful compilation did not finish before own first capture")
    return {
        "first_compile_before_own_capture_ranks": list(range(4)),
        "successful_compile_completion_directly_observed_rank": 0,
        "per_rank": {r: {"first_compile_line": min(starts[r]),
                         "first_capture_line": min(captures[r]),
                         "compile_complete_lines": finishes.get(r, [])} for r in owned},
        "service_log_sha256": hashlib.sha256(log_bytes).hexdigest(),
        "scope": "per-worker first compile starts before own capture; official local-first TP0 successful compile completion precedes own capture; not four direct completion logs or per-token graph coverage",
    }


def audit(contract_path, *, live_release=False):
    path = Path(contract_path).resolve()
    contract = predecessor._read(path)
    binding = contract.get("compile_order_audit", {}).get("source_sha256")
    predecessor._sources(path.parent, binding)
    if (binding.get(ENTRY) != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            or binding.get(PARENT) != hashlib.sha256(Path(predecessor.__file__).read_bytes()).hexdigest()):
        raise ValueError("actual independent predecessor/order auditor identities differ")
    if contract.get("graph_canary_group") != "G3":
        raise ValueError("source-owned warmup treatment audit is G3 only")
    report = predecessor.audit(path, live_release=live_release)
    manifest_path = path.parent / contract["cache_diagnostic"]["compact_manifest"]
    manifest = predecessor._read(manifest_path)
    if "graph_candidate/native_warmup.py" not in manifest["source_sha256"]:
        raise ValueError("actual warmup runtime helper must be bound")
    raw = Path(contract["raw_root"])
    report["compile_order"] = parse_compile_order(
        predecessor._read(raw / "service.log", json_value=False),
        report["hot"]["worker_pids"])
    report["warmup_repair_bounded_valid"] = True
    report["scope"] += "; first compiler ordering independently verified, not speed or fullquality"
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--live-release", action="store_true")
    args = parser.parse_args()
    print(json.dumps(audit(args.contract, live_release=args.live_release)))
