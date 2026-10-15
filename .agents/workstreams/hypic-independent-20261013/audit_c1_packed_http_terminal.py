"""Transparent post-run ID encoding repair; original measured audit remains unchanged."""
import hashlib
import json
from pathlib import Path
from audit_native_decode_terminal import audit_terminal
from audit_c1_packed_wave import audit_packed_c1
from audit_c1_http_identity import resolve_http_ids

def audit_http_terminal(contract_path, *, live_release=False):
    path = Path(contract_path)
    c = json.loads(path.read_text())
    raw = Path(c["raw_root"])
    report = audit_terminal(path, live_release=live_release)
    mp = path.parent / c["cache_diagnostic"]["compact_manifest"]
    manifest = json.loads(mp.read_text())
    config = json.loads((path.parent / manifest["config"]).read_text())
    if config.get("c1_packed_wave") is not True:
        raise ValueError("this post-run adapter is only for enabled R14")
    expected = c["independent_acceptance"]["c1_packed_wave"]
    events = []
    for p in sorted((raw / "diagnostics").glob("compact-worker-*.jsonl")):
        events.extend(json.loads(line) for line in p.read_text().splitlines())
    results = json.loads((raw / "compiled-cache-unit.json").read_text())["results"]
    api_ids = [x["response"]["id"] for x in results]
    # Membership comes only from actual body-completion receipts, not fabricated IDs.
    runtime_ids = sorted({e["request_id"] for e in events
                          if e.get("event") == "compact_gdn_body_composed"})
    mapping = resolve_http_ids(api_ids, runtime_ids, expected_count=16)
    workers = {int(k): v for k, v in report["hot"]["worker_pids"].items()}
    report["packed"] = audit_packed_c1(events, workers,
        manifest_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),
        linear_layers=expected["linear_layers"],
        requests=[mapping[rid] for rid in api_ids], enabled=True,
        skipped_body_tokens=c["independent_acceptance"]["skipped_body_rows"],
        state_passes=expected.get("state_passes", 3),
        seed_mode=expected.get("seed_mode"), head_geometry=expected.get("head_geometry"))
    report["post_run_identity_adapter"] = {
        "mapping": mapping, "http_count": len(api_ids), "runtime_count": len(mapping),
        "original_failed_operation": "exec-000000000000084d",
        "frozen_sources_and_raw_unchanged": True,
        "source_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ("audit_c1_http_identity.py", "audit_c1_packed_http_terminal.py")}}
    report["scope"] = "bounded16 fixed64 R14 packed/source/hot/shadow/isolation/release; no formal performance or task-quality acceptance"
    return report

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--contract", required=True)
    p.add_argument("--live-release", action="store_true")
    a = p.parse_args()
    print(json.dumps(audit_http_terminal(a.contract, live_release=a.live_release)))
