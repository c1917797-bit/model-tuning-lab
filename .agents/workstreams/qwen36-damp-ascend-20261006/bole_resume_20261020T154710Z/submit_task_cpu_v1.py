"""Submit one finite serial CPU/tokenizer/HE-controls software owner."""
import pathlib,hashlib,json,subprocess
T=pathlib.Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUT={"path":"/opt/host/vnf/austinov/bole-task-cpu-20261020T154710Z-v1/OWNER_INPUTS.json","bytes":52333,"sha256":"a5a94e16e2789530a252943c5f818c1210954853a4546048b96ae893db95af93"}
ROOT=pathlib.Path('/opt/host/vnf/austinov/bole-task-cpu-owned-unit-20261020T154710Z-v1')
OUT=pathlib.Path('/opt/host/vnf/austinov/run-bole-task-cpu-20261020T154710Z-v1')
def ref(p):
 p=pathlib.Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUT['path'])==INPUT and not OUT.exists()
assert json.loads((T/'TASK_CPU_V1_SOURCE_AUDIT.json').read_text())['exit_code']==0
ROOT.mkdir()
args=['/usr/bin/systemd-run','--quiet','--unit=bole-task-cpu-20261020t154710z-v1','--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(ROOT/'owner.stdout'),'--property=StandardError=append:'+str(ROOT/'owner.stderr'),'/usr/bin/env','BOLE_TASK_CPU_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(pathlib.Path(INPUT['path']).parent/'cpu_host.py'),'--execute','--inputs-ref',json.dumps(INPUT)]
r=subprocess.run(args,capture_output=True,text=True,timeout=30)
x=dict(schema='bole.finite-task-CPU-unit-submission/v1',unit='bole-task-cpu-20261020t154710z-v1.service',inputs=INPUT,controller=ref(__file__),argv=args,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,phase_seconds=3600,cleanup_seconds=180,runtime_max_seconds=3900,restart='no',independent_of_agentweb=True,NPU=False,model_ready=False,task_score_produced=False,formal_success=False)
(ROOT/'SUBMITTED.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({k:v for k,v in x.items()if k!='argv'}));raise SystemExit(r.returncode)
