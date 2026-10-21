
"""Assemble the source-only cold-integrated actual13 G3 successor packet."""
import argparse,ast,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT13=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13')
def R(p,n,h):return dict(path=str(p),bytes=n,sha256=h)
SR13=R(ROOT13/'SOURCE_BOUND.json',994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
LM=R(T/'g3_source13_layer_v4/LAYER_MANIFEST.json',6914,'c9d6f4079ceb6ba81014693af85437bc6ceea026c02fc6ceb564de939d76c57b')
LI=R(T/'g3_source13_layer_v4/WHOLE_INVERSE.json',217663,'b95196606e50fe88c1162db9b58a46fafdc1a2468187acfdf2a6c5eb59ba827d')
STAGES=R(T/'g3_software_stages_proposal_v1/g3_software_stages.py',10388,'718d5497287c0da57e35e1840fca6fbb0510af891deb7242d43e67b64cac09a5')
CONTROLS=R(T/'g3_software_stages_proposal_v1/g3_exact_controls.py',2525,'4950cd7f562b4db1fd1e693190e3f8d579a32e37c85e1ef23bd5976057c5f69e')
OLD_ARGV=R(T/'g3_long_output_v2/assemble_g3_command.py',1260,'9d501c7d3953c030fffb9ceb82c08d1d84d0d89bf8aa1843178b62f0191ac5f1')
TESTS=tuple('test_g3_'+n+'.py'for n in('budget','client','coverage','domain','lifecycle','parent','prepare','tensor_operands'))
ARGV_TEXT=r'''"""Print an exact source-preparation argv; never execute it."""
import argparse,json
from pathlib import Path
KEYS=('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json','advisory-manifest-ref','parent-source-audit-ref','cold-handoff-layer-ref')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--assemble',action='store_true')
 for key in KEYS:p.add_argument('--'+key)
 for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
 a=p.parse_args()
 if not a.assemble:print('{"enabled":false,"execution_performed":false,"NPU":false}');return 0
 if not all(v is not None for k,v in vars(a).items()if k!='assemble'):raise ValueError('all explicit reviewed actual operands required')
 if not all(getattr(a,k).is_absolute()for k in('overlay','new_root','output_root')):raise ValueError('absolute source/packet/output paths')
 for key in KEYS:json.loads(getattr(a,key.replace('-','_')))
 argv=['/usr/bin/python3','-I','-B',str(a.overlay/'prepare_g3.py'),'--execute']
 for key in KEYS:argv.extend(('--'+key,getattr(a,key.replace('-','_'))))
 for key in('overlay','new-root','output-root'):argv.extend(('--'+key,str(getattr(a,key.replace('-','_')))))
 print(json.dumps(dict(argv=argv,execution_performed=False,actual_G2_qualification_required=True,exact_cold_layer_required=True,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
'''
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact source')
 a=p.stat();b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==z.st_size,'stable complete read')
 return R(p,len(b),hashlib.sha256(b).hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0 and ref(r['path'])==r,'actual exact Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def write(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def text(p,value):
 with p.open('x')as f:f.write(value)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true')
 keys=('parent-module-ref','validator-module-ref','builder-module-ref','fixture-manifest-ref','cold-module-manifest-ref','cold-namespace-ref','cold-helper-ref','cold-derivation-ref')
 for key in keys:p.add_argument('--'+key)
 p.add_argument('--new-packet',type=Path);a=p.parse_args()
 if not a.prepare:print('{"enabled":false,"NPU":false}');return 0
 need(all(v is not None for k,v in vars(a).items()if k!='prepare'),'all exact actual reviewed inputRefs required')
 new=a.new_packet;need(new.is_absolute()and new.parent==T and new.name.startswith('g3_source13_rebuild_packet_')and not new.exists(),'fresh isolated packet leaf')
 parent=obj(SR13);layer=obj(LM);obj(LI);checked(OLD_ARGV)
 need(parent['root']==str(ROOT13)and layer['baseline_source']==SR13 and layer['whole_inverse']==LI and len(layer['files'])==17,'actual source13 and reviewed runtime layer4')
 for name,r in parent['files'].items():need(checked(r)==ROOT13/name,'exact original source-owned file '+name)
 for r in layer['files'].values():checked(r)
 given={key:json.loads(getattr(a,key.replace('-','_')))for key in keys}
 parent_ref=given['parent-module-ref'];validator_ref=given['validator-module-ref'];builder_ref=given['builder-module-ref'];fixture_manifest=given['fixture-manifest-ref']
 cold_inputs=dict(namespace_ref=given['cold-namespace-ref'],helper_ref=given['cold-helper-ref'],derivation_ref=given['cold-derivation-ref'],module_manifest_ref=given['cold-module-manifest-ref'])
 for r in given.values():checked(r)
 for r in(parent_ref,validator_ref,builder_ref,STAGES,CONTROLS,cold_inputs['namespace_ref'],cold_inputs['helper_ref']):compile(checked(r).read_bytes(),r['path'],'exec')
 B=module('_g3_reviewed_prepare_definitions',checked(builder_ref))
 need(B.SOURCE13==SR13 and B.LAYER==LM and B.LAYER_INVERSE==LI,'exact reviewed builder constants')
 modules=obj(cold_inputs['module_manifest_ref'])
 need(modules['schema']=='bole.G3-source13-isolated-cold-modules/v1'and modules['baseline_source']==SR13 and all(modules[k]==cold_inputs[k]for k in('namespace_ref','helper_ref','derivation_ref')),'exact actual standalone cold module group')
 B.cold_derivation(checked(parent['files']['g2_handoff_cold.py']).read_text(),checked(cold_inputs['helper_ref']).read_text(),obj(cold_inputs['derivation_ref']))
 module('sourceio',checked(parent['files']['sourceio.py']));PARENT=module('g3_parent',checked(parent_ref))
 need(PARENT.ACTUAL['source']==SR13,'strict actual13 parent module')
 PARENT.actual_qualified(SR13,parent,PARENT.ACTUAL['owner_result'],PARENT.ACTUAL['qualification'],source_audit_ref=PARENT.ACTUAL['source_audit'])
 fixtures=obj(fixture_manifest)
 need(fixtures['schema']=='bole.G3-original32-fixture-rebase-preparation/v1'and fixtures['baseline_source']==SR13 and fixtures['enumerated_methods']==32 and fixtures['actual_sameimage_executed']is False and set(fixtures['files'])==set(TESTS),'complete source-only original32 fixture layer')
 fproof=obj(fixtures['whole_inverse'])
 need(fproof['schema']=='bole.G3-original32-fixture-rebase/v1'and fproof['baseline_source']==SR13 and set(fproof['files'])==set(TESTS),'complete fixture inverse')
 for name,r in fixtures['files'].items():checked(r);need(fproof['files'][name]['after']==r,'exact fixture postimage');checked(fproof['files'][name]['before'])
 checked(fproof['donor_manifest']);new.mkdir()
 for name,r in layer['files'].items():shutil.copyfile(checked(r),new/name)
 for name in('sourceio.py','g2_consumer.py','g2_cold_clock.py','g2_handoff_cold.py'):shutil.copyfile(checked(parent['files'][name]),new/name)
 origins={'g3_parent.py':parent_ref,'g3_validate.py':validator_ref,'prepare_g3.py':builder_ref,'g3_software_stages.py':STAGES,'g3_exact_controls.py':CONTROLS,'g3_cold_namespace.py':cold_inputs['namespace_ref'],'g3_handoff_cold.py':cold_inputs['helper_ref']}
 for name,r in origins.items():need(not(new/name).exists(),'one reviewed source origin per file '+name);shutil.copyfile(checked(r),new/name)
 host_before=B.two_hook_host(layer);text(new/'G3_HOST_BEFORE_COLD.txt',host_before)
 host_after=B.once(host_before,"str(P/'g2_handoff_cold.py')","str(P/'g3_handoff_cold.py')");(new/'host_service.py').write_text(host_after)
 entry=checked(parent['files']['service_entry.py']).read_text();entry=B.once(B.once(entry,'g2_validate','g3_validate'),'g2_software_stages','g3_software_stages');text(new/'service_entry.py',entry)
 contract=B.once(checked(parent['files']['contract090.py']).read_text(),'HTTP_tree_request_count=2','HTTP_tree_request_count=1');text(new/'contract090.py',contract)
 commands=checked(parent['files']['command_contract.py']).read_text()
 need(commands.count('G2_stream_protocol')>0 and commands.count('actual_G2_execution_claimed')>0,'original command protocol keys')
 commands=commands.replace('G2_stream_protocol','G3_stream_protocol').replace('actual_G2_execution_claimed','actual_G3_execution_claimed');text(new/'command_contract.py',commands)
 for name,r in fixtures['files'].items():shutil.copyfile(checked(r),new/name)
 shutil.copyfile(checked(fixtures['whole_inverse']),new/'G3_FIXTURE_EDITS_V1.json')
 original_cold=checked(parent['files']['g2_handoff_cold.py']).read_text();derived_cold=checked(cold_inputs['helper_ref']).read_text();namespace=checked(cold_inputs['namespace_ref']).read_text()
 combined=dict(schema=B.COLD_SCHEMA,baseline_source=SR13,runtime_layer_manifest=LM,reviewed_inputs=cold_inputs,
  files={'g3_cold_namespace.py':dict(before=None,after=cold_inputs['namespace_ref'],source=namespace),
   'g3_handoff_cold.py':dict(before=parent['files']['g2_handoff_cold.py'],after=cold_inputs['helper_ref'],edits=[dict(before=original_cold,after=derived_cold)])},
  host=dict(before=ref(new/'G3_HOST_BEFORE_COLD.txt'),after=ref(new/'host_service.py'),edits=[dict(before=host_before,after=host_after)]),
  production_handoff_changed=False,software_protocol_changed=False,actual_sameimage_executed=False,actual_model_executed=False,NPU=False)
 write(new/'G3_COLD_LAYER.json',combined);cold_ref=ref(new/'G3_COLD_LAYER.json');coldproof,coldrefs=B.packet_semantics(parent,new,layer,cold_ref)
 for name in TESTS:need((new/name).read_bytes()==checked(fixtures['files'][name]).read_bytes(),'whole exact fixture postimage '+name)
 methods=[(name,n.name)for name in TESTS for n in ast.walk(ast.parse((new/name).read_bytes()))if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')]
 need(len(methods)==32 and len(set(methods))==32,'all32 methods enumerated without execution')
 text(new/'assemble_g3_command.py',ARGV_TEXT)
 text(new/'README.md','Source-only actual13 successor: fixed prefix131,1024 outputs, independent ACK/oracle every frame.\n'
  'TP4/common CPU/image/options and original3600+180/cutoff/raw1GiB/metadata64MiB remain.\n'
  'Predicted fit is unknown; this permits one finite full1024 diagnostic, not a measured fit or performance claim.\n'
  'Fresh381=old8 whole279+old10 pure25+old11 pure18+readonly13 ACK/HTTP27+current32.\n'
  'Actual13 successful full metadata qualification is reopened independently; it is not a current G3 result.\n'
  'Cold namespace modules are prepared first; combined cold+host ledger binds their exact CLI Refs.\n'
  'prepare_g3.py default OFF additionally requires exact --cold-handoff-layer-ref; outputs must remain fresh.\n')
 for f in new.glob('*.py'):compile(f.read_bytes(),str(f),'exec')
 inventory={f.name:ref(f)for f in sorted(new.iterdir())if f.is_file()}
 inputs=dict(given,source13=SR13,layer4=LM,layer4_inverse=LI,stages=STAGES,controls=CONTROLS,original_argv_helper=OLD_ARGV,fixture_inverse=fixtures['whole_inverse'])
 manifest=dict(schema='bole.G3-source13-fixed1024-rebuild-packet/v2',baseline_source=SR13,required_actual_G2_refs=PARENT.ACTUAL,runtime_layer_manifest=LM,runtime_layer_inverse=LI,cold_handoff_layer=cold_ref,overlay_files=[*inventory,'MANIFEST.json'],inventory=inventory,preparation_inputs=inputs,historical_sources_keep_original_paths=True,current_binding_only_two_output_constants=True,original32_fixture_inverse=ref(new/'G3_FIXTURE_EDITS_V1.json'),enumerated_current_methods=32,prospective_sameimage_cases=381,predicted_fits=None,observed_fit=None,actual_sameimage_executed=False,actual_G3_model_executed=False,default_enabled=False,formal_success=False,timing_is_formal=False,model_ready=False,NPU=False)
 write(new/'MANIFEST.json',manifest)
 print(json.dumps(dict(manifest=ref(new/'MANIFEST.json'),files=len(manifest['overlay_files']),cold_handoff_layer=cold_ref,fixture_inverse=manifest['original32_fixture_inverse'],cold_inverse_recomputed=coldproof['derivation_recomputed'],enumerated_current_methods=32,prospective_sameimage_cases=381,actual_sameimage_executed=False,actual_G3_model_executed=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
