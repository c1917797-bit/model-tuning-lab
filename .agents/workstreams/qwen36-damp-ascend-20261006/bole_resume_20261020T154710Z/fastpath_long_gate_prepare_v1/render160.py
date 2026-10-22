"""Exact source-only160 component adaptation; NEVER binds/adopts a runtime authority."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render_page_delta as PAGE


def once(text,old,new):
    if text.count(old)!=1:raise ValueError('exact160 source operand: '+old[:100])
    return text.replace(old,new,1)


def adapt(files):
    result=dict(files)
    def edit(name,pairs):
        text=result[name].decode()
        for old,new in pairs:text=once(text,old,new)
        result[name]=text.encode()
    edit('short_state_digest.py',[
        ('output_tokens=8, generations=2, ordinals=list(range(7))','output_tokens=160, generations=2, ordinals=list(range(159))'),
        ('source=self.source, profile=self.profile,',"source=self.source, profile=dict(schema='bole.lossless-profile-reference/v1',sha256=hashlib.sha256(canonical(self.profile)).hexdigest()),"),
        ("        need(len(data) <= CAP and self.bytes+len(data) <= TOTAL_CAP, 'bounded complete state metadata')",
         "        need(len(data) <= (2048 if kind=='STEP'else CAP) and self.bytes+len(data) <= TOTAL_CAP, 'bounded complete state metadata')")])
    edit('bole_performance_profile.py',[
        ('"output_tokens": 8,','"output_tokens": 160,'),('output_tokens: int = 8','output_tokens: int = 160'),
        ("'profile': 'short8'","'profile': 'qualifier160'"),
        ("'max_steps_per_request': 7","'max_steps_per_request': 159"),
        ("'max_output_tokens': 8","'max_output_tokens': 160")])
    edit('live_owner.py',[('output_budget == 8and','output_budget == 160and')])
    edit('performance_service_client.py',[
        ("ids,-1,8,'warmup'","ids,-1,160,'warmup'"),("ids,0,8,'measured'","ids,0,160,'measured'")])
    edit('performance_host.py',[("'output_tokens': 8, 'concurrency': 1,","'output_tokens': 160, 'concurrency': 1,")])
    edit('validated_performance_policy.py',[("scope['output_tokens']==8 and","scope['output_tokens']==160 and")])
    result['fastpath_numeric_consumer.py']=PAGE.render(result['fastpath_numeric_consumer.py'].decode()).encode()
    for name in('fastpath_numeric_sink.py','fastpath_numeric_observer.py','qualification_state_probe.py'):
        result[name]=('import long_gate_primitives as LONG\n'+result[name].decode()).encode()
    edit('fastpath_numeric_sink.py',[
        ("    logical=logical_bytes(t,frame)","    C.need(C.ref(LONG.__file__)==m['files']['long_gate_primitives.py'],'source-bound lossless transport helper')\n    logical=logical_bytes(t,frame)"),
        ("['output_tokens']==8","['output_tokens']==160"),
        ("report_ref=metadata(c,c['root']/(stem+'.json'),report)",
         "report_ref=LONG.store_report(c,c['root'],stem,report,durable_json=lambda path,value:metadata(c,path,value))")])
    edit('fastpath_numeric_observer.py',[("report=self.C.obj(proof['report'])","report,_envelope=LONG.read_report(self.C,proof['report'])")])
    edit('qualification_state_probe.py',[
        ("report=C.obj(ref)","report,envelope=LONG.read_report(C,ref)"),
        ("0<=key[1]<7","0<=key[1]<159"),
        ("rows=sorted(rows,key=lambda r:(r['layer'],r['kind']))",
         "rows_reference=LONG.compact_rows_reference(report,envelope['wire'],envelope['codec'])")])
    edit('compare_state_digest.py',[
        ('from pathlib import Path','from pathlib import Path\nimport long_gate_primitives as LONG\n_TRANSPORT_READSET=[]\n_BOUND_PROFILE={}'),
        ("    return json.loads(Path(r['path']).read_bytes())",'''    value=json.loads(Path(r['path']).read_bytes())
    if value.get('schema')==SCHEMA:
        need(_BOUND_PROFILE and value['profile']==dict(schema='bole.lossless-profile-reference/v1',
             sha256=hashlib.sha256(LONG.canonical(_BOUND_PROFILE)).hexdigest()),'lossless actual source-bound full profile identity')
        value['profile']=dict(_BOUND_PROFILE)
    if value.get('schema')==SCHEMA and value.get('kind')=='STEP':
        need('rows'not in value['record']and 'rows_reference'in value['record'],'only lossless160 STATE row transport')
        expected={k:value[k]for k in('source','rank','generation','ordinal')}
        reference=value['record']['rows_reference']
        def exact(rr):
            need(ref(rr['path'])==rr,'actual complete lossless numeric report Ref')
            _TRANSPORT_READSET.append(rr)
            return Path(rr['path']).read_bytes()
        rows,full=LONG.resolve_rows(reference,expected,read_exact_ref=exact)
        value['record']['rows']=rows
    return value'''),
        ("    m=obj(source_ref);profile=select", "    _TRANSPORT_READSET.clear()\n    m=obj(source_ref);profile=select"),
        ("    need(profile['observation']==expected_mode", "    _BOUND_PROFILE.clear();_BOUND_PROFILE.update(profile)\n    need(profile['observation']==expected_mode"),
        ("for row,n in zip(rows,(8,8,1)):","for row,n in zip(rows,(160,160,1)):"),
        ("4<=nr<=7","80<=nr<=159"),
        ("['request']['max_tokens']==8","['request']['max_tokens']==160"),
        ("4<=r['steps']<=7","80<=r['steps']<=159"),
        ("    return m,evidence,readset","    return m,evidence,readset+list(_TRANSPORT_READSET)"),
        ("32<=len(a)<=56","640<=len(a)<=1272"),
        ("generations=2,output_tokens=8","generations=2,output_tokens=160")])
    edit('performance_client_consumer.py',[("32<=len(evidence)<=56","640<=len(evidence)<=1272")])
    edit('qualification_smoke_join.py',[
        ('from pathlib import Path','from pathlib import Path\nimport long_gate_primitives as LONG'),
        ("['output_tokens']==8 and","['output_tokens']==160 and"),
        ("['output_tokens']==8,'short8 domain only'","['output_tokens']==160,'explicit160 intermediate domain only'"),
        ("r=C.ref(root/(stem+'.json'));report=C.obj(r)","r=C.ref(root/(stem+'.json'));report,envelope=LONG.read_report(C,r)\n                expected.add(stem+'.zjson')"),
        ("observed={(x['layer'],x['kind']):x for x in state['rows']}",
         "rows,_full=LONG.resolve_rows(state['rows_reference'],{k:report[k]for k in('source','rank','generation','ordinal')},read_exact_ref=lambda rr:C.checked(rr).read_bytes())\n                observed={(x['layer'],x['kind']):x for x in rows}"),
        ("{p.name for p in root.glob('*.json')}==expected","{p.name for p in root.glob('*.json')}=={n for n in expected if n.endswith('.json')}"),
        ("reports.extend([r,release_ref])","reports.extend([r,envelope['wire'],release_ref])"),
        ("json_bytes=sum(p.stat().st_size for p in all_files if p.suffix=='.json')",
         "json_bytes=sum(p.stat().st_size for p in all_files if p.suffix in('.json','.zjson'))"),
        ("        budget.append(dict(rank=rank,actual_total_bytes=total,actual_JSON_bytes=json_bytes,",'''        import g3_budget as OLD_BUDGET
        need(C.ref(OLD_BUDGET.__file__)==m['files']['g3_budget.py'],'original budget reader source retained')
        legacy=OLD_BUDGET.actual(C,m,rank,references=True)
        # Union actual Refs, never double-count STATE already charged by old
        # boundary mode; do not omit STATE when that mode is disabled.
        combined={rr['path']:rr for rr in legacy['references']}
        for p in list(all_files)+list(receipt.glob('STATE-*-R%d.json'%rank)):
            if p.suffix=='.pt':continue
            rr=C.ref(p);C.checked(rr);combined[rr['path']]=rr
        combined_bytes=sum(rr['bytes']for rr in combined.values())
        need(combined_bytes<=64*2**20,'ONE combined actual legacy/new/STATE per-rank metadata ledger')
        need(sum(p.stat().st_size for p in all_files if p.suffix=='.pt')+combined_bytes<=2**30,
             'actual retained first raw plus combined metadata within original1GiB')
        budget.append(dict(rank=rank,combined_actual_metadata_bytes=combined_bytes,
                           combined_readset=list(combined.values()),actual_total_bytes=total,actual_JSON_bytes=json_bytes,'''),
        ("short8_numeric_scope_passed=True","intermediate160_numeric_scope_passed=True"),
        ("bole.actual-fastpath-short8-independent-numeric-scope/v1","bole.actual-fastpath-160-independent-numeric-scope/v1")])
    result['long_gate_primitives.py']=(HERE/'long_gate_primitives.py').read_bytes()
    for name,raw in result.items():
        if name.endswith('.py'):compile(raw,name,'exec')
    return result


def render(short_bundle):
    if short_bundle.get('prepared_only')is not True:raise ValueError('only reviewed unbound short preparation may derive160')
    files=adapt(short_bundle['files']);m=copy.deepcopy(short_bundle['manifest'])
    m['fastpath_numeric_qualification']['output_tokens']=160
    p=m['short_state_digest_profile'];p.update(output_tokens=160,ordinals=list(range(159)))
    m['performance_profile']['scope']['output_tokens']=160
    m['service_experiment'].update(profile='qualifier160',max_steps_per_request=159,max_output_tokens=160)
    m['profile']['HTTP_output_tokens']=160;m['performance_client_contract']['output_tokens']=160
    old_refs={r['path']:name for name,r in m['files'].items()}
    root=HERE/'prepared-source-160';output=HERE/'reserved-output-160'
    m['files']={n:dict(path=str(root/n),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())for n,raw in files.items()}
    def rebase(value):
        if type(value)is dict:
            if set(value)=={'path','bytes','sha256'}and value['path']in old_refs:return dict(m['files'][old_refs[value['path']]])
            return {k:rebase(v)for k,v in value.items()}
        if type(value)is list:return [rebase(v)for v in value]
        return value
    for key in('dependencies','service_runtime_source_snapshots','performance_timing_donor','performance_streaming_client'):
        m[key]=rebase(m[key])
    m.update(root=str(root),output_root=str(output),model_receipt_root=str(output/'dense/receipts'),
        prepared_only=True,performance_ready=False,numerical_qualified=False,
        qualification_execution_authority_pending=True,qualification_source_binding_pending=True)
    m['stream_channel_root']=str(output/'dense/receipts/STREAM')
    m['stream_channel_contract_path']=str(output/'dense/receipts/STREAM/CHANNEL.json')
    changed={n:dict(before=hashlib.sha256(short_bundle['files'][n]).hexdigest()if n in short_bundle['files']else None,
                    after=hashlib.sha256(raw).hexdigest())for n,raw in files.items()
             if n not in short_bundle['files']or short_bundle['files'][n]!=raw}
    return dict(files=files,manifest=m,delta=changed,prepared_only=True,execution_ready=False,
        pending=['160 whole-source rebuild validator/producer and new legal source binding',
            'fresh raw first/current/checkpoint joint1GiB budget from actual short8 capture',
            'same-image160 entry controls; unchanged original mathematical/STATE/HTTP checks on actual NPU'])


def inverse(bundle,short_bundle):
    parent=short_bundle['files'];files=bundle['files']
    changed={n for n in files if n not in parent or parent[n]!=files[n]}
    if changed!=set(bundle['delta']):raise ValueError('complete exact160 delta ledger')
    restored=dict(files)
    for n in changed:
        d=bundle['delta'][n]
        if hashlib.sha256(files[n]).hexdigest()!=d['after']:raise ValueError('actual160 successor hash')
        if n in parent:
            if hashlib.sha256(parent[n]).hexdigest()!=d['before']:raise ValueError('actual short parent hash')
            restored[n]=parent[n]
        else:restored.pop(n)
    if restored!=parent:raise ValueError('inverse restores ALL original short source bytes')
    return restored


if __name__=='__main__':
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: pure source --check only')
    sys.path.insert(0,str(HERE.parent/'fastpath_numeric_bridge_prepare_v1'))
    import qualification_short_prepare as Q
    b=Q.render();out=render(b);inverse(out,b)
    # Original runtime authority gate is intentionally NOT bypassed here.
    print(json.dumps(dict(schema='bole.prepared160-component-source-delta/v1',files=len(out['files']),
        changed=sorted(out['delta']),prepared_only=True,execution_ready=False,NPU=False,pending=out['pending']),sort_keys=True))
