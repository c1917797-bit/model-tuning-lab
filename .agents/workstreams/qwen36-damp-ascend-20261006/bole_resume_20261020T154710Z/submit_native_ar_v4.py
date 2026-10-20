"""Submit one finite native AR reference owner after source audit."""
import pathlib,json,hashlib,subprocess
T=pathlib.Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUT={"path":"/opt/host/vnf/austinov/bole-native-ar-owner-20261020T154710Z-v4/INPUTS.json","bytes":13055,"sha256":"acb3b514ed9a468cd30f5d4b2e450c26de18f98d3037cf534b6d1c6520ce4b31"}
P=pathlib.Path(INPUT['path']).parent
ROOT=pathlib.Path('/opt/host/vnf/austinov/bole-native-ar-owned-unit-20261020T154710Z-v4')
OUT=pathlib.Path('/opt/host/vnf/austinov/run-bole-native-ar-20261020T154710Z-v4')
def ref(p):
 p=pathlib.Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUT['path'])==INPUT and not OUT.exists()
a=json.loads((T/'NATIVE_AR_V4_SOURCE_AUDIT.json').read_text());assert a['exit_code']==0
LOCK=T/'MAIN_ADMISSION.lock'
assert LOCK.is_file() and not LOCK.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(LOCK),'/usr/bin/true'],capture_output=True).returncode==0
ROOT.mkdir()
args=['/usr/bin/systemd-run','--quiet','--unit=bole-native-ar-20261020t154710z-v4','--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(ROOT/'owner.stdout'),'--property=StandardError=append:'+str(ROOT/'owner.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(LOCK),'/usr/bin/env','BOLE_NATIVE_AR_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(P/'native_ar_host.py'),'--execute','--inputs-ref',json.dumps(INPUT)]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-native-ar-unit-submission/v1',unit='bole-native-ar-20261020t154710z-v4.service',inputs=INPUT,controller=ref(__file__),argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,restart='no',independent_of_agentweb=True,formal_success=False,MAIN_admission_lock=dict(path=str(LOCK),lifetime='entire-owner',argv_prefix=['/usr/bin/flock','--nonblock','--no-fork',str(LOCK)]))
(ROOT/'SUBMITTED.json').write_text(json.dumps(event,indent=2)+'\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
