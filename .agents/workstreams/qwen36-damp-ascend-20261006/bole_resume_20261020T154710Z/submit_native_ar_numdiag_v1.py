"""Submit exact finite saved-native FA coordinate diagnostic once."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");INPUTS={"path":"/opt/host/vnf/austinov/bole-native-ar-numdiag-control-v1/INPUTS.json","bytes":7112,"sha256":"8edd96f8c8bb4c1207c0ff4deaf0a1a1034c435c23357817efff6ecfa5c86d7a"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUTS['path'])==INPUTS
x=json.loads(P(INPUTS['path']).read_text());assert x['schema']=='bole.native-ar-numeric-diagnostic-inputs/v1'and x['NPU']is False and x['formal_success']is False
assert not P(x['output_root']).exists()
prep=json.loads((T/'NATIVE_AR_NUMERIC_DIAGNOSTIC_V1_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs']==INPUTS
audit=json.loads((T/'NATIVE_AR_NUMERIC_DIAGNOSTIC_V1_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
a=json.loads(audit['stdout']);assert a['inputs']==INPUTS and a['readset_count']==874 and a['resources_admitted']is False and a['original_G1_math_rerun']is False
authority=json.loads(P(x['authority']['path']).read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
record=T/'NATIVE_AR_NUMERIC_DIAGNOSTIC_V1_SUBMITTED.json';assert not record.exists()
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
host=P(INPUTS['path']).parent/'numeric_cpu_owner.py';unit='bole-native-ar-numdiag-20261020t154710z-v1.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'native-ar-numdiag-v1.stdout'),'--property=StandardError=append:'+str(T/'native-ar-numdiag-v1.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_NATIVE_NUMERIC_DIAGNOSTIC_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
v=dict(schema='bole.finite-native-FA-numeric-diagnostic-submission/v1',unit=unit,argv=argv,inputs=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,NPU=False,diagnostic_pending=True,formal_success=False)
with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({k:w for k,w in v.items()if k!='argv'}))
raise SystemExit(p.returncode)
