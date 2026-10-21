"""Default OFF immutable G2 HTTP visibility repair; no resource creation."""
import argparse,ast,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/SOURCE_BOUND.json',bytes=908497,sha256='6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15')
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13')
OUT=ROOT.with_name('run-'+ROOT.name)
OLD_OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12')
RESULT=dict(path=str(OLD_OUT/'RESULT.json'),bytes=1205776,sha256='046dd18f22d6e1df8ea138253fedfdc9862f89ba04e61858d2892dae008b7c0d')
CHANGED={'host_service.py','contract090.py','G2_STREAM_EDITS_V1.json'}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute whole source')
 a=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and size==z.st_size,'stable full file')
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'complete exact Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def replace(p,v):
 if Path(p).exists():Path(p).unlink()
 return write(p,v)
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tests(p):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(Path(p).read_bytes())))
def collector(m):
 r=next(r for r in m['dependencies']if r['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3')
 return module(checked(r),'_g2_http13_original_collector')
def evidence():
 parent=obj(SOURCE);failed=obj(RESULT)
 need(failed['source']==SOURCE and failed['cpu_only']is False and failed['primary']=="ValueError('actual independent final identity/coverage/budget join failed')"and failed['secondary']==[]and failed['source_before']==failed['source_after']and len(failed['source_before'])==3679,'exact failed v12 whole MODEL preserved, never successful parent')
 unit=ref(T/'G2_V12_MODEL_SYSTEMD_TERMINAL.json');u=obj(unit)
 need(u['properties']==dict(Id='bole-g2-v12-model-20261020t154710z.service',Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='exit-code',ExecMainStatus='3',ActiveState='failed',SubState='failed'),'actual terminal failed v12 unit, no remaining owner PID')
 cleanup=ref(T/'G2_V12_MODEL_FAILURE_AUDIT.json');a=obj(cleanup)
 need(a['result']==RESULT and a['unit']==unit and a['all_four_stopped_retained']is True and len(a['owned'])==4,'actual independently reopened retained cleanup')
 refs=[SOURCE,RESULT,unit,cleanup]
 for row in a['owned']:
  for k in('owner','cleanup','after_inspect'):checked(row[k]);refs.append(row[k])
 fault=ref(OLD_OUT/'HOST-FIRST-FAULT.json');err=ref(OLD_OUT/'cpu-consumer/FINAL.stderr')
 need("http = C.obj(bundle[\"http\"])" in checked(err).read_text()and 'ordinary exact evidence bytes'in checked(err).read_text(),'actual finalizer failure at original full HTTP Ref')
 refs.extend([fault,err])
 http=ref(OLD_OUT/'dense/HTTP_RESULT.json');h=obj(http);refs.append(http)
 need(h['source']==SOURCE and len(h['rows'])==3,'actual complete original HTTP ledger')
 for row in h['rows']:checked(row['response']);refs.append(row['response'])
 client=ref(OLD_OUT/'dense/CLIENT-TERMINAL.json');consumer=ref(OLD_OUT/'cpu-consumer/STREAM-TERMINAL.json')
 need(obj(client)['exit_code']==obj(consumer)['exit_code']==0,'actual HTTP and numerical-consumer terminals0')
 exit_ref=ref(OLD_OUT/'dense/receipts/STREAM/STREAM_CONSUMER_EXIT.json');e=obj(exit_ref)
 need(e['source']==SOURCE and e['primary']is None and e['completed']is True and e['source_unchanged']is True and e['actual_frame_batches']==9 and len(e['ACKs'])==36,'actual complete four-rank9-frame consumer; no final identity qualification')
 for r in e['ACKs']:checked(r);refs.append(r)
 refs.extend([client,consumer,exit_ref])
 return parent,refs,dict(failed_source=SOURCE,failed_owner=RESULT,failed_unit=unit,cleanup_audit=cleanup,finalizer_stderr=err,actual_HTTP=http,actual_HTTP_response_refs=[r['response']for r in h['rows']],HTTP_client_exit0=True,stream_consumer_exit0=True,all36_ACKs_retained=True,old_MODEL_failed=True,full_MODEL_qualified=False)

def audit(sr):
 m=obj(sr);parent,observed,cause=evidence();d=m['g2_http_visibility_v13'];old=Path(parent['root'])
 need(sr==ref(ROOT/'SOURCE_BOUND.json')and m['root']==str(ROOT)and m['output_root']==str(OUT)and m['prepared_only']is False and m['default_enabled']is False,'actual new source13 binding')
 for k,v in cause.items():need(d[k]==v,'actual retained failure authority '+k)
 for n,r in parent['files'].items():
  if n not in CHANGED:need(checked(m['files'][n]).read_bytes()==checked(r).read_bytes(),'entire old341 controls/math/ACK/client/clock/transport/resource files unchanged '+n)
 B=module(checked(m['files']['g2_http_visibility_v13.py']),'_g2_http13_bound_proof')
 route=B.audit_host(checked(parent['files']['host_service.py']).read_text(),checked(m['files']['host_service.py']).read_text())
 H=collector(m);need(H.outputs((ROOT/'contract090.py').read_text(),parent['output_root'])==checked(parent['files']['contract090.py']).read_text(),'only registered contract output assignments')
 ledger=obj(d['whole_current_inverse']);need(ledger['baseline']==SOURCE and set(ledger['files'])==CHANGED,'complete explicit new layer inverse')
 for n,row in ledger['files'].items():
  need(row['before']==parent['files'][n]and row['after']==m['files'][n]and row['edits']==[dict(before=checked(row['before']).read_text(),after=checked(row['after']).read_text())],'whole source delta exactly bound '+n)
 sys.path.insert(0,str(ROOT))
 import g2_cold_clock as K,g2_software_stages as S
 clock=K.validate((ROOT/'host_service.py').read_text());scope=S.scope(m,sr)
 count=tests(ROOT/'test_g2_ack_http.py')
 need(count==d['new_HTTP_controls']>0 and scope['new_current_cases']==19+count and m['service_required_sameimage_software_cases']==341+count,'fresh original341 and additional actual HTTP controls')
 need(m['files']['g2_software_stages.py']['sha256']==parent['files']['g2_software_stages.py']['sha256']and m['files']['g2_exact_controls.py']['sha256']==parent['files']['g2_exact_controls.py']['sha256'],'unchanged actual dynamic stage/runner counts')
 closure=H.collect(sr);baseline=H.collect(SOURCE);present={r['path']:r for r in closure['refs']}
 need(all(present.get(r['path'])==r for r in baseline['refs']+observed),'all original readset and actual failure inputs retained exactly')
 return dict(schema='bole.G2-v13-HTTP-visibility-source-audit/v1',source=sr,commands=closure['commands'],readset_count=len(present),route=route,firstentry_clock=clock,all_original341_test_files_byteexact=True,original_math_ACK_cap_argv_transport_resources_unchanged=True,HTTP_files_produced_in_existing_channel=True,original_finalizer_budget_selects_HTTP_files=True,new_mounts=False,new_RW_alias=False,source8_fresh_cases=279,source10_fresh_cases=25,source11_fresh_cases=18,current_ACK_cases=19,new_HTTP_cases=count,prospective_sameimage_cases=341+count,software_allocation_seconds=S.CAPS,aggregate_cap_seconds=S.LANE_CAP,actual_software_executed=False,actual_model_executed=False,NPU=False)

def prepare(mr):
 manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'exact actual reviewed HTTP packet')
 for n,r in manifest['overlay_files'].items():
  need(Path(n).name==n and Path(r['path']).name==n and all(ref(P/n)[k]==r[k]for k in('bytes','sha256')),'portable exact new packet '+n)
 parent,observed,cause=evidence();H=collector(parent);baseline=H.collect(SOURCE);old=Path(parent['root'])
 need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'fresh source/model/CPU leaves only')
 B=module(P/'g2_http_visibility_v13.py','_g2_http13_packet_proof')
 host=B.patch_host(checked(parent['files']['host_service.py']).read_text())
 shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'))
 (ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V12_SOURCE_BOUND.json')
 for n in('COMMANDS.json',parent['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V12_'+n))
 for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
 (ROOT/'host_service.py').write_text(host)
 (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)))
 shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_HTTP_V13_MANIFEST.json')
 for n,r in parent['files'].items():
  if n not in CHANGED:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all source12 bytes retained '+n)
 g1=parent['g2_predecessor']['source'];g1m=obj(g1);delta={}
 for n,r in g1m['files'].items():
  if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(g1m['root'])):
   before=checked(r).read_text();after=(ROOT/n).read_text()
   if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
 replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1,files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
 ledger=replace(ROOT/'G2_HTTP_EDITS_V13.json',dict(schema='bole.exact-G2-HTTP-output-visibility-inverse/v13',baseline=SOURCE,files={n:dict(before=parent['files'][n],after=ref(ROOT/n),edits=[dict(before=checked(parent['files'][n]).read_text(),after=(ROOT/n).read_text())])for n in CHANGED},only_computational_change='HTTP client output and finalizer ledger input use the existing owned channel',no_mount_or_checked_or_finalizer_change=True))
 m=json.loads(json.dumps(parent));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
 def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
 m['files']={n:remap(r)for n,r in m['files'].items()}
 for n in(*manifest['overlay_files'],'G2_HTTP_V13_MANIFEST.json','G2_HTTP_EDITS_V13.json'):m['files'][n]=ref(ROOT/n)
 for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
 for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
 m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json')
 m['stream_consumer_source']=m['files']['g2_consumer.py'];m['reviewed_stream_consumer']=parent['reviewed_stream_consumer']
 count=tests(ROOT/'test_g2_ack_http.py');need(count>0,'actual included HTTP controls')
 m['service_software_scope']['new_current_cases']=19+count;m['service_required_sameimage_software_cases']=341+count
 m['g2_http_visibility_v13']=dict(cause,parent_source=SOURCE,manifest=mr,actual_preparer=ref(__file__),whole_current_inverse=ledger,new_HTTP_controls=count,original_ACK_controls=19,current_ACK_pattern_cases=19+count,actual_current_stage_source_is_SOURCE_BOUND=True,inherited_current12_label_is_runner_compatibility_only=True,inherited_ACK_v12_descriptor_is_historical_layer=True,all_original341_test_files_byteexact=True,HTTP_output_relative='dense/receipts/STREAM',HTTP_files_counted_by_unchanged_finalizer=True,no_new_mount=True,no_new_RW_alias=True,original_phase_seconds=3600,cleanup_seconds=180,fixed_cutoff=1792597630)
 m['dependencies']=H.unique([*parent['dependencies'],*baseline['refs'],*observed,mr,ref(__file__),*[ref(P/n)for n in manifest['overlay_files']]])
 for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
 tr=ref(ROOT/'SOURCE_TEMPLATE.json')
 q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60)
 need(q.returncode==0,'actual new source13 binding failed '+q.stdout+q.stderr)
 sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.modules.pop('sourceio',None);sys.path.insert(0,str(ROOT));cc=module(ROOT/'command_contract.py','_g2_http13_exact_commands')
 need(ref(cc.C.__file__)==bound['files']['sourceio.py'],'current exact source-owned canonical helper')
 history=obj(m['command_scope']['historical_ref'])
 commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=341+count,historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
 replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=341+count))
 cc.validate(cc.C,sr,bound);closure=H.collect(sr);present={r['path']:r for r in closure['refs']}
 need(all(present.get(r['path'])==r for r in baseline['refs']+observed),'complete original and failed source readset preserved')
 for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 return dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=341+count,actual_software_executed=False,actual_model_executed=False,NPU=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true');p.add_argument('--manifest-ref');p.add_argument('--source-ref');a=p.parse_args()
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 need(a.source_ref if a.source_audit else a.manifest_ref,'explicit complete actual source/manifest Ref required')
 print(json.dumps(audit(json.loads(a.source_ref))if a.source_audit else prepare(json.loads(a.manifest_ref)),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
