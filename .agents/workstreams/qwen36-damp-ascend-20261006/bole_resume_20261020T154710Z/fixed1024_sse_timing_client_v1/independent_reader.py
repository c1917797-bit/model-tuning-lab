"""Independent raw SSE/chunk replay. Formal comparison remains hard disabled.

This module does not import the client parser or trust its metric/token claims.
No HTTP, process, accelerator, owner creation or qualification stub exists here.
"""
import argparse,bisect,hashlib,json,re
from fractions import Fraction
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from evidence import need,strict_json,ref,checked,obj
OUTPUT=1024;INPUT=131;WIRE_CAP=8*2**20;JOURNAL_CAP=8*2**20
MODEL='qwen36-mxr-eager'
MODEL_FOUR_REFS=dict(source=None,owner_result=None,qualification=None,source_audit=None)
FIXED1024_CORRECTNESS_QUALIFICATION=None
CAPTURE_OFF_PRODUCTION_QUALIFICATION=None
PAIRED_OWNER_REF=None
SOURCE_BOUND_OWNER_REVIEWER_REF=None

def expected_request(ids):
 need(type(ids)is list and len(ids)==131 and all(type(x)is int and x>=0 for x in ids),'complete131 actual input IDs')
 return dict(model=MODEL,prompt=ids,max_tokens=1024,temperature=0,top_p=1,n=1,stream=True,ignore_eos=True,return_token_ids=True,echo=False,stream_options=dict(include_usage=True))

def replay_chunks(raw,rows,start_ns,eof_ns):
 need(type(start_ns)is int and type(eof_ns)is int and 0<start_ns<=eof_ns and type(raw)is bytes and len(raw)<=WIRE_CAP,'bounded raw and actual integer monotonic interval')
 need(type(rows)is list and rows,'all actual read1 chunks including EOF')
 offset=0;last=start_ns;ends=[];times=[]
 for i,r in enumerate(rows):
  need(set(r)=={'chunk','offset','bytes','sha256','read_start_monotonic_ns','received_monotonic_ns','eof'}and type(r['chunk'])is int and r['chunk']==i and type(r['offset'])is int and r['offset']==offset and type(r['bytes'])is int and 0<=r['bytes']<=65536,'exact ordered gapless chunk framing')
  n=r['bytes'];end=offset+n;part=raw[offset:end]
  need(type(r['read_start_monotonic_ns'])is int and type(r['received_monotonic_ns'])is int and last<=r['read_start_monotonic_ns']<=r['received_monotonic_ns']<=eof_ns,'actual serial monotonic read timestamps, no wall-clock substitution')
  need(len(part)==n and hashlib.sha256(part).hexdigest()==r['sha256']and type(r['eof'])is bool and r['eof']==(i==len(rows)-1)and (n==0)==r['eof'],'full exact chunk SHA and unique final zero-byte EOF')
  if n:ends.append(end);times.append(r['received_monotonic_ns'])
  offset=end;last=r['received_monotonic_ns']
 need(offset==len(raw)and last==eof_ns,'every raw byte charged to a retained actual read; no omitted suffix')
 return ends,times

