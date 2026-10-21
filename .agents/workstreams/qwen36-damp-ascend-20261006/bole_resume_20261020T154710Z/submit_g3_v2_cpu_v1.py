
"""Default-OFF single finite G3 v2 CPU381/parser/saved-cold qualification."""
import argparse,hashlib,json,os,resource,subprocess,time
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g3-fixed1024-20261020T154710Z-v2/SOURCE_BOUND.json',bytes=1223544,sha256='ca87c8547a449f71994866e191ee40816a1e52f395e68f752c092f8c58637a85')
COMMANDS=dict(path='/opt/host/vnf/austinov/bole-g3-fixed1024-20261020T154710Z-v2/COMMANDS.json',bytes=3575,sha256='aef7f66a2cccab96eea85de256808621a5e9f859e753cfb4ddfdd174069857b4')
AUDIT=dict(path=str(T/'G3_V2_HOST_SOURCE_AUDIT.json'),bytes=1015,sha256='2121f9c1645569724de4d720782355bdbda9a74bac6d2af52e5273ec1499fb5b')
FIXTURES=dict(path=str(T/'G3_ACTUAL13_PARENT_PREPARE_FIXTURE_CONTROLS_V2.json'),bytes=2246,sha256='1e4f81dda2c131dd1270834c41e2d2e74c8c9b95f6c266beb9ac5f638faa07f9')
PREPARATION=dict(path=str(T/'G3_SOURCE13_ACTUAL_SOURCE_PREPARATION_EXECUTION_V2.json'),bytes=14422,sha256='e8cb2f475f2b39e94e2140be3943ad721c21352dc4f731e798e166dc81874730')
OBSERVER=dict(path=str(T/'main_unit_observer96_v1/main_unit_observer96.py'),bytes=22264,sha256='c3544f0a26d686c55d6570442e32ff6c5fdadc4891adc7ff03cc7521635b6c94')
HISTORY=dict(path=str(T/'main_unit_observer96_actual_v1/OBSERVATION.json'),bytes=174383,sha256='cbb38a5166193462058fe317c011bab4ecd1c897952b357ce5306c3e3b9e8925')
GDN_RESULT=dict(path='/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v5/RESULT.json',bytes=238251,sha256='8bad263436d441dd1e84d0147788bd9ff2d04ccf77cb86f55c8335e41d0b5bd0')
UNIT='bole-g3-v2-cpu-20261020t154710z.service'
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0;a=p.stat()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and n==z.st_size,'stable complete streaming hash')
 return dict(path=str(p),bytes=n,sha256=h.hexdigest())
def full(r):
 a=ref(r['path']);need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'exact original Ref2/Ref3 full bytes')
 return a
