"""Independent actual4x48 PID-join and raw SSE response consumption."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
def need(v,m):
 if not v:raise ValueError(m)
def obj(r):
 b=Path(r['path']).read_bytes();need(set(r)=={'path','bytes','sha256'}and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact complete Ref3');return json.loads(b)
def response(request,wire):
 body=request['payload'];need(body['n']==1 and body['max_tokens']==body['min_tokens']==10 and body['ignore_eos']is True and body['echo']is False and body['return_token_ids']is True and body['temperature']==0 and body['seed']==0,'frozen diagnostic-only request')
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
 from request_identity import identities
 identity=identities(request['request_id']);need(items and all(v['id']==identity['response_id']for v in items),'actual660 header to response ID source relation')
 need(done==1 and len(ids)==10 and finish==['length']and len(usages)==1 and usages[0]['prompt_tokens']==len(body['prompt'])and usages[0]['completion_tokens']==10,'strict actual original tokens/finish/usage/DONE')
 return dict(prompt_tokens=len(body['prompt']),output_tokens=10,token_ids=ids,finish='length')
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--loaded-ref');ap.add_argument('--client-ref');ap.add_argument('--audit',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 sr=json.loads(a.source_ref);import owner_overlay as O
 m=O.current(sr);ps=m['plugin_source'];pm=obj(ps)
 from consume_trajectory import check
 trajectory=[json.loads(p.read_bytes())for p in (a.audit/'dispatch-trajectory').glob('worker-*-epoch-*.json')]
 need(all(r['source']==sr and r['plugin_source']==ps for r in trajectory),'same-source frozen trace')
 dispatch=check(trajectory)
 loaded=obj(json.loads(a.loaded_ref));need(loaded['schema']=='deltalog.actual-all4-loaded/v004'and loaded['source']==sr and [r['rank']for r in loaded['rows']]==[0,1,2,3],'sourcebound original owned worker joins')
 from consume_trajectory import pid_join
 pid_join(trajectory,loaded['rows'])
 events=[json.loads(x)for p in a.audit.glob('worker-*.jsonl')for x in p.read_text().splitlines()]
 joins=[]
 for r in loaded['rows']:
  own=[v for v in events if v['rank']==r['rank']];need(own and {x['pid']for x in own}=={r['namespace_pid']}and r['physical']==r['logical']+4,'event PIDs join independently original native loaded worker and owned physical card')
  precision=[v for v in own if v['event']=='actual_common_precision_policy'];need(len(precision)==1 and precision[0]['matmul_allow_hf32']is False and precision[0]['conv_allow_hf32']is False,'actual perworker common HF32 OFF before real core')
  need(all(v['source']==ps and v['performance']is False and v['graph']is False for v in own),'actual same plugin diagnostic event source')
  prefixes=set(next(v['registered_prefixes']for v in trajectory if v['rank']==r['rank']))
  for name in('actual_qwen_core','actual_arena','actual_decode_binding','candidate_decode_executed'):
   chosen=[v for v in own if v['event']==name];need({v['prefix']for v in chosen}==prefixes and len(chosen)==48,'complete exactly48 source-bound '+name)
  need(all(v['library']==pm['library_ref']and v['mapped_rows']for v in own if v['event']=='actual_qwen_core'),'actual production DSO mapped at each original Qwen target')
  proof=r['actual_host_process'];native=obj(r['loaded_receipt']);need(proof['namespace_pids'][-1]==r['namespace_pid']==native['pid']and proof['physical']==r['physical']and proof['start_ticks']==int(native['stat'][native['stat'].rfind(')')+2:].split()[19]),'actual PID/start/cgroup + original receipt')
  joins.append(dict(rank=r['rank'],physical=r['physical'],namespace_pid=r['namespace_pid'],host_pid=proof['pid'],start_ticks=proof['start_ticks'],cgroup=proof['cgroup']))
 cr=json.loads(a.client_ref);cv=obj(cr);need(cv['schema']=='deltalog.actual-short-client/v004'and cv['source']==sr and cv['performance_ready']is False,'same-source actual client')
 responses=[]
 for row in cv['rows']:
  request=obj(row['request']);w=Path(row['wire']['path']).read_bytes();need(len(w)==row['wire']['bytes']and hashlib.sha256(w).hexdigest()==row['wire']['sha256']and request['request_id']==row['request_id'],'actual wire/input identity')
  result=response(request,w);need(result['prompt_tokens']==row['prompt_tokens'],'exact short lengths');responses.append(result)
 need([r['prompt_tokens']for r in responses]==[2048,2048],'both true model requests')
 from request_identity import identities
 from identity_events import validate_join
 assignments=validate_join(a.audit,[identities(r['request_id'])['response_id']for r in cv['rows']],sr,trajectory,loaded['rows'])
 expected={r['engine_id']for r in assignments}
 need(len(expected)==2,'two distinct observed internal IDs')
 for assignment in assignments:
  need(all(assignment['owner_cid']in r['actual_host_process']['cgroup']for r in loaded['rows']),'source-captured assignment actual Owned CID joins physical workers')
 need(all(set(r['request_ids'][0]for r in trajectory if r['rank']==rank)==expected for rank in range(4)),'source captured assigned IDs, never inferred suffix')
 import tensor_consumer
 tensor=tensor_consumer.consume(a.audit,sr,trajectory,expected,a.output.with_name('TENSOR_DIAGNOSTIC.json'))
 need(tensor['validation_contract']==tensor_consumer.VALIDATION_CONTRACT,'explicit selected-model direct-RNE036R1 numerical contract; legacy unknown PASS refused')
 need(tensor['modified_decode_arithmetic_pass']is True,'selected modified decode failed strict CPU64/nativepeer; preserve original raw')
 from identity_events import retirement
 actual_retirement=retirement(a.audit,sr,assignments,loaded['rows'])
 tp=a.output.with_name('TENSOR_DIAGNOSTIC.json');tb=tp.read_bytes()
 out=dict(schema='deltalog.model-selected-tensor-independent-consumption/v026',component_prior_scope=m['short_model_diagnostic_scope'],long_history_160_qualified=False,production_admitted=False,source=sr,validation_contract=tensor['validation_contract'],actual_loaded_workers=json.loads(a.loaded_ref),actual_client=cr,dispatch=dispatch,actual_PID_joins=joins,actual_assignments=assignments,actual_retirement=actual_retirement,selected_tensor_ref=dict(path=str(tp),bytes=len(tb),sha256=hashlib.sha256(tb).hexdigest()),selected_modified_decode_pass=True,unchanged_prefill_diagnostic_only=True,actual_slot_reuse_observed=tensor['actual_second_request_slot_reuse_observed'],responses=responses,smoke_dispatch_and_response_pass=True,model_numeric_qualified=False,performance_ready=False,task_accuracy=False,graph=False,PDC=False)
 with a.output.open('x',encoding='utf8')as f:json.dump(out,f,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
