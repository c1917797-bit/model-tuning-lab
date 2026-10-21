
"""Prepare finite fixed1024 from qualified actual13; no resource execution."""
import argparse,ast,copy,hashlib,importlib.util,json,re,shutil,subprocess,sys
from pathlib import Path
BASE=Path('/opt/host/vnf/austinov')
T=BASE/'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
ROOT13=BASE/'bole-g2-stream-smoke4-20261020T154710Z-v13'
SOURCE13=dict(path=str(ROOT13/'SOURCE_BOUND.json'),bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
LAYER=dict(path=str(T/'g3_source13_layer_v4/LAYER_MANIFEST.json'),bytes=6914,sha256='c9d6f4079ceb6ba81014693af85437bc6ceea026c02fc6ceb564de939d76c57b')
LAYER_INVERSE=dict(path=str(T/'g3_source13_layer_v4/WHOLE_INVERSE.json'),bytes=217663,sha256='b95196606e50fe88c1162db9b58a46fafdc1a2468187acfdf2a6c5eb59ba827d')
COLD_SCHEMA='bole.G3-source13-cold-namespace-and-host-path-layer/v1'
COLD_ORIGINAL_SHA='43fe83203ddbe1394fdead9af54241ed61abad08107f4034f5ee12f3d14c52fb'
REF_MAPS=('runtime_sources','service_runtime_source_snapshots','stream_runtime_sources')
SAFE_MATH=('core112.py','adapter.py','oracle112.py','native_seams.py','treeconv118.py','independent_model.py','model_entry.py','service_bridge.py','model_process_calibration.py','model_calibration131r12.py','calibrate_conv118.py','transaction.py','eligibility.py')
HOST_HOOK=("m=C.source(sr);import g3_validate as G3V;C.need(C.ref(G3V.__file__)==m['files']['g3_validate.py'],'current complete G3 source gate');"
 "_g3_source_proof=G3V.validate(sr);C.need(type(_g3_source_proof)is dict and _g3_source_proof['schema']=='bole.G3-fixed131-long1024-source-validation/v1' and _g3_source_proof['source']==sr and _g3_source_proof['source_validated']is True,'full current G3 source validation')")
TESTS=tuple('test_g3_'+n+'.py'for n in('budget','client','coverage','domain','lifecycle','parent','prepare','tensor_operands'))
def need(v,s):
 if not v:raise ValueError(s)
def typed(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and Path(r['path']).is_absolute()and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'exact typed absolute Ref3');return r
def ordinary_ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'actual ordinary file without symlink')
 a=p.stat();h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for block in iter(lambda:f.read(2**20),b''):h.update(block);n+=len(block)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable full file read')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def obj(r):typed(r);need(ordinary_ref(r['path'])==r,'actual full Ref3');return json.loads(Path(r['path']).read_bytes())
def portable_inventory(overlay,name,advisory):
 need(type(name)is str and Path(name).name==name and name not in('.','..'),'flat packet name');typed(advisory)
 need(Path(advisory['path']).name==name,'advisory filename; original path is lineage only')
 actual=ordinary_ref(Path(overlay)/name);need(all(actual[k]==advisory[k]for k in('bytes','sha256')),'reviewed portable bytes '+name);return actual
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
def unique(refs):
 result={}
 for r in refs:
  typed(r);need(ordinary_ref(r['path'])==r,'complete exact prerequisite');need(r['path']not in result or result[r['path']]==r,'no conflicting prerequisite path');result[r['path']]=r
 return list(result.values())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def replace_copied(p,v):
 if Path(p).exists():Path(p).unlink()
 write(p,v)
def same(a,b):return Path(a['path']).read_bytes()==Path(b['path']).read_bytes()
def once(text,old,new):need(text.count(old)==1,'one exact source anchor '+old);return text.replace(old,new,1)
def two_hook_host(layer):
 text=Path(layer['files']['host_service.py']['path']).read_text()
 return once(once(text,'g2_software_stages','g3_software_stages'),'m=C.source(sr)',HOST_HOOK)
def output_bind(text,out):
 for key,value in(('OUTPUT_POSIX',str(out)),('CPU_OUTPUT_POSIX',str(out)+'-CPU')):
  nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==key]
  need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and type(nodes[0].value.value)is str,'one output constant '+key)
  old=ast.get_source_segment(text,nodes[0]);text=once(text,old,key+'='+repr(value))
 return text
