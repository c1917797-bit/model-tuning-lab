"""Read-only current whole inverse + exact original canonical command closure."""
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
    B=load(P/'prepare_g2_cold_v9.py','_g2_v9_exact_source_audit');sr=json.loads(a.source_ref);m=B.obj(sr);proof=m['g2_cold_clock_v9']
    B.need(sr==B.ref(P/'SOURCE_BOUND.json')and m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False and m['files']['audit_source_v9.py']==B.ref(__file__)and m['files']['prepare_g2_cold_v9.py']==B.ref(P/'prepare_g2_cold_v9.py'),'exact current immutable source-owned audit/preparer')
    parent,observed,cause=B.evidence(proof['parent_source'],proof['failed_cpu_owner'],proof['parent_source_audit'])
    B.need(all(proof[k]==v for k,v in cause.items()),'source-bound historical software/parser-only failure; never cold/model qualification')
    K=load(P/'g2_cold_clock.py','_g2_v9_source_bound_clock');clock=K.validate((P/'host_service.py').read_text());B.need(proof['clock']==clock,'exact actual main first clock/same original deadline')
    for n in B.CHANGED:B.need(B.inverse(n,(P/n).read_text())==B.checked(parent['files'][n]).read_text(),'precise complete original v8 lifecycle inverse '+n)
    ledger=B.obj(m['files']['G2_COLD_EDITS_V9.json']);B.need(ledger['baseline']==B.SOURCE and m['files']['G2_COLD_EDITS_V9.json']==proof['whole_current_inverse'],'new current ledger distinct from historical v8 handoff proof')
    for n,row in ledger['files'].items():B.need(row['before']==parent['files'][n]and row['after']==m['files'][n]and row['edits']==[dict(before=B.checked(row['before']).read_text(),after=B.checked(row['after']).read_text())],'exact complete before/after whole-file inverse '+n)
    changed={*B.CHANGED,'contract090.py','G2_STREAM_EDITS_V1.json'}
    for n,r in parent['files'].items():
        if n not in changed:B.need(B.checked(r).read_bytes()==B.checked(m['files'][n]).read_bytes(),'all279 originals/whole math/argv/atomic/coldcode/resources byteexact '+n)
    collectors=[r for r in m['dependencies']if r['sha256']==B.COLLECTOR_SHA];B.need(collectors,'original canonical source-owned command/readset collector');H=load(B.checked(collectors[0]),'_g2_v9_original_readset')
    B.need(H.outputs((P/'contract090.py').read_text(),parent['output_root'])==B.checked(parent['files']['contract090.py']).read_text(),'only original registered output operands change')
    count=sum(B.tests(P/n)for n in m['files']if n.startswith('test_g2_cold')and n.endswith('.py'));scope=m['service_software_scope']
    B.need(scope==dict(schema='bole.G2-cold-clock-historical-plus-current-controls/v9',parent_source=B.SOURCE,parent_exact_cases=279,parent_suite_runs_in_separate_exact_source_process=True,current_pattern='test_g2_cold*.py',new_current_cases=count)and m['service_required_sameimage_software_cases']==279+count and proof['new_controls']==count,'all279 fresh in exact original source plus exact new current controls, no cached or omitted tests')
    closure=H.collect(sr)
    print(json.dumps(dict(schema='bole.G2-v9-source-readonly-audit/v1',source=sr,audit_source=B.ref(__file__),commands=closure['commands'],readset_count=len(closure['refs']),whole_source_original_functions_used=closure['source_owned_original_functions'],parent_source=B.SOURCE,parent_failed_cpu=B.FAILED_OWNER,whole_current_inverse=True,all_original279_test_bytes_unchanged=True,original_math_128_argv_atomic_metadata_caps_unchanged=True,cold_main_clock=clock,old_elapsed_not_rewritten=True,candidate_is_original_allowed_exclusive_leaf=True,prospective_sameimage_cases=279+count,actual_sameimage_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,model_ready=False,NPU=False),sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
