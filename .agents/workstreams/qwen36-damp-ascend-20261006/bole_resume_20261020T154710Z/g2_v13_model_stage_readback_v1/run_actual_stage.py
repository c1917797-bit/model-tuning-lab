import argparse,hashlib,json,os,pathlib,resource,subprocess,time
T=pathlib.Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
SOURCE={"bytes":994678,"path":"/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json","sha256":"545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345"}
RESULT={"path":"/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13/RESULT.json","bytes":1340078,"sha256":"e326a53f47c65aff4a498ac30da5568009c22e81cd9e469b2f46a28f086ebb67"}
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def check(r):
 p=pathlib.Path(r['path']);need(ref(p)==r,'whole file '+str(p));return json.loads(p.read_bytes())
def save(p,x):
 with p.open('x')as f:json.dump(x,f,sort_keys=True);f.write('\n')
 return ref(p)
def main():
 a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('--execute',action='store_true');q=a.parse_args()
 if not q.execute:print('{"enabled":false,"NPU":false}');return
 os.sched_setaffinity(0,{166});resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
 owner=check(RESULT);check(SOURCE)
 need(owner['source']==SOURCE and owner['primary'] is None and owner['secondary']==[] and owner['cpu_only'] is False and owner['source_before']==owner['source_after'] and len(owner['source_before'])==4088,'actual closed successful MODEL result')
 unit='bole-g2-v13-model-20261020t154710z.service'
 expected=dict(Id=unit,Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited')
 p=subprocess.run(['systemctl','show',unit,'--property='+','.join(expected)],capture_output=True,text=True,timeout=20)
 need(p.returncode==0 and p.stderr=='','actual terminal observation')
 props=dict(line.split('=',1) for line in p.stdout.splitlines());need(props==expected,'actual terminal no remaining PID')
 ur=save(T/'G2_V13_MODEL_SYSTEMD_TERMINAL.json',dict(schema='bole.actual-finite-unit-terminal/v1',properties=props))
 root=T/'g2_v13_model_stage_readback_v1'
 commands=[
 ['/usr/bin/python3','-I','-B',str(root/'derive_model_stage13.py'),'--execute','--base',str(T/'g2_v13_cpu_readback_v1/readback_cpu.py'),'--output',str(root/'model_stage_actual.py'),'--inverse',str(root/'ACTUAL_INVERSE.json'),'--model-result-ref',json.dumps(RESULT),'--unit-terminal-ref',json.dumps(ur)],
 ['/usr/bin/python3','-I','-B',str(root/'model_stage_actual.py')],
 ['/usr/bin/python3','-I','-B',str(root/'model_stage_actual.py'),'--help'],
 ['/usr/bin/python3','-I','-B',str(root/'model_stage_actual.py'),'--execute','--source-ref',json.dumps(SOURCE),'--result-ref',json.dumps(RESULT),'--unit-terminal-ref',json.dumps(ur),'--output',str(T/'G2_V13_MODEL_STAGE_READBACK.json')]
 ]
 records=[]
 for i,cmd in enumerate(commands):
  start=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=180);record=dict(requested_argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr,elapsed=time.monotonic()-start)
  records.append(record);need(p.returncode==0,'actual stage operation failed '+json.dumps(record))
 out=dict(schema='bole.G2-v13-MODEL-stage-readback-main-execution/v1',result_ref=RESULT,unit_terminal_ref=ur,records=records,stage_reader_ref=ref(root/'model_stage_actual.py'),qualification_ref=ref(T/'G2_V13_MODEL_STAGE_READBACK.json'))
 er=save(T/'G2_V13_MODEL_STAGE_READBACK_EXECUTION.json',out)
 print(json.dumps(dict(execution_ref=er,unit_terminal_ref=ur,qualification_ref=out['qualification_ref'],reader_ref=out['stage_reader_ref'],actual_exit_codes=[r['exit_code']for r in records],elapsed=[r['elapsed']for r in records],NPU=False)))
if __name__=='__main__':main()
