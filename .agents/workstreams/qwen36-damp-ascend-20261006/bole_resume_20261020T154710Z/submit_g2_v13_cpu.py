"""Default OFF exact G2 v13 CPU349/parser/cold submission."""
import argparse
import pathlib,json,hashlib,subprocess,time
def main():
 a0=argparse.ArgumentParser(allow_abbrev=False);a0.add_argument("--execute",action="store_true");a0v=a0.parse_args()
 if not a0v.execute:print('{"enabled":false,"NPU":false}');return 0
 P=pathlib.Path;T=P("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z");SOURCE={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json","bytes":994678,"sha256":"545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345"};COMMANDS={"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/COMMANDS.json","bytes":3620,"sha256":"93b6cf7022a491e4d7e048c87b0bc889c18ce822da2f2c82a9111ab4be9623c3"}
 def ref(p):
  p=P(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 assert ref(SOURCE['path'])==SOURCE and ref(COMMANDS['path'])==COMMANDS
 m=json.loads(P(SOURCE['path']).read_text());x=json.loads(P(COMMANDS['path']).read_text())
 assert x['bound_source']==SOURCE and x['required_sameimage_software_cases']==m['service_required_sameimage_software_cases']==349
 a=json.loads((T/'G2_V13_SOURCE_AUDIT.json').read_text());assert a['exit_code']==0
 q=json.loads(a['stdout']);assert q['source']==SOURCE and q['readset_count']==4088 and q['original_math_ACK_cap_argv_transport_resources_unchanged']is True and q['original_finalizer_budget_selects_HTTP_files']is True and q['NPU']is False
 authority=json.loads(P(m['authority_ref']['path']).read_text());assert ref(m['authority_ref']['path'])==m['authority_ref'] and time.time()+3780<=authority['cutoff_epoch']
 record=T/'G2_V13_CPU_SUBMITTED.json';assert not record.exists()
 assert not P(m['output_root']+'-CPU').exists()
 prior=json.loads((T/'NATIVE_AR_FIA_V2_SYSTEMD_TERMINAL.json').read_text())['properties']
 assert prior['MainPID']==prior['ControlPID']=='0' and prior['ExecMainStatus']in('0','3') and prior['SubState']in('exited','failed')
 now=dict(line.split('=',1)for line in subprocess.run(['/usr/bin/systemctl','show','bole-native-ar-fia-20261020t154710z-v2.service','--property=MainPID,ControlPID,ExecMainStatus,Result,ActiveState,SubState'],capture_output=True,text=True,check=True).stdout.splitlines())
 assert all(now[k]==prior[k]for k in now)and now['MainPID']==now['ControlPID']=='0'
 assert authority['cutoff_epoch']==1792597630 and m['g2_http_visibility_v13']['new_HTTP_controls']==8
 lock=T/'MAIN_ADMISSION.lock';cmd=x['CPU'];assert cmd[:6]==['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','/usr/bin/python3','-I','-B']and str(lock)not in cmd
 assert subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True).returncode==0
 unit='bole-g2-v13-cpu-20261020t154710z.service'
 argv=['/usr/bin/systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RemainAfterExit=yes','--property=Restart=no','--property=RuntimeMaxSec=3900','--property=TimeoutStopSec=180','--property=KillSignal=SIGTERM','--property=CPUAffinity=166','--property=MemoryMax=512M','--property=WorkingDirectory=/opt/host/vnf/austinov/model-tuning-lab','--property=StandardOutput=append:'+str(T/'g2-v13-cpu.stdout'),'--property=StandardError=append:'+str(T/'g2-v13-cpu.stderr'),'/usr/bin/flock','--nonblock','--no-fork',str(lock),*cmd]
 p=subprocess.run(argv,cwd=T,capture_output=True,text=True,timeout=30)
 v=dict(schema='bole.finite-G2-v13-CPU-submission/v1',unit=unit,argv=argv,source=SOURCE,commands=COMMANDS,controller=ref(__file__),submit_exit=p.returncode,stdout=p.stdout,stderr=p.stderr,phase_seconds=3600,cleanup_seconds=180,NPU=False,pending=True,formal_success=False)
 with record.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({k:w for k,w in v.items()if k!='argv'}))
 return p.returncode

if __name__=="__main__":raise SystemExit(main())
