"""Full fixed131/1024 source gate; never a new G3 mathematical qualification."""
import ast,json
from pathlib import Path
import sourceio as C
import g2_contract as G2
import g3_parent as PARENT
import g3_readset as READSET
import g3_budget as BUDGET
REF_MAPS=('runtime_sources','service_runtime_source_snapshots','stream_runtime_sources')
ENTRYPOINTS=('host_service.py','service_entry.py','g3_software_stages.py')
SAFE_MATH=('core112.py','adapter.py','oracle112.py','native_seams.py','treeconv118.py','independent_model.py','model_entry.py','service_bridge.py','model_process_calibration.py','model_calibration131r12.py','calibrate_conv118.py','transaction.py','eligibility.py')
LAYER=PARENT.R(PARENT.T/'g3_source13_layer_v4/LAYER_MANIFEST.json',6914,'c9d6f4079ceb6ba81014693af85437bc6ceea026c02fc6ceb564de939d76c57b')
LAYER_INVERSE=PARENT.R(PARENT.T/'g3_source13_layer_v4/WHOLE_INVERSE.json',217663,'b95196606e50fe88c1162db9b58a46fafdc1a2468187acfdf2a6c5eb59ba827d')
SCOPE=dict(schema='bole.c1-single-request-fixed1024-stream-service/v3',profile='fixed1024',prefix=131,request_count=1,max_steps_per_request=1023,max_output_tokens=1024,capture_protocol='every-frame-independent-CPU-ACK/v1')
def same_bytes(a,b):return C.checked(a).read_bytes()==C.checked(b).read_bytes()
def history_fields(parent):return sorted({k for k in parent if k.startswith('g2_')}|{k for k in('g1_overlay','g1_repair_v2_overlay')if k in parent})
def source_hooks(m):
 rows={}
 for name in ENTRYPOINTS:
  text=C.checked(m['files'][name]).read_text();tree=ast.parse(text);aliases=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):
    for a in n.names:
     if a.name=='g3_validate':aliases.append(a.asname or a.name)
  calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='validate'and isinstance(n.func.value,ast.Name)and n.func.value.id in aliases and len(n.args)==1 and isinstance(n.args[0],ast.Name)and n.args[0].id=='sr'and not n.keywords]
  C.need(aliases and len(calls)==1,'one explicit current full-source gate in '+name)
  rows[name]=dict(source=m['files'][name],validator_aliases=aliases,validation_calls=1)
 r=m['files']['g2_cold_clock.py'];C.need(r['bytes']==3942 and r['sha256']=='16d34037defad4901c2b9904995f074d6ed80e615591ddc031cd8dc085f2177f','whole original firstentry clock implementation')
 return rows
