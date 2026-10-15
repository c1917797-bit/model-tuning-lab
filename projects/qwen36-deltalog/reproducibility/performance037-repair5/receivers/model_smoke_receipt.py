"""Consume actual032 bounded diagnostic smoke, never promote full48 numerical scope."""
import json
from pathlib import Path,PurePosixPath

def admit_bridge(C,plan):
 """Re-use exact reviewedMODEL036 lightweight typed035 reader, not math."""
 import importlib.util,sys
 pins=json.loads(Path(__file__).with_name('DOMAIN_PINS.json').read_bytes())
 sr=plan['model_diagnostic_source_ref'];m=C.obj(sr);template=C.obj(pins['model036_template'])
 C.need(m['schema']=='deltalog.service023-owned-overlay/v025'and m['prepared_only']is False and m['admission_mode']=='actual035-directRNE-domain-diagnostic-only','only actual reviewed boundMODEL036, not old032/future template')
 C.need(m['files']==pins['model036_files']==template['files']and m['root']==template['root'],'actualMODEL036 final source pins')
 changed={'plugin_source','composite_source_ref','composite_cpu_owner_ref','bridge024_source_ref','bridge024_qualification_api_ref','bridge024_owner_ref','expected_bound_bridge_ref','prepared_only'}
 C.need(set(m)==set(template)and all(m[k]==v for k,v in template.items()if k not in changed),'only original reviewed binder fields may change')
 C.need(m['window']==dict(start=1791962297,cutoff=1792135097)and m['reviewed_domain_files']==pins['reviewed_domain_files']and m['reviewed_domain_template_ref']==pins['reviewed_domain_template_ref'],'unchanged final035 template/files/window')
 C.need(m['plugin_source']==plan['production_source_ref']==m['expected_bound_plugin_ref']and m['bridge024_source_ref']==plan['bridge_source_ref']==m['expected_bound_bridge_ref']and m['bridge024_owner_ref']==plan['qualification_ref'],'same actual023R1 runtime and source035160 owner')
 for r in m['files'].values():C.checked(r)
 root=str(Path(m['root']));sys.path.insert(0,root)
 import owner_overlay
 C.need(Path(owner_overlay.__file__).resolve()==Path(m['files']['owner_overlay.py']['path']).resolve(),'reviewedMODEL036 real owner-overlay module; no shadow/namespace replacement')
 C.checked(m['files']['owner_overlay.py']);r=m['files']['domain_qualification.py'];C.checked(r)
 spec=importlib.util.spec_from_file_location('_pf037_reviewedMODEL036_typed035',r['path']);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
 C.need(api.C is owner_overlay,'typed035 reader uses actual reviewed source adapter')
 v=api.consume(m)
 C.need(v['schema']=='deltalog.model-directRNE-diagnostic-load-admission/v036'and v['source']==plan['bridge_source_ref']and v['owner']==plan['qualification_ref']and v['diagnostic_smoke_admitted']is True and v['model_numeric_qualified']is False and v['performance_ready']is False,'actual035160 qualified DIAGNOSTIC domain only')
 return m,v

def validate_terminal(C,rec,m,sr):
 C.need(rec['exitCode']==0 and rec['state']=='completed'and rec['timedOut']is False and rec['cancelled']is False,'actual successful terminal, not parent recollection')
 args=rec['args'];cmd=rec['command']
 if cmd=='/usr/bin/prlimit':
  C.need(args[:4]==['--as=536870912:unlimited','--','/usr/bin/python3','-B'],'exact original prlimit host launch');args=args[3:]
 else:C.need(cmd=='/usr/bin/python3','no unreviewed wrapper launcher')
 C.need(len(args)==5 and args[:3]==['-B',str(PurePosixPath(m['root'])/'host_ticket.py'),'--execute']and args[3]=='--source-ref'and json.loads(args[4])==sr,'exact source-bound032 actual host CLI')
 return True

