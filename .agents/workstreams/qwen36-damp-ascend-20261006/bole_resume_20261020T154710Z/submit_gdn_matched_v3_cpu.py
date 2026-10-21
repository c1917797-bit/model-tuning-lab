"""Submit exact GDN matched v3 CPU qualification once under original MAIN clock."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
source=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v3/SOURCE_BOUND.json',bytes=112215,sha256='f1c1c96aee26844daaf538d516bd65791d83ada35737f3b10aef198329d69e88')
commands=dict(path='/opt/host/vnf/austinov/bole-gdn-g1-probe-matched-v3/COMMANDS.json',bytes=3848,sha256='6610ba8aa6d4a23d2c9cc0dc8ed89e4d0a3dcb87dcc3143761ec56870f52ecca')
assert ref(source['path'])==source and ref(commands['path'])==commands
x=json.loads(P(commands['path']).read_text());assert x['bound_source']==source and x['required_sameimage_software_cases']==240
audit=json.loads((T/'GDN_SERVICE_MATCHED_V3_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
a=json.loads(audit['stdout']);assert a['source']==source and a['readset']==744 and a['resources_admitted']is False
s=json.loads(P(source['path']).read_text());authority=json.loads(P(s['authority_ref']['path']).read_text());assert ref(s['authority_ref']['path'])==s['authority_ref']
assert time.time()+3780<=authority['cutoff_epoch']
record=T/'GDN_MATCHED_V3_CPU_SUBMITTED.json';assert not record.exists()
assert not P('/opt/host/vnf/austinov/run-bole-gdn-g1-probe-matched-v3-CPU').exists()
lock=T/'MAIN_ADMISSION.lock';cmd=x['CPU'];assert cmd[:4]==['/usr/bin/flock','--nonblock','--no-fork',str(lock)]and cmd.count(str(lock))==1
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
term=json.loads((T/'NATIVE_AR_FIA_V1_SYSTEMD_TERMINAL.json').read_text())['properties'];assert term['MainPID']==term['ControlPID']=='0'
unit='bole-gdn-matched-v3-cpu-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'gdn-matched-v3-cpu.stdout'),'--property=StandardError=append:'+str(T/'gdn-matched-v3-cpu.stderr'),*cmd]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
v=dict(schema='bole.finite-GDN-matched-v3-CPU-submission/v1',unit=unit,argv=argv,source=source,commands=commands,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,NPU=False,pending=True,formal_success=False)
with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({k:w for k,w in v.items()if k!='argv'}))
raise SystemExit(p.returncode)
