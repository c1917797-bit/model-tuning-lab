"""Submit the exact source-audited finite CPU0 saved mask diagnostic once."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path
T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
INPUTS={"path":"/opt/host/vnf/austinov/bole-native-ar-mask-control-v3/INPUTS.json","bytes":5511,"sha256":"f4bcc31d0fe26a82771a872c54dbad846fe31d38e945a894eda319ae14184c09"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUTS['path'])==INPUTS
x=json.loads(P(INPUTS['path']).read_text())
assert x['schema']=='bole.native-ar-mask-diagnostic-inputs/v1' and x['NPU'] is False
assert not P(x['output_root']).exists()
for n,r in x['files'].items():assert ref(r['path'])==r and P(r['path'])==P(INPUTS['path']).parent/n
prep=json.loads((T/'NATIVE_AR_MASK_V3_PREPARATION.json').read_text())
assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs']==INPUTS
audit=json.loads((T/'NATIVE_AR_MASK_V3_SOURCE_AUDIT.json').read_text())
assert audit['exit_code']==0
proof=json.loads(audit['stdout'])
assert proof['inputs']==INPUTS and proof['readset_count']==791 and proof['resources_admitted'] is False and proof['original_G1_math_rerun'] is False
authority=json.loads(P(x['authority']['path']).read_text())
assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock'
assert lock.is_file() and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
record=T/'NATIVE_AR_MASK_V3_SUBMITTED.json'
assert not record.exists()
unit='bole-native-ar-mask-diagnostic-20261020t154710z-v3.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'native-ar-mask-v3.stdout'),'--property=StandardError=append:'+str(T/'native-ar-mask-v3.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_NATIVE_MASK_DIAGNOSTIC_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(P(INPUTS['path']).parent/'mask_cpu_owner.py'),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.saved-mask-diagnostic-unit-submission/v1',unit=unit,argv=argv,inputs=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,source_preflight_seconds=300,metadata_child_seconds=900,guest_CPU=0,NPU=False,mathematics_recomputed=False,formal_success=False)
with record.open('x') as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items() if k!='argv'}))
raise SystemExit(p.returncode)
