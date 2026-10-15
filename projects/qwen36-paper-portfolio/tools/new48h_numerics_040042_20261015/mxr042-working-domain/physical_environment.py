"""Bind actual create/inspect environment to e.physical, never truthy service Path."""
import hashlib,importlib.util
from pathlib import Path
SHA='7789d63886da0ebe9420b0f56b584c81eae9e50ab561dbf64940df37eb31aa6a'
def need(x,s):
 if not x:raise ValueError(s)
def install(C,previous):
 leaves={};original=C.create_argv
 def environment(service,leaf):
  key=str(Path(leaf));need(key in leaves,'environment needs registered exact output leaf')
  value=previous(service,leaf);value.update(MXR_ORIGINAL_A32_RESIDUAL027_ENABLE='1',MXR_SAVED_FRAME_REPLAY_ENABLE='1',MXR_Y16_EXPERIMENT_ENABLE='1',TORCH_DEVICE_BACKEND_AUTOLOAD='0',ASCEND_RT_VISIBLE_DEVICES=''if leaves[key]is None else'0');return value
 def create(e):
  key=str(Path(e['output']));card=e['physical'];need(card is None or type(card)is int and card==4,'physical-bound CPU or4')
  need(key not in leaves or leaves[key]==card,'leaf cannot change physical ownership');leaves[key]=card
  return original(e)
 C.environment=environment
 original.__globals__['environment']=environment;C.inspect_owned.__globals__['environment']=environment
 C.create_argv=create
 return leaves
def check(ref):
 raw=Path(ref['path']).read_bytes();need(len(raw)==16480 and hashlib.sha256(raw).hexdigest()==SHA and ref['sha256']==SHA,'actual original createargv source')
 spec=importlib.util.spec_from_file_location('_cold_actual_once025',ref['path']);C=importlib.util.module_from_spec(spec);exec(compile(raw,ref['path'],'exec'),C.__dict__)
 install(C,C.environment);rows=[]
 for physical,leaf in ((None,'/fixture025/cpu'),(4,'/fixture025/npu')):
  e=dict(name='cold025-'+str(physical),physical=physical,guest_cpu=1,source=dict(sha256='0'*64),host_sha256='1'*64,numeric_sha256='2'*64,service='/nonempty/truthy/service',output=leaf,mounts={},cid='a'*64)
  argv=C.create_argv(e);env=[argv[i+1]for i,v in enumerate(argv[:-1])if v=='--env'];expected=''if physical is None else'0'
  need(env.count('ASCEND_RT_VISIBLE_DEVICES='+expected)==1 and env.count('TORCH_DEVICE_BACKEND_AUTOLOAD=0')==1,'real original createargv physical env')
  devices=C.devices(physical);need(argv.count('--device')==len(devices),'actual createargv Devices[] vs singlecard')
  x=dict(Id=e['cid'],Name='/'+e['name'],Image=C.IMAGE,Config=dict(Image=C.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(C.CANONICAL),Labels=C.labels(e),Env=env),HostConfig=dict(Privileged=False,Memory=C.GUEST,MemorySwap=C.GUEST,NanoCpus=10**9,CpusetCpus='1',NetworkMode='none',IpcMode='private',ShmSize=2*1024**3,PidsLimit=512,DeviceRequests=[],DeviceCgroupRules=[],CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Devices=[dict(PathOnHost=h,PathInContainer=g,CgroupPermissions='rwm')for h,g in devices.items()]),Mounts=[])
  C.inspect_owned(x,e)
  bad=dict(x);bad['Config']=dict(x['Config'],Env=[z for z in env if not z.startswith('ASCEND_RT_VISIBLE_DEVICES=')]+['ASCEND_RT_VISIBLE_DEVICES='+('0'if physical is None else'')])
  try:C.inspect_owned(bad,e)
  except ValueError:rejected=True
  else:rejected=False
  need(rejected,'real original inspect rejects wrong CPU/NPU visibility');rows.append(dict(physical=physical,argv=argv,wrong_env_rejected=True))
 return dict(schema='mxr.actual-create-inspect-environment/v042',original_contract=ref,rows=rows,docker_executed=False)
