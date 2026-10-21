"""Submit one exact G2-v12 MODEL after independent CPU341 qualification."""
import argparse,hashlib,json,pathlib,subprocess,time
P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/SOURCE_BOUND.json","bytes":908497,"sha256":"6c925c8e827b4761926645b89c5897ef25d7e81a80664cb4b4def75076c05d15"}
COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12/COMMANDS.json","bytes":3620,"sha256":"90634912628ba38bb1d9087915d963ab99fa9aaf7d4e2ee20770784267672bb6"}
QUAL={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V12_CPU_READBACK.json","bytes":787650,"sha256":"259c07e794a336f66678b1c9caceb8c8200b157b897764f6e980c28c63904a5a"}
RESULT={"path":"/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12-CPU/RESULT.json","bytes":1202315,"sha256":"d7f90208d7faf168fda68d61b08e15c066e00b0e37da54111445bd41b9b34cee"}
UNIT={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V12_CPU_SYSTEMD_TERMINAL.json","bytes":361,"sha256":"f98de0d3d059dd979f24ab662d50c8908d1be5caa604825372c3aeceb69341c3"}
READER=dict(path=str(T/'g2_v12_cpu_readback_v2/readback_cpu.py'),bytes=51180,sha256='bbd3f5502ab28f9fe5957c678114faaf34a9a5b70419c97c8681f22f83e18c33')
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
 assert q['schema']=='bole.actual-G2-v12-CPU-independent-qualification/v1' and q['source']==SOURCE and q['result_ref']==RESULT and q['finite_unit_ref']==UNIT and q['finite_unit']==u
 assert q['sameimage_341_parser_and_actual_cold_handoff_pass']is True and q['all_owned_stopped_retained']is True and q['source_nonempty_before_after_equal']is True and q['source_readset_count']==3679 and q['software']['tests']==341 and q['stdlib_only']is True and q['NPU']is False and q['model_ready']is False and q['formal_success']is False
 assert r['source']==SOURCE and r['primary']is None and r['secondary']==[] and r['source_before']==r['source_after']and len(r['source_before'])==3679
 assert u['properties']['MainPID']==u['properties']['ControlPID']=='0'and u['properties']['Result']=='success'and u['properties']['ExecMainStatus']=='0'
 assert x['bound_source']==SOURCE and x['required_sameimage_software_cases']==m['service_required_sameimage_software_cases']==341
 audit=json.loads((T/'G2_V12_SOURCE_AUDIT.json').read_text());assert audit['exit_code']==0 and json.loads(audit['stdout'])['source']==SOURCE
 authority=obj(m['authority_ref']);assert time.time()+3780<=authority['cutoff_epoch']
 assert not P(m['output_root']).exists()
 record=T/'G2_V12_MODEL_SUBMITTED.json';assert not record.exists()
 lock=T/'MAIN_ADMISSION.lock';cmd=x['model']
 assert cmd[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']and str(lock)not in cmd
 assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
 for unit in ['bole-g2-v12-cpu-20261020t154710z.service','bole-gdn-matched-v4-cpu-20261020t154710z.service']:
  state=subprocess.run(['systemctl','show',unit,'--property=MainPID,ControlPID'],capture_output=True,text=True,check=True)
  fields=dict(v.split('=',1)for v in state.stdout.splitlines());assert fields==dict(MainPID='0',ControlPID='0')
 unit='bole-g2-v12-model-20261020t154710z.service'
 argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'g2-v12-model.stdout'),'--property=StandardError=append:'+str(T/'g2-v12-model.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*cmd]
 z=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
 v=dict(schema='bole.finite-G2-v12-MODEL-submission/v1',unit=unit,argv=argv,source=SOURCE,commands=COMMANDS,CPU_qualification=QUAL,controller=ref(__file__),submit_exit=z.returncode,stdout=z.stdout,stderr=z.stderr,phase_seconds=3600,cleanup_seconds=180,NPU_requested=True,MODEL_qualification_pending=True,formal_success=False)
 with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:w for k,w in v.items()if k!='argv'}));return z.returncode
if __name__=='__main__':raise SystemExit(main())
