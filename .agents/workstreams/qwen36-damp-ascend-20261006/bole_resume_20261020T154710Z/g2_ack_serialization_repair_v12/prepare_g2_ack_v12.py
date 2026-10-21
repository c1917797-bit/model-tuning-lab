"""New immutable lossless ACK wire/source12; default OFF, no resource action."""
import argparse,ast,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from g2_ack_proof import SOURCE
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12');OUT=ROOT.with_name('run-'+ROOT.name)
CHANGED=('g2_channel.py','g2_consumer.py','g2_finalize.py','g2_software_stages.py','g2_exact_controls.py','contract090.py','G2_STREAM_EDITS_V1.json')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary full exact Ref3 source')
 a=p.stat();h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and size==z.st_size,'stable whole source read')
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def checked(r):need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'full input path/size/SHA exact');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def legacy(r):
 need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'only actual producerRef2/3');a=ref(r['path']);need(all(a[k]==v for k,v in r.items()),'actual complete Ref2 normalization');return a
def write(p,v):
 with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
 return ref(p)
def replace(p,v):
 if Path(p).exists():Path(p).unlink()
 return write(p,v)
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def tests(p):return sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for n in ast.walk(ast.parse(Path(p).read_bytes())))
def evidence():
 import g2_ack_proof as Q,g2_channel as CH
 f,records=Q.fixture(P/'ACTUAL_ACK_FIXTURE.json');parent=obj(SOURCE);owner=obj(f['failed_model_ref'])
 need(owner['source']==SOURCE and owner['cpu_only']is False and owner['primary']=="ValueError('one bounded actual model smoke client')"and owner['secondary']==[]and owner['source_before']and owner['source_before']==owner['source_after']and owner['phase_seconds']==3600 and owner['cleanup_seconds']==180 and 0<=owner['cleanup_spent']<=180 and 0<=owner['elapsed']<=3600,'actual retained failed source-stable MODEL, never successful qualification')
 refs=[SOURCE,f['failed_model_ref']]
 for name,row in f['records'].items():
  r=row['actual_ref'];need(checked(r).read_bytes()==records[name],'whole actual failure operand reopened at original path '+name);refs.append(r)
 for n in('g2_channel.py','g2_consumer.py'):
  need(f['records']['SOURCE/'+n]['actual_ref']==parent['files'][n],'actual failed actor source '+n);Q.check_pair(n,(P/n).read_bytes(),records['SOURCE/'+n])
 Q.check_pair('g2_finalize.py',(P/'g2_finalize.py').read_bytes(),checked(parent['files']['g2_finalize.py']).read_bytes())
 e=json.loads(records['STREAM/STREAM_CONSUMER_EXIT.json']);ack,frame,report=Q.actual_step(f,records)
 need(e['source']==SOURCE and e['completed']is False and e['source_unchanged']is True and e['actual_frame_batches']==1 and e['primary']=="ValueError('bounded complete per-frame oracle ACK')"and len(e['ACKs'])==4 and 'g2_consumer.py'in e['traceback']and 'line 105'in e['traceback'],'actual original first STEP ACK cap fault, no full-model pass')
 for rank in range(4):
  name='STREAM/ACK-RANK-%d-000000.json'%rank;a=json.loads(records[name]);ar=f['records'][name]['actual_ref']
  need(ar in e['ACKs']and a['source']==SOURCE and a['rank']==rank and a['sequence']==0 and a['kind']=='open'and a['passed']is True and a['complete_frame_consumed']is True and a['previous_ack']is None,'all4 actual OPEN ACKs, no STEP ACK')
  need(CH.decode_ack(CH.ack_bytes(a))==a,'whole original OPEN lossless roundtrip')
 need(report['source']==frame['source']==SOURCE and frame['rank']==0 and frame['sequence']==1 and frame['kind']=='step'and report['raw']==frame['raw']and report['coverage']==frame['coverage']and report['passed']is True and report['primary']is None and report['boolean_conjunctions']and all(v is True for v in report['boolean_conjunctions'].values()),'one actual saved rank0 STEP passed original oracle; not all-frame/retirement qualification')
 old=(json.dumps(ack,sort_keys=True)+'\n').encode();compact=(json.dumps(ack,sort_keys=True,separators=(',',':'))+'\n').encode();wire=CH.ack_bytes(ack)
 need(len(old)==3307 and len(compact)==3197 and len(wire)==2846 and CH.decode_ack(wire)==ack,'actual exact firstSTEP reconstruction, whitespace alone insufficient')
 need(not(Path(parent['stream_channel_root'])/'ACK-RANK-0-000001.json').exists(),'failed STEP ACK never written; old output/pending raw untouched')
 clean=[]
 for role,r in f['cleanup_refs'].items():
  v=obj(r);need(v['stopped']is True and v['retained']is True and v['deleted']is False and v['errors']==[],'actual retained failure cleanup '+role);refs.append(r)
  own=ref(Path(r['path']).parent/'OWNED.json');o=obj(own);need(o['source']==SOURCE and o['cid']==v['container'],'actual saved CID/source OWNED join '+role);refs.append(own)
  for key in('before_inspect','after_inspect','stop_receipt','release_smi'):refs.append(legacy(v[key]))
  rows=json.loads(obj(legacy(v['after_inspect']))['stdout']);need(len(rows)==1 and rows[0]['Id']==o['cid']and rows[0]['Image']==o['image']and rows[0]['State']['Running']is False and rows[0]['State']['Pid']==0 and not rows[0].get('ExecIDs')and not rows[0]['State'].get('OOMKilled'),'same actual CID stopped init/execs/no OOM '+role);clean.append(o['cid'])
 need(len(clean)==len(set(clean))==4,'four distinct retained failed-run owners')
 return parent,refs,dict(failed_source=SOURCE,failed_owner=f['failed_model_ref'],consumer_exit=f['records']['STREAM/STREAM_CONSUMER_EXIT.json']['actual_ref'],first_step_report=f['records']['STREAM/REPORT-RANK-0-000001.json']['actual_ref'],actual_default_JSON_bytes=3307,actual_canonical_object_JSON_bytes=3197,lossless_v3_wire_bytes=2846,wire_cap_bytes=3072,all_twenty_original_fields_retained=True,full_cgroup_and_six_Ref3_retained=True,only_saved_first_STEP_math_pass=True,complete_MODEL_qualified=False,all_owned_stopped_retained_observed=True,actual_live_identity_qualified=False)

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--manifest-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 mr=json.loads(a.manifest_ref);manifest=obj(mr);need(mr==ref(P/'MANIFEST.json'),'actual reviewed new v12 packet')
 for n,r in manifest['overlay_files'].items():
  need(Path(n).name==n and Path(r['path']).name==n and all(ref(P/n)[k]==r[k]for k in('bytes','sha256')),'ordinary portable reviewed overlay bytes/SHA '+n)
 parent,observed,cause=evidence()
 old=Path(parent['root']);need(not any(p.exists()for p in(ROOT,OUT,Path(str(OUT)+'-CPU'))),'NEW source/output-v12 only, preserve every previous failed run')
 for n in('host_service.py','service_entry.py','service_metadata.py'):
  need(n not in manifest['overlay_files']and ref(old/n)==parent['files'][n],'original host/firstclock/CANN/parser/model and complete metadata untouched '+n)
 collector=next(r for r in parent['dependencies']if r['sha256']=='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3');H=module(checked(collector),'_g2_v12_exact_original_collector');baseline=H.collect(SOURCE)
 shutil.copytree(old,ROOT,ignore=shutil.ignore_patterns('__pycache__'));(ROOT/'SOURCE_BOUND.json').rename(ROOT/'FAILED_G2_V11_SOURCE_BOUND.json')
 for n in('COMMANDS.json',parent['command_scope']['compatibility_file']):(ROOT/n).rename(ROOT/('FAILED_G2_V11_'+n))
 for n in manifest['overlay_files']:shutil.copyfile(P/n,ROOT/n)
 (ROOT/'contract090.py').write_text(H.outputs((old/'contract090.py').read_text(),str(OUT)));shutil.copyfile(P/'MANIFEST.json',ROOT/'G2_ACK_V12_MANIFEST.json')
 for n,r in parent['files'].items():
  if n not in CHANGED:need((ROOT/n).read_bytes()==checked(r).read_bytes(),'all old322 test/math128/argv/clock/caps/atomic/metadata/resource files byteequal '+n)
 import g2_ack_proof as Q
 for n in Q.ORIGINALS:Q.check_pair(n,(ROOT/n).read_bytes(),checked(parent['files'][n]).read_bytes())
 g1=parent['g2_predecessor']['source'];g1m=obj(g1);delta={}
 for n,r in g1m['files'].items():
  if(ROOT/n).is_file()and Path(r['path']).is_relative_to(Path(g1m['root'])):
   before=checked(r).read_text();after=(ROOT/n).read_text()
   if before!=after:delta[n]=dict(before=r,after=ref(ROOT/n),edits=[dict(before=before,after=after)])
 replace(ROOT/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=g1,files=delta,original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
 ledger=replace(ROOT/'G2_ACK_EDITS_V12.json',dict(schema='bole.exact-lossless-ACK-wire-and-controls-inverse/v12',baseline=SOURCE,files={n:dict(before=parent['files'][n],after=ref(ROOT/n),edits=[dict(before=checked(parent['files'][n]).read_text(),after=(ROOT/n).read_text())])for n in CHANGED},original3072_wire_cap_unchanged=True,original_math128_and_phase3600_cleanup180_unchanged=True,whole_original_sender_and_validator_unchanged=True))
 m=json.loads(json.dumps(parent));m.pop('prepared_template',None);m.update(root=str(ROOT),output_root=str(OUT),model_receipt_root=str(OUT/'dense/receipts'),prepared_only=True,default_enabled=False)
 def remap(r):return ref(ROOT/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
 m['files']={n:remap(r)for n,r in m['files'].items()}
 for n in(*manifest['overlay_files'],'G2_ACK_V12_MANIFEST.json','G2_ACK_EDITS_V12.json'):m['files'][n]=ref(ROOT/n)
 for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):m[key]={n:remap(r)for n,r in m.get(key,{}).items()}
 for row in m['g2_builder_portability_v2']['inventory'].values():row['actual_bound']=m['files'][Path(row['actual_bound']['path']).name]
 m['stream_channel_root']=str(OUT/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(OUT/'dense/receipts/STREAM/CHANNEL.json');m['stream_consumer_source']=m['files']['g2_consumer.py'];m['reviewed_stream_consumer']=ref(P/'g2_consumer.py')
 count=sum(tests(ROOT/n)for n in manifest['overlay_files']if n.startswith('test_g2_ack')and n.endswith('.py'));need(count==19,'all nineteen actual included ACK controls')
 m['service_required_sameimage_software_cases']=322+count;m['service_software_scope']=dict(schema='bole.G2-four-source-ACK-staged-software-scope/v12',parent_source=parent['service_software_scope']['parent_source'],parent_exact_cases=279,parent_suite_runs_in_separate_exact_source_process=True,controls_source=parent['service_software_scope']['controls_source'],controls_source_cases=25,controls_run_only_tests_in_exact_source_process=True,historical_stage_source=SOURCE,historical_stage_cases=18,current_pattern='test_g2_ack*.py',new_current_cases=count,allocation_seconds=dict(parent279=120.,controls=60.,metadata=120.),aggregate_cap_seconds=300.)
 m['g2_ack_serialization_v12']=dict(cause,parent_source=SOURCE,manifest=mr,actual_preparer=ref(__file__),whole_current_inverse=ledger,wire_schema='bole.actual-independent-frame-ACK-wire/v3',semantic_schema='bole.actual-independent-frame-ACK/v2',original322_tests_byteexact=True,software_sources_fresh=dict(source8=279,source10=25,source11=18,current12=count),no_old_whole_software_replay=True,no_new_RW_alias=True,actual_parser_and_cold_before_NPU_required=True)
 m['dependencies']=H.unique([*parent['dependencies'],*baseline['refs'],*observed,mr,ref(__file__),*[ref(P/n)for n in manifest['overlay_files']]])
 for n in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(ROOT/n,m)
 tr=ref(ROOT/'SOURCE_TEMPLATE.json');q=subprocess.run(['/usr/bin/python3','-I','-B',str(ROOT/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),'--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=60);need(q.returncode==0,'actual NEW v12 bind rejected '+q.stdout+q.stderr)
 sr=ref(ROOT/'SOURCE_BOUND.json');bound=obj(sr);sys.modules.pop('sourceio',None);sys.path.insert(0,str(ROOT));cc=module(ROOT/'command_contract.py','_g2_v12_current_exact_commands');need(ref(cc.C.__file__)==bound['files']['sourceio.py'],'actual current source-owned canonical C.ref namespace')
 history=obj(m['command_scope']['historical_ref']);commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,**cc.expected(str(ROOT),str(OUT),sr,tr,m['component_refs']),required_sameimage_software_cases=322+count,historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,G2_stream_protocol=True,actual_G2_execution_claimed=False)
 replace(ROOT/'COMMANDS.json',commands);replace(ROOT/m['command_scope']['compatibility_file'],dict(source=sr,template=tr,commands=ref(ROOT/'COMMANDS.json'),model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=322+count));cc.validate(cc.C,sr,bound);closure=H.collect(sr)
 present={r['path']:r for r in closure['refs']};need(all(present.get(r['path'])==r for r in baseline['refs']+observed),'full original readset and actual failed source/ACK/lifecycle exact readonly operands, no broad mounts')
 for f in ROOT.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
 print(json.dumps(dict(source=sr,commands=ref(ROOT/'COMMANDS.json'),prospective_sameimage_cases=341,source8_fresh_cases=279,source10_fresh_cases=25,source11_fresh_cases=18,current12_fresh_cases=count,original3072_wire_cap_unchanged=True,actual_first_STEP_wire_bytes=2846,stage_allocation_seconds=m['service_software_scope']['allocation_seconds'],aggregate_cap_seconds=300,original_phase_seconds=3600,cleanup_seconds=180,actual_sameimage_executed=False,actual_model_executed=False,NPU=False)));return 0
if __name__=='__main__':raise SystemExit(main())