def validate(sr):
 PARENT.typed(sr);m=C.obj(sr);root=Path(m['root'])
 C.need(root==Path(sr['path']).parent==Path(__file__).resolve().parent and C.ref(__file__)==m['files']['g3_validate.py'],'exact current source-owned validator/root')
 for name,mod in(('sourceio.py',C),('g2_contract.py',G2),('g3_parent.py',PARENT),('g3_readset.py',READSET),('g3_budget.py',BUDGET)):
  C.need(C.ref(mod.__file__)==m['files'][name],'current source-owned imported validation helper '+name)
 C.need(m['prepared_only']is False and m['default_enabled']is False and m['service_experiment']==SCOPE==G2.SCOPE and G2.FLAG=='BOLE_G3_STREAM_ENABLE','explicit defaultOFF single fixed1024 scope')
 C.need(m['profile']==dict(input_tokens=131,tree_nodes=3,HTTP_output_tokens=1024,HTTP_tree_request_count=1,retirement_barrier_output_tokens=1,concurrency=1,max_model_len=4096,max_num_batched_tokens=4096,max_num_seqs=1,prefix_cache=False,async_scheduling=False,enforce_eager=True,mamba_cache_mode='none'),'one unchanged fixed-input/image diagnostic workload')
 C.need(m['native_speculative_config']==dict(method='mtp',num_speculative_tokens=8)and m['cache_memory_config']==dict(gpu_memory_utilization=0.8,kv_cache_memory_bytes=None,num_gpu_blocks_override=None),'original native MTP/common memory options')
 for name,r in m['files'].items():
  PARENT.typed(r);C.need(Path(r['path'])==root/name,'every current file belongs to current owned root');C.checked(r)
 C.need(type(m['dependencies'])is list,'explicit dependency Ref list');current_dependencies={}
 for r in m['dependencies']:
  PARENT.typed(r);C.need(r['path']not in current_dependencies or current_dependencies[r['path']]==r,'no conflicting prerequisite path');C.checked(r);current_dependencies[r['path']]=r
 d=m['g3_source_descriptor'];C.need(d['schema']=='bole.G3-source13-rebuild-descriptor/v1'and d['baseline_source']==PARENT.ACTUAL['source']and d['runtime_layer_manifest']==LAYER and d['runtime_layer_inverse']==LAYER_INVERSE,'new current descriptor separate from historical ledgers')
 prior=m['g3_predecessor'];C.need(set(prior)=={'source','owner_result','qualification','source_audit'},'four actual predecessor Ref operands')
 parent=C.obj(prior['source']);parentproof=PARENT.actual_qualified(prior['source'],parent,prior['owner_result'],prior['qualification'],source_audit_ref=prior['source_audit'])
 C.need(d['current_ref_maps']==list(REF_MAPS)and d['preserved_parent_fields']==history_fields(parent),'explicit current/history domains')
 for key in history_fields(parent):C.need(m[key]==parent[key],'original history authority is unchanged '+key)
 def rebound(r):
  p=Path(r['path']);old=Path(parent['root'])
  return C.ref(root/p.relative_to(old))if p.is_relative_to(old)else r
 for key in REF_MAPS:
  C.need(type(parent.get(key,{}))is dict,'direct source Ref map '+key);expected={k:rebound(r)for k,r in parent.get(key,{}).items()}
  C.need(m.get(key,{})==expected,'only explicit current Ref map rebound '+key)
 C.need(m['stream_consumer_source']==m['files']['g2_consumer.py']and same_bytes(m['stream_consumer_source'],m['reviewed_stream_consumer']),'separately reviewed exact current consumer')
 C.need(same_bytes(m['files']['g2_consumer.py'],parent['files']['g2_consumer.py']),'whole original13 consumer including ACK-v3')
 C.need(Path(m['prepared_template']['path'])==root/'SOURCE_TEMPLATE.json','new prepared template; original parent template stays in dependencies');C.checked(m['prepared_template'])
 for key in('component_refs','actual118c','authority_ref','stream_executor_sources','stream_executor_proof','stream_runtime_sources','stream_resource_profile'):
  if key not in REF_MAPS:C.need(m[key]==parent[key],'unchanged numerical/executor/resource authority '+key)
 for name in SAFE_MATH:C.need(same_bytes(m['files'][name],parent['files'][name]),'original numerical/calibration bytes '+name)
 layer=C.obj(LAYER);C.checked(LAYER_INVERSE)
 C.need(layer['baseline_source']==prior['source']and len(layer['files'])==17 and layer['whole_inverse']==LAYER_INVERSE,'actual reviewed runtime layer4')
 C.need(d['post_layer_files']==['host_service.py'],'only host source/stage hooks follow the runtime layer')
 for name,r in layer['files'].items():
  C.checked(r)
  if name not in d['post_layer_files']:C.need(same_bytes(m['files'][name],r),'all reviewed runtime/domain actors retained '+name)
 proof=C.obj(m['files']['G3_LONG_EDITS_V1.json'])
 C.need(d['whole_inverse']==m['files']['G3_LONG_EDITS_V1.json']and proof['schema']=='bole.exact-G3-source13-whole-file-inverse/v1'and proof['baseline']==prior['source'],'current whole-file inverse to actual13')
 changed={name for name,r in parent['files'].items()if not same_bytes(r,m['files'][name])}
 C.need(set(proof['files'])==changed,'all and only changed predecessor files have whole inverses')
 for name,row in proof['files'].items():
  C.need(row['before']==parent['files'][name]and row['after']==m['files'][name]and row['edits']==[dict(before=C.checked(row['before']).read_text(),after=C.checked(row['after']).read_text())],'complete exact current actor inverse '+name)
 advisory=d['advisory_manifest'];PARENT.typed(advisory);manifest=C.obj(advisory)
 C.need(manifest['baseline_source']==prior['source']and manifest['required_actual_G2_refs']==PARENT.ACTUAL,'new packet is explicitly based on successful actual13, never an old v6 proposal')
 names=manifest['overlay_files']
 C.need(type(names)is list and len(names)==len(set(names))and all(type(n)is str and Path(n).name==n and n not in('.','..')for n in names),'unique flat reviewed packet files')
 C.need(set(d['actual_overlay_files'])==set(names),'complete actual portable overlay inventory')
 binding=C.obj(d['binding_inverse'])
 C.need(d['binding_inverse']==m['files']['G3_BINDING_EDITS_V1.json']and binding['schema']=='bole.G3-exact-output-binding-inverse/v1'and set(binding['files'])=={'contract090.py'},'only two output constants may differ from packet bytes during binding')
 for name in names:
  ar=d['actual_overlay_files'][name];PARENT.typed(ar);C.checked(ar)
  if name=='MANIFEST.json':C.need(ar==advisory,'exact external packet manifest')
  else:
   expected=manifest['inventory'][name];PARENT.typed(expected)
   C.need(Path(expected['path']).name==name and all(ar[k]==expected[k]for k in('bytes','sha256')),'complete reviewed packet bytes despite advisory path '+name)
  C.need(name in m['files'],'every packet file is current source-owned '+name)
  if name!='contract090.py':C.need(same_bytes(m['files'][name],ar),'packet bytes retained '+name)
  else:
   row=binding['files'][name]
   C.need(row['before']==ar and row['after']==m['files'][name]and row['edits']==[dict(before=C.checked(ar).read_text(),after=C.checked(m['files'][name]).read_text())],'whole exact output binding inverse')
   before=C.checked(ar).read_text();after=C.checked(m['files'][name]).read_text();rebuilt=before
   for key,value in(('OUTPUT_POSIX',m['output_root']),('CPU_OUTPUT_POSIX',m['output_root']+'-CPU')):
    def assignment(text):
     nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==key]
     C.need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and type(nodes[0].value.value)is str,'one exact bound output assignment '+key)
     return nodes[0],ast.get_source_segment(text,nodes[0])
    oldnode,oldtext=assignment(before);newnode,newtext=assignment(after)
    C.need(newnode.value.value==value and rebuilt.count(oldtext)==1,'exact current output binding '+key);rebuilt=rebuilt.replace(oldtext,newtext,1)
   C.need(rebuilt==after,'output binding changes no other packet byte')
 C.need(set(binding['files'])<=set(names),'binding operands are reviewed packet files')
 oldscope=parent['service_software_scope']
 expected_scope=dict(schema='bole.G3-five-source-staged-software-scope/v1',parent_source=oldscope['parent_source'],parent_exact_cases=279,controls_source=oldscope['controls_source'],controls_source_cases=25,historical_stage_source=oldscope['historical_stage_source'],historical_stage_cases=18,historical_ACK_source=prior['source'],historical_ACK_cases=27,historical_runner_ref=parent['files']['g2_exact_controls.py'],parent_suite_runs_in_separate_exact_source_process=True,controls_run_only_tests_in_exact_source_process=True,current_pattern='test_g3_*.py',new_current_cases=32,allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300.)
 C.need(m['service_software_scope']==expected_scope and m['service_required_sameimage_software_cases']==381,'fresh279+25+18+readonly13 ACK/HTTP27+current32; no cached software result')
 testnames=sorted(n for n in m['files']if n.startswith('test_g3_')and n.endswith('.py'))
 C.need(testnames==sorted('test_g3_'+n+'.py'for n in('budget','client','coverage','domain','lifecycle','parent','prepare','tensor_operands')),'all eight original current fixture modules remain present')
 methods=[]
 for name in testnames:
  for node in ast.walk(ast.parse(C.checked(m['files'][name]).read_bytes())):
   if isinstance(node,ast.FunctionDef)and node.name.startswith('test_'):methods.append((name,node.name))
 C.need(len(methods)==32 and len(methods)==len(set(methods)),'exactly32 current methods enumerated; this source gate does not claim execution')
 reservation=BUDGET.reservation()
 C.need(BUDGET.EVENT_CAPS==dict(FRAME=2048,ACK=3072,RELEASE=1536,REPORT=4000)and reservation['max_success_events']==1026 and reservation['terminal_failure_events']==1 and reservation['maximum_metadata_bytes']==56032480 and reservation['cap_bytes']==64*2**20 and reservation['logical_plus_serialized_plus_checkpoint_plus_metadata']==2**30 and G2.RAW_CAP==2**30 and G2.METADATA_CAP==64*2**20 and G2.FRAME_LOGICAL_CAP==384*2**20 and G2.FRAME_WIRE_CAP==448*2**20 and G2.CHECKPOINT_CAP==128*2**20,'full1024 every-frame ACK/oracle/raw reservation stays inside original budgets')
 C.need(m['stream_metadata_reservation']==reservation and m['stream_long_time_budget']==dict(owner_phase=3600,shared_cleanup=180,client_cap=3000,HTTP_request_timeout=2400,formal_timing=False)and m['stream_raw_success_replay_available']is False and m['stream_timing_is_formal']is False,'one original3600+180 finite diagnostic, without a predicted-fits admission gate')
 hooks=source_hooks(m);parent_original=READSET.collect(prior['source'])
 required=READSET.unique([*parent_original['refs'],*prior.values(),*parentproof['retained_refs'],LAYER,LAYER_INVERSE,advisory,d['binding_inverse'],*d['actual_overlay_files'].values()])
 missing=[r for r in required if current_dependencies.get(r['path'])!=r]
 C.need(not missing,'all retained parent/packet prerequisites must be explicit current dependencies '+json.dumps(missing))
 closure=READSET.audit(sr);actual={r['path']:r for r in closure['current_refs']}
 C.need(all(actual.get(r['path'])==r for r in required),'original current readset reopens every retained prerequisite')
 def digest(value):
  raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
  import hashlib
  return dict(items=len(value),canonical_JSON_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),complete_collection_reopened=True,sampled=False)
 return dict(schema='bole.G3-fixed131-long1024-source-validation/v1',source=sr,source_validated=True,descriptor_schema=d['schema'],runtime_layer_manifest=LAYER,runtime_layer_inverse=LAYER_INVERSE,current_whole_inverse=d['whole_inverse'],output_binding_inverse=d['binding_inverse'],advisory_manifest=advisory,parent_source=prior['source'],parent_owner_result=prior['owner_result'],parent_qualification=prior['qualification'],parent_source_audit=prior['source_audit'],parent_retained=digest(parentproof['retained_refs']),required_retained=digest(required),current_readset=digest(closure['current_refs']),current_commands=closure['current_original_commands'],historical_software_cases=349,current_methods_enumerated=32,prospective_sameimage_cases=381,current_methods=digest(methods),actual_sameimage_executed=False,scope=SCOPE,reservation=reservation,source_hooks=hooks,predicted_fits=None,original_numerical_consumer_completed=True,current_G3_numerical_qualification=False,actual_scheduler_executed=False,model_ready=False,formal_success=False,timing_is_formal=False,NPU=False)
