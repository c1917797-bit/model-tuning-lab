"""In-memory complete paired source preparation; no writes, binding, Docker or device action."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import performance_followup_delta as D
import paired_contract as PAIR
import paired_receipt_consumer as RECEIPTS
import validated_performance_policy as FAST
import followup_binding_delta as BIND

HELPERS=('validated_performance_policy.py','paired_receipt_consumer.py','paired_contract.py',
         'paired_prepare.py','performance_followup_delta.py','followup_binding_delta.py','followup_source_validate.py')


def need(v,s):
    if not v:raise ValueError(s)


def refbytes(path,raw):
    return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def checked(r):
    p=Path(r['path'])
    need(p.is_absolute() and p.is_file() and not any(x.is_symlink()for x in(p,*p.parents)),
         'ordinary source path without links')
    raw=p.read_bytes();need(refbytes(p,raw)==r,'complete original source identity '+str(p))
    return raw


def output_contract(text,output):
    for name,value in(('OUTPUT_POSIX',output),('CPU_OUTPUT_POSIX',output+'-CPU')):
        nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign) and len(n.targets)==1
               and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
        need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant),'exact original output constant '+name)
        text=D.once(text,ast.get_source_segment(text,nodes[0]),name+'='+repr(value))
    return text


def read_parent():
    raw=D.PARENT.read_bytes();m=json.loads(raw)
    originals={n:checked(r)for n,r in m['files'].items()}
    return m,originals,refbytes(D.PARENT,raw)


def render_pair(*,base_root=None,permit_materialized=False,authority_ref=None):
    base_root=HERE if base_root is None else Path(base_root)
    need(base_root.is_absolute() and '..'not in base_root.parts,'explicit absolute preparation root')
    need(type(permit_materialized)is bool,'explicit read-only validation mode')
    parent,originals,parentref=read_parent()
    runtime=D.render({n:originals[n].decode()for n in D.RUNTIME})
    shared=dict(originals);shared.update({n:s.encode()for n,s in runtime.items()})
    shared['performance_client_consumer.py']=RECEIPTS.wrap_consumer(originals['performance_client_consumer.py'].decode()).encode()
    # Same setting in both arms, before branch. No actual current environment changes.
    server=shared['server090.py'].decode()
    server=D.once(server,' m=C.obj(sr)',' e.update(HCCL_DETERMINISTIC=\'true\')\n m=C.obj(sr)')
    shared['server090.py']=server.encode()
    for n in HELPERS:shared[n]=(HERE/n).read_bytes()
    obs_scope=None
    tree=ast.parse(shared['observation_profile.py'].decode())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='DECLARATION'for t in node.targets):
            obs_scope=ast.literal_eval(node.value)
    need(type(obs_scope)is dict,'exact inherited OBS elision declaration')
    bundles={}
    for arm in('bole','native_ar'):
        root=base_root/('prepared-source-'+arm);output=base_root/('reserved-future-output-'+arm)
        need(permit_materialized or(not root.exists() and not output.exists()),'future-only exclusive source/output operands')
        files=dict(shared)
        files['contract090.py']=output_contract(files['contract090.py'].decode(),str(output)).encode()
        files=BIND.render(files)
        m=copy.deepcopy(parent)
        m.update(root=str(root),output_root=str(output),model_receipt_root=str(output/'dense/receipts'),
            stream_channel_root=str(output/'dense/receipts/STREAM'),
            stream_channel_contract_path=str(output/'dense/receipts/STREAM/CHANNEL.json'),
            prepared_only=True,default_enabled=False,performance_ready=False,numerical_qualified=False,
            performance_arm=arm,paired_common_environment=dict(PAIR.COMMON_ENV),
            effective_speculative_config=dict(method='mtp',num_speculative_tokens=8)if arm=='bole'else None,
            followup_parent_source=parentref,pending_current_authority=authority_ref is None,
            pending_model_correctness=True,pending_runtime_validator=False,
            followup_source_schema='bole.followup-whole-source-validation/v1',
            followup_preparation_root=str(base_root),followup_authority_ref=authority_ref,
            pending_fastpath_runtime_qualification=True)
        m.pop('prepared_template',None)
        if arm=='bole':
            m['validated_performance_profile']=dict(FAST.DECLARATION)
            m['observation_only_profile']=obs_scope
        else:
            m.pop('validated_performance_profile',None);m.pop('observation_only_profile',None)
        m['files']={n:refbytes(root/n,raw)for n,raw in sorted(files.items())}
        # Preserve installed runtime identities while rebasing copied snapshots.
        bypath={r['path']:n for n,r in parent['files'].items()}
        m['service_runtime_source_snapshots']={k:m['files'][bypath[r['path']]]
             for k,r in parent['service_runtime_source_snapshots'].items()}
        m['performance_timing_donor']=m['files']['benchmark_shared_prefix.py']
        m['performance_streaming_client']=m['files']['performance_service_client.py']
        additions=[parentref,*parent['files'].values()]
        if authority_ref is not None:
            authority=json.loads(checked(authority_ref))
            additions.extend([authority_ref,authority['MAIN_review_ref']])
            checked(authority['MAIN_review_ref'])
        m['dependencies']=[*parent['dependencies'],*additions,m['performance_timing_donor'],m['performance_streaming_client']]
        unique={}
        for r in m['dependencies']:
            need(r['path']not in unique or unique[r['path']]==r,'unambiguous retained dependency identity')
            unique[r['path']]=r
        m['dependencies']=list(unique.values())
        changed={n:dict(before=parent['files'].get(n),after=m['files'][n])
                 for n in files if n not in originals or files[n]!=originals[n]}
        ledger=dict(schema='bole.prepared-complete-followup-delta/v1',parent=parentref,
            changed=changed,removed=[],performance_ready=False,numerical_qualified=False)
        for n,raw in files.items():
            if n.endswith('.py'):compile(raw,n,'exec')
        bundles[arm]=dict(manifest=m,files=files,ledger=ledger)
    proof=PAIR.pair(bundles['bole']['manifest'],bundles['native_ar']['manifest'])
    return dict(schema='bole.in-memory-paired-followup-preparation/v1',arms=bundles,proof=proof,
        pending=['distinct MAIN-approved performance execution authority and source/output binding',
                 'related real NPU model correctness under this exact common policy',
                 'same-image import and worker-loaded closure','paired runtime admission'],
        NPU=False,owner_created=False,source_bound=False,performance_ready=False)


def inverse_files(arm_bundle):
    parent,originals,_=read_parent();actual=arm_bundle['files'];ledger=arm_bundle['ledger']['changed']
    restored=dict(actual)
    expected_changed={n for n in actual if n not in originals or actual[n]!=originals[n]}
    need(set(ledger)==expected_changed,'complete all-and-only source inverse delta')
    for name in expected_changed:
        row=ledger[name]
        need(row['before']==parent['files'].get(name) and
             row['after']==arm_bundle['manifest']['files'][name] and
             row['after']==refbytes(Path(row['after']['path']),actual[name]),'actual whole-file inverse identity')
        if name in originals:restored[name]=originals[name]
        else:restored.pop(name)
    need(restored==originals,'inverse reconstructs every original source byte and no additions')
    return restored


def validate_preparation(bundle):
    # Full deterministic reconstruction prevents caller-injected file or ledger substitutions.
    expected=render_pair()
    need(bundle==expected,'complete source bytes, identities, inverse ledger and arm policies')
    for arm in bundle['arms'].values():inverse_files(arm)
    return bundle['proof']


def main():
    import argparse
    p=argparse.ArgumentParser(description='Read-only in-memory source preparation, no launch')
    p.add_argument('--review',action='store_true')
    args=p.parse_args()
    if not args.review:
        print(json.dumps(dict(enabled=False,NPU=False,performance_ready=False)));return
    b=render_pair()
    print(json.dumps(dict(schema=b['schema'],proof=b['proof'],pending=b['pending'],
        arms={arm:dict(root=v['manifest']['root'],source_files=len(v['files']),
            changed=v['ledger']['changed'])for arm,v in b['arms'].items()},
        source_bound=False,performance_ready=False),sort_keys=True))


if __name__=='__main__':main()
