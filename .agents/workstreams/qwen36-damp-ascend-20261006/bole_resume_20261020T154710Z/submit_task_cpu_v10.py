"""Submit the exact full15525/HE Devices[] software qualification once."""
import json,hashlib,subprocess
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
record=T/'TASK_CPU_V10_SUBMITTED.json';assert not record.exists()
prep=json.loads((T/'TASK_CPU_V10_PREPARATION.json').read_text());assert prep['exit_code']==0
ip=json.loads(prep['stdout'])['inputs_ref'];assert ref(ip['path'])==ip
x=json.loads(Path(ip['path']).read_text());assert x['schema']=='bole.task-finite-CPU-owner-inputs/v3'and x['diagnostic_only']is False and x['qualification_profile']=='full-v012-public-backend/v2'
assert x['phase_order']==['cpu-preflight','he-controls','cpu-consumer']and not Path(x['output_root']).exists()
host=Path(ip['path']).parent/'cpu_host.py';lock=T/'MAIN_ADMISSION.lock'
assert lock.is_file()and not lock.is_symlink()and subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
audit=subprocess.run(['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(ip)],capture_output=True,text=True,timeout=150)
with(T/'TASK_CPU_V10_SOURCE_AUDIT.json').open('x')as f:json.dump(dict(exit_code=audit.returncode,stdout=audit.stdout,stderr=audit.stderr,inputs_ref=ip),f,indent=2);f.write('\n')
assert audit.returncode==0,audit.stderr
unit='bole-task-cpu-20261020t154710z-v10.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'task-cpu-v10.stdout'),'--property=StandardError=append:'+str(T/'task-cpu-v10.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(ip)]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.actual-full-software-owned-unit-submission/v10',unit=unit,argv=argv,inputs_ref=ip,controller=ref(__file__),submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,software_qualification_pending=True,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
