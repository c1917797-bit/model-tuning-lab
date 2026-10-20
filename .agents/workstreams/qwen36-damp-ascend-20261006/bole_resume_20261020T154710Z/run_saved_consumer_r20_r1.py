"""Reconsume saved r20 tensors in a fresh bounded Devices[] container.

The failed producer/controller result and all four original raw refs stay
immutable. Only the consumer counter name and explicit reader provenance change.
"""
from pathlib import Path
import ast,hashlib,json,os,subprocess,time,traceback
BASE=Path('/opt/host/vnf/austinov')
TASK=BASE/'model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z'
SRC=BASE/'bole-model-fa64-fp16-20261020T154710Z-r20'
OLD=BASE/'run-bole-model-fa64-fp16-20261020T154710Z-r20'
OUT=BASE/'run-bole-model-fa64-fp16-20261020T154710Z-r20-CONSUMER-R1'
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
DOCKER='/usr/bin/docker'
def ref(p):
 p=Path(p);b=p.read_bytes()
 return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 assert not OUT.exists()
 mem=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()if x.startswith('MemAvailable:'))
 assert mem>=20*2**30 and 166 in os.sched_getaffinity(0)
 import shutil
 assert shutil.disk_usage(BASE).free>=40*2**30
 OUT.mkdir(mode=0o700);(OUT/'consumer').mkdir()
 original=(SRC/'consume_model.py').read_text()
 edited=(TASK/'readers/r20_counter_r1.py').read_text()
 plan=json.loads((TASK/'R20_CONSUMER_REPAIR.json').read_bytes())
 assert ref(SRC/'consume_model.py')==plan['original']and ref(TASK/'readers/r20_counter_r1.py')==plan['reader']
 inverse=edited
 for e in reversed(plan['edits']):
  assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'])
 assert inverse==original
 for n in ('independent_model.py','oracle112.py','core112.py','adapter.py'):
  assert ref(SRC/n)==plan['unchanged_math'][n]
 child=json.loads((OLD/'cpu-consumer/INDEPENDENT-CHILD.json').read_bytes())
 argv=child['requested_argv'];sr=json.loads(argv[argv.index('--source-ref')+1]);ir=json.loads(argv[argv.index('--inputs-ref')+1])
 assert ref(sr['path'])==sr and ref(ir['path'])==ir
 inspect_files=list((OLD/'cpu-consumer').glob('inspect-*.json'))
 saved=json.loads(max(inspect_files,key=lambda x:x.stat().st_mtime).read_bytes())
 previous=json.loads(saved['stdout'])[0]
 assert previous['Image']==IMAGE and not previous['HostConfig'].get('Devices')
 mounts={m['Destination']:m['Source']for m in previous['Mounts']if m['Type']=='bind'}
 assert len(mounts)==len(previous['Mounts'])
 mounts[str(TASK/'readers')]=str(TASK/'readers')
 mounts[str(TASK/'service_v1')]=str(TASK/'service_v1')
 mounts[str(TASK/'R20_CONSUMER_REPAIR.json')]=str(TASK/'R20_CONSUMER_REPAIR.json')
 sources={str(p):ref(p)for p in map(Path,mounts.values())if p.is_file()}
 for root in (TASK/'readers',TASK/'service_v1'):
  for p in root.glob('*.py'):sources[str(p)]=ref(p)
 sources[str(Path(__file__))]=ref(__file__)
 primary=None;cleanup=[];cid=None;started=time.monotonic()
 def call(label,args,limit):
  remaining=360-(time.monotonic()-started)
  assert remaining>0 or label in('STOP','FINAL_INSPECT')
  result=subprocess.run(args,capture_output=True,text=True,timeout=min(limit,remaining)if remaining>0 else limit)
  record=dict(argv=args,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
  (OUT/(label+'.json')).write_text(json.dumps(record,indent=2)+'\n')
  return record
 try:
  args=[DOCKER,'create','--name','bole-r20-consumer-r1-20261020t154710z',
   '--label','model-tuning-lab.owner=bole-r20-consumer-r1-20261020T154710Z',
   '--memory',str(8*2**30),'--memory-swap',str(8*2**30),'--cpus','1','--cpuset-cpus','144',
   '--network','none','--ipc','private','--pids-limit','256','--cap-drop','ALL',
   '--security-opt','no-new-privileges','--read-only','--tmpfs','/tmp:rw,size=536870912',
   '--env','ASCEND_RT_VISIBLE_DEVICES=','--env','TORCH_DEVICE_BACKEND_AUTOLOAD=0',
   '--env','OMP_NUM_THREADS=1','--env','OPENBLAS_NUM_THREADS=1',
   '--env','PYTHONDONTWRITEBYTECODE=1','--env','HOME=/tmp']
  for dest,source in sorted(mounts.items()):args+=['--mount','type=bind,src='+source+',dst='+dest+',readonly']
  args+=['--mount','type=bind,src='+str(OUT)+',dst='+str(OUT),
         '--entrypoint','/bin/sleep',IMAGE,'420']
  r=call('CREATE',args,30);assert r['returncode']==0;cid=r['stdout'].strip();assert len(cid)==64
  r=call('INSPECT',[DOCKER,'inspect',cid],15);x=json.loads(r['stdout'])[0];hc=x['HostConfig']
  assert x['Id']==cid and x['Image']==IMAGE and not hc.get('Devices')and hc['Privileged']is False
  assert hc['NetworkMode']=='none'and hc['Memory']==hc['MemorySwap']==8*2**30 and hc['NanoCpus']==10**9 and hc['ReadonlyRootfs']is True
  assert {m['Destination']:m['Source']for m in x['Mounts']}==dict(mounts,**{str(OUT):str(OUT)})
  assert all(m['RW']==(m['Destination']==str(OUT))for m in x['Mounts'])
  assert call('START',[DOCKER,'start',cid],20)['returncode']==0
  guest="""import sys,json,pathlib,unittest
sys.path[:0]=[SERVICE,SOURCE]
assert not list(pathlib.Path('/dev').glob('davinci[0-9]*'))
import torch
assert not hasattr(torch,'npu')or not torch.npu.is_initialized()
suite=unittest.defaultTestLoader.loadTestsFromName('test_transaction.Tests')
r=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(software_only=True,NPU=False,tests=r.testsRun,passed=r.wasSuccessful())))
raise SystemExit(0 if r.wasSuccessful()and r.testsRun==5 else 3)
""".replace('SERVICE',repr(str(TASK/'service_v1'))).replace('SOURCE',repr(str(SRC)))
  assert call('SERVICE_SOFTWARE',[DOCKER,'exec',cid,'/usr/local/python3.12.13/bin/python3','-I','-B','-c',guest],90)['returncode']==0
  args=[DOCKER,'exec',cid,'/bin/bash','-c','source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',
   'bole-saved-consumer','/usr/local/python3.12.13/bin/python3','-I','-B',
   str(TASK/'readers/r20_counter_r1.py'),'--execute','--source-ref',json.dumps(sr),
   '--inputs-ref',json.dumps(ir),'--output',str(OUT/'consumer')]
  assert call('INDEPENDENT',args,200)['returncode']==0,'independent original mathematical gates failed or reader failed'
 except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  if cid:
   try:
    assert call('STOP',[DOCKER,'stop','--time','10',cid],25)['returncode']==0
    r=call('FINAL_INSPECT',[DOCKER,'inspect',cid],15);x=json.loads(r['stdout'])[0]
    assert x['Id']==cid and not x['State']['Running']and x['State']['Pid']==0 and not x.get('ExecIDs')
   except BaseException as e:cleanup.append(repr(e))
  changed=[k for k,r in sources.items()if ref(k)!=r]
  value=dict(schema='bole.saved-r20-independent-counter-repair-owner/v1',
   producer_source=sr,inputs=ir,reader=plan['reader'],reader_plan=ref(TASK/'R20_CONSUMER_REPAIR.json'),
   original_failure=ref(OLD/'RESULT.json'),primary=primary,cleanup_errors=cleanup,
   source_before_after_equal=not changed,changed=changed,sources=list(sources.values()),cid=cid,
   elapsed=time.monotonic()-started,actual_NPU_executed=False,original_r20_result_relabelled=False,final_success=False)
  (OUT/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n')
  print(json.dumps({k:v for k,v in value.items()if k!='sources'}))
 return 0 if primary is None and not cleanup and not changed else 3
if __name__=='__main__':raise SystemExit(main())
