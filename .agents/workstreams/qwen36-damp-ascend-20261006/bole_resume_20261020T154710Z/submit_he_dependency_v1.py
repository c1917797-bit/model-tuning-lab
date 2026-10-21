"""Audit then submit the exact finite HE dependency-only preflight v1 once."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUTS={"path":"/opt/host/vnf/austinov/bole-task-cpu-he-dependency-20261020T154710Z-v1/PREFLIGHT_INPUTS.json","bytes":9974,"sha256":"314087c46c79400f5317d9dc9f160ec591ba1c8ca64da36134c2bda14874a2d7"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUTS['path'])==INPUTS
x=json.loads(P(INPUTS['path']).read_text());assert x['schema']=='bole.HE-dependency-preflight-inputs/v1'and x['full_software_qualification_accepted']is False and x['generated_code_executed']is False
assert not P(x['output_root']).exists()
prep=json.loads((T/'HE_DEPENDENCY_V1_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs_ref']==INPUTS
record=T/'HE_DEPENDENCY_V1_SUBMITTED.json';assert not record.exists()
host=P(INPUTS['path']).parent/'preflight_host.py'
cmd=['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(cmd,cwd=T,capture_output=True,text=True,timeout=180)
with(T/'HE_DEPENDENCY_V1_SUBMISSION_SOURCE_AUDIT.json').open('x')as f:json.dump(dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr),f,sort_keys=True);f.write('\n')
assert p.returncode==0,p.stderr
v=json.loads(p.stdout);assert v['inputs_ref']==INPUTS and v['resources_admitted']is False and v['qualified']is False and v['readset_files']==290
authority=json.loads(P(x['authority_ref']['path']).read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
unit='bole-task-cpu-he-dependency-20261020t154710z-v1.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'he-dependency-v1.stdout'),'--property=StandardError=append:'+str(T/'he-dependency-v1.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-fullCPU-unit-submission/v4',unit=unit,argv=argv,inputs_ref=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,import_only_preflight_pending=True,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(p.returncode)
