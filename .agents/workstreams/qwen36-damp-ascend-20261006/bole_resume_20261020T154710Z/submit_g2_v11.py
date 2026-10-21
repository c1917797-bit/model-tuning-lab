"""Submit the exact source-audited G2-v11 CPU or model phase once."""
import argparse,json,hashlib,subprocess,time
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11/SOURCE_BOUND.json","bytes":824421,"sha256":"0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01"}
COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11/COMMANDS.json","bytes":3620,"sha256":"c3a85458a4ccfe56192f53fbb929db6026051146d593330badcb529d7028005f"}
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('phase',choices=['cpu','model']);a=a.parse_args()
assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
prep=json.loads((T/'G2_V11_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['source']==SOURCE
audit=json.loads((T/'G2_V11_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
proof=json.loads(audit['stdout']);assert proof['schema']=='bole.G2-v11-software-stages-readonly-audit/v1' and proof['source']==SOURCE
assert proof['whole_host_inverse']is True and proof['all_original304_test_files_byteexact']is True
assert proof['original_math128_argv_transport_caps_metadata_resources_unchanged']is True and proof['readset_count']==3280
assert proof['software_allocation_seconds']==dict(parent279=120.0,controls=60.0,metadata=120.0)and proof['software_aggregate_cap_seconds']==300.0
assert (proof['source8_fresh_cases'],proof['source10_fresh_cases'],proof['current11_fresh_cases'],proof['prospective_sameimage_cases'])==(279,25,18,322)
assert all(proof['firstentry_clock'][k]is True for k in ('source_hashes_in_phase','one_main_entry_clock','deadline_renewal_forbidden'))
commands=json.loads(Path(COMMANDS['path']).read_text());assert commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==322
if a.phase=='model':
 gate=json.loads((T/'G2_V11_CPU_READBACK.json').read_text())
 assert gate['source']==SOURCE and gate['sameimage_322_parser_and_actual_cold_handoff_pass'] is True and gate['all_owned_stopped_retained'] is True
 assert ref(gate['result_ref']['path'])==gate['result_ref']
target=commands['CPU' if a.phase=='cpu'else'model']
assert target[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']
assert target[6]==str(Path(SOURCE['path']).parent/'host_service.py')and('--cpu-only'in target)==(a.phase=='cpu')
output=target[target.index('--output')+1];assert not Path(output).exists()
authority=json.loads((T/'MODEL_AUTHORITY.json').read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
root=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v11');root.mkdir(exist_ok=True)
record=root/(a.phase+'-SUBMITTED.json');assert not record.exists()
unit='bole-g2-v11-'+a.phase+'-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(root/(a.phase+'.stdout')),'--property=StandardError=append:'+str(root/(a.phase+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*target]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v3',unit=unit,source=SOURCE,commands=COMMANDS,phase=a.phase,argv=argv,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,controller=ref(__file__),required_fresh_sameimage_cases=322,actual_cold_handoff_before_NPU_required=True,phase_seconds=3600,cleanup_seconds=180,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
