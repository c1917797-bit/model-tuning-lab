"""Submit CPU or model once for the frozen G2 stream diagnostic."""
import argparse,json,hashlib,subprocess
from pathlib import Path
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v2/SOURCE_BOUND.json","bytes":217765,"sha256":"8ec7b3d7f7f8d070124adce92971059285026f688799645ff14342e85dbfa153"}
P=Path(SOURCE['path']).parent
ROOT=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v2')
OUT='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v2'
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['cpu','model']);a=ap.parse_args()
assert ref(SOURCE['path'])==SOURCE
ROOT.mkdir(exist_ok=True);record=ROOT/(a.phase+'-SUBMITTED.json');assert not record.exists()
output=OUT+('-CPU'if a.phase=='cpu'else'');assert not Path(output).exists()
unit='bole-g2-v2-'+a.phase+'-20261020t154710z'
args=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(ROOT/(a.phase+'.stdout')),'--property=StandardError=append:'+str(ROOT/(a.phase+'.stderr')),'/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(P/'host_service.py'),'--execute']
if a.phase=='cpu':args+=['--cpu-only']
args+=['--source-ref',json.dumps(SOURCE),'--output',output]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v1',unit=unit+'.service',source=SOURCE,phase=a.phase,argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,restart='no',independent_of_agentweb=True,controller=ref(__file__),formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
