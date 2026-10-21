"""Submit exact G2 v12 CPU341/parser/actual cold handoff once."""
import pathlib,json,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/SOURCE_BOUND.json","bytes":908497,"sha256":"6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15"};COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/COMMANDS.json","bytes":3620,"sha256":"90634912628ba38bb1d9087915d963ab99fa9aaf7d4e2ee20770784267672bb6"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
m=json.loads(P(SOURCE['path']).read_text());x=json.loads(P(COMMANDS['path']).read_text())
assert x['bound_source']==SOURCE and x['required_sameimage_software_cases']==m['service_required_sameimage_software_cases']==341
a=json.loads((T/'G2_V12_SOURCE_AUDIT.json').read_text());assert a['exit_code']==0
q=json.loads(a['stdout']);assert q['source']==SOURCE and q['readset_count']==3679 and q['original3072_wire_cap_unchanged']is True and q['NPU']is False
authority=json.loads(P(m['authority_ref']['path']).read_text());assert ref(m['authority_ref']['path'])==m['authority_ref'] and time.time()+3780<=authority['cutoff_epoch']
record=T/'G2_V12_CPU_SUBMITTED.json';assert not record.exists()
assert not P(m['output_root']+'-CPU').exists()
lock=T/'MAIN_ADMISSION.lock';cmd=x['CPU'];assert cmd[:4]==['/usr/bin/flock','--nonblock','--no-fork',str(lock)]and cmd.count(str(lock))==1
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
unit='bole-g2-v12-cpu-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'g2-v12-cpu.stdout'),'--property=StandardError=append:'+str(T/'g2-v12-cpu.stderr'),*cmd]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
v=dict(schema='bole.finite-G2-v12-CPU-submission/v1',unit=unit,argv=argv,source=SOURCE,commands=COMMANDS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,NPU=False,pending=True,formal_success=False)
with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({k:w for k,w in v.items()if k!='argv'}))
raise SystemExit(p.returncode)
