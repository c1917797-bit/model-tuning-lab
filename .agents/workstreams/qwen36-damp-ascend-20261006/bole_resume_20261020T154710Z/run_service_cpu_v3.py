"""One finite Devices[] software check for the pending service transaction."""
from pathlib import Path
import hashlib,json,os,subprocess,time,traceback
BASE=Path('/opt/host/vnf/austinov')
TASK=BASE/'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
QUALIFIED=BASE/'bole-model-fa64-fp16-20261020T154710Z-r23'
OUT=BASE/'run-bole-service-cpu-20261020T154710Z-v3'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
DOCKER='/usr/bin/docker'
def ref(p):
 p=Path(p);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 assert not OUT.exists();OUT.mkdir(mode=0o700)
 sources=[ref(p)for root in (QUALIFIED,TASK/'service_v1')for p in root.rglob('*.py')if '__pycache__'not in p.parts]
 primary=None;cid=None;cleanup=[];start=time.monotonic()
 def call(label,argv,timeout):
  t=time.monotonic();r=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
  value=dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,elapsed=time.monotonic()-t)
  (OUT/(label+'.json')).write_text(json.dumps(value,indent=2)+'\n')
  return value
 try:
  args=[DOCKER,'create','--name','bole-service-cpu-20261020t154710z-v3',
   '--label','model-tuning-lab.owner=bole-service-cpu-20261020T154710Z-v3',
   '--memory',str(2*2**30),'--memory-swap',str(2*2**30),'--cpus','1','--cpuset-cpus','145',
   '--network','none','--ipc','private','--pids-limit','128','--cap-drop','ALL',
   '--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:rw,size=536870912',
   '--mount','type=bind,src='+str(QUALIFIED)+',dst=/qualified,readonly',
   '--mount','type=bind,src='+str(TASK/'service_v1')+',dst=/candidate,readonly',
   '--env','ASCEND_RT_VISIBLE_DEVICES=','--env','TORCH_DEVICE_BACKEND_AUTOLOAD=0',
   '--env','OMP_NUM_THREADS=1','--env','OPENBLAS_NUM_THREADS=1',
   '--env','PYTHONDONTWRITEBYTECODE=1','--env','HOME=/tmp',
   '--entrypoint','/bin/sleep',IMAGE,'240']
  created=call('CREATE',args,25);assert created['returncode']==0
  cid=created['stdout'].strip();assert len(cid)==64
  ins=call('INSPECT',[DOCKER,'inspect',cid],15);x=json.loads(ins['stdout'])[0]
  assert x['Id']==cid and x['Image']==IMAGE and not x['HostConfig'].get('Devices')
  assert x['HostConfig']['NetworkMode']=='none'and x['HostConfig']['Memory']==2*2**30
  assert x['HostConfig']['MemorySwap']==2*2**30 and x['HostConfig']['NanoCpus']==10**9
  assert x['HostConfig']['Privileged']is False and x['HostConfig']['ReadonlyRootfs']is True
  started=call('START',[DOCKER,'start',cid],20);assert started['returncode']==0
  guest="""import sys,json,pathlib,unittest
sys.path[:0]=['/candidate','/qualified']
assert not list(pathlib.Path('/dev').glob('davinci[0-9]*'))
import ast
for p in pathlib.Path('/candidate').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
import service_bridge,service_fia
import torch
assert not hasattr(torch,'npu')or not torch.npu.is_initialized()
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)for name in('test_transaction.Tests','test_eligibility.Tests','test_live_owner.Tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(software_only=True,NPU=False,torch_version=torch.__version__,tests=result.testsRun,passed=result.wasSuccessful())))
raise SystemExit(0 if result.wasSuccessful()and result.testsRun==18 else 3)
"""
  result=call('SOFTWARE',[DOCKER,'exec',cid,'/usr/local/python3.12.13/bin/python3','-I','-B','-c',guest],120)
  assert result['returncode']==0,'service software failure, raw output retained'
 except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if cid:
   try:
    stopped=call('STOP',[DOCKER,'stop','--time','10',cid],25);assert stopped['returncode']==0
    ins=call('FINAL_INSPECT',[DOCKER,'inspect',cid],15);x=json.loads(ins['stdout'])[0]
    assert x['Id']==cid and not x['State']['Running']and x['State']['Pid']==0 and not x.get('ExecIDs')
   except BaseException as e:cleanup.append(repr(e))
  changed=[r['path']for r in sources if ref(r['path'])!=r]
  value=dict(schema='bole.service-transaction-devicefree-software/v1',primary=primary,
   cleanup_errors=cleanup,cid=cid,source_before_after_equal=not changed,
   changed=changed,sources=sources,elapsed=time.monotonic()-start,
   actual_NPU_executed=False,actual_scheduler_executed=False,final_success=False)
  (OUT/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n')
  print(json.dumps({k:v for k,v in value.items()if k!='sources'}))
 return 0 if primary is None and not cleanup and not changed else 3
if __name__=='__main__':raise SystemExit(main())