def obj(r):full(r);return json.loads(Path(r['path']).read_bytes())
def save(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def run(argv,limit):
 t=time.monotonic();r=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=limit)
 return dict(argv=argv,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed=time.monotonic()-t)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--controller-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(a.controller_ref and json.loads(a.controller_ref)==ref(__file__),'exact source-owned controller Ref')
 os.sched_setaffinity(0,{166});_,hard=resource.getrlimit(resource.RLIMIT_AS);need(hard==resource.RLIM_INFINITY,'original Go child hard AS infinity');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 m=obj(SOURCE);commands=obj(COMMANDS);audit=obj(AUDIT);fixtures=obj(FIXTURES);prep=obj(PREPARATION)
 need(audit['source']==SOURCE and audit['exit_code']==0 and audit['stderr']=='','actual exact full host source audit')
 av=json.loads(audit['stdout']);need(av['source']==SOURCE and av['readset']==5118 and av['NPU']is False and av['resources_admitted']is False,'actual complete5118 ordered host source audit')
 need(fixtures['source']==SOURCE and fixtures['exit_code']==0 and json.loads(fixtures['stdout'])==dict(tests=6,failures=0,errors=0,success=True,NPU=False),'actual six original pure parent/prepare controls')
 need(prep['exit_code']==0 and prep['stderr']=='','actual source preparation');pv=json.loads(prep['stdout']);proof=pv['source_gate']
 need(pv['source']==SOURCE and pv['commands']==COMMANDS and proof['source_validated']is True and proof['current_readset']['items']==5017 and proof['required_retained']['items']==4647 and proof['parent_retained']['items']==4559,'actual complete independently reopened parent and cold-integrated current source gate')
 need(commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==381 and commands['G3_stream_protocol']is True,'exact current381 commands')
 previous=obj(GDN_RESULT);need(previous['primary']is None and previous['secondary']==[]and previous['source_before']==previous['source_after'],'last original model owner completed')
 for name in ('CPU_release','model_release','independent_release'):
  release=obj(previous['summary'][name]);need(release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[],'last model all original owners stopped retained')
  row=obj(release['after_inspect']);need(row['exit_code']==0,'original saved after-inspect completed');items=json.loads(row['stdout']);need(len(items)==1,'one exact saved owned container');i=items[0]
  need(i['Id']==release['container']and i['State']['Running']is False and i['State']['Pid']==0 and i['State']['OOMKilled']is False and not i.get('ExecIDs'),'last model stopped saved PID/oom/exec closure')
 authority=obj(m['authority_ref']);need(authority['cutoff_epoch']==1792597630 and time.time()+3780<=1792597630,'unchanged3600+180 and fixed cutoff')
 record=T/'G3_V2_CPU_SUBMITTED.json';out=m['output_root']+'-CPU';need(not record.exists()and not Path(out).exists(),'exclusive new current CPU output and submission')
 need(ref(OBSERVER['path'])==OBSERVER,'exact observer');obj(HISTORY)
 call=run(['/usr/bin/python3','-I','-B',OBSERVER['path'],'--execute','--source-ref',json.dumps(OBSERVER),'--history-ref',json.dumps(HISTORY),'--output',str(T/'main_unit_observer96_pre_g3_v2_cpu')],320)
 save(T/'G3_V2_CPU_PRE_SUBMIT_UNIT_OBSERVATION.json',call);need(call['exit_code']==0,'fresh complete all-unit quiescence')
 o=json.loads(call['stdout']);need(o['observation_checks_pass']is True,'actual observer pass');obs=obj(o['observation_ref'])
 need(obs['all_remaining_PIDs_zero']is True and obs['all_units_quiescent']is True and obs['source_input_equal']is True and obs['actual_entry_sources_complete']is True and 0<=time.time()-obs['observed_epoch']<=60 and UNIT not in obs['unit_names'],'fresh complete closure and no unit reuse')
 lock=T/'MAIN_ADMISSION.lock';cmd=commands['CPU'];need(cmd[:4]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3']and str(lock)not in cmd and cmd[-1]==out,'original source-owned CPU command has no outer lock')
 need(run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],10)['exit_code']==0,'original MAIN lock free')
 need(time.time()+3780<=1792597630,'unchanged cutoff after all reads')
 owner=['/usr/bin/flock','--nonblock','--no-fork',str(lock),*cmd]
 argv=['/usr/bin/systemd-run','--quiet','--unit='+UNIT,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'g3-v2-cpu.stdout'),'--property=StandardError=append:'+str(T/'g3-v2-cpu.stderr'),*owner]
 result=run(argv,30)
 v=dict(schema='bole.finite-G3-v2-CPU381-submission/v1',unit=UNIT,argv=argv,controller=ref(__file__),source=SOURCE,commands=COMMANDS,source_preparation=PREPARATION,full_host_source_audit=AUDIT,actual_fixture_controls=FIXTURES,closed_model_owner_lineage=GDN_RESULT,pre_submit_observation=o['observation_ref'],submit_exit=result['exit_code'],stdout=result['stdout'],stderr=result['stderr'],phase_seconds=3600,cleanup_seconds=180,fixed_cutoff=1792597630,NPU=False,pending=True,actual381_pass=False,formal_success=False)
 rr=save(record,v);print(json.dumps(dict(submission_ref=rr,unit=UNIT,submit_exit=result['exit_code'],pending=True,NPU=False,formal_success=False)));return result['exit_code']
if __name__=='__main__':raise SystemExit(main())
