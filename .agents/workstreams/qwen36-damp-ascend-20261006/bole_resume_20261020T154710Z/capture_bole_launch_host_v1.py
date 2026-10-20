"""Capture only explicitly owned BOLE frontend framework settings; no tensor/runtime import."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
P=Path(__file__).resolve()
PREFIXES=('VLLM_','ASCEND_','HCCL_','TORCH_','CANN_','MXR_','MST_MXR_','QWEN36_','DLOG_')
SECRETS=('TOKEN','SECRET','PASSWORD','API_KEY','CREDENTIAL','PRIVATE_KEY')
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True);f.write('\n')
 return ref(p)
def process(pid):
 p=Path('/proc')/str(pid);s=(p/'stat').read_text();r=s[s.rfind(')')+2:].split()
 return dict(pid=pid,start_ticks=int(r[19]),cgroup=(p/'cgroup').read_text())
def main():
 a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');a.add_argument('--source-ref');a.add_argument('--output',type=Path);x=a.parse_args()
 if not x.execute:print('{"enabled":false,"NPU":false}');return
 sr=json.loads(x.source_ref);need(ref(sr['path'])==sr,'exact current frozen ON source');m=json.loads(Path(sr['path']).read_bytes());need(m['service_experiment']['schema']=='bole.c1-two-request-service/v1','bounded ON subject')
 need(x.output.is_absolute()and not x.output.exists(),'fresh owned external observation leaf')
 q=subprocess.run(['/usr/bin/docker','ps','--no-trunc','--format','{{json .}}'],capture_output=True,text=True,timeout=15,check=True)
 candidates=[json.loads(s)for s in q.stdout.splitlines()if s.strip()]
 candidates=[r for r in candidates if 'g1-two-request' in r['Names']and 'v2' in r['Names']and 'dense'in r['Names']]
 need(len(candidates)==1,'one actual current G1v2 dense container')
 cid=candidates[0]['ID'];q=subprocess.run(['/usr/bin/docker','inspect',cid],capture_output=True,text=True,timeout=15,check=True);rows=json.loads(q.stdout);need(len(rows)==1,'one actual inspect')
 c=rows[0];need(c['Id']==cid and c['State']['Running']and c['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1','actual current same-image running owned container')
 need(any(z['Source']==m['root']and z['Destination']==m['root']and z['RW']is False for z in c['Mounts']),'actual frozen ON source readonly mount')
 devices={(z['PathOnHost'],z['PathInContainer'])for z in c['HostConfig']['Devices']if Path(z['PathInContainer']).name.startswith('davinci')and Path(z['PathInContainer']).name[7:].isdigit()}
 need(devices=={('/dev/davinci'+str(i+4),'/dev/davinci'+str(i))for i in range(4)},'actual allowed physical4..7 mapping')
 script=str(Path(m['root'])/'server090.py');owned=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   v=process(int(p.name))
   if cid not in v['cgroup']:continue
   args=(p/'cmdline').read_bytes().split(b'\0')
   if script.encode()in args:owned.append((p,v,args))
  except(FileNotFoundError,PermissionError,ProcessLookupError):continue
 need(len(owned)==1,'one actual source-bound owned frontend')
 p,before,args=owned[0];i=args.index(b'--source-ref');need(json.loads(args[i+1])==sr,'actual frontend CLI ON source')
 raw=(p/'environ').read_bytes();need(len(raw)<=2**20,'bounded owned environment')
 common={};excluded=[];plugins=[]
 for item in raw.split(b'\0'):
  if not item:continue
  key,sep,value=item.partition(b'=');need(sep,'actual environment row');key=key.decode()
  if key=='VLLM_PLUGINS':plugins=value.decode().split(',')
  elif key.startswith(('BOLE_','BOLE111_','DENSE_OPPORTUNITY090_')):excluded.append(key)
  elif key.startswith(PREFIXES)and not any(z in key.upper()for z in SECRETS):
   need(len(value)<=65536,'bounded public framework setting');common[key]=value.decode()
 after=process(int(p.name));need(after==before and ref(sr['path'])==sr,'stable owned process and source')
 status=(p/'status').read_text();nspid=next([int(z)for z in line.split()[1:]]for line in status.splitlines()if line.startswith('NSpid:'))
 x.output.mkdir(mode=0o700);ins=write(x.output/'DOCKER_INSPECT.json',rows)
 value=dict(schema='bole.actual-host-launch-profile-observation/v1',source=sr,variant='BOLE',collector=ref(P),identity=before,NSpid=nspid,owned_cid=cid,container_inspection=ins,common_environment=common,plugins=plugins,declared_algorithm_or_observer_environment_keys=sorted(excluded),credential_values_retained=False,plugin_effect_classification_performed=False,source_before=sr,source_after=ref(sr['path']),observed_epoch_ns=time.time_ns(),actual_model_or_task_result_claimed=False,formal_success=False)
 result=write(x.output/'LAUNCH_PROFILE.json',value);print(json.dumps(dict(result=result,identity=before,NSpid=nspid,common_environment_keys=sorted(common),plugins=plugins,credential_values_retained=False)))
if __name__=='__main__':main()