def consume(C,plan):
 m,bridge=admit_bridge(C,plan);sr=plan['model_diagnostic_source_ref']
 owner_ref=plan['model_smoke_owner_ref'];v=C.obj(owner_ref)
 C.need(owner_ref['path']==str(Path(m['output_root'])/'RESULT.json'),'actual032 sole owned output')
 C.need(v['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and v['source']==sr and v['component_owner']==plan['qualification_ref'],'actual source-bound model owner')
 C.need(v['primary']is None and v['secondary']==[]and v['status']=='actual-DL-smoke-only'and v['all_created_containers_release_verified']is True,'actual model smoke completed/releases')
 states=v['owned_containers'];C.need(len(states)==3 and all(x['cid']and x['exact_owned_release_verified']is True for x in states)and len({x['cid']for x in states})==3,'all three exact Owned CIDs released')
 terminal=C.obj(plan['model_smoke_terminal_ref']);terminal=terminal.get('structuredContent',terminal)
 validate_terminal(C,terminal['result']['record'],m,sr)
 loaded=C.obj(v['actual_loaded_workers']);r=C.obj(v['independent_smoke_consumer']);tensor=C.obj(r['selected_tensor_ref'])
 pins=json.loads(Path(__file__).with_name('DOMAIN_PINS.json').read_bytes())
 C.need(r.get('validation_contract')==tensor.get('validation_contract')==pins['selected_model_validation_contract'],'explicit MODEL036R5 direct-RNE selected-model contract in BOTH reports; old unknown-v026 PASS refused')
 C.need(loaded['schema']=='deltalog.actual-all4-loaded/v004'and loaded['source']==sr and [x['rank']for x in loaded['rows']]==[0,1,2,3],'actual allfour loaded workers')
 C.need(r['schema']=='deltalog.model-selected-tensor-independent-consumption/v026'and r['source']==sr and r['actual_loaded_workers']==v['actual_loaded_workers']and r['actual_client']==v['client']and r['selected_modified_decode_pass']is True and r['smoke_dispatch_and_response_pass']is True,'actual independent model tensor/client joins')
 d=r['dispatch'];C.need(d['dispatch_trajectory_pass']is True and [x['rank']for x in d['rows']]==[0,1,2,3],'actual fourrank dispatch')
 for row in d['rows']:C.need(row['all48']is True and len(row['requests'])==2 and all(x['prefill']is True and x['decode']>=9 for x in row['requests'].values()),'each actual rank48 layers both requests >=9decode')
 C.need([(x['prompt_tokens'],x['output_tokens'])for x in r['responses']]==[(16,10),(129,10)],'two real requests, not warmup/sample')
 C.need(tensor['source']==sr and tensor['primary']is None and tensor['modified_decode_arithmetic_pass']is True and tensor['full48_tensor_qualified']is False and tensor['model_numeric_qualified']is False,'selected numeric scope, not all48 proof')
 return dict(schema='deltalog.actualMODEL036R5-model-diagnostic-smoke/v037-repair5',owner=owner_ref,terminal=plan['model_smoke_terminal_ref'],source=sr,consumer=v['independent_smoke_consumer'],selected_tensor=r['selected_tensor_ref'],loaded=v['actual_loaded_workers'],all4x48_dispatch=True,selected_numeric_pass=True,task_smoke_admitted=True,model_numeric_qualified=False,full_task_admitted=False,performance_ready=False)

def closure(C,plan):
 pins=json.loads(Path(__file__).with_name('DOMAIN_PINS.json').read_bytes())
 refs=[pins['model036_template'],plan['model_diagnostic_source_ref'],plan['model_smoke_owner_ref'],plan['model_smoke_terminal_ref']]
 m=C.obj(plan['model_diagnostic_source_ref']);refs.extend(m['files'].values());v=C.obj(plan['model_smoke_owner_ref']);refs.extend([v['actual_loaded_workers'],v['client'],v['independent_smoke_consumer']]);r=C.obj(v['independent_smoke_consumer']);refs.append(r['selected_tensor_ref'])
 refs.extend([m['reviewed_domain_template_ref'],m['bridge024_source_ref'],m['bridge024_owner_ref']])
 bridge=C.obj(m['bridge024_source_ref']);refs.extend(bridge['files'].values())
 b=C.obj(m['bridge024_owner_ref']);refs.extend([b['source'],b['result'],b['independent_consumer']]);refs.extend(C.obj(b['source'])['files'].values())
 pair=C.obj(b['independent_consumer']);refs.extend([pair['domain_consumer'],pair['original_strict_consumer']])
 return refs