def cold_derivation(original,derived,proof):
 need(len(original.encode())==3692 and hashlib.sha256(original.encode()).hexdigest()==COLD_ORIGINAL_SHA,'actual13 original cold whole bytes')
 need(proof['schema']=='bole.exact-G3-isolated-saved-cold-derivation/v1'and proof['baseline_whole_bytes']==3692 and proof['baseline_whole_sha256']==COLD_ORIGINAL_SHA and proof['before']==original and proof['after']==derived,'exact reviewed cold derivation operands')
 for key in('whole_text_inverse','whole_AST_inverse','original_two_function_calls_preserved','original_guard_semantics_preserved'):need(proof[key]is True,'required cold derivation predicate '+key)
 need(proof['production_handoff_changed']is False and proof['software_protocol_changed']is False,'no production handoff/software protocol rewrite')
 edits=proof['edits'];need(type(edits)is list and len(edits)==4,'exact four reviewed cold edits')
 def main_tree(text):
  tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main'];need(len(nodes)==1,'one original main')
  lines=text.splitlines(keepends=True);lo=sum(map(len,lines[:nodes[0].lineno-1]));hi=sum(map(len,lines[:nodes[0].end_lineno]))
  nodes[0].body=[ast.Pass()];return ast.dump(tree,include_attributes=False),lo,hi
 masked,lo,hi=main_tree(original);current_mask,_,_=main_tree(derived)
 need(masked==current_mask,'all module AST outside cold main remains original, including load/imports/bootstrap/guard')
 ordered=sorted(edits,key=lambda r:r['start']);last=lo;rebuilt=original
 for row in ordered:
  need(set(row)=={'start','end','before','after'}and type(row['start'])is int and type(row['end'])is int and type(row['before'])is str and type(row['after'])is str,'typed narrow edit')
  a,z=row['start'],row['end'];need(last<=a<z<=hi and original[a:z]==row['before']and original.count(row['before'])==1,'four exact nonoverlapping unique main-only anchors');last=z
 for row in reversed(ordered):rebuilt=rebuilt[:row['start']]+row['after']+rebuilt[row['end']:]
 need(rebuilt==derived,'rerun four forward edits exactly equals actual new cold')
 shift=0;positions=[]
 for row in ordered:
  a=row['start']+shift;z=a+len(row['after']);need(derived[a:z]==row['after'],'exact inverse interval');positions.append((a,z,row['before']));shift+=len(row['after'])-(row['end']-row['start'])
 restored=derived
 for a,z,value in reversed(positions):restored=restored[:a]+value+restored[z:]
 need(restored==original and ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(original),include_attributes=False),'recomputed full text and AST inverse')
 return dict(edits=4,forward_equal=True,whole_text_inverse=True,whole_AST_inverse=True,outside_main_AST_unchanged=True)
