"""Submit the exact source-audited G2-v8 CPU or model phase once."""
import argparse,json,hashlib,subprocess,time
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v8/SOURCE_BOUND.json","bytes":612583,"sha256":"ae03ae1e05711105642b4d07763384f38ed190f1defa4a9ac748389e88daa601"}
COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v8/COMMANDS.json","bytes":3610,"sha256":"1111830416da84474b08f56b3ba5e3360e0c89dccf5dc62fa6c32a475052baa1"}
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('phase',choices=['cpu','model']);a=a.parse_args()
assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
prep=json.loads((T/'G2_V8_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['source']==SOURCE
audit=json.loads((T/'G2_V8_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
proof=json.loads(audit['stdout']);assert proof['schema']=='bole.G2-v8-source-readonly-audit/v1' and proof['source']==SOURCE
assert proof['exact_metadata_and_lifecycle_inverse'] is True and proof['original266_assertions_math_consumer_finalizer_resources_preserved'] is True
assert proof['original_15_stream_test_bodies_AST_exact'] is True and proof['original64MiB_per_rank_metadata_cap_unchanged'] is True
commands=json.loads(Path(COMMANDS['path']).read_text());assert commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==279
if a.phase=='model':
 gate=json.loads((T/'G2_V8_CPU_READBACK.json').read_text())
 assert gate['source']==SOURCE and gate['sameimage_279_parser_and_actual_cold_handoff_pass'] is True and gate['all_owned_stopped_retained'] is True
 assert ref(gate['result_ref']['path'])==gate['result_ref']
target=commands['CPU' if a.phase=='cpu'else'model']
assert target[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']
assert target[6]==str(Path(SOURCE['path']).parent/'host_service.py')and('--cpu-only'in target)==(a.phase=='cpu')
output=target[target.index('--output')+1];assert not Path(output).exists()
authority=json.loads((T/'MODEL_AUTHORITY.json').read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
root=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v8');root.mkdir(exist_ok=True)
record=root/(a.phase+'-SUBMITTED.json');assert not record.exists()
unit='bole-g2-v8-'+a.phase+'-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(root/(a.phase+'.stdout')),'--property=StandardError=append:'+str(root/(a.phase+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*target]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v3',unit=unit,source=SOURCE,commands=COMMANDS,phase=a.phase,argv=argv,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,controller=ref(__file__),required_fresh_sameimage_cases=279,actual_cold_handoff_before_NPU_required=True,phase_seconds=3600,cleanup_seconds=180,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