def parse_raw(raw,ends,times,*,request_id,input_ids):
 tokens=[];token_times=[];events=[];offset=0;done=False;finished=False;usage_seen=False;prompt_seen=False;created=None
 for match in re.finditer(rb'\r?\n\r?\n',raw):
  end=match.end();block=raw[offset:match.start()];offset=end
  lines=[x for x in re.split(rb'\r?\n',block)if x and not x.startswith(b':')]
  if not lines:continue
  need(all(x.startswith(b'data:')for x in lines),'actual completion SSE data-only wire')
  payload=b'\n'.join(x[5:][1:]if x[5:].startswith(b' ')else x[5:]for x in lines)
  need(not done,'no data after DONE')
  index=bisect.bisect_left(ends,end);need(index<len(ends),'complete event ends in an actual nonempty read');received=times[index]
  if payload==b'[DONE]':
   need(finished and usage_seen and len(tokens)==1024,'DONE only after terminal length and complete usage/output');done=True;ids=[];kind='done'
  else:
   v=strict_json(payload);need(type(v)is dict and 'error'not in v and v['id']==request_id and v['model']==MODEL and v['object']=='text_completion','actual completion identity and no error SSE')
   need(type(v['created'])is int and v['created']>=0 and (created is None or created==v['created']),'one server request creation identity');created=v['created']
   choices=v['choices'];need(type(choices)is list and len(choices)in(0,1),'C1 completion choices only');ids=[]
   if not choices:
    need(not usage_seen and finished and len(tokens)==1024,'one final usage-only event after all generated tokens');u=v['usage'];need(type(u)is dict and type(u['prompt_tokens'])is int and type(u['completion_tokens'])is int and type(u['total_tokens'])is int and (u['prompt_tokens'],u['completion_tokens'],u['total_tokens'])==(131,1024,1155),'actual full usage, no 2048 or character count');usage_seen=True
   else:
    need(not usage_seen and not finished and v.get('usage')is None,'no choice after terminal or continuous usage under fixed options')
    c=choices[0];need(type(c)is dict and type(c['index'])is int and c['index']==0,'one exact index0 choice')
    delta=c.get('token_ids');need(delta is None or type(delta)is list,'explicit generated token ID deltas')
    ids=[]if delta is None else delta;need(all(type(x)is int and x>=0 for x in ids),'ordered real integer token IDs, no text retokenization')
    if not ids:need(not c.get('text')and not(c.get('delta')or{}).get('content'),'text without generated IDs cannot be counted')
    prompt=c.get('prompt_token_ids')
    if prompt is not None:need(not prompt_seen and not tokens and ids and prompt==input_ids,'first actual prompt IDs exact, never count prompt IDs as generated');prompt_seen=True
    if ids:need(prompt_seen,'return_token_ids actual first prompt provenance required')
    reason=c.get('finish_reason');need(reason is None or reason=='length','fixed ignoreEOS requires terminal length')
    need(len(tokens)+len(ids)<=1024,'no truncation or extra generated IDs')
    if reason is not None:need(len(tokens)+len(ids)==1024,'no early length terminal');finished=True
   kind='tokens'if ids else'non-token'
  tokens.extend(ids);token_times.extend([received]*len(ids));events.append(dict(event=len(events),wire_end=end,received_monotonic_ns=received,kind=kind,token_ids=ids))
 need(offset==len(raw)and done and finished and usage_seen and prompt_seen and len(tokens)==1024,'complete raw SSE including unique DONE and all actual1024 IDs')
 return tokens,token_times,events

def read_observation(trace_ref):
 trace=obj(trace_ref);need(trace['schema']=='bole.fixed1024-SSE-client-observation/v1'and trace['primary']is None and trace['http_status']==200 and trace['content_type']=='text/event-stream','actual complete retained client observation, not failed/partial')
 ids=trace['request']['prompt'];need(json.dumps(trace['request'],sort_keys=True,allow_nan=False)==json.dumps(expected_request(ids),sort_keys=True,allow_nan=False),'same strictly typed fixed131/input1024/output streaming options')
 need(type(trace['request_id'])is str and re.fullmatch('cmpl-[A-Za-z0-9_-]{1,160}',trace['request_id'])and trace['expected_request_headers']=={'Content-Type':'application/json','X-Request-Id':trace['request_id'][5:]},'expected exact source-owned request header/completion id join; actual POST proof remains required in owner')
 need(trace['raw']['bytes']<=WIRE_CAP and trace['chunks']['bytes']<=JOURNAL_CAP,'complete bounded raw and timing ledger')
 raw=checked(trace['raw']).read_bytes();data=checked(trace['chunks']).read_bytes();need(data.endswith(b'\n'),'complete newline-terminated timing ledger')
 rows=[strict_json(line)for line in data.splitlines()];ends,times=replay_chunks(raw,rows,trace['request_start_monotonic_ns'],trace['eof_monotonic_ns'])
 tokens,ts,events=parse_raw(raw,ends,times,request_id=trace['request_id'],input_ids=ids);ttft=ts[0]-trace['request_start_monotonic_ns'];span=ts[-1]-ts[0];total=ts[-1]-trace['request_start_monotonic_ns']
 need(ttft>0 and span>=0 and total>0 and total==ttft+span,'actual token-receipt total equals TTFT plus1023*TPOT')
 need(trace['ordered_token_ids']==tokens and trace['token_receive_monotonic_ns']==ts and trace['events']==events and trace['actual_returned_tokens']==1024 and trace['TTFT_ns']==ttft and trace['TPOT_numerator_ns']==span and trace['TPOT_denominator']==1023 and trace['T_total_ns']==total,'client claims exactly equal independent whole-raw/chunk replay')
 for r in(trace_ref,trace['raw'],trace['chunks']):checked(r)
 return dict(schema='bole.fixed1024-SSE-independent-observation/v1',trace_ref=trace_ref,raw=trace['raw'],chunks=trace['chunks'],request=trace['request'],request_id=trace['request_id'],request_start_monotonic_ns=trace['request_start_monotonic_ns'],eof_monotonic_ns=trace['eof_monotonic_ns'],ordered_token_ids=tokens,token_receive_monotonic_ns=ts,TTFT_ns=ttft,TPOT_numerator_ns=span,TPOT_denominator=1023,T_total_ns=total,owner_identity=trace['owner_identity'],formal_qualification=False,all_actual_owner_qualification_pending=True)

