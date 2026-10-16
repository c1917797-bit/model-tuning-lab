"""Actual source-pinned assignment capture; observed IDs, not suffix inference."""
import functools,hashlib,importlib.util,json,os
from pathlib import Path
P=Path(__file__).resolve().parent
def load(name,sha):
 path=P/'dependencies'/name;b=path.read_bytes()
 if hashlib.sha256(b).hexdigest()!=sha:raise ValueError('original identity helper')
 s=importlib.util.spec_from_file_location('_dl026_'+name[:-3],path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def install(R,sr,m):
 if os.environ.get('QWEN36_DELTALOG_TENSOR026_ENABLE')!='1':raise ValueError('explicit diagnostic identity capture')
 C=load('identity_capture.py','1cfb4c995917c5d89868102e6bd8b4c6d68fe1f59881186be6e7831ff0ccaec5')
 root=Path(os.environ['QWEN36_DELTALOG_SERVICE023_AUDIT'])/'identity026';root.mkdir(exist_ok=True)
 journal_bytes=0
 def emit(label,event):
  nonlocal journal_bytes
  owner=os.environ.get('DL026_ACTUAL_OWNER_CID','')
  if len(owner)!=64:raise ValueError('actual Owned exec CID required')
  if label=='assignment':name='assignment-'+hashlib.sha256(event['before_request_id'].encode()).hexdigest()+'.json'
  else:name='worker-%d-%d-%012d.json'%(event['rank'],event['identity']['pid'],event['seq'])
  value=dict(schema='deltalog.actual-identity-event/v026',source=sr,owner_cid=owner,event=event)
  raw=(json.dumps(value,sort_keys=True)+'\n').encode();journal_bytes+=len(raw)
  if journal_bytes>8*1024**2:raise ValueError('bounded actual identity journal')
  with(root/name).open('xb')as f:f.write(raw)
 from vllm.v1.engine.input_processor import InputProcessor
 C.install_assignment(InputProcessor,emit)
 from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
 from vllm.distributed import parallel_state as ps
 old=NPUModelRunner.__init__
 @functools.wraps(old)
 def init(self,*a,**kw):
  old(self,*a,**kw);C.install_worker(NPUModelRunner,ps.get_tensor_model_parallel_rank(),emit)
 NPUModelRunner.__init__=init
def mapping(audit,server_id,sr):
 O=load('identity_oracle.py','f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333')
 passed=server_id+'-0';p=Path(audit)/'identity026'/('assignment-'+hashlib.sha256(passed.encode()).hexdigest()+'.json');v=json.loads(p.read_bytes())
 if v['source']!=sr or v['schema']!='deltalog.actual-identity-event/v026':raise ValueError('same source actual assignment')
 before,after=O.validate_assignment(server_id,dict(endpoint='/v1/completions',prompt_count=1,n=1,beam_search=False,streaming_input=False),v['event'])
 raw=p.read_bytes()
 return dict(passed=before,engine_id=after,owner_cid=v['owner_cid'],event=v['event'],event_ref=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
def validate_join(audit,server_ids,sr,trajectory,loaded_rows):
 rows=[mapping(audit,sid,sr)for sid in server_ids];expected={x['engine_id']for x in rows}
 if len(rows)!=2 or len(expected)!=2:raise ValueError('two one-to-one observed mappings')
 if {x['rank']for x in loaded_rows}!={0,1,2,3}:raise ValueError('four actual worker bindings')
 for x in rows:
  if not all(x['owner_cid']in r['actual_host_process']['cgroup']for r in loaded_rows):raise ValueError('actual assignment Owned CID scope')
 for rank in range(4):
  if {r['request_ids'][0]for r in trajectory if r['rank']==rank}!=expected:raise ValueError('observed assigned IDs must join all real worker step keys')
 return rows
def retirement(audit,sr,assignments,loaded_rows):
 O=load('identity_oracle.py','f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333');events={r:[]for r in range(4)};bindings={}
 for row in loaded_rows:
  p=row['actual_host_process'];bindings[row['rank']]=dict(pid=row['namespace_pid'],start_ticks=p['start_ticks'],cgroup=None)
 for p in sorted((Path(audit)/'identity026').glob('worker-*.json')):
  v=json.loads(p.read_bytes());e=v['event'];rank=e['rank'];b=bindings[rank]
  if v['source']!=sr or e['identity']['pid']!=b['pid']or e['identity']['start_ticks']!=b['start_ticks']:raise ValueError('actual worker birth/retirement PID/start join')
  bindings[rank]=e['identity'];events[rank].append(e)
 result=[]
 for assigned in assignments:
  engine_id=assigned['engine_id'];traces=[dict(schema='vllm023.actual-worker-retirement/v1',rank=r,identity=bindings[r],events=sorted([e for e in events[r]if engine_id in e['new_req_ids']+e['finished_req_ids']],key=lambda e:e['seq']))for r in range(4)]
  try:O.validate_worker_retirement(engine_id,traces,bindings);error=None
  except ValueError as e:error=str(e)
  result.append(dict(engine_id=engine_id,all4_actual_retirement_pass=error is None,error=error))
 return result
