"""Read-only whole source/command/inverse closure; never model qualification."""
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
    if not a.source_ref:raise ValueError('actual fully bound new source Ref3')
    B=load(P/'prepare_g2_consumer_v7.py','_g2_v7_exact_source_auditor');sr=json.loads(a.source_ref);m=B.obj(sr)
    B.need(m['root']==str(P)and sr==B.ref(P/'SOURCE_BOUND.json')and m['files']['audit_source_v7.py']==B.ref(__file__)and m['files']['prepare_g2_consumer_v7.py']==B.ref(P/'prepare_g2_consumer_v7.py'),'exact new source-owned read-only audit files')
    B.need(m['prepared_only']is False and m['default_enabled']is False and m['service_required_sameimage_software_cases']==266 and m['service_software_scope']['parent_exact_cases']==214 and m['service_software_scope']['new_current_cases']==52,'new prospective266 scope only, no actual execution inferred')
    repair=m['g2_exact_consumer_v7'];failed,refs,cause=B.evidence(repair['failed_source'],repair['failed_model_owner'])
    B.need(cause==repair['cause']and B.inverse((P/'g2_stream_owner.py').read_text())==B.checked(failed['files']['g2_stream_owner.py']).read_text(),'actual retained failure/BOOT joined and exact whole-owner inverse')
    collector=[r for r in m['dependencies']if r['sha256']==B.COLLECTOR_SHA];B.need(collector,'exact frozen source-owned collector declared');H=load(B.checked(collector[0]),'_g2_v7_frozen_readset_collector');result=H.collect(sr)
    B.need(H.outputs((P/'contract090.py').read_text(),failed['output_root'])==B.checked(failed['files']['contract090.py']).read_text(),'only exact current output operand delta')
    changed={'g2_stream_owner.py','contract090.py','G2_STREAM_EDITS_V1.json'}
    for name,old in failed['files'].items():
        B.need(name in m['files'],'all old source file operands retained '+name)
        if name not in changed:B.need(B.checked(old).read_bytes()==B.checked(m['files'][name]).read_bytes(),'consumer/runtime/oracle/resource/all original258 tests byteexact '+name)
    ledger=B.obj(m['files']['G2_STREAM_EDITS_V1.json']);B.need(ledger['baseline']==m['g2_predecessor']['source'],'same actual qualified G1v2 inverse basis')
    for name,row in ledger['files'].items():
        before=B.checked(row['before']).read_text();after=B.checked(row['after']).read_text();B.need(row['after']==m['files'][name]and row['edits']==[dict(before=before,after=after)],'whole exact current inverse ledger closure '+name)
    value=dict(schema='bole.G2-v7-source-readonly-audit/v1',source=sr,audit_source=B.ref(__file__),files=len(m['files']),readset_count=len(result['refs']),commands=result['commands'],whole_source_original_functions_used=result['source_owned_original_functions'],failed_v6_source=repair['failed_source'],failed_v6_owner=repair['failed_model_owner'],actual_failure_cause=cause,exact_owner_inverse=True,original_runtime_math_consumer_resource_and258_controls_unchanged=True,prospective_sameimage_cases=266,actual_sameimage_executed=False,actual_model_executed=False,model_ready=False,formal_success=False,NPU=False)
    print(json.dumps(value,sort_keys=True,allow_nan=False));return 0


if __name__=='__main__':raise SystemExit(main())
