"""Submit one exact G2-v13 MODEL after independent CPU349 qualification."""
import argparse,hashlib,json,pathlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"bytes":994678,"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json","sha256":"545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345"}
COMMANDS={"bytes":3620,"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/COMMANDS.json","sha256":"93b6cf7022a491e4d7e048c87b0bc889c18ce822da2f2c82a9111ab4be9623c3"}
QUAL={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V13_CPU_READBACK.json","bytes":886254,"sha256":"180f5e76f067e60c901e5e397cc03b225cf41a81f4d24f3669a3d96609c9b490"}
RESULT={"path":"/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13-CPU/RESULT.json","bytes":1336395,"sha256":"94ac87cf1cb556c5c17f8924e72a4036c5fc8d1e9c1b3fdbe1546a6859ec6d48"}
UNIT={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V13_CPU_SYSTEMD_TERMINAL.json","bytes":312,"sha256":"01881f65a064d7686ef1a0777290478cf8a4a637991faf1cdfa267359b4ae168"}
READER={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_v13_cpu_readback_v1/readback_cpu.py","bytes":57773,"sha256":"88453a988febf2d074ca4315a8e376faca6038ef0b54369deb0343034d2cfeef"}
def ref(p):
 p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 assert ref(r['path'])==r
 return json.loads(P(r['path']).read_text())
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 q=obj(QUAL);m=obj(SOURCE);x=obj(COMMANDS);r=obj(RESULT);u=obj(UNIT);obj(READER) if False else None
 assert ref(READER['path'])==READER and q['reader_ref']==READER and q['reader_source_before_after_equal']is True
 assert q['schema']=='bole.actual-G2-v13-CPU-independent-qualification/v1' and q['source']==SOURCE and q['result_ref']==RESULT and q['finite_unit_ref']==UNIT and q['finite_unit']==u
 assert q['sameimage_349_parser_and_actual_cold_handoff_pass']is True and q['all_owned_stopped_retained']is True and q['source_nonempty_before_after_equal']is True and q['source_readset_count']==4088 and q['software']['tests']==349 and q['stdlib_only']is True and q['NPU']is False and q['model_ready']is False and q['formal_success']is False
 assert r['source']==SOURCE and r['primary']is None and r['secondary']==[] and r['source_before']==r['source_after']and len(r['source_before'])==4088
 assert u['properties']['MainPID']==u['properties']['ControlPID']=='0'and u['properties']['Result']=='success'and u['properties']['ExecMainStatus']=='0'
 assert x['bound_source']==SOURCE and x['required_sameimage_software_cases']==m['service_required_sameimage_software_cases']==349
 audit=json.loads((T/'G2_V13_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0 and json.loads(audit['stdout'])['source']==SOURCE
 authority=obj(m['authority_ref']);assert authority['cutoff_epoch']==1792597630 and time.time()+3780<=authority['cutoff_epoch']
 assert not P(m['output_root']).exists()
 record=T/'G2_V13_MODEL_SUBMITTED.json';assert not record.exists()
 lock=T/'MAIN_ADMISSION.lock';cmd=x['model']
 assert cmd[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']and str(lock)not in cmd
 assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
 for unit in ['bole-g2-v13-cpu-20261020t154710z.service','bole-gdn-matched-v4-cpu-20261020t154710z.service','bole-native-ar-fia-20261020t154710z-v2.service']:
  state=subprocess.run(['systemctl','show',unit,'--property=MainPID,ControlPID'],capture_output=True,text=True,check=True)
  fields=dict(v.split('=',1)for v in state.stdout.splitlines());assert fields==dict(MainPID='0',ControlPID='0')
 unit='bole-g2-v13-model-20261020t154710z.service'
 argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'g2-v13-model.stdout'),'--property=StandardError=append:'+str(T/'g2-v13-model.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*cmd]
 z=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
 v=dict(schema='bole.finite-G2-v13-MODEL-submission/v1',unit=unit,argv=argv,source=SOURCE,commands=COMMANDS,CPU_qualification=QUAL,controller=ref(__file__),submit_exit=z.returncode,stdout=z.stdout,stderr=z.stderr,phase_seconds=3600,cleanup_seconds=180,NPU_requested=True,MODEL_qualification_pending=True,formal_success=False)
 with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:w for k,w in v.items()if k!='argv'}));return z.returncode
if __name__=='__main__':raise SystemExit(main())