def verify_cold(parent,files,cold_ref,layer):
 data=obj(cold_ref);need(data['schema']==COLD_SCHEMA and data['baseline_source']==SOURCE13 and data['runtime_layer_manifest']==LAYER,'exact source13 cold layer')
 inputs=data['reviewed_inputs'];need(set(inputs)=={'namespace_ref','helper_ref','derivation_ref','module_manifest_ref'},'four explicit reviewed cold CLI operands')
 for r in inputs.values():typed(r);need(ordinary_ref(r['path'])==r,'whole reviewed cold input')
 modules=obj(inputs['module_manifest_ref'])
 need(modules['schema']=='bole.G3-source13-isolated-cold-modules/v1'and modules['baseline_source']==SOURCE13 and all(modules[k]==inputs[k]for k in('namespace_ref','helper_ref','derivation_ref')),'standalone cold modules exact canonical group; no host cycle')
 refs=[cold_ref,*inputs.values()]
 need(set(modules['files'])=={'g3_cold_namespace.py','g3_handoff_cold.py','COLD_DERIVATION.json'}and modules['files']['g3_cold_namespace.py']==inputs['namespace_ref']and modules['files']['g3_handoff_cold.py']==inputs['helper_ref']and modules['files']['COLD_DERIVATION.json']==inputs['derivation_ref'],'standalone exact role/file binding')
 nr=modules['namespace_input_ref'];typed(nr);need(ordinary_ref(nr['path'])==nr and same(nr,inputs['namespace_ref']),'whole reviewed namespace input copied exactly');refs.append(nr)
 hp=modules['host_patch']
 need(hp['function']=='patch_host_cold'and hp['before_context']=='reviewed host output after G3 stager and validator hooks'and hp['old_literal']=='g2_handoff_cold.py'and hp['new_literal']=='g3_handoff_cold.py'and hp['unique_AST_constant']is True and hp['host_not_yet_patched']is True,'standalone planned host operation only, no back-link')
 typed(hp['implementation_ref']);need(ordinary_ref(hp['implementation_ref']['path'])==hp['implementation_ref'],'complete host patch implementation lineage');refs.append(hp['implementation_ref'])
 need(modules['baseline_cold_ref']==parent['files']['g2_handoff_cold.py'],'standalone original cold is exact actual13')
 for r in[modules['actual_preparer_ref'],*modules['files'].values()]:
  typed(r);need(ordinary_ref(r['path'])==r,'complete standalone cold preparation lineage');refs.append(r)
 for name in('g2_handoff.py','g2_handoff_cold.py','g2_cold_clock.py'):
  need(ordinary_ref(files[name]['path'])==files[name]and same(files[name],parent['files'][name]),'original production/cold/clock whole bytes '+name);refs.append(parent['files'][name])
 for name,key in(('g3_cold_namespace.py','namespace_ref'),('g3_handoff_cold.py','helper_ref')):
  row=data['files'][name];need(ordinary_ref(files[name]['path'])==files[name]and row['after']==inputs[key]and ordinary_ref(row['after']['path'])==row['after']and same(files[name],row['after']),'exact reviewed new cold module '+name)
  refs.append(row['after'])
 ns=Path(inputs['namespace_ref']['path']).read_text()
 need('bole.explicit-G3-saved-v7-metadata-namespace/v1'in{n.value for n in ast.walk(ast.parse(ns))if isinstance(n,ast.Constant)and type(n.value)is str},'explicit saved-v7 five-module namespace protocol')
 original=Path(parent['files']['g2_handoff_cold.py']['path']).read_text();derived=Path(inputs['helper_ref']['path']).read_text()
 row=data['files']['g3_handoff_cold.py']
 need(row['before']==parent['files']['g2_handoff_cold.py']and row['edits']==[dict(before=original,after=derived)],'full cold whole-file inverse to actual13')
 nr=data['files']['g3_cold_namespace.py'];need(nr['before']is None and nr['source']==ns,'complete newly added namespace source')
 detail=cold_derivation(original,derived,obj(inputs['derivation_ref']))
 host=data['host'];before=host['before'];after=host['after']
 need(ordinary_ref(before['path'])==before and ordinary_ref(after['path'])==after,'whole host path operands');refs.extend((before,after))
 oldhost=Path(before['path']).read_text();newhost=Path(after['path']).read_text()
 need(sum(isinstance(n,ast.Constant)and n.value=='g2_handoff_cold.py'for n in ast.walk(ast.parse(oldhost)))==1 and sum(isinstance(n,ast.Constant)and n.value=='g3_handoff_cold.py'for n in ast.walk(ast.parse(newhost)))==1,'one real host AST filename constant')
 need(oldhost==two_hook_host(layer),'host cold inverse starts at exact already-reviewed two-hook host')
 need(newhost==once(oldhost,"str(P/'g2_handoff_cold.py')","str(P/'g3_handoff_cold.py')")and same(files['host_service.py'],after),'only host cold script path changes')
 need(host['edits']==[dict(before=oldhost,after=newhost)],'complete host path whole inverse')
 need(same(files['G3_HOST_BEFORE_COLD.txt'],before),'complete host before archive is source-owned')
 return dict(schema=COLD_SCHEMA,layer=cold_ref,namespace=files['g3_cold_namespace.py'],helper=files['g3_handoff_cold.py'],derivation=inputs['derivation_ref'],host_before=before,host_after=files['host_service.py'],production_handoff_unchanged=True,software_protocol_unchanged=True,derivation_recomputed=detail,NPU=False),refs
