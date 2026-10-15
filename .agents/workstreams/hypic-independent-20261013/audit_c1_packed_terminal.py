"""Packed-C1 terminal audit joins base transport/physical/release and new receipts."""
import hashlib,json
from pathlib import Path
from audit_native_decode_terminal import audit_terminal
from audit_c1_packed_wave import audit_packed_c1
from audit_c1_layer_completion import audit_c1_completion

def audit_packed_terminal(contract_path,*,live_release=False):
    contract_path=Path(contract_path);c=json.loads(contract_path.read_text())
    base=contract_path.parent;raw=Path(c['raw_root'])
    report=audit_terminal(contract_path,live_release=live_release)
    manifest_path=base/c['cache_diagnostic']['compact_manifest']
    manifest=json.loads(manifest_path.read_text())
    config=json.loads((base/manifest['config']).read_text())
    flag=config.get('c1_packed_wave')
    if type(flag)is not bool:raise ValueError('explicit packed route required')
    expected=c['independent_acceptance']['c1_packed_wave']
    events=[]
    for p in sorted((raw/'diagnostics').glob('compact-worker-*.jsonl')):
        events.extend(json.loads(line) for line in p.read_text().splitlines())
    results=json.loads((raw/'compiled-cache-unit.json').read_text())['results']
    workers=report['hot']['worker_pids']
    # Existing JSON transport can preserve integer keys as strings when loaded
    # externally; the base live Python auditor provides integer rank keys.
    workers={int(rank):pid for rank,pid in workers.items()}
    digest=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    packed=audit_packed_c1(events,workers,manifest_sha256=digest,
        linear_layers=expected['linear_layers'],requests=[x['response']['id'] for x in results],
        enabled=flag,skipped_body_tokens=c['independent_acceptance']['skipped_body_rows'],
        state_passes=expected.get('state_passes',3),seed_mode=expected.get('seed_mode'))
    if not flag:
        report['serial_completion']=audit_c1_completion(events,workers,
            manifest_sha256=digest,enabled=True,require_shadow=True)
    report['packed']=packed
    report['scope']='bounded16 source/hot/packed-or-disabled/serial-shadow/isolation/release; no formal performance or quality acceptance'
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True)
    p.add_argument('--live-release',action='store_true');a=p.parse_args()
    print(json.dumps(audit_packed_terminal(a.contract,live_release=a.live_release)))
