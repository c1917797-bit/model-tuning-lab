"""Source-audit and submit the exact bounded HE runtime-only diagnostic once."""
import json,pathlib,hashlib,subprocess
P=pathlib.Path
T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUTS={"path":"/opt/host/vnf/austinov/bole-task-cpu-he-runtime-20261020T154710Z-v2/DIAGNOSTIC_INPUTS.json","bytes":9073,"sha256":"bc2065b93df1d803e39518dbd5f5c98fca2a5182dc1b79604c34fddfc439f49c"}
def ref(p):
 p=P(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
assert ref(INPUTS['path'])==INPUTS
host=P(INPUTS['path']).parent/'diagnostic_host.py'
record=T/'HE_RUNTIME_DIAGNOSTIC_V2_SUBMITTED.json'
assert not record.exists()
x=json.loads(P(INPUTS['path']).read_text())
assert x['diagnostic_revision']==2 and x['diagnostic_only'] is True and not P(x['output_root']).exists()
prep=json.loads((T/'HE_RUNTIME_DIAGNOSTIC_V2_PREPARATION.json').read_text())
assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs_ref']==INPUTS
cmd=['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(cmd,cwd=T,capture_output=True,text=True,timeout=180)
with (T/'HE_RUNTIME_DIAGNOSTIC_V2_SOURCE_AUDIT.json').open('x') as f:
 json.dump({'argv':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},f,indent=2);f.write('\n')
assert p.returncode==0,p.stderr
v=json.loads(p.stdout)
assert v['inputs_ref']==INPUTS and v['resources_admitted'] is False and v['full_input_decode_repeated'] is False
lock=T/'MAIN_ADMISSION.lock'
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
unit='bole-he-runtime-diagnostic-20261020t154710z-v2.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'he-runtime-diagnostic-v2.stdout'),'--property=StandardError=append:'+str(T/'he-runtime-diagnostic-v2.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.HE-runtime-diagnostic-unit-submission/v2',unit=unit,argv=argv,inputs_ref=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,probe_cap_seconds=90,full_qualification_accepted=False,formal_success=False)
with record.open('x') as f:
 json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items() if k!='argv'}))
raise SystemExit(p.returncode)
