
"""Default-OFF finite exact GDN candidate-v5 CPU qualification."""
import argparse,hashlib,json,os,pathlib,resource,subprocess,time
P=pathlib.Path
T=P('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-candidate-v5/SOURCE_BOUND.json',bytes=118267,sha256='f4dca1e9a13efbe7921a2e6157e950d00727e634cc2b341e63eacbc1f3ded3f6')
COMMANDS=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-candidate-v5/COMMANDS.json',bytes=3868,sha256='5af4a0133bdb930c76a7faa398c476c65f42f56d06978573aec6147db4e157af')
OBSERVER=dict(path=str(T/'main_unit_observer96_v1/main_unit_observer96.py'),bytes=22264,sha256='c3544f0a26d686c55d6570442e32ff6c5fdadc4891adc7ff03cc7521635b6c94')
HISTORY=dict(path=str(T/'main_unit_observer96_actual_v1/OBSERVATION.json'),bytes=174383,sha256='cbb38a5166193462058fe317c011bab4ecd1c897952b357ce5306c3e3b9e8925')
UNIT='bole-gdn-candidate-v5-cpu-20261020t154710z.service'
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
 start=time.monotonic();p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=timeout)
 return dict(requested_argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed=time.monotonic()-start)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--controller-ref');p.add_argument('--audit-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.controller_ref and a.audit_ref,'explicit full controller and actual source-audit Refs')
 need(json.loads(a.controller_ref)==ref(__file__),'exact current source-owned admission controller')
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Go child hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 m=obj(SOURCE);commands=obj(COMMANDS);audit=obj(json.loads(a.audit_ref))
 prior=obj({'path': '/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G3_V1_CPU_FAILURE_AUDIT.json', 'bytes': 4094, 'sha256': 'bab235a5bb7d9436f02a5b93dfb1d5bf37d7772a26e1eb86d025cc4f2ded767e'});need(prior['stopped_retained']is True and prior['noOOM']is True and prior['source5000_equal']is True and prior['unit_terminal_PIDs_zero']is True,'last G3 CPU owner closed before this admission')
 need(m['gdn_service_extension']['mode']=='candidate','only explicit candidate source')
 need(audit['exit_code']==0 and audit['stderr']=='' and audit['original_51_test_files_byte_equal']is True and audit['all_four_qualified_mathematical_sources_byte_equal']is True and audit['mode']=='candidate' and audit['source']==SOURCE and audit['removed_files']==[] and audit['added_files']=={} and {r['name']for r in audit['changed_existing_files']}=={'FA_BOUNDARY_EDITS_R14.json','G1_LIFECYCLE_EDITS_V1.json','contract090.py'},'actual narrow source preparation and complete original tests preserved')
 ar=json.loads(audit['stdout']);need(ar['source']==SOURCE and ar['NPU']is False and ar['resources_admitted']is False and type(ar['readset'])is int and ar['readset']>0,'actual original full readonly source audit')
 need(commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==240,'exact original240 source/commands')
 for n in ('GDN_ASSEMBLED_MATH_V5.json','GDN_POSTBOUND_MATH_V5.json'):
  q=json.loads((P(m['root'])/n).read_bytes());need(q['all_four_equal']is True,'all four exact qualified mathematical sources')
  for v in q['files'].values():
   need(ref(v['assembled']['path'])==v['assembled']and ref(v['qualified']['path'])==v['qualified']and P(v['assembled']['path']).read_bytes()==P(v['qualified']['path']).read_bytes(),'independent whole-byte qualified source reopening')
 authority=obj(m['authority_ref']);need(authority['cutoff_epoch']==1792597630 and time.time()+3780<=authority['cutoff_epoch'],'original3600+180 within unchanged cutoff')
 record=T/'GDN_CANDIDATE_V5_CPU_SUBMITTED.json';out=commands['CPU'][-1]
 need(out==m['output_root']+'-CPU'and not record.exists()and not P(out).exists(),'new exclusive original CPU output')
 need(ref(OBSERVER['path'])==OBSERVER,'whole observer');obj(HISTORY)
 call=run(['/usr/bin/python3','-I','-B',OBSERVER['path'],'--execute','--source-ref',json.dumps(OBSERVER),'--history-ref',json.dumps(HISTORY),'--output',str(T/'main_unit_observer96_pre_gdn_candidate_v5_cpu')],320)
 save(T/'GDN_CANDIDATE_V5_CPU_PRE_SUBMIT_UNIT_OBSERVATION.json',call);need(call['exit_code']==0,'fresh complete actual unit quiescence')
 o=json.loads(call['stdout']);need(o['observation_checks_pass']is True,'actual observer checks');obs=obj(o['observation_ref'])
 need(obs['all_remaining_PIDs_zero']is True and obs['all_units_quiescent']is True and obs['source_input_equal']is True and obs['actual_entry_sources_complete']is True and 0<=time.time()-obs['observed_epoch']<=60 and UNIT not in obs['unit_names'],'fresh full unit closure; no unit reuse')
 lock=T/'MAIN_ADMISSION.lock';cmd=commands['CPU'];need(cmd[:4]==['/usr/bin/flock','--nonblock','--no-fork',str(lock)]and cmd.count(str(lock))==1,'one original MAIN outer flock')
 need(run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],10)['exit_code']==0,'original MAIN lock free')
 need(time.time()+3780<=authority['cutoff_epoch'],'unchanged cutoff after source and quiescence reads')
 argv=['/usr/bin/systemd-run','--quiet','--unit='+UNIT,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'gdn-candidate-v5-cpu.stdout'),'--property=StandardError=append:'+str(T/'gdn-candidate-v5-cpu.stderr'),*cmd]
 result=run(argv,30)
 v=dict(schema='bole.finite-GDN-candidate-v5-CPU-submission/v1',unit=UNIT,argv=argv,source=SOURCE,commands=COMMANDS,controller=ref(__file__),source_audit=json.loads(a.audit_ref),actual_source_audit_readset=ar['readset'],pre_submit_observation=o['observation_ref'],submit_exit=result['exit_code'],stdout=result['stdout'],stderr=result['stderr'],phase_seconds=3600,cleanup_seconds=180,fixed_cutoff=1792597630,NPU=False,pending=True,formal_success=False)
 rr=save(record,v);print(json.dumps(dict(submission_ref=rr,unit=UNIT,submit_exit=result['exit_code'],pending=True,formal_success=False)));return result['exit_code']
if __name__=='__main__':raise SystemExit(main())
