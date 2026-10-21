"""Default-OFF exact finite GDN matched-v5 MODEL submission under original authority."""
import argparse,hashlib,json,os,pathlib,resource,subprocess,time
P=pathlib.Path
T=P('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v5/SOURCE_BOUND.json',bytes=117604,sha256='f5308ea9d74e92293fd00a73f156a324fab064bfb2dcca3997728054deff4831')
COMMANDS=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v5/COMMANDS.json',bytes=3848,sha256='f753c9b49b7967f77662ee02ba8ad422b176927634131f122b085faeb0d2004e')
CPU_RESULT=dict(path='/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5-CPU/RESULT.json',bytes=235527,sha256='73733f6268cea5226dbcb9f5099c461e396b72c3aa274e5726b5a9d0e796ffa0')
OBSERVER=dict(path=str(T/'main_unit_observer96_v1/main_unit_observer96.py'),bytes=22264,sha256='c3544f0a26d686c55d6570442e32ff6c5fdadc4891adc7ff03cc7521635b6c94')
HISTORY=dict(path=str(T/'main_unit_observer96_actual_v1/OBSERVATION.json'),bytes=174383,sha256='cbb38a5166193462058fe317c011bab4ecd1c897952b357ce5306c3e3b9e8925')
MODEL_Q=dict(path=str(T/'G2_V13_MODEL_METADATA_READBACK.json'),bytes=1240436,sha256='989edb4d558c0006327ee3b1e432263a7090a80cda8e196147966f102481c7a0')
CPU_Q=dict(path=str(T/'GDN_MATCHED_V5_CPU_METADATA_READBACK.json'),bytes=146721,sha256='d260ad4e5324e96ee3c44aaa9258c2ae6bfcbc86415ff45e03e1e3ea46571c63')
UNIT='bole-gdn-matched-v5-model-20261020t154710z.service'
def need(v,s):
 if not v:raise ValueError(s)
def ref(path):
 p=P(path);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(ref(r['path'])==r,'whole exact source/evidence '+r['path']);return json.loads(P(r['path']).read_bytes())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def run(argv,timeout):
 start=time.monotonic();p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=timeout);return dict(requested_argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed=time.monotonic()-start)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 os.sched_setaffinity(0,{166});soft,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Go child hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 m=obj(SOURCE);commands=obj(COMMANDS);cpu=obj(CPU_RESULT);prior=obj(MODEL_Q);cq=obj(CPU_Q)
 need(cq['source']==SOURCE and cq['result_ref']==CPU_RESULT and cq['actual240_sameimage_pass']is True and cq['owned_stopped_retained']is True and cq['source_readset_count']==732 and cq['original_full_source_and_software_gate_reexecuted']is True,'actual independently reopened current CPU240 qualification')
 for r in cq['retained_refs']:need(ref(r['path'])==r,'whole current independently retained CPU/source evidence')
 need(commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==240,'exact prepared current240 source/commands')
 need(cpu['source']==SOURCE and cpu['cpu_only']is True and cpu['primary']is None and cpu['secondary']==[]and cpu['source_before']==cpu['source_after']and len(cpu['source_before'])==732 and cpu['actual_host_argv']==commands['CPU'][8:]and cpu['entry_clock_before_source_replay']is True and cpu['deadline_renewed']is False,'actual prior sameimage CPU240 result')
 need(prior['all_four_owned_stopped_retained']is True and prior['sameimage_349_and_original_MODEL_metadata_independent_readback_pass']is True,'last actual G2 MODEL closed and independently read back')
 authority=obj(m['authority_ref']);need(authority['cutoff_epoch']==1792597630 and time.time()+3780<=authority['cutoff_epoch'],'original3600+180 within unchanged fixed cutoff')
 record=T/'GDN_MATCHED_V5_MODEL_SUBMITTED.json';need(not record.exists()and not P(m['output_root']).exists(),'exclusive new model output/submission')
 host=m['files']['host_service.py'];need(ref(host['path'])==host,'whole exact actual host')
 audit=run(['/usr/bin/python3','-I','-B',host['path'],'--source-audit','--source-ref',json.dumps(SOURCE)],300);save(T/'GDN_MATCHED_V5_MODEL_SOURCE_AUDIT.json',audit)
 need(audit['exit_code']==0,'actual readonly GDN source audit');v=json.loads(audit['stdout']);need(v['source']==SOURCE and v['readset']==755 and v['resources_admitted']is False,'exact current full original GDN source audit')
 need(ref(OBSERVER['path'])==OBSERVER,'whole observer');obj(HISTORY)
 observation=run(['/usr/bin/python3','-I','-B',OBSERVER['path'],'--execute','--source-ref',json.dumps(OBSERVER),'--history-ref',json.dumps(HISTORY),'--output',str(T/'main_unit_observer96_pre_gdn_v5_model')],320)
 save(T/'GDN_MATCHED_V5_MODEL_PRE_SUBMIT_UNIT_OBSERVATION.json',observation);need(observation['exit_code']==0,'fresh complete actual unit quiescence')
 o=json.loads(observation['stdout']);need(o['observation_checks_pass']is True,'actual observer checks');obs=obj(o['observation_ref'])
 need(obs['all_remaining_PIDs_zero']is True and obs['all_units_quiescent']is True and obs['source_input_equal']is True and obs['actual_entry_sources_complete']is True and 0<=time.time()-obs['observed_epoch']<=60 and UNIT not in obs['unit_names'],'all fresh original/new units stopped; no reused model unit')
 lock=T/'MAIN_ADMISSION.lock';cmd=commands['model'];need(cmd[:4]==['/usr/bin/flock','--nonblock','--no-fork',str(lock)]and cmd.count(str(lock))==1,'one original outer MAIN flock')
 free=run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],10);need(free['exit_code']==0,'original MAIN lock free before single atomic owner admission')
 need(time.time()+3780<=authority['cutoff_epoch'],'unchanged cutoff after all precreate reads')
 argv=['/usr/bin/systemd-run','--quiet','--unit='+UNIT,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'gdn-matched-v5-model.stdout'),'--property=StandardError=append:'+str(T/'gdn-matched-v5-model.stderr'),*cmd]
 call=run(argv,30);v=dict(schema='bole.finite-GDN-matched-v5-MODEL-submission/v1',unit=UNIT,argv=argv,source=SOURCE,commands=COMMANDS,prior_CPU_result=CPU_RESULT,prior_CPU_qualification=CPU_Q,last_actual_MODEL_readback=MODEL_Q,controller=ref(__file__),pre_submit_observation=o['observation_ref'],source_audit=ref(T/'GDN_MATCHED_V5_MODEL_SOURCE_AUDIT.json'),submit_exit=call['exit_code'],stdout=call['stdout'],stderr=call['stderr'],phase_seconds=3600,cleanup_seconds=180,fixed_cutoff=1792597630,NPU=True,pending=True,formal_success=False)
 rr=save(record,v);print(json.dumps(dict(submission_ref=rr,unit=UNIT,submit_exit=call['exit_code'],pending=True,formal_success=False)));return call['exit_code']
if __name__=='__main__':raise SystemExit(main())
