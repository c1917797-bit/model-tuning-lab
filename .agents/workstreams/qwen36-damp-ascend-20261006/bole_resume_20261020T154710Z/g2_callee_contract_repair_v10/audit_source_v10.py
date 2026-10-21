"""Read-only exact actual025 helper inverse and unmodified runtime/test closure."""
import argparse
import importlib.util
import json
from pathlib import Path
P=Path(__file__).resolve().parent


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    B=load(P/'prepare_g2_callee_v10.py','_g2_v10_source_owned_audit');sr=json.loads(a.source_ref);m=B.obj(sr);proof=m['g2_callee_contract_v10']
    B.need(sr==B.ref(P/'SOURCE_BOUND.json')and m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False and m['files']['audit_source_v10.py']==B.ref(__file__)and m['files']['prepare_g2_callee_v10.py']==B.ref(P/'prepare_g2_callee_v10.py'),'actual current bound defaultOFF source-owned audit/preparer')
    parent,observed,cause=B.evidence(proof['parent_source'],proof['failed_cpu_owner']);B.need(all(proof[k]==v for k,v in cause.items()),'actual no-CID API first-fault, not a cached software/model pass')
    B.need(B.inverse((P/'g2_cold_parent_output.py').read_text())==B.checked(parent['files']['g2_cold_parent_output.py']).read_text(),'complete actual v9 helper inverse; alias guard intact')
    Q=B.proof_module(P,m['files']['sourceio.py']);snapshot=Q.verify_snapshot(m);B.need(snapshot==proof['CPU_source_test_snapshot']and Q.declarations(P/'owned_substrate.py')==proof['original025_sources'],'actual original025 full source/snapshot mapping and closed readset')
    K=load(P/'g2_cold_clock.py','_g2_v10_unchanged_clock');clock=K.validate((P/'host_service.py').read_text())
    changed={'g2_cold_parent_output.py','contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in parent['files'].items():
        if n not in changed:B.need(B.checked(r).read_bytes()==B.checked(m['files'][n]).read_bytes(),'all original297 test bytes/math/128/argv/clock/candidate/metadata/resources unchanged '+n)
    ledger=B.obj(proof['whole_current_inverse']);B.need(ledger==B.obj(m['files']['G2_CALLEE_EDITS_V10.json'])and ledger['baseline']==B.SOURCE and ledger['added_CPU_source_snapshot']==snapshot,'separate current whole inverse plus nonexecuted CPU source snapshot')
    for n,row in ledger['files'].items():B.need(row['before']==parent['files'][n]and row['after']==m['files'][n]and row['edits']==[dict(before=B.checked(row['before']).read_text(),after=B.checked(row['after']).read_text())],'whole declared callee/output inverse '+n)
    added=sum(B.tests(P/n)for n in m['files']if n.startswith('test_g2_cold_callee_v10')and n.endswith('.py'));scope=m['service_software_scope']
    B.need(scope['parent_source']==parent['service_software_scope']['parent_source']and scope['parent_exact_cases']==279 and scope['new_current_cases']==18+added and m['service_required_sameimage_software_cases']==297+added and proof['current_source_v10_new_real_callee_controls']==added,'exact source-v8 fresh279 plus current original18 and new real-callee controls; no phantom fresh297-source claim')
    rows=[r for r in m['dependencies']if r['sha256']==B.COLLECTOR_SHA];B.need(rows,'original canonical source-owned command/readset collector');H=load(B.checked(rows[0]),'_g2_v10_original_readset');B.need(H.outputs((P/'contract090.py').read_text(),parent['output_root'])==B.checked(parent['files']['contract090.py']).read_text(),'only original output operands changed');closure=H.collect(sr)
    B.need(any(r==snapshot['snapshot_ref']for r in closure['refs'])and all(any(r==v for r in closure['refs'])for v in proof['original025_sources'].values()),'all actual source-test snapshot and original025 Refs mounted explicitly')
    print(json.dumps(dict(schema='bole.G2-v10-source-readonly-audit/v1',source=sr,audit_source=B.ref(__file__),commands=closure['commands'],readset_count=len(closure['refs']),whole_source_original_functions_used=closure['source_owned_original_functions'],parent_failed_source=B.SOURCE,parent_failed_cpu=B.FAILED_OWNER,whole_callee_inverse=True,all_original297_test_bytes_preserved=True,cold_clock=clock,original_candidate_leaf=True,original_math_128_argv_metadata_caps_resources_unchanged=True,CPU_source_snapshot=snapshot,historical_source_v8_fresh_cases=279,current_source_v10_original18=True,new_real_callee_controls=added,prospective_sameimage_cases=297+added,actual_sameimage_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,model_ready=False,NPU=False),sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
