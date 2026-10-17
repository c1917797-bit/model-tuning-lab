"""Independent CPU dispatcher-count check; deliberately NOT tensor correctness."""
def pid_join(rows,workers):
 byrank={r['rank']:r['namespace_pid']for r in workers}
 if set(byrank)!={0,1,2,3}or len(workers)!=4 or len(set(byrank.values()))!=4:raise ValueError('four actual owned worker PID identities')
 if any(r['rank']not in byrank or r['pid']!=byrank[r['rank']]for r in rows):raise ValueError('trajectory PID must join actual owned loaded worker')
 return True

def check(rows):
 byrank={}
 for r in rows:
  if r['schema']!='deltalog.actual-dispatch-trajectory/v025'or not r['all48_finished']or r['numerical_qualified']or r['actual_merge_observed']:raise ValueError('honest typed dispatch-only rows')
  byrank.setdefault(r['rank'],[]).append(r)
 if set(byrank)!={0,1,2,3}:raise ValueError('all4 actual ranks')
 sets=[];proof=[]
 for rank,rs in sorted(byrank.items()):
  rs=sorted(rs,key=lambda r:r['epoch']);prefixes=set(rs[0]['registered_prefixes']);sets.append(prefixes)
  if len(prefixes)!=48 or len({r['pid']for r in rs})!=1 or len({r['epoch']for r in rs})!=len(rs):raise ValueError('all48/pid/uniqueepochs')
  previous={p:0 for p in prefixes};requests={}
  for r in rs:
   if set(r['registered_prefixes'])!=prefixes or set(r['decode_calls'])!=prefixes:raise ValueError('stable all48 inventory')
   if len(r['request_ids'])!=1:raise ValueError('preregistered B1 dispatch trajectory')
   rid=r['request_ids'][0];n=sum(len(g['decode'])for g in r['groups'].values());p=sum(len(g['prefill'])for g in r['groups'].values())
   # Multiple GDN groups repeat the same B1 state; classify, do not add counts.
   if n and p:raise ValueError('single-request row cannot be mixed')
   inc=1 if n else 0
   if any(type(r['decode_calls'][x])is not int or r['decode_calls'][x]-previous[x]!=inc for x in prefixes):raise ValueError('every actual layer decode increments exactly once')
   previous=dict(r['decode_calls']);q=requests.setdefault(rid,dict(prefill=False,decode=0))
   if p:q['prefill']=True
   if n:
    if not q['prefill']:raise ValueError('actual own prefill must precede decode')
    q['decode']+=1
  if len(requests)!=2 or any(not q['prefill']or q['decode']<9 for q in requests.values()):raise ValueError('both real requests need>=9 decode dispatches, not2tokens')
  proof.append(dict(rank=rank,requests=requests,all48=True))
 if any(s!=sets[0]for s in sets):raise ValueError('same48 prefixes all4 ranks')
 return dict(dispatch_trajectory_pass=True,rows=proof,capacity7_merge_reachable=True,actual_merge_observed=False,model_numeric_qualified=False,performance_ready=False)
