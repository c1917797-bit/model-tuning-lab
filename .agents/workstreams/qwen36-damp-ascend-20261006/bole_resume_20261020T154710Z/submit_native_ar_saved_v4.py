"""Submit exact finite saved-nativeAR-v4 numerical CPU owner once."""
import json,pathlib,hashlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");INPUTS={"path":"/opt/host/vnf/austinov/bole-native-ar-saved-cpu-control-v4/INPUTS.json","bytes":15313,"sha256":"6cf2fcea6ae9cb25a57449c91931215851281e9a16b84a6f0b3555d707d7b95c"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
assert ref(INPUTS['path'])==INPUTS
x=json.loads(P(INPUTS['path']).read_text());assert x['schema']=='bole.native-ar-saved-requalification-inputs/v4'and x['NPU']is False and x['model_reexecution_permitted']is False
assert not P(x['output_root']).exists()
prep=json.loads((T/'NATIVE_AR_SAVED_V4_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['inputs']==INPUTS
audit=json.loads((T/'NATIVE_AR_SAVED_V4_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
v=json.loads(audit['stdout']);assert v['inputs']==INPUTS and v['readset_count']==834 and v['resources_admitted']is False and v['original_producer_failed']is True
authority=json.loads(P(x['authority']['path']).read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
record=T/'NATIVE_AR_SAVED_V4_SUBMITTED.json';assert not record.exists()
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
host=P(INPUTS['path']).parent/'saved_cpu_owner.py';unit='bole-native-ar-saved-cpu-20261020t154710z-v4.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'native-ar-saved-v4.stdout'),'--property=StandardError=append:'+str(T/'native-ar-saved-v4.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),'/usr/bin/env','BOLE_SAVED_AR_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B',str(host),'--execute','--inputs-ref',json.dumps(INPUTS)]
p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
v=dict(schema='bole.finite-saved-nativeAR-unit-submission/v4',unit=unit,argv=argv,inputs=INPUTS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,NPU=False,numerical_qualification_pending=True,formal_success=False)
with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
print(json.dumps({k:w for k,w in v.items()if k!='argv'}))
raise SystemExit(p.returncode)
