"""Submit one exact source-bound finite GDN timing owner."""
import hashlib,json,subprocess
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SRC=T/'gdn_timing_v3'
ROOT=Path('/opt/host/vnf/austinov/bole-gdn-timing-owned-unit-20261020T154710Z-v3')
OUT=Path('/opt/host/vnf/austinov/run-bole-gdn3-timing-20261020T154710Z-v3')
INPUT={'path':str(SRC/'INPUTS.json'),'bytes':5287,'sha256':'2b4ee50cd0abe010d9f688a1c29fa04af0814b2163d4eae223eec725e2e57222'}
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUT['path'])==INPUT
x=json.loads(Path('/opt/host/vnf/austinov/run-bole-gdn-timing-cpu-20261020T154710Z-v3/RESULT.json').read_text())
assert x['pass_gate'] and x['primary'] is None and x['secondary']==[] and x['source_before']==x['source_after']
assert all(ref(p)==r for p,r in x['source_before'].items())
g=json.loads(Path('/opt/host/vnf/austinov/run-bole-g1-two-request-20261020T154710Z-v2/RESULT.json').read_text())
assert g['primary'] is None and g['secondary']==[] and g['source_before']==g['source_after']
assert not OUT.exists()
ROOT.mkdir(exist_ok=False)
LOCK=T/'MAIN_ADMISSION.lock'
assert LOCK.is_file() and not LOCK.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(LOCK),'/usr/bin/true'],capture_output=True).returncode==0
args=['/usr/bin/systemd-run','--quiet','--unit=bole-gdn3-timing-20261020t154710z-v3','--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=1950','--property=TimeoutStopSec=130','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(ROOT/'owner.stdout'),'--property=StandardError=append:'+str(ROOT/'owner.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(LOCK),'/usr/bin/env','BOLE_GDN3_TIMING_OWNER_ENABLE=1','/usr/bin/python3','-I','-B',str(SRC/'gdn_timing_owner/timing_owner.py'),'--execute','--inputs-ref',json.dumps(INPUT),'--output',str(OUT)]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-gdn-timing-unit-submission/v1',unit='bole-gdn3-timing-20261020t154710z-v3.service',inputs=INPUT,controller=ref(__file__),argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=1800,cleanup_seconds=120,runtime_max_seconds=1950,restart='no',independent_of_agentweb=True,formal_success=False,MAIN_admission_lock=dict(path=str(LOCK),lifetime='entire-owner',argv_prefix=['/usr/bin/flock','--nonblock','--no-fork',str(LOCK)]))
(ROOT/'SUBMITTED.json').write_text(json.dumps(event,indent=2)+'\n')
print(json.dumps({k:v for k,v in event.items() if k!='argv'}))
raise SystemExit(r.returncode)
