"""Audit then submit the exact finite fullCPUv13 once."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUTS={"path":"/opt/host/vnf/austinov/bole-task-cpu-20261020T154710Z-v13/OWNER_INPUTS.json","bytes":63020,"sha256":"f31b0e29e5098db2c3b291b7f7393c838cddf8a5080f60fd9b9ed1abf04ce407"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUTS['path'])==INPUTS
x=json.loads(P(INPUTS['path']).read_text());assert x['schema']=='bole.task-finite-CPU-owner-inputs/v5'and x['qualification_profile']=='full-v012-public-backend-network-isolation-python312/v4'
assert not P(x['output_root']).exists()
prep=json.loads((T/'TASK_CPU_V13_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs_ref']==INPUTS
record=T/'TASK_CPU_V13_SUBMITTED.json';assert not record.exists()
host=P(INPUTS['path']).parent/'cpu_host.py'
cmd=['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(cmd,cwd=T,capture_output=True,text=True,timeout=180)
with(T/'TASK_CPU_V13_SUBMISSION_SOURCE_AUDIT.json').open('x')as f:json.dump(dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr),f,sort_keys=True);f.write('\n')
assert p.returncode==0,p.stderr
v=json.loads(p.stdout);assert v['inputs_ref']==INPUTS and v['resources_admitted']is False and v['weight_hashes_performed']is False
authority=json.loads(P(x['authority_ref']['path']).read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
unit='bole-task-cpu-20261020t154710z-v13.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'task-cpu-v13.stdout'),'--property=StandardError=append:'+str(T/'task-cpu-v13.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-fullCPU-unit-submission/v4',unit=unit,argv=argv,inputs_ref=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,software_qualification_pending=True,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(p.returncode)
