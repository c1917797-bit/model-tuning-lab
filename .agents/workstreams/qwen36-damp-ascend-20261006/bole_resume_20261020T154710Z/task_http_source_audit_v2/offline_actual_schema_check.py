"""Explicit local whole-copy controls; not the remote MAIN complete getter.

The supplied primary copies are routed by exact original Refs from the given
indexes. No caller-supplied root is treated as an ambient runtime mount.
"""
import argparse
import copy
import hashlib
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import audit_common as A
import source_audit as S


def run(primary_root, create_root, decoder_root):
    routes={};originals={}
    for root in (primary_root,create_root):
        index=A.parse((root/'ACTUAL_REFS.json').read_bytes())
        for name,r in index.items():
            actual=A.ref(root/name)
            A.need((actual['bytes'],actual['sha256'])==(r['bytes'],r['sha256']),'actual complete local primary copy '+name)
            A.need(r['path']not in routes,'distinct explicit actual primary path')
            routes[r['path']]=root/name;originals[r['path']]=r
    A.need(len(routes)==42,'all original39 plus actual3 whole create receipts')
    def obj(r):
        A.need(originals[r['path']]['sha256']==r['sha256'],'exact original Ref through verified local whole-copy route')
        return A.parse(routes[r['path']].read_bytes())
    owner=obj(A.parse((primary_root/'ACTUAL_REFS.json').read_bytes())['RESULT.json'])
    inputs=obj(owner['inputs_ref']);first=obj(owner['summary']['CPU']['report']);source=first['payload']['bound_task_source_ref'];task=obj(source)
    policy_ref=task['files']['he_policy.py'];local_policy=A.ref(decoder_root/'he_policy.py')
    A.need((local_policy['bytes'],local_policy['sha256'])==(policy_ref['bytes'],policy_ref['sha256']),'same complete actually qualified policy source for pure projection')
    policy=A.load(local_policy,'_offline_exact_qualified_HE_policy')
    positives=[];negatives=[]
    def denied(label,call):
        try:call()
        except(ValueError,KeyError,TypeError):negatives.append(label)
        else:raise AssertionError('negative must reject: '+label)
    image=inputs['image_id']
    for phase in('cpu-preflight','he-controls','cpu-consumer'):
        owned=A.parse((primary_root/phase/'OWNED.json').read_bytes());created=obj(owned['create_receipt'])
        S.creation_argv(owned,created,image);positives.append(phase+'-actual-create')
        for kind in('Ref-instead-of-list','tuple-instead-of-list','nonstring-token','duplicate-name','wrapper-drift'):
            bad=copy.deepcopy(created)
            if kind=='Ref-instead-of-list':bad['requested_argv']=owned['create_receipt']
            elif kind=='tuple-instead-of-list':bad['requested_argv']=tuple(bad['requested_argv'])
            elif kind=='nonstring-token':bad['requested_argv'][0]=True
            elif kind=='duplicate-name':bad['requested_argv']+=['--name','foreign']
            else:bad['argv']=bad['requested_argv']
            denied(phase+'-'+kind,lambda b=bad,o=owned:S.creation_argv(o,b,image))
        if phase=='he-controls':
            he=obj(owner['summary']['HE_owner_ref']);stage=obj(he['stage_ref']);argv=obj(he['create_argv_ref'])
            inspect=obj(he['inspect_ref']);binding=obj(owner['summary']['HE_binding']);stdout=routes[he['created_id_ref']['path']].read_bytes()
            args=[owned,created,he,argv,policy,stage,inspect,binding,stdout,image]
            proof=S.verify_HE_create(*args);positives.append('HE-actual-OWNED-receipt-argvfile-policy-inspect-binding')
            for kind in('OWNED-list-as-Ref','argvfile-network-host','inspect-network-host','binding-root-uid','foreign-create-stdout'):
                bad=list(args)
                if kind=='OWNED-list-as-Ref':bad[0]=copy.deepcopy(owned);bad[0]['create_argv']=he['create_argv_ref']
                elif kind=='argvfile-network-host':bad[3]=argv.copy();bad[3][bad[3].index('--network')+1]='host'
                elif kind=='inspect-network-host':bad[6]=copy.deepcopy(inspect);bad[6][0]['HostConfig']['NetworkMode']='host'
                elif kind=='binding-root-uid':bad[7]=copy.deepcopy(binding);bad[7]['uid']=0
                else:bad[8]=('b'*64+'\n').encode()
                denied('HE-'+kind,lambda b=bad:S.verify_HE_create(*b))
    return dict(schema='bole.HTTP-getter-v2-offline-actual-create-schema-controls/v1',whole_primary_copies_verified=len(routes),
        actual_create_receipts_verified=3,positive_controls=positives,negative_controls=negatives,
        actual_HE_create_join=proof,source_policy_ref=policy_ref,local_policy_exact_copy=local_policy,
        complete_remote_MAIN_getter_executed=False,CPU14_rerun=False,model_executed=False,HTTP_executed=False,
        actual_three_create_refs=[r for r in originals.values()if r['path']in{A.parse((primary_root/ph/'OWNED.json').read_bytes())['create_receipt']['path']for ph in('cpu-preflight','he-controls','cpu-consumer')}])


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--check',action='store_true')
    for n in('primary-root','create-root','decoder-root','output'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if not a.check:print('{"enabled":false,"model_executed":false}');return 0
    A.need(all(v is not None for v in vars(a).values()),'explicit actual whole-copy roots and new output')
    print(A.canonical(A.write(a.output,run(a.primary_root,a.create_root,a.decoder_root))).decode());return 0


if __name__=='__main__':raise SystemExit(main())
