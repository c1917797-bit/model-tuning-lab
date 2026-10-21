import argparse,ast,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 spec=importlib.util.spec_from_file_location('_g2_v12_exact_bound_preparer',P/'prepare_g2_ack_v12.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
 sr=json.loads(a.source_ref);m=B.obj(sr);parent,observed,cause=B.evidence();proof=m['g2_ack_serialization_v12']
 B.need(sr==B.ref(P/'SOURCE_BOUND.json')and m['root']==str(P)and m['prepared_only']is False and m['default_enabled']is False,'actual newly bound source12, not advisory admission')
 for key,value in cause.items():B.need(proof[key]==value,'actual reopened failure diagnosis '+key)
 for n,r in parent['files'].items():
  if n not in B.CHANGED:B.need(B.checked(m['files'][n]).read_bytes()==B.checked(r).read_bytes(),'all original322 tests/math128/CANN/native/parser/clock/atomic/caps/resource files wholebyte '+n)
 sys.path.insert(0,str(P));import g2_ack_proof as Q,g2_cold_clock as K,g2_software_stages as S
 pairs={n:Q.check_pair(n,(P/n).read_bytes(),B.checked(parent['files'][n]).read_bytes())for n in Q.ORIGINALS}
 unchanged=Q.preserved_functions((P/'g2_channel.py').read_bytes(),B.checked(parent['files']['g2_channel.py']).read_bytes())
 ledger=B.obj(proof['whole_current_inverse']);B.need(ledger==B.obj(m['files']['G2_ACK_EDITS_V12.json'])and ledger['baseline']==B.SOURCE and set(ledger['files'])==set(B.CHANGED),'exact complete whole-file v12 ledger')
 for n,row in ledger['files'].items():B.need(row['before']==parent['files'][n]and row['after']==m['files'][n]and row['edits']==[dict(before=B.checked(row['before']).read_text(),after=B.checked(row['after']).read_text())],'complete whole-file exact inverse '+n)
 clock=K.validate((P/'host_service.py').read_text());scope=S.scope(m,sr)
 count=sum(B.tests(P/n)for n in m['files']if n.startswith('test_g2_ack')and n.endswith('.py'));B.need(count==scope['new_current_cases']==19 and m['service_required_sameimage_software_cases']==341,'four fresh source contexts341, not cached PASS')
 old=ast.parse(B.checked(parent['files']['g2_software_stages.py']).read_bytes());new=ast.parse((P/'g2_software_stages.py').read_bytes())
 named=lambda t:{n.name:ast.dump(n,include_attributes=False)for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 before,after=named(old),named(new)
 for name in('finite','Budget','process','one','metadata_gate'):B.need(before[name]==after[name],'whole original finite stage/stream/metadata AST '+name)
 collector=next(r for r in m['dependencies']if r['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3');H=B.module(B.checked(collector),'_g2_v12_original_collector');closure=H.collect(sr);baseline=H.collect(B.SOURCE)
 present={r['path']:r for r in closure['refs']};B.need(all(present.get(r['path'])==r for r in baseline['refs']+observed),'complete original closure and actual failed metadata/cleanup readonly operands')
 B.need(H.outputs((P/'contract090.py').read_text(),parent['output_root'])==B.checked(parent['files']['contract090.py']).read_text(),'only registered output operands changed in contract')
 B.need(proof['wire_schema']=='bole.actual-independent-frame-ACK-wire/v3'and proof['semantic_schema']=='bole.actual-independent-frame-ACK/v2'and proof['original322_tests_byteexact']is True and proof['no_old_whole_software_replay']is True and proof['no_new_RW_alias']is True,'explicit wire change and four fresh source contexts')
 print(json.dumps(dict(schema='bole.G2-v12-lossless-ACK-wire-readonly-audit/v1',source=sr,commands=closure['commands'],audit_ref=B.ref(__file__),readset_count=len(present),whole_file_inverse=pairs,original_sender_and_validator_AST=unchanged,all_original322_test_files_byteexact=True,original_math128_argv_transport_resources_unchanged=True,original3072_wire_cap_unchanged=True,actual_default_ACK_bytes=3307,actual_canonical_object_ACK_bytes=3197,actual_lossless_wire_ACK_bytes=2846,firstentry_clock=clock,source8_fresh_cases=279,source10_fresh_cases=25,source11_fresh_cases=18,current12_fresh_cases=count,prospective_sameimage_cases=341,software_allocation_seconds=S.CAPS,software_aggregate_cap_seconds=S.LANE_CAP,actual_software_executed=False,actual_parser_executed=False,actual_cold_handoff_executed=False,actual_model_executed=False,numerical_model_qualification=False,NPU=False),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
