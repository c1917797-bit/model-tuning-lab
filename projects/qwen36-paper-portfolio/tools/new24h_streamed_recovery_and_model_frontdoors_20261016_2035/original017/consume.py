"""Independent actual4x48 PID-join and raw SSE response consumption."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def obj(r):
 b=Path(r['path']).read_bytes();need(set(r)=={'path','bytes','sha256'}and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact complete Ref3');return json.loads(b)
def response(request,wire):
 body=request['payload'];need(body['n']==1 and body['max_tokens']==body['min_tokens']==2 and body['ignore_eos']is True and body['echo']is False and body['return_token_ids']is True and body['temperature']==0 and body['seed']==0,'frozen diagnostic-only request')
 items=[];done=0;ids=[];finish=[];usages=[]
 for line in wire.decode().splitlines():
  if not line.startswith('data: '):continue
  data=line[6:]
  if data=='[DONE]':done+=1;continue
  need(done==0,'no events after DONE');v=json.loads(data);items.append(v)
  if v.get('usage'):usages.append(v['usage'])
  for ch in v.get('choices',[]):
   need(ch['index']==0,'single original request output')
   token=ch.get('token_ids')or[];need(type(token)is list and all(type(x)is int and x>=0 for x in token),'actual generated output IDs');ids.extend(token)
   if ch.get('finish_reason')is not None:finish.append(ch['finish_reason'])
 need(done==1 and len(ids)==2 and finish==['length']and len(usages)==1 and usages[0]['prompt_tokens']==len(body['prompt'])and usages[0]['completion_tokens']==2,'strict actual original tokens/finish/usage/DONE')
 return dict(prompt_tokens=len(body['prompt']),output_tokens=2,token_ids=ids,finish='length')
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--loaded-ref');ap.add_argument('--client-ref');ap.add_argument('--audit',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 sr=json.loads(a.source_ref);m=obj(sr);ps=m['plugin_source'];pm=obj(ps);rr=pm['files']['consume_audit.py'];b=Path(rr['path']).read_bytes();need(len(b)==rr['bytes']and hashlib.sha256(b).hexdigest()==rr['sha256'],'true003 dispatch consumer')
 spec=importlib.util.spec_from_file_location('_dl004_dispatch_consumer',rr['path']);D=importlib.util.module_from_spec(spec);exec(compile(b,rr['path'],'exec'),D.__dict__);dispatch=D.consume(a.audit,ps,pm['library_ref'])
 loaded=obj(json.loads(a.loaded_ref));need(loaded['schema']=='deltalog.actual-all4-loaded/v004'and loaded['source']==sr and [r['rank']for r in loaded['rows']]==[0,1,2,3],'sourcebound original owned worker joins')
 events=[json.loads(x)for p in a.audit.glob('worker-*.jsonl')for x in p.read_text().splitlines()]
 joins=[]
 for r in loaded['rows']:
  own=[v for v in events if v['rank']==r['rank']];need(own and {x['pid']for x in own}=={r['namespace_pid']}and r['physical']==r['logical']+4,'event PIDs join independently original native loaded worker and owned physical card')
  proof=r['actual_host_process'];native=obj(r['loaded_receipt']);need(proof['namespace_pids'][-1]==r['namespace_pid']==native['pid']and proof['physical']==r['physical']and proof['start_ticks']==int(native['stat'][native['stat'].rfind(')')+2:].split()[19]),'actual PID/start/cgroup + original receipt')
  joins.append(dict(rank=r['rank'],physical=r['physical'],namespace_pid=r['namespace_pid'],host_pid=proof['pid'],start_ticks=proof['start_ticks'],cgroup=proof['cgroup']))
 cr=json.loads(a.client_ref);cv=obj(cr);need(cv['schema']=='deltalog.actual-short-client/v004'and cv['source']==sr and cv['performance_ready']is False,'same-source actual client')
 responses=[]
 for row in cv['rows']:
  request=obj(row['request']);w=Path(row['wire']['path']).read_bytes();need(len(w)==row['wire']['bytes']and hashlib.sha256(w).hexdigest()==row['wire']['sha256']and request['request_id']==row['request_id'],'actual wire/input identity')
  result=response(request,w);need(result['prompt_tokens']==row['prompt_tokens'],'exact short lengths');responses.append(result)
 need([r['prompt_tokens']for r in responses]==[16,129],'both true model requests')
 out=dict(schema='deltalog.model-smoke-independent-consumption/v004',source=sr,actual_loaded_workers=json.loads(a.loaded_ref),actual_client=cr,dispatch=dispatch,actual_PID_joins=joins,responses=responses,smoke_dispatch_and_response_pass=True,model_numeric_qualified=False,performance_ready=False,task_accuracy=False,graph=False,PDC=False)
 with a.output.open('x',encoding='utf8')as f:json.dump(out,f,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
