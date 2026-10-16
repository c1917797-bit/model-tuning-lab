"""R17 full40 audit: distinguish native, blocking HYPIC and async HYPIC."""
import json
from pathlib import Path
from audit_r16_performance import audit as audit_full40

def validate_transfer_mode(contract,config):
    mode=contract.get('transfer_treatment')
    if mode not in ('native','blocking','async'):
        raise ValueError('explicit R17 transfer attribution arm required')
    if (type(config.get('c1_async_material_transfer'))is not bool
            or config.get('c1_async_material_transfer')is not (mode=='async')
            or config.get('c1_async_material_verify')is not False):
        raise ValueError('timed transfer mode or verification overhead mismatch')
    if contract.get('performance_group')!=('G1'if mode=='native'else 'G3'):
        raise ValueError('transfer attribution group mismatch')
    return mode

def audit(path,*,live_release=False):
    cp=Path(path);contract=json.loads(cp.read_text());base=cp.parent
    manifest=json.loads((base/contract['successor_manifest']).read_text())
    config=json.loads((base/manifest['config']).read_text())
    mode=validate_transfer_mode(contract,config)
    report=audit_full40(path,live_release=live_release)
    installs=[]
    for file in (Path(contract['raw_root'])/'diagnostics').glob('compact-worker-*.jsonl'):
        for line in file.read_text().splitlines():
            row=json.loads(line)
            if row.get('event')=='c1_private_material_transfer_verified':
                raise ValueError('full-copy diagnostic in timed phase')
            if row.get('event')=='compact_hypic_hooks_installed':
                installs.append(row)
                if (row.get('c1_async_material_transfer')is not (mode=='async')
                        or row.get('c1_async_material_verify')is not False):
                    raise ValueError('worker transfer mode contradicts timed arm')
    if mode!='native' and len(installs)!=4:
        raise ValueError('exact fourworker transfer activation required')
    if mode=='native' and installs:raise ValueError('algorithm marker in native arm')
    return dict(report,transfer_treatment=mode,timed_transfer_policy_verified=True,
        scope='one same-protocol R17 full40 arm; attribution/repetitions/quality/lifecycle separate')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--contract',required=True)
    parser.add_argument('--live-release',action='store_true');args=parser.parse_args()
    print(json.dumps(audit(args.contract,live_release=args.live_release)))
