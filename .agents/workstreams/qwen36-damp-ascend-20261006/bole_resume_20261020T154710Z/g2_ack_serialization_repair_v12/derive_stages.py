from pathlib import Path
P=Path(__file__).resolve().parent;OLD=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11')
s=(OLD/'g2_exact_controls.py').read_text()
s=s.replace("choices=('source10','current11')","choices=('source10','source11','current12')")
s=s.replace("scope['schema']=='bole.G2-three-source-staged-software-scope/v11'","scope['schema']=='bole.G2-four-source-ACK-staged-software-scope/v12'")
a="selected=scope['controls_source']if a.role=='source10'else sr;target=obj(selected);path=Path(target['root'])"
b="selected={'source10':scope['controls_source'],'source11':scope['historical_stage_source'],'current12':sr}[a.role];target=obj(selected);path=Path(target['root'])"
assert s.count(a)==1;s=s.replace(a,b,1)
a="pattern='test_g2_cold*.py'if a.role=='source10'else'test_g2_stage*.py';count=scope['controls_source_cases']if a.role=='source10'else scope['new_current_cases']"
b="pattern={'source10':'test_g2_cold*.py','source11':'test_g2_stage*.py','current12':'test_g2_ack*.py'}[a.role];count={'source10':scope['controls_source_cases'],'source11':scope['historical_stage_cases'],'current12':scope['new_current_cases']}[a.role]"
assert s.count(a)==1;s=s.replace(a,b,1)
s=s.replace("result.wasSuccessful()and not result.skipped and result.testsRun==count","result.wasSuccessful()and not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses and result.testsRun==count")
s=s.replace("schema='bole.actual-exact-source-only-unittest/v11'","schema='bole.actual-exact-source-only-unittest/v12'")
(P/'g2_exact_controls.py').write_text(s)
s=(OLD/'g2_software_stages.py').read_text();a=s.index('def scope(m,sr):');b=s.index('\n\ndef run(',a)
s=s[:a]+'''def scope(m,sr):
 from g2_ack_proof import SOURCE
 s=m['service_software_scope']
 C.need(s['schema']=='bole.G2-four-source-ACK-staged-software-scope/v12'and
  s['parent_exact_cases']==279 and s['controls_source_cases']==25 and s['historical_stage_cases']==18 and
  s['historical_stage_source']==SOURCE==m['g2_ack_serialization_v12']['parent_source']and
  s['parent_source']==m['g2_cold_clock_v9']['parent_source']and s['controls_source']==m['g2_software_phases_v11']['parent_source']and
  s['allocation_seconds']==CAPS and s['aggregate_cap_seconds']==LANE_CAP and
  s['parent_suite_runs_in_separate_exact_source_process']is True and s['controls_run_only_tests_in_exact_source_process']is True and
  s['current_pattern']=='test_g2_ack*.py'and type(s['new_current_cases'])is int and s['new_current_cases']>0 and
  m['service_required_sameimage_software_cases']==322+s['new_current_cases'],
  'source8 fresh279/source10 fresh25/source11 fresh18/current12 ACK controls, no old whole-software replay or output alias')
 return s
'''+s[b:]
s=s.replace("root=actual/'G2-V11-SOFTWARE'","root=actual/'G2-V12-SOFTWARE'")
s=s.replace("schema='bole.actual-three-source-software-admission/v11'","schema='bole.actual-four-source-software-admission/v12'")
a="(('source10',25,s['controls_source']),('current11',s['new_current_cases'],sr))"
b="(('source10',25,s['controls_source']),('source11',18,s['historical_stage_source']),('current12',s['new_current_cases'],sr))"
assert s.count(a)==1;s=s.replace(a,b,1)
s=s.replace("'bole.actual-exact-source-only-unittest/v11'","'bole.actual-exact-source-only-unittest/v12'")
s=s.replace("schema='bole.actual-exact-source-only-unittest/v11'","schema='bole.actual-exact-source-only-unittest/v12'")
s=s.replace("pattern='test_g2_cold*.py'if role=='source10'else'test_g2_stage*.py'","pattern={'source10':'test_g2_cold*.py','source11':'test_g2_stage*.py','current12':'test_g2_ack*.py'}[role]")
s=s.replace("schema='bole.actual-G2-three-source-staged-software-gate/v11'","schema='bole.actual-G2-four-source-staged-software-gate/v12'")
s=s.replace("current11_fresh_cases=s['new_current_cases']","source11_fresh_cases=18,current12_fresh_cases=s['new_current_cases']")
s=s.replace("'bole.actual-G2-three-source-staged-software-gate/v11'","'bole.actual-G2-four-source-staged-software-gate/v12'")
(P/'g2_software_stages.py').write_text(s)
import ast
old=ast.parse((OLD/'g2_software_stages.py').read_bytes());new=ast.parse(s)
def named(t):return{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=named(old),named(new)
assert all(a[n]==b[n]for n in('finite','Budget','process','one','metadata_gate'))
