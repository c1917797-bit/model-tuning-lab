"""Source-bound explicit registry/policy metadata only; no lifecycle action."""
import argparse
import json
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import main_quiescence as Q


def prepare(base_ref,entries_ref,authority_ref,registry_output,policy_output):
    C.authority(authority_ref,3600);base=C.obj(base_ref);entry=C.obj(entries_ref)
    C.need(type(base)is dict and set(base)=={'schema','authority_ref','declared_complete_MAIN_NPU_inventory','units','owned_refs','serial_schedule'}
        and base['schema']=='bole.MAIN-NPU-quiescence-policy/v1'and base['authority_ref']==authority_ref,
        'fresh exact complete explicit MAIN inventory under same authority')
    C.need(entry['schema']=='bole.known-MAIN-CPU3-entry-inputs/v1'and type(entry['entries'])is list,
        'explicit actual fullRef3 owned/source/CID/profile entry data')
    registry=C.write(registry_output,dict(schema=Q.REGISTRY_SCHEMA,authority_ref=authority_ref,entries=entry['entries']))
    Q.registry(registry,authority_ref=authority_ref)
    value=dict(base,schema=Q.SCHEMA,CPU3_registry_ref=registry)
    policy=C.write(policy_output,value);Q.policy(policy,authority_ref=authority_ref)
    return dict(registry_ref=registry,policy_ref=policy,resources_admitted=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
    for n in('base-policy-ref','entries-ref','authority-ref'):p.add_argument('--'+n)
    for n in('registry-output','policy-output'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.prepare:print('{"enabled":false,"resources_admitted":false,"NPU":false}');return 0
    C.need(all(v is not None for v in vars(a).values()),'all actual inventory/entry/authority refs and absent new output paths')
    print(json.dumps(prepare(json.loads(a.base_policy_ref),json.loads(a.entries_ref),json.loads(a.authority_ref),a.registry_output,a.policy_output)));return 0


if __name__=='__main__':raise SystemExit(main())
