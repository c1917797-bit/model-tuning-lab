"""Submit exact G2 v7 current source-owned CPU or model command once."""
import argparse,json,hashlib,subprocess
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v7/SOURCE_BOUND.json","bytes":542194,"sha256":"a1f7238ccde08744e90a69a30b316bc10bfe1995e57d3898ced46779ee067032"}
COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v7/COMMANDS.json","bytes":3610,"sha256":"b871bf1e0599fe73a45eae5ade839d646675e47a8057eb2e2eeb115d808b4a12"}
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('phase',choices=['cpu','model'])
a=p.parse_args()
assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
prep=json.loads((T/'G2_V7_PREPARATION.json').read_text())
assert prep['exit_code']==0 and json.loads(prep['stdout'])['source']==SOURCE
audit=json.loads((T/'G2_V7_SOURCE_AUDIT.json').read_text())
assert audit['exit_code']==0
proof=json.loads(audit['stdout'])
assert proof['schema']=='bole.G2-v7-source-readonly-audit/v1' and proof['source']==SOURCE
assert proof['exact_owner_inverse'] is True and proof['original_runtime_math_consumer_resource_and258_controls_unchanged'] is True
commands=json.loads(Path(COMMANDS['path']).read_text())
assert commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==266
target=commands['CPU' if a.phase=='cpu' else 'model']
assert target[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']
assert target[6]==str(Path(SOURCE['path']).parent/'host_service.py')
output=target[target.index('--output')+1]
assert not Path(output).exists()
lock=T/'MAIN_ADMISSION.lock'
assert lock.is_file() and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
root=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v7')
root.mkdir(exist_ok=True)
record=root/(a.phase+'-SUBMITTED.json')
assert not record.exists()
unit='bole-g2-v7-'+a.phase+'-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(root/(a.phase+'.stdout')),'--property=StandardError=append:'+str(root/(a.phase+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*target]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v2',unit=unit,source=SOURCE,commands=COMMANDS,phase=a.phase,argv=argv,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,restart='no',independent_of_agentweb=True,controller=ref(__file__),actual_software_cases_pending=266,formal_success=False,MAIN_admission_lock=dict(path=str(lock),lifetime='entire-owner',argv_prefix=['/usr/bin/flock','--nonblock','--no-fork',str(lock)]))
with record.open('x') as f:
 json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items() if k!='argv'}))
raise SystemExit(r.returncode)
