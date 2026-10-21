"""Submit the exact source-audited G2-v10 CPU or model phase once."""
import argparse,json,hashlib,subprocess,time
from pathlib import Path
T=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v10/SOURCE_BOUND.json","bytes":752323,"sha256":"af907e01b7143a476459095fad32db5110a940392584c40a4886763a03a9081c"}
COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v10/COMMANDS.json","bytes":3620,"sha256":"ffcdcb1934e94dc9eb4a7d47ced43d5cc6bb3ce862ec5e315e8e5009f0c2a32b"}
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('phase',choices=['cpu','model']);a=a.parse_args()
assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
prep=json.loads((T/'G2_V10_PREPARATION.json').read_text());assert prep['exit_code']==0 and json.loads(prep['stdout'])['source']==SOURCE
audit=json.loads((T/'G2_V10_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0
proof=json.loads(audit['stdout']);assert proof['schema']=='bole.G2-v10-source-readonly-audit/v1' and proof['source']==SOURCE
assert proof['whole_callee_inverse']is True and proof['all_original297_test_bytes_preserved']is True and proof['original_candidate_leaf']is True
assert proof['original_math_128_argv_metadata_caps_resources_unchanged']is True and proof['readset_count']==2936
assert all(proof['cold_clock'][k]is True for k in ('source_hashes_in_phase','one_main_entry_clock','deadline_renewal_forbidden'))
commands=json.loads(Path(COMMANDS['path']).read_text());assert commands['bound_source']==SOURCE and commands['required_sameimage_software_cases']==304
if a.phase=='model':
 gate=json.loads((T/'G2_V10_CPU_READBACK.json').read_text())
 assert gate['source']==SOURCE and gate['sameimage_304_parser_and_actual_cold_handoff_pass'] is True and gate['all_owned_stopped_retained'] is True
 assert ref(gate['result_ref']['path'])==gate['result_ref']
target=commands['CPU' if a.phase=='cpu'else'model']
assert target[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']
assert target[6]==str(Path(SOURCE['path']).parent/'host_service.py')and('--cpu-only'in target)==(a.phase=='cpu')
output=target[target.index('--output')+1];assert not Path(output).exists()
authority=json.loads((T/'MODEL_AUTHORITY.json').read_text());assert time.time()+3600+180<=authority['cutoff_epoch']
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file()and not lock.is_symlink()
assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
root=Path('/opt/host/vnf/austinov/bole-g2-owned-units-20261020T154710Z-v10');root.mkdir(exist_ok=True)
record=root/(a.phase+'-SUBMITTED.json');assert not record.exists()
unit='bole-g2-v10-'+a.phase+'-20261020t154710z.service'
argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(root/(a.phase+'.stdout')),'--property=StandardError=append:'+str(root/(a.phase+'.stderr')),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*target]
r=subprocess.run(argv,capture_output=True,text=True,timeout=30)
event=dict(schema='bole.finite-owned-G2-unit-submission/v3',unit=unit,source=SOURCE,commands=COMMANDS,phase=a.phase,argv=argv,submit_exit=r.returncode,stdout=r.stdout,stderr=r.stderr,controller=ref(__file__),required_fresh_sameimage_cases=304,actual_cold_handoff_before_NPU_required=True,phase_seconds=3600,cleanup_seconds=180,formal_success=False)
with record.open('x')as f:json.dump(event,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in event.items()if k!='argv'}))
raise SystemExit(r.returncode)
