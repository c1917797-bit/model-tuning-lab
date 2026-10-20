"""Submit one frozen actual Devices[] tokenizer diagnostic; no qualification claim."""
import argparse,json,subprocess,hashlib
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('mode',choices=('auto','public-backend'));a=ap.parse_args()
record=T/('TASK_CPU_V8_'+a.mode.upper().replace('-','_')+'_SUBMITTED.json');assert not record.exists()
prep=json.loads((T/('TASK_CPU_V8_'+a.mode.upper().replace('-','_')+'_PREPARATION.json')).read_text());assert prep['exit_code']==0
ip=json.loads(prep['stdout'])['inputs_ref'];assert ref(ip['path'])==ip
x=json.loads(Path(ip['path']).read_text());assert x['diagnostic_only']is True and x['tokenizer_probe']==a.mode and not Path(x['output_root']).exists()
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
host=Path(ip['path']).parent/'cpu_host.py'
audit=subprocess.run(['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(ip)],capture_output=True,text=True,timeout=120)
assert audit.returncode==0,audit.stderr
with(T/('TASK_CPU_V8_'+a.mode.upper().replace('-','_')+'_SOURCE_AUDIT.json')).open('x')as f:json.dump(dict(exit_code=audit.returncode,stdout=audit.stdout,stderr=audit.stderr,inputs_ref=ip),f,indent=2);f.write('\n')
unit='bole-task-cpu-20261020t154710z-v8-'+a.mode+'.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/('task-cpu-v8-'+a.mode+'.stdout')),'--property=StandardError=append:'+str(T/('task-cpu-v8-'+a.mode+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(ip)]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-tokenizer-diagnostic-unit/v8',unit=unit,argv=argv,inputs_ref=ip,controller=ref(__file__),submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,mode=a.mode,diagnostic_only=True,software_qualification=False,formal_success=False,phase_seconds=3600,cleanup_seconds=180)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