def _after_full_qualification_math(verified_pairs):
 """Private arithmetic after future real source-bound qualification; unit-only now.

 Public execute never reaches this function while four MODEL Refs, captureOFF
 production proof, original resource/clock/cleanup and paired-owner are pending.
 """
 need(type(verified_pairs)is list and len(verified_pairs)==3,'exactly three independently qualified matched pairs')
 ratios=[]
 common_keys=('image','model','input_ref','source_ref','runtime_refs','process_options_ref','resource_profile_ref','concurrency','capture_off_qualification_ref','main_clock_ref','actual_input_ids')
 seen_requests=set();last_end=0;global_common=None
 for index,pair in enumerate(verified_pairs):
  need(pair['pair_index']==index and set(pair)=={'pair_index','OFF','ON'},'ordered unique three pairs')
  off=pair['OFF'];on=pair['ON'];a=off['identity'];b=on['identity']
  need(a['mode']=='OFF'and b['mode']=='ON'and a['capture_mode']==b['capture_mode']=='OFF'and a['concurrency']==b['concurrency']==1,'one matched OFF/ON request, production captureOFF both')
  common={k:a[k]for k in common_keys};need(common=={k:b[k]for k in common_keys}and(global_common is None or common==global_common),'same source/image/model/input/runtime/process options/resources across all three pairs');global_common=common
  need(a['image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and a['model']==MODEL,'current exact image/model')
  for row in(off,on):
   v=row['observation'];ident=row['identity'];need(v['request']==expected_request(v['request']['prompt'])and ident['actual_input_ids']==v['request']['prompt']and len(v['ordered_token_ids'])==1024,'same actual fixed input/options/output and ordered token IDs')
   need(v['request_id']not in seen_requests and last_end<=v['request_start_monotonic_ns']<v['eof_monotonic_ns'],'unique serial C1 actual requests, no overlap or replay');seen_requests.add(v['request_id']);last_end=v['eof_monotonic_ns']
   need(ident['work_start_ns']<=v['request_start_monotonic_ns']<v['eof_monotonic_ns']<=ident['work_deadline_ns'],'same original admitted finite main work window')
   need(type(ident['frontend_pid'])is int and ident['frontend_pid']>0 and len(ident['worker_processes'])==4 and len({(r['host_pid'],r['start_ticks'])for r in ident['worker_processes']})==4 and {r['physical']for r in ident['worker_processes']}=={4,5,6,7},'source-qualified frontend/all4 fresh worker identity required')
   need(all(type(v[k])is int and v[k]>=0 for k in('TTFT_ns','TPOT_numerator_ns','T_total_ns'))and v['T_total_ns']>0 and v['TPOT_denominator']==1023 and v['T_total_ns']==v['TTFT_ns']+v['TPOT_numerator_ns'],'integer actual receive metrics and full1024 timing identity only')
  need(off['observation']['request']==on['observation']['request'],'byte-equivalent common request body options')
  x=off['observation'];y=on['observation'];need(10*x['T_total_ns']>=11*y['T_total_ns'],'EVERY pair actual E2E total speedup must be at least11/10; no average substitution')
  ratio=lambda a,b:None if b==0 else str(Fraction(a,b))
  ratios.append(dict(pair=index,E2E_ratio=ratio(x['T_total_ns'],y['T_total_ns']),E2E_at_least_1_10=True,TTFT_ratio=ratio(x['TTFT_ns'],y['TTFT_ns']),TPOT_ratio=ratio(x['TPOT_numerator_ns'],y['TPOT_numerator_ns']),OFF_metrics={k:x[k]for k in('TTFT_ns','TPOT_numerator_ns','TPOT_denominator','T_total_ns')},ON_metrics={k:y[k]for k in('TTFT_ns','TPOT_numerator_ns','TPOT_denominator','T_total_ns')}))
 return dict(schema='bole.fixed1024-three-pair-arithmetic-only/v1',pairs=ratios,all_three_E2E_at_least_1_10=True,extra_TTFT_threshold_imposed=False,extra_TPOT_threshold_imposed=False,formal_qualification=False)

def qualified_three_pairs(*args,**kwargs):
 need(all(r is not None for r in MODEL_FOUR_REFS.values())and FIXED1024_CORRECTNESS_QUALIFICATION is not None and CAPTURE_OFF_PRODUCTION_QUALIFICATION is not None and PAIRED_OWNER_REF is not None and SOURCE_BOUND_OWNER_REVIEWER_REF is not None,'SOURCE_ONLY: real MODEL four Refs, captureOFF production qualification, original all4/7CPU/clock/cleanup and paired owner remain pending')
 raise ValueError('SOURCE_ONLY: exact future owner review interface not bound; no truth-valued or metadata PASS fallback')

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"HTTP":false,"NPU":false,"formal_qualification":false}');return 0
 qualified_three_pairs()
if __name__=='__main__':raise SystemExit(main())
