"""Submit exact saved-evidence CPU repair v3 once after actual source audit."""
import pathlib,json,subprocess,hashlib,os
P=pathlib.Path
T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
record=T/'NATIVE_AR_SAVED_CPU_V3_SUBMITTED.json'
assert not record.exists()
prep=json.loads((T/'NATIVE_AR_SAVED_V3_PREPARATION.json').read_text())
assert prep['returncode']==0
ip=json.loads(prep['stdout'])['inputs']
assert ref(ip['path'])==ip
y=json.loads(P(ip['path']).read_text())
assert y['schema']=='bole.native-ar-saved-requalification-inputs/v3' and not P(y['output_root']).exists()
root=P(ip['path']).parent
host=root/'saved_cpu_owner.py'
lock=T/'MAIN_ADMISSION.lock'
assert lock.is_file() and not lock.is_symlink() and lock.stat().st_mode & 0o777 == 0o600
audit=json.loads((T/'NATIVE_AR_SAVED_V3_SOURCE_AUDIT.json').read_text())
assert audit['returncode']==0
assert audit['argv']==['/usr/bin/python3','-I','-B',str(host),'--source-audit','--inputs-ref',json.dumps(ip)]
proof=json.loads(audit['stdout'])
assert proof['inputs']==ip and proof['resources_admitted'] is False and proof['original_producer_failed'] is True and proof['readset_count']>=767
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
unit='bole-native-ar-saved-cpu-20261020t154710z-v3.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'native-ar-saved-cpu-v3.stdout'),'--property=StandardError=append:'+str(T/'native-ar-saved-cpu-v3.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_SAVED_AR_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(ip)]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.saved-AR-CPU-repair-unit-submission/v3',unit=unit,argv=argv,inputs_ref=ip,controller=ref(__file__),submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,formal_success=False)
with record.open('x') as f:
 json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items() if k!='argv'}))
raise SystemExit(r.returncode)