def packet_semantics(parent,overlay,layer,cold_ref):
 expected=two_hook_host(layer);expected=once(expected,"str(P/'g2_handoff_cold.py')","str(P/'g3_handoff_cold.py')")
 need((overlay/'host_service.py').read_text()==expected,'host only stager/fullV hooks then exact cold-script path')
 original=Path(parent['files']['service_entry.py']['path']).read_text()
 expected=once(once(original,'g2_validate','g3_validate'),'g2_software_stages','g3_software_stages')
 need((overlay/'service_entry.py').read_text()==expected,'only current audit/stage entry imports')
 original=Path(parent['files']['command_contract.py']['path']).read_text()
 need(original.count('G2_stream_protocol')>0 and original.count('actual_G2_execution_claimed')>0,'original command keys')
 expected=original.replace('G2_stream_protocol','G3_stream_protocol').replace('actual_G2_execution_claimed','actual_G3_execution_claimed')
 need((overlay/'command_contract.py').read_text()==expected,'only command protocol keys change')
 original=Path(parent['files']['contract090.py']['path']).read_text()
 need((overlay/'contract090.py').read_text()==once(original,'HTTP_tree_request_count=2','HTTP_tree_request_count=1'),'only workload request count changes before binding')
 for name,r in layer['files'].items():
  if name!='host_service.py':need((overlay/name).read_bytes()==Path(r['path']).read_bytes(),'complete reviewed layer actor '+name)
 for name in('sourceio.py','g2_consumer.py','g2_cold_clock.py','g2_handoff_cold.py'):
  need((overlay/name).read_bytes()==Path(parent['files'][name]['path']).read_bytes(),'whole original support/consumer '+name)
 current=dict(parent['files']);current.update({f.name:ordinary_ref(f)for f in overlay.iterdir()if f.is_file()})
 return verify_cold(parent,current,cold_ref,layer)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json','advisory-manifest-ref','parent-source-audit-ref','cold-handoff-layer-ref'):p.add_argument('--'+key)
 for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
 a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(all(v is not None for k,v in vars(a).items()if k!='execute'),'all explicit actual operands and fresh leaves required')
 ps=json.loads(a.parent_source_ref);need(ps==SOURCE13,'only successful actual source13 baseline');parent=obj(ps)
 need(parent['root']==str(ROOT13),'actual baseline root')
 for name,r in parent['files'].items():need(Path(r['path'])==ROOT13/name and ordinary_ref(r['path'])==r,'source13 owned helper '+name)
 advisory=json.loads(a.advisory_manifest_ref);need(advisory==ordinary_ref(a.overlay/'MANIFEST.json'),'exact externally reviewed packet MANIFEST')
 manifest=obj(advisory);need(manifest['schema']=='bole.G3-source13-fixed1024-rebuild-packet/v2'and manifest['baseline_source']==ps,'explicit cold-integrated packet version')
 names=manifest['overlay_files'];need(type(names)is list and len(names)==len(set(names))and'MANIFEST.json'in names,'complete unique packet files')
 actual={}
 for name in names:
  need(type(name)is str and Path(name).name==name and name not in('.','..'),'flat packet file')
  actual[name]=advisory if name=='MANIFEST.json'else portable_inventory(a.overlay,name,manifest['inventory'][name])
  if name.endswith('.py'):compile((a.overlay/name).read_bytes(),str(a.overlay/name),'exec')
 required={'sourceio.py','g2_consumer.py','g2_cold_clock.py','g2_handoff_cold.py','g3_parent.py','g3_validate.py','g3_readset.py','g3_budget.py','g3_software_stages.py','g3_exact_controls.py','prepare_g3.py','contract090.py','command_contract.py','service_entry.py','g3_cold_namespace.py','g3_handoff_cold.py','G3_COLD_LAYER.json','G3_HOST_BEFORE_COLD.txt','G3_FIXTURE_EDITS_V1.json'}
 need(required<=set(names),'complete current source/cold/fixture packet')
 need(actual['prepare_g3.py']==ordinary_ref(Path(__file__).absolute()),'executing exact reviewed portable builder')
 need((a.overlay/'sourceio.py').read_bytes()==Path(parent['files']['sourceio.py']['path']).read_bytes(),'unchanged generic sourceio')
 cold_ref=json.loads(a.cold_handoff_layer_ref)
 need(cold_ref==manifest['cold_handoff_layer']==actual['G3_COLD_LAYER.json'],'explicit actual combined cold layer, no implicit fallback')
 C=module('sourceio',Path(parent['files']['sourceio.py']['path']));sys.path.insert(0,str(a.overlay))
 PARENT=module('g3_parent',a.overlay/'g3_parent.py')
 need(manifest['required_actual_G2_refs']==PARENT.ACTUAL,'all actual source/result/Q/unit/helper pins')
 po=json.loads(a.parent_owner_result_ref);pq=json.loads(a.parent_qualification_ref);pa=json.loads(a.parent_source_audit_ref)
 parentproof=PARENT.actual_qualified(ps,parent,po,pq,source_audit_ref=pa)
 layer=obj(LAYER);obj(LAYER_INVERSE)
 need(layer['baseline_source']==ps and layer['whole_inverse']==LAYER_INVERSE and len(layer['files'])==17,'actual source13 layer4')
 for r in layer['files'].values():need(ordinary_ref(r['path'])==r,'exact reviewed runtime layer source')
 need(set(layer['files'])<=set(names),'all17 runtime/domain actors supplied')
 coldproof,coldrefs=packet_semantics(parent,a.overlay,layer,cold_ref)
 G2=module('g2_contract',a.overlay/'g2_contract.py');BUDGET=module('g3_budget',a.overlay/'g3_budget.py');READSET=module('g3_readset',a.overlay/'g3_readset.py')
 EP=module('g2_executor_proof',Path(parent['files']['g2_executor_proof.py']['path']))
 consumer=json.loads(a.consumer_source_ref);need(consumer==actual['g2_consumer.py'],'explicit separately reviewed whole consumer')
 executors=json.loads(a.executor_sources_json)
 need(set(executors)=={'multiproc_executor','worker_base','ascend_worker','ompmultiprocessing','cpu_binding','ascend_config'}and executors==parent['stream_executor_sources'],'same complete native launcher/source/image route')
 for r in executors.values():need(ordinary_ref(r['path'])==r,'exact native launcher');compile(Path(r['path']).read_bytes(),r['path'],'exec')
 executor_proof=EP.consume(executors)
 need(executor_proof==parent['stream_executor_proof']and EP.installed(executors)==parent['stream_runtime_sources'],'unchanged installed launcher proof')
 old=ROOT13;new,out=a.new_root,a.output_root
 need(new.is_absolute()and out.is_absolute()and new.parent==out.parent==BASE and new.name.startswith('bole-g3-fixed1024-')and out.name=='run-'+new.name and not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),'new independent source/model/CPU leaves')
 parent_readset=READSET.collect(ps)['refs']
 shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
 (new/'SOURCE_BOUND.json').rename(new/'PARENT_G2_SOURCE_BOUND.json')
 for name in('COMMANDS.json',parent['command_scope']['compatibility_file']):(new/name).rename(new/('PARENT_G2_'+name))
 for name in names:shutil.copyfile(a.overlay/name,new/name)
 before=actual['contract090.py'];(new/'contract090.py').write_text(output_bind((new/'contract090.py').read_text(),out))
 binding=dict(schema='bole.G3-exact-output-binding-inverse/v1',files={'contract090.py':dict(before=before,after=ordinary_ref(new/'contract090.py'),edits=[dict(before=Path(before['path']).read_text(),after=(new/'contract090.py').read_text())])})
 replace_copied(new/'G3_BINDING_EDITS_V1.json',binding)
 allowed=set(layer['files'])|{'contract090.py','command_contract.py','service_entry.py','README.md','MANIFEST.json'}
 for name in parent['files']:
  if name not in allowed:need((new/name).read_bytes()==(old/name).read_bytes(),'every other original file wholebyte, including stream owner/cold/transport '+name)
 for name in SAFE_MATH:need((new/name).read_bytes()==(old/name).read_bytes(),'whole original numerical/ownership/calibration '+name)
 delta={}
 for name,r in parent['files'].items():
  after=ordinary_ref(new/name)
  if Path(r['path']).read_bytes()!=(new/name).read_bytes():delta[name]=dict(before=r,after=after,edits=[dict(before=Path(r['path']).read_text(),after=(new/name).read_text())])
 replace_copied(new/'G3_LONG_EDITS_V1.json',dict(schema='bole.exact-G3-source13-whole-file-inverse/v1',baseline=ps,files=delta,original_math_and_128_destination_transaction_preserved=True,original_phase_cleanup_cutoff_preserved=True,actual_G3_execution_claimed=False))
 m=copy.deepcopy(parent);m.update(root=str(new),output_root=str(out),model_receipt_root=str(out/'dense/receipts'),prepared_only=True,default_enabled=False,service_experiment=G2.SCOPE);m.pop('prepared_template',None)
 m['files']={name:ordinary_ref(new/name)for name in parent['files']}
 for name in names:m['files'][name]=ordinary_ref(new/name)
 for name in('G3_LONG_EDITS_V1.json','G3_BINDING_EDITS_V1.json'):m['files'][name]=ordinary_ref(new/name)
 def rebound(r):
  path=Path(r['path']);return ordinary_ref(new/path.relative_to(old))if path.is_relative_to(old)else r
 for key in REF_MAPS:m[key]={k:rebound(r)for k,r in parent.get(key,{}).items()}
 history=sorted({k for k in parent if k.startswith('g2_')}|{k for k in('g1_overlay','g1_repair_v2_overlay')if k in parent})
 for key in history:need(m[key]==parent[key],'original historical authority unchanged '+key)
 prior=dict(source=ps,owner_result=po,qualification=pq,source_audit=pa)
 m['g3_predecessor']=prior;m['g3_overlay']={name:m['files'][name]for name in names}
 m['profile']=dict(parent['profile'],HTTP_output_tokens=1024,HTTP_tree_request_count=1)
 m['service_activation']=dict(parent['service_activation'],enable_environment=G2.FLAG,request_count=1,monotonic_generations=[1],first_request_only=True,slot_reuse_must_be_observed=False,reuse_observation_required=False,capture_protocol=G2.SCOPE['capture_protocol'],model_ready=False,actual_scheduler_executed=False)
 m['stream_channel_root']=str(out/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(out/'dense/receipts/STREAM/CHANNEL.json')
 m['stream_consumer_source']=m['files']['g2_consumer.py'];m['reviewed_stream_consumer']=consumer
 m['stream_executor_sources']=executors;m['stream_executor_proof']=executor_proof
 m['stream_resource_profile']=copy.deepcopy(parent['stream_resource_profile'])
 if 'stream_CPU_binding_override'in parent:m['stream_CPU_binding_override']=copy.deepcopy(parent['stream_CPU_binding_override'])
 m['stream_metadata_reservation']=BUDGET.reservation()
 m['stream_long_time_budget']=dict(owner_phase=3600,shared_cleanup=180,client_cap=3000,HTTP_request_timeout=2400,formal_timing=False)
 m['stream_raw_success_replay_available']=False;m['stream_timing_is_formal']=False
 m['stream_capacity_scope']=dict(initial_physical_block_tokens=1536,real_sequence_growth=True,physical_allocation_growth_proven=False,task_total_capacity_required=5199,task_capacity_proven=False,normal_EOS_qualified=False,native_AR_token_identity_compared=False)
 oldscope=parent['service_software_scope']
 m['service_software_scope']=dict(schema='bole.G3-five-source-staged-software-scope/v1',parent_source=oldscope['parent_source'],parent_exact_cases=279,controls_source=oldscope['controls_source'],controls_source_cases=25,historical_stage_source=oldscope['historical_stage_source'],historical_stage_cases=18,historical_ACK_source=ps,historical_ACK_cases=27,historical_runner_ref=parent['files']['g2_exact_controls.py'],parent_suite_runs_in_separate_exact_source_process=True,controls_run_only_tests_in_exact_source_process=True,current_pattern='test_g3_*.py',new_current_cases=32,allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300.)
 current_tests=sorted(n for n in names if n.startswith('test_g3_')and n.endswith('.py'));need(current_tests==sorted(TESTS),'all original eight fixture modules')
 methods=[(name,n.name)for name in current_tests for n in ast.walk(ast.parse((new/name).read_bytes()))if isinstance(n,ast.FunctionDef)and n.name.startswith('test_')]
 need(len(methods)==32 and len(set(methods))==32,'exact32 current methods enumerated, not execution')
 m['service_required_sameimage_software_cases']=381
 fixture=obj(actual['G3_FIXTURE_EDITS_V1.json']);need(fixture['schema']=='bole.G3-original32-fixture-rebase/v1'and fixture['baseline_source']==ps and set(fixture['files'])==set(current_tests),'complete original32 fixture inverse')
 fixture_refs=[fixture['donor_manifest'],*[r[k]for r in fixture['files'].values()for k in('before','after')]]
 m['g3_source_descriptor']=dict(schema='bole.G3-source13-rebuild-descriptor/v2',baseline_source=ps,runtime_layer_manifest=LAYER,runtime_layer_inverse=LAYER_INVERSE,current_ref_maps=list(REF_MAPS),preserved_parent_fields=history,post_layer_files=['host_service.py'],whole_inverse=m['files']['G3_LONG_EDITS_V1.json'],binding_inverse=m['files']['G3_BINDING_EDITS_V1.json'],advisory_manifest=advisory,actual_overlay_files=actual,cold_handoff_layer=cold_ref,finite_diagnostic_only=True,predicted_fits=None,observed_fit=None,original_G2_metadata_qualification=pq,current_G3_model_qualification=None)
 extras=[ps,po,pq,pa,parent['prepared_template'],ordinary_ref(old/'SOURCE.json'),ordinary_ref(old/'COMMANDS.json'),ordinary_ref(old/parent['command_scope']['compatibility_file']),*parent_readset,*parent['files'].values(),*parentproof['retained_refs'],*executors.values(),consumer,LAYER,LAYER_INVERSE,*layer['files'].values(),advisory,ordinary_ref(Path(__file__).absolute()),*actual.values(),m['files']['G3_LONG_EDITS_V1.json'],m['files']['G3_BINDING_EDITS_V1.json'],*fixture_refs,*coldrefs]
 m['dependencies']=unique([*parent['dependencies'],*extras]);m['command_scope']=dict(parent['command_scope'],compatibility_file='COMMANDS_G3.json')
 for name in('SOURCE_TEMPLATE.json','SOURCE.json'):replace_copied(new/name,m)
 template=ordinary_ref(new/'SOURCE_TEMPLATE.json')
 bind_argv=['/usr/bin/python3','-I','-B',str(new/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(template),'--component-refs-json',json.dumps(parent['component_refs'])]
 b=subprocess.run(bind_argv,capture_output=True,text=True,timeout=30)
 write(new/'G3_PREPARE_BINDING_EXECUTION.json',dict(argv=bind_argv,exit_code=b.returncode,stdout=b.stdout,stderr=b.stderr,NPU=False))
 need(b.returncode==0,'binding failed; complete G3_PREPARE_BINDING_EXECUTION.json retained')
 sr=ordinary_ref(new/'SOURCE_BOUND.json');bound=obj(sr)
 cc=module('_g3_new_command_contract',new/'command_contract.py');historical=obj(m['command_scope']['historical_ref'])
 commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,**cc.expected(str(new),str(out),sr,template,parent['component_refs']),required_sameimage_software_cases=381,historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G3_stream_protocol=True,actual_G3_execution_claimed=False)
 replace_copied(new/'COMMANDS.json',commands)
 replace_copied(new/'COMMANDS_G3.json',dict(source=sr,template=template,commands=ordinary_ref(new/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=381))
 cc.validate(C,sr,bound)
 for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 program="import json,sys\nfrom pathlib import Path\nsr=json.loads(sys.argv[1]);sys.path.insert(0,str(Path(sr['path']).parent))\nimport g3_validate as V\nprint(json.dumps(V.validate(sr),sort_keys=True,allow_nan=False))\n"
 argv=['/usr/bin/python3','-I','-B','-c',program,json.dumps(sr)];q=subprocess.run(argv,capture_output=True,text=True,timeout=180)
 write(new/'G3_PREPARE_SOURCE_AUDIT_EXECUTION.json',dict(argv=argv,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,NPU=False))
 need(q.returncode==0 and q.stderr=='','full source gate failed; complete G3_PREPARE_SOURCE_AUDIT_EXECUTION.json retained')
 gate=json.loads(q.stdout);need(type(gate)is dict and gate['schema']=='bole.G3-fixed131-long1024-source-validation/v1'and gate['source']==sr and gate['source_validated']is True,'complete actual current source validation')
 need(not out.exists()and not Path(str(out)+'-CPU').exists(),'no model/CPU output or resource created by preparation')
 print(json.dumps(dict(source=sr,commands=ordinary_ref(new/'COMMANDS.json'),source_gate=gate,source_audit_execution=ordinary_ref(new/'G3_PREPARE_SOURCE_AUDIT_EXECUTION.json'),binding_execution=ordinary_ref(new/'G3_PREPARE_BINDING_EXECUTION.json'),cold_handoff_layer=cold_ref,enumerated_current_cases=32,prospective_sameimage_cases=381,actual_sameimage_executed=False,actual_scheduler_executed=False,actual_G3_model_executed=False,model_ready=False,formal_success=False,timing_is_formal=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
