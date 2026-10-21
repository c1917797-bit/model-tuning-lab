"""Read-only complete inverse/readset verification for actual newly bound source."""
import argparse,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent


def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 s=importlib.util.spec_from_file_location('_g2_v11_bound_preparer',P/'prepare_g2_phases_v11.py');B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
 sr=json.loads(a.source_ref);m=B.obj(sr);parent,observed,cause=B.evidence();proof=m['g2_software_phases_v11'];B.need(sr==B.ref(P/'SOURCE_BOUND.json')and m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False,'actual current bound source')
 for key,v in cause.items():B.need(proof[key]==v,'whole actual failed-owner cause '+key)
 B.need(B.inverse_host((P/'host_service.py').read_text())==B.checked(parent['files']['host_service.py']).read_text(),'complete software-only host inverse')
 for n,r in parent['files'].items():
  if n not in B.CHANGED:B.need(B.checked(m['files'][n]).read_bytes()==B.checked(r).read_bytes(),'all original304 tests/native128/math/argv/caps/atomic/metadata unchanged '+n)
 L=B.obj(proof['whole_current_inverse']);B.need(L==B.obj(m['files']['G2_PHASES_EDITS_V11.json'])and L['baseline']==B.SOURCE,'actual whole current inverse ledger')
 for n,row in L['files'].items():B.need(row['before']==parent['files'][n]and row['after']==m['files'][n]and row['edits']==[dict(before=B.checked(row['before']).read_text(),after=B.checked(row['after']).read_text())],'complete declared whole file inverse '+n)
 import sys
 sys.path.insert(0,str(P));import g2_cold_clock as K,g2_software_stages as S
 clock=K.validate((P/'host_service.py').read_text());scope=S.scope(m,sr);count=sum(B.tests(P/n)for n in m['files']if n.startswith('test_g2_stage')and n.endswith('.py'));B.need(count==scope['new_current_cases'],'distinct current exact test count')
 r=next(r for r in m['dependencies']if r['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3');H=B.module(B.checked(r),'_g2_v11_original_full_collector');closure=H.collect(sr);old=H.collect(B.SOURCE);present={r['path']:r for r in closure['refs']};B.need(all(present.get(r['path'])==r for r in old['refs']+observed),'full exactsource10 tests/old279 dependencies/current closure')
 B.need(H.outputs((P/'contract090.py').read_text(),parent['output_root'])==B.checked(parent['files']['contract090.py']).read_text(),'only preregistered new output operands changed')
 print(json.dumps(dict(schema='bole.G2-v11-software-stages-readonly-audit/v1',source=sr,commands=closure['commands'],audit_ref=B.ref(__file__),readset_count=len(closure['refs']),whole_host_inverse=True,all_original304_test_files_byteexact=True,original_math128_argv_transport_caps_metadata_resources_unchanged=True,firstentry_clock=clock,source8_fresh_cases=279,source10_fresh_cases=25,current11_fresh_cases=count,prospective_sameimage_cases=304+count,software_allocation_seconds=S.CAPS,software_aggregate_cap_seconds=S.LANE_CAP,actual_software_executed=False,actual_parser_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,NPU=False),sort_keys=True));return 0


if __name__=='__main__':raise SystemExit(main())
