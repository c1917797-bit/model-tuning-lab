"""Default-OFF finite CPU map diagnostic under the original MAIN authority."""
import argparse,hashlib,json,os,pathlib,resource,subprocess,time
P=pathlib.Path
T=P('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE=dict(path='/opt/host/vnf/austinov/bole-native-ar-map-control-v3/INPUTS.json',bytes=20720,sha256='1cf3f2074f59a7d4c769c129afdecd644b33d32c0e264cbf8090dd126045cd27')
DIAGNOSTIC=dict(path='/opt/host/vnf/austinov/bole-native-ar-map-control-v3/DIAGNOSTIC-INPUTS.json',bytes=6668,sha256='e8092573410f0064a5daeec92c008008faf06bbbe83320180fb11266c355ff5c')
PREPARATION=dict(path='/opt/host/vnf/austinov/bole-native-ar-map-control-v3/PREPARATION.json',bytes=1173,sha256='b470e8431a29951e50110da9ab2cd956bf09e5c3ab68aef35771037d96cf01a0')
ORIGINAL=dict(path='/opt/host/vnf/austinov/bole-native-ar-fia-control-v2/INPUTS.json',bytes=15602,sha256='767c1e9209805f1f9eed6a6861482254ae884656e7747674a69dfa82eda1bb92')
OBSERVER=dict(path=str(T/'main_unit_observer96_v1/main_unit_observer96.py'),bytes=22264,sha256='c3544f0a26d686c55d6570442e32ff6c5fdadc4891adc7ff03cc7521635b6c94')
HISTORY=dict(path=str(T/'main_unit_observer96_actual_v1/OBSERVATION.json'),bytes=174383,sha256='cbb38a5166193462058fe317c011bab4ecd1c897952b357ce5306c3e3b9e8925')
MODEL_Q=dict(path=str(T/'G2_V13_MODEL_METADATA_READBACK.json'),bytes=1240436,sha256='989edb4d558c0006327ee3b1e432263a7090a80cda8e196147966f102481c7a0')
GDN_AUDIT=dict(path=str(T/'GDN_MATCHED_V4_MODEL_FAILURE_AUDIT_V2.json'),bytes=4157,sha256='ba6cda7a281ca01b4a4834e31571197a44e60fbe17f27f63ded2a4a49577dd9b')
UNIT='bole-native-ar-map-v3-20261020t154710z.service'
def need(v,s):
 if not v:raise ValueError(s)
def ref(path):
 p=P(path);before=p.stat();b=p.read_bytes();after=p.stat()
 need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'stable exact file')
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'whole exact source/evidence '+r['path']);return json.loads(P(r['path']).read_bytes())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def run(argv,timeout):
 start=time.monotonic();p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=timeout)
 return dict(requested_argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed=time.monotonic()-start)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--controller-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.controller_ref is not None,'exact controller source Ref3 required')
 own=json.loads(a.controller_ref);need(ref(__file__)==own,'this exact source-owned controller')
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Go-child hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 m=obj(SOURCE);d=obj(DIAGNOSTIC);prep=obj(PREPARATION);original=obj(ORIGINAL);prior=obj(MODEL_Q);gdn=obj(GDN_AUDIT)
 need(m['schema']=='bole.native-ar-map-diagnostic-owner-inputs/v1'and m['default_enabled']is False and m['original_fia_inputs_ref']==ORIGINAL and m['diagnostic_inputs_ref']==DIAGNOSTIC,'exact separate CPU diagnostic and original admission source')
 need(m['source_root']=='/opt/host/vnf/austinov/bole-native-ar-map-control-v3'and m['output_root']=='/opt/host/vnf/austinov/run-bole-native-ar-map-v3','new exact source/output')
 need(prep['owner_inputs']==SOURCE and prep['diagnostic_inputs']==DIAGNOSTIC and prep['prepared_module_path_identity_verified']is True and prep['resources_admitted']is False and type(prep['readset_count'])is int and prep['readset_count']>1047,'actual full source preparation')
 need(d['diagnostic_seconds']==600 and d['default_enabled']is False and d['output_dir']==m['output_root']+'/cpu-preflight/map-identity','original finite600 CPU-only diagnostic')
 for r in m['files'].values():need(ref(r['path'])==r,'current control source whole bytes')
 need(prior['all_four_owned_stopped_retained']is True and prior['sameimage_349_and_original_MODEL_metadata_independent_readback_pass']is True,'last successful G2 model closed')
 terminal=obj(gdn['unit'])['properties']
 need(terminal['MainPID']==terminal['ControlPID']=='0'and gdn['secondary']==[]and len(gdn['cleanups'])==2 and all(row['value']['stopped']is True and row['value']['retained']is True and row['value']['deleted']is False and row['value']['errors']==[]for row in gdn['cleanups']),'failed GDN owners stopped-retained; no failure promotion')
 authority=obj(original['authority']);need(authority['cutoff_epoch']==1792597630 and time.time()+3780<=1792597630,'original phase3600/cleanup180 within fixed cutoff')
 record=T/'NATIVE_AR_MAP_V3_SUBMITTED.json';need(not record.exists()and not P(m['output_root']).exists(),'exclusive new CPU map source submission/output')
 cold=[]
 for name in('map_cpu_owner.py','map_diagnostic_entry.py','prepare_map_owner.py'):
  for flags in([],['--help']):
   row=run(['/usr/bin/python3','-I','-B',m['files'][name]['path'],*flags],15);cold.append(row);need(row['exit_code']==0,'actual source-owned cold entry')
 save(T/'NATIVE_AR_MAP_V3_COLD_CLI.json',dict(records=cold,NPU=False,resources_admitted=False))
 host=m['files']['map_cpu_owner.py']
 audit=run(['/usr/bin/python3','-I','-B',host['path'],'--source-audit','--inputs-ref',json.dumps(SOURCE)],300)
 audit_ref=save(T/'NATIVE_AR_MAP_V3_SOURCE_AUDIT.json',audit);need(audit['exit_code']==0 and audit['stderr']=='','fresh full map owner source audit')
 v=json.loads(audit['stdout']);need(v['owner_inputs']==SOURCE and v['original_inputs']==ORIGINAL and v['diagnostic_inputs']==DIAGNOSTIC and v['readset_count']==prep['readset_count']and v['resources_admitted']is False and v['NPU']is False and v['diagnostic_only']is True and v['original_native_numerical_pass']is False and v['formal_success']is False,'actual complete original/new source closure; CPU map is no native math pass')
 need(ref(OBSERVER['path'])==OBSERVER,'whole observer');obj(HISTORY)
 observation=run(['/usr/bin/python3','-I','-B',OBSERVER['path'],'--execute','--source-ref',json.dumps(OBSERVER),'--history-ref',json.dumps(HISTORY),'--output',str(T/'main_unit_observer96_pre_native_ar_map_v3')],320)
 save(T/'NATIVE_AR_MAP_V3_PRE_SUBMIT_UNIT_OBSERVATION.json',observation);need(observation['exit_code']==0,'fresh complete actual unit quiescence')
 o=json.loads(observation['stdout']);need(o['observation_checks_pass']is True,'actual fixed96 observer');obs=obj(o['observation_ref'])
 need(obs['all_remaining_PIDs_zero']is True and obs['all_units_quiescent']is True and obs['source_input_equal']is True and obs['actual_entry_sources_complete']is True and 0<=time.time()-obs['observed_epoch']<=60 and UNIT not in obs['unit_names'],'fresh all-unit PID0 and actual source entry closure')
 lock=T/'MAIN_ADMISSION.lock';free=run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],10);need(free['exit_code']==0,'original MAIN lock free')
 need(time.time()+3780<=1792597630 and ref(__file__)==own and ref(SOURCE['path'])==SOURCE,'same fixed cutoff/source before single MAIN admission')
 cmd=['/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_NATIVE_AR_MAP_MAIN_ENABLE=1','/usr/bin/python3','-I','-B',host['path'],'--execute','--inputs-ref',json.dumps(SOURCE)]
 argv=['/usr/bin/systemd-run','--quiet','--unit='+UNIT,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'native-ar-map-v3.stdout'),'--property=StandardError=append:'+str(T/'native-ar-map-v3.stderr'),*cmd]
 call=run(argv,30)
 rr=save(record,dict(schema='bole.finite-native-ar-map-v3-MAIN-submission/v1',unit=UNIT,argv=argv,source=SOURCE,diagnostic=DIAGNOSTIC,preparation=PREPARATION,controller=own,original_resource_admission_source=ORIGINAL,last_successful_G2_readback=MODEL_Q,previous_GDN_failure_closed=GDN_AUDIT,pre_submit_observation=o['observation_ref'],source_audit=audit_ref,submit_exit=call['exit_code'],stdout=call['stdout'],stderr=call['stderr'],phase_seconds=3600,cleanup_seconds=180,diagnostic_seconds=600,fixed_cutoff=1792597630,NPU=False,pending=True,formal_success=False))
 print(json.dumps(dict(submission_ref=rr,unit=UNIT,submit_exit=call['exit_code'],pending=True,formal_success=False)));return call['exit_code']
if __name__=='__main__':raise SystemExit(main())
