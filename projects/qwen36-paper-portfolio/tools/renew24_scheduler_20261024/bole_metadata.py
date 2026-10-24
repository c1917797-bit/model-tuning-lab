"""BOLE original metadata reader only. No launch, new approval, readiness or release factory."""
import hashlib
import json
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def strict_json(raw):
 def pairs(rows):
  d={}
  for k,v in rows:
   need(k not in d,'no duplicate JSON keys');d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs)
def bounded(C,r,cap=8*2**20):
 C.checked(r);need(r['bytes']<=cap,'bounded source/metadata JSON')
 raw=Path(r['path']).read_bytes()
 need(len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'],'same complete JSON bytes after checked read')
 return strict_json(raw)
def operand(argv,key):
 need(type(argv)is list and all(type(x)is str and x and '\0'not in x for x in argv),'nonempty exact argv metadata')
 need(argv.count(key)==1 and argv.index(key)+1<len(argv),'one exact command operand '+key)
 return argv[argv.index(key)+1]
def normalize(C,*,source_ref,commands_ref,stage,now,cpu_millis,docker_write_bound=None):
 """Actual original source/authority/review/COMMANDS -> inert registration.
 MAIN still consumes source-audit and gate predecessors and sets READY separately.
 """
 need(stage in('CPU','model','consume')and type(now)is int,'fixed original role and actual MAIN clock')
 need(type(cpu_millis)is int and cpu_millis>0 and (docker_write_bound is None or (type(docker_write_bound)is int and docker_write_bound>=0)),'MAIN registered original CPU quota/docker-write bound, not guessed')
 m=bounded(C,source_ref);commands=bounded(C,commands_ref)
 need(commands['schema']=='bole.performance-actual-bound-commands/v1'and commands['bound_source']==source_ref,'actual bound command source, not source-template Ref')
 root=Path(m['root']);out=Path(m['output_root'])
 need(Path(source_ref['path'])==root/'SOURCE_BOUND.json'and Path(commands_ref['path'])==root/'COMMANDS.json','same actual source-owned metadata locations')
 auth_ref=m['qualification_authority_ref'];auth=bounded(C,auth_ref)
 need(auth['schema']=='bole.MAIN-reviewed-fastpath-short8-qualification-authority/v1'and auth['approved']is True,'original BOLE source authority, not a new scheduler ticket')
 need(type(auth['start_epoch'])is int and type(auth['cutoff_epoch'])is int and
      auth['start_epoch']<=now<auth['cutoff_epoch'],'original current window; expired historical command cannot launch')
 review_ref=auth['MAIN_review_ref'];review=bounded(C,review_ref)
 need(review['schema']=='bole.MAIN-fastpath-short8-qualification-source-review/v1'and review['approved']is True and
      review['scope']==auth['scope']and review['source_root']==str(root)and review['output_root']==str(out),'original exact source-specific MAIN review')
 for k,mk in(('files','files'),('parent_preparation_readset','qualification_parent_preparation_readset'),
              ('historical_short_source','qualification_historical_short_source'),('short2k_helper_refs','short2k_helper_refs')):
  need(review[k]==m[mk],'original full review operand '+k)
 scope=auth['scope'];resources=m['resources'];p=m['input_resource_profile32k']
 need(scope['physical_NPUs']==[4,5,6,7]and scope['input_tokens']==32768 and scope['output_tokens']==8 and
      scope['generations']==2 and scope['formal_performance']is False,'BOLE32K/short8 only, not task/performance permission')
 need(scope['phase_seconds']==resources['whole_seconds']and scope['cleanup_seconds']==resources['shared_cleanup_seconds'],'original phase/cleanup budget, no scheduler extension')
 argv=commands[stage]
 if stage in('CPU','model'):
  need(operand(argv,'--source-ref')and strict_json(operand(argv,'--source-ref'))==source_ref,'real embedded bound Ref3 source operand')
  target=str(out)+('-CPU'if stage=='CPU'else'')
  need(operand(argv,'--output')==target and argv.count('--execute')==1 and
       argv.count('--cpu-only')==(1 if stage=='CPU'else 0),'exact original CPU/model role and output')
  entry=root/'host_service.py'
 else:
  target=str(out/'FASTPATH_NUMERIC_SCOPE_RESULT.json')
  need(operand(argv,'--source')==source_ref['path']and operand(argv,'--host-result')==str(out/'RESULT.json')and
       operand(argv,'--output')==target and argv.count('--consume')==1,'actual source-specific numerical consumer command')
  entry=root/'qualification_smoke_join.py'
 entry_ref=m['files'][entry.name];C.checked(entry_ref)
 need(entry_ref['path']==str(entry)and argv.count(str(entry))==1,'actual source-owned registered entry, not arbitrary script')
 reserves=p['reserves'];role_ram=resources['guest_model_GiB']if stage=='model'else resources['guest_CPU_GiB']
 need(resources['guest_model_GiB']*2**30==reserves['model_cgroup']and
      resources['guest_CPU_GiB']*2**30==reserves['independent_CPU_guest']and
      resources['host_GiB']*2**30==reserves['host_controller']and
      resources['RAMreserve_GiB']*2**30==reserves['host_RAM']and
      resources['Docker_reserve_GiB']*2**30==reserves['Docker_free'],'original derived resource/reserve identity')
 return dict(schema='bole.scheduler-stage-metadata/v1',paper='BOLE',stage=stage,normalizer_ref=C.reference(__file__),
  source_ref=source_ref,commands_ref=commands_ref,authority_ref=auth_ref,review_ref=review_ref,
  entry_ref=entry_ref,argv=argv,output_root=target,physical=[4,5,6,7]if stage=='model'else[],
  kind='model'if stage=='model'else'cpu',budget=dict(ram=int((role_ram+resources['host_GiB'])*2**30),
  cpu_millis=cpu_millis,disk={'docker':docker_write_bound,'output':reserves['output_cap']}),
  reserves=dict(ram=reserves['host_RAM'],docker=reserves['Docker_free']),
  start_epoch=auth['start_epoch'],deadline_epoch=auth['cutoff_epoch'],
  wall_seconds=scope['phase_seconds']+scope['cleanup_seconds'],
  state='preparing',ready=False,dispatch_executed=False,
  missing_registration=['actual source-reviewed Docker future-write bound']if docker_write_bound is None else[],
  required_actual_predecessors=['original source-audit accepted']+
   (['original model RESULT plus complete 4rank/64layer/128write numerical data']if stage=='consume'else[]),
  standalone_CPU_before_model_required=False,model_already_runs_original_CPU_preflight=True,
  release_verified=False)
def checked_old_leaf(C,value):
 need(type(value)is dict and set(value)=={'path','sha256'},'exact original historical Ref2')
 r=C.reference(value['path']);need(r['sha256']==value['sha256'],'complete original leaf SHA, no invented bytes')
 return r
def historical_result(C,*,source_ref,result_ref,cleanup_refs):
 v=bounded(C,result_ref)
 need(v['schema']=='bole.actual-three-node-model-owned/v131'and v['source']==source_ref and
      v['source_before']==v['source_after'],'original exact whole-host source unchanged')
 rows=[]
 for r in cleanup_refs:
  c=bounded(C,r)
  need(Path(r['path']).name=='cleanup.json'and c['stopped']is True and c['retained']is True and
       c['deleted']is False and c['errors']==[],'actual lower-case original own cleanup')
  need(type(c['container'])is str and len(c['container'])==64 and
       c['protected_boundary']['own_on_protected']is False,'exact owned CID and original protected observation')
  refs={k:checked_old_leaf(C,c[k])for k in('after_inspect','before_inspect','release_smi','stop_receipt')}
  rows.append(dict(cleanup_ref=r,cid=c['container'],original_leaf_refs=refs))
 return dict(schema='bole.scheduler-historical-result-observation/v1',source_ref=source_ref,result_ref=result_ref,
  failed=v['primary']is not None or bool(v['secondary']),primary=v['primary'],secondary=v['secondary'],
  own_cleanup_recorded=rows,current_release_verified=False,lease_must_hold_until_MAIN_fresh_owner_inspect=True,
  numeric_or_performance_pass_claimed=False)
