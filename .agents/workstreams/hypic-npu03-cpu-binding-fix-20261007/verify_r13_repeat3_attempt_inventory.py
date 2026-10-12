"""Read-only validation of the retained r13 final-phase attempt inventory."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-hotpath-cache10perf-hypic-only-repeat3"

def audit(ledger):
    entries = ledger["entries"]
    assert ledger["root_prefix"] == PREFIX
    assert [e["attempt"] for e in entries] == list(range(22))
    expected_roots = {PREFIX + ("" if i == 0 else "-retry" + str(i)) for i in range(22)}
    assert {str(p) for p in Path(PREFIX).parent.glob(Path(PREFIX).name + "*") if p.is_dir()} == expected_roots
    for e in entries:
        i = e["attempt"]
        root = Path(PREFIX + ("" if i == 0 else "-retry" + str(i)))
        assert e["root"] == str(root)
        assert e["included_in_frozen_six_phase_result"] == (i == 21)
        expected_names = {"contract.json", "arm-result.json", "performance.json",
                          "hypic-only/lane-guard.json", "hypic-only/pre-health-release.json",
                          "hypic-only/service-stop.json"}
        assert set(e["receipts"]) == expected_names
        raw = {}
        for rel, digest in e["receipts"].items():
            p = root / rel
            if digest is None:
                assert not p.exists(), (i, rel, "formerly missing receipt appeared")
                raw[rel] = None
            else:
                b = p.read_bytes()
                assert hashlib.sha256(b).hexdigest() == digest, (i, rel)
                raw[rel] = json.loads(b)
        result = raw["arm-result.json"]
        assert e["result_valid"] == (result.get("valid") if result else None)
        assert e["recorded_error"] == (result.get("error") if result else None)
        assert e["recorded_result_time"] == (result.get("at_utc") if result else None)
        perf = raw["performance.json"]
        rows = perf["results"] if perf else None
        assert e["benchmark_rows"] == (len(rows) if rows is not None else None)
        assert e["ok_rows"] == (sum(r.get("ok") is True for r in rows) if rows is not None else None)
        assert e["fixed_1024_ok_rows"] == (sum(r.get("ok") is True and r.get("output_tokens") == 1024 for r in rows) if rows is not None else None)
        guard = raw["hypic-only/lane-guard.json"]
        assert e["guard_samples"] == (guard.get("samples") if guard else None)
        assert e["probe_errors"] == (guard.get("probe_errors") if guard else None)
        obs = guard.get("foreign") if guard else None
        assert e["foreign_observations_count"] == (len(obs) if obs is not None else None)
        processes = None if obs is None else list({
            (p.get("physical_npu"), p.get("pid"), p.get("container_id")): p
            for o in obs for p in o.get("processes", [])}.values())
        assert e["foreign_processes"] == processes
        release = {}
        for rel in ["hypic-only/pre-health-release.json", "hypic-only/service-stop.json"]:
            if raw[rel] is not None:
                release[rel] = {k: raw[rel].get(k) for k in [
                    "container_removed", "worker_release_proven", "owned_npus_released",
                    "port_released", "at_utc"]}
        assert e["release_facts"] == release
    assert sum(e["result_valid"] is False for e in entries) == 19
    assert [e["attempt"] for e in entries if e["result_valid"] is None] == [5, 6]
    assert [e["attempt"] for e in entries if e["result_valid"] is True] == [21]
    assert (entries[4]["benchmark_rows"], entries[4]["ok_rows"], entries[4]["fixed_1024_ok_rows"]) == (40, 16, 15)
    assert (entries[21]["benchmark_rows"], entries[21]["ok_rows"], entries[21]["fixed_1024_ok_rows"]) == (40, 40, 40)
    return {"roots": 22, "excluded": 21, "admitted": 1,
            "invalid_terminal_receipts": 19, "missing_terminal_receipts": 2,
            "scope": "inventory only; no new scientific verdict or device work"}

if __name__ == "__main__":
    print(json.dumps(audit(json.loads((HERE / "HYPIC_R13_REPEAT3_ATTEMPTS_20261012.json").read_text())), sort_keys=True))
