"""Read-only exact inverse/readset audit; no model or current-live promotion."""
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
    B=load(P/'prepare_g2_handoff_v8.py','_g2_v8_source_owned_audit');sr=json.loads(a.source_ref);m=B.obj(sr);repair=m['g2_metadata_handoff_v8']
    B.need(sr==B.ref(P/'SOURCE_BOUND.json')and m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False and m['files']['audit_source_v8.py']==B.ref(__file__)and m['files']['prepare_g2_handoff_v8.py']==B.ref(P/'prepare_g2_handoff_v8.py'),'exact current bound source-owned audit/preparer')
    failed,observed,cause=B.evidence(repair['failed_source'],repair['failed_owner'])
    B.need(all(repair[k]==v for k,v in cause.items())and repair['sameimage_cold_before_any_NPU_required']is True,'actual stopped-failure/visibility/normalization cause, cold handoff still mandatory')
    for name in B.CHANGED:B.need(B.inverse(name,(P/name).read_text())==B.checked(failed['files'][name]).read_text(),'exact whole declared lifecycle/metadata/fixture inverse '+name)
    B.fixture_assertions(B.checked(failed['files']['test_g2_stream.py']).read_text(),(P/'test_g2_stream.py').read_text())
    changed={*B.CHANGED,'contract090.py','G2_STREAM_EDITS_V1.json'}
    for name,r in failed['files'].items():
        if name not in changed:B.need(B.checked(r).read_bytes()==B.checked(m['files'][name]).read_bytes(),'all original numerical/128/consumer/finalizer/argv8/resource/other controls byteexact '+name)
    collectors=[r for r in m['dependencies']if r['sha256']==B.COLLECTOR_SHA];B.need(collectors,'declared exact original canonical-source readset collector');H=load(B.checked(collectors[0]),'_g2_v8_original_readset');closure=H.collect(sr)
    B.need(H.outputs((P/'contract090.py').read_text(),failed['output_root'])==B.checked(failed['files']['contract090.py']).read_text(),'only source/output operand delta in original command')
    ledger=B.obj(m['files']['G2_HANDOFF_EDITS_V8.json']);B.need(ledger['baseline']==B.SOURCE,'same retained failed-source inverse baseline')
    for name,row in ledger['files'].items():B.need(row['before']==failed['files'][name]and row['after']==m['files'][name]and row['edits']==[dict(before=B.checked(row['before']).read_text(),after=B.checked(row['after']).read_text())],'complete precise current before/after source ledger '+name)
    added=sum(B.tests(P/n)for n in m['files']if n.startswith('test_g2_handoff')and n.endswith('.py'))
    B.need(added==repair['new_controls']and m['service_required_sameimage_software_cases']==266+added and m['service_software_scope']['new_current_cases']==52+added,'all original266 plus exact included new methods, no host-only/cached count')
    print(json.dumps(dict(schema='bole.G2-v8-source-readonly-audit/v1',source=sr,audit_source=B.ref(__file__),commands=closure['commands'],readset_count=len(closure['refs']),whole_source_original_functions_used=closure['source_owned_original_functions'],failed_v7_source=B.SOURCE,failed_v7_owner=B.FAILED_OWNER,exact_metadata_and_lifecycle_inverse=True,original266_assertions_math_consumer_finalizer_resources_preserved=True,whole_v7_bind_argv_and8controls_byteexact=True,original_15_stream_test_bodies_AST_exact=True,total_saved_actual_copy_bytes=cause['total_actual_copy_bytes'],original64MiB_per_rank_metadata_cap_unchanged=True,sameimage_cold_original_contract_and_owner_reader_before_NPU_required=True,prospective_sameimage_cases=266+added,actual_sameimage_executed=False,actual_model_executed=False,actual_live_identity_qualified=False,model_ready=False,formal_success=False,NPU=False),sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
