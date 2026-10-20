"""Submit CPU or model once for the frozen G2 stream diagnostic."""
import argparse,json,hashlib,subprocess
from pathlib import Path
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v4/SOURCE_BOUND.json","bytes":328177,"sha256":"c20ff6d58e8ac9a44f20060f96b20c71c56ebaa4425eb33590f77e35644b0877"}
P=Path(SOURCE['path']).parent
ROOT=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v4')
OUT='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v4'
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['cpu','model']);a=ap.parse_args()
assert ref(SOURCE['path'])==SOURCE
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
LOCK=T/'MAIN_ADMISSION.lock'
assert LOCK.is_file() and not LOCK.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(LOCK),'/usr/bin/true'],capture_output=True).returncode==0
prep=json.loads((T/'G2_V4_PREPARATION.json').read_text());assert prep['exit_code']==0
presult=json.loads(prep['stdout']);assert presult['source']==SOURCE and presult['runtime_math_stream_CPUbudget_unchanged'] is True and presult['exact_readset_closure']['missing']==[]
ROOT.mkdir(exist_ok=True);record=ROOT/(a.phase+'-SUBMITTED.json');assert not record.exists()
output=OUT+('-CPU'if a.phase=='cpu'else'');assert not Path(output).exists()
unit='bole-g2-v4-'+a.phase+'-20261020t154710z'
args=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(ROOT/(a.phase+'.stdout')),'--property=StandardError=append:'+str(ROOT/(a.phase+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(LOCK),'/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(P/'host_service.py'),'--execute']
if a.phase=='cpu':args+=['--cpu-only']
args+=['--source-ref',json.dumps(SOURCE),'--output',output]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v1',unit=unit+'.service',source=SOURCE,phase=a.phase,argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,restart='no',independent_of_agentweb=True,controller=ref(__file__),formal_success=False,MAIN_admission_lock=dict(path=str(LOCK),lifetime='entire-owner',argv_prefix=['/usr/bin/flock','--nonblock','--no-fork',str(LOCK)]))
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
