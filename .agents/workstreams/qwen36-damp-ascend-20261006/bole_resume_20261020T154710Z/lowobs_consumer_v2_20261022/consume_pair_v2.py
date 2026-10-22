"""Independent saved-result paired screen reader; never invokes candidate computation."""
import argparse,hashlib,json,math,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref')
 p=Path(r['path']);need(p.is_absolute()and type(r['bytes'])is int and 0<r['bytes']<=16*2**20,'bounded metadata')
 b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'immutable metadata')
 return json.loads(b)
def cleanup_obj(summary,expected_path):
 p=Path(__file__).resolve().parent/'cleanup_summary.py'
 need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary pinned cleanup helper')
 with p.open('rb')as f:b=f.read(3958)
 need(len(b)==3957 and hashlib.sha256(b).hexdigest()=='1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687','exact copied cleanup summary helper')
 scope={'__name__':'_bole_lowobs_cleanup_summary_v2','__file__':str(p)}
 exec(compile(b,str(p),'exec'),scope)
 return scope['read_cleanup_summary'](summary,expected_path)[1]
def finite(x):return type(x)in(int,float)and math.isfinite(x)
def metrics(row):
 t=row['timing'];n=t['output_tokens'];d=t['duration_s'];f=t['ttft_ms']
 need(n==1024 and finite(d)and d>0 and finite(f)and 0<=f<=d*1000,'valid fixed-output client clocks')
 return dict(output_tokens=1024,TTFT_ms=f,TPOT_ms=max(0.,d-f/1000)*1000/1023,output_tokens_per_second=1024/d,duration_s=d)
def arm(sr,rr,want):
 m=obj(sr);r=obj(rr);out=Path(m['output_root']);need(Path(rr['path'])==out/'RESULT.json','actual arm output')
 need(r['source']==sr and r['schema']=='bole.actual-three-node-model-owned/v131'and r['cpu_only']is False
  and r['primary']is None and r['secondary']==[] and r['source_before']==r['source_after'],'complete successful actual model result')
 s=r['summary'];need(m['performance_arm']==s['performance_arm']==want,'actual arm')
 for key in ('model_release','CPU_release'):
  release=cleanup_obj(s[key],out/('dense'if key=='model_release'else'cpu-preflight')/'cleanup.json');need(release['stopped']is True and release['retained']is True and release['errors']==[],'actual owned release')
 cpu=obj(s['CPU_report']);need(cpu['pass_preflight']is True and cpu['source']==sr and cpu['Devices']==[],'actual same-image preflight')
 term=obj(s['actual_client_terminal']);need(term['exit_code']==0,'actual streaming client exit')
 root=out/'dense';httpref=s['streaming_validation']['HTTP'];http=obj(httpref)
 need(httpref==ref(root/'performance-client/HTTP_RESULT.json')and http['source']==sr,'exact original HTTP result')
 inp=obj(ref(root/'performance-client/INPUTS.json'));need(inp['source']==sr and inp['input_tokens']==len(inp['token_ids'])==131,'exact input IDs')
 rows=http['rows'];need([x['label']for x in rows]==['warmup','measured','retirement-barrier'],'request order')
 for row,n in zip(rows,(1024,1024,1)):
  p=row['request'];need(row['status']==200 and row['done']is True and row['id']=='cmpl-'+row['header']and len(row['token_ids'])==n
   and all(type(i)is int and i>=0 for i in row['token_ids'])and row['usage']==dict(row['usage'],prompt_tokens=131,completion_tokens=n)
   and row['timing']['ok']is True and row['timing']['output_tokens']==n,'successful complete HTTP tokens')
  need(p['prompt']==inp['token_ids']and p['max_tokens']==n and p['temperature']==0 and p['seed']==0
   and p['stream']is True and p['return_token_ids']is True and p['top_p']==1 and p['n']==1,'exact common payload')
  if n>1:need(p['ignore_eos']is True and row['timing']['finish_reason']=='length','fixed output no early EOS')
 receipts=[]
 if want=='bole':
  for rank in range(4):
   for g in (1,2):
    a=ref(root/'receipts'/('PERF-ACTIVE-GEN-%d-RANK-%d.json'%(g,rank)));v=obj(a)
    need(v['source']==sr and v['rank']==rank and v['generation']==g and v['kind']=='ACTIVE'and v['record']==dict(algorithm='BOLE',
      replay_observation_off=True,collect_observation_only=False,helper=m['files']['formal_observation.py'],runner=m['files']['service_runner.py']),'actual all-rank active mechanism')
    b=ref(root/'receipts'/('PERF-RETIRE-GEN-%d-RANK-%d.json'%(g,rank)));v=obj(b)
    need(v['source']==sr and v['rank']==rank and v['generation']==g and v['kind']=='RETIRE','actual retirement')
    record=v['record'];cv=record['algorithm_coverage'];need(record['output_token_ids']==rows[g-1]['token_ids']and record['request']==rows[g-1]['id']+'-0','native/HTTP join')
    need(cv['schema']=='bole.actual-publication-coverage/v1'and cv['algorithm']=='BOLE'and cv['generation']==g and cv['request']==record['request']
      and type(cv['frames'])is int and 512<=cv['frames']<=1023 and cv['all64_frames']==cv['frames']and cv['prefill_tokens']==1
      and cv['published_tokens']==1023 and cv['output_tokens']==1024 and cv['unattributed_generated_tokens']==0
      and cv['publication_token_ids']==rows[g-1]['token_ids'][1:],'complete actual BOLE publication coverage')
    receipts.extend((a,b))
   c=ref(root/'receipts'/('PERF-COMPLETE-GEN-2-RANK-%d.json'%rank));v=obj(c)
   need(v['source']==sr and v['rank']==rank and v['generation']==2 and v['kind']=='COMPLETE'
    and len(v['record']['requests'])==2 and v['record']['calibration_generations']==[1,2],'two-generation calibration reuse')
   receipts.append(c)
  need(not list((root/'receipts').glob('PERF-FAILURE-*.json')),'no sticky failure')
 for v in s['worker_snapshots']:need(v['source_ref']==sr and v['native_core']is True and v['native_inverse']is True and v['allow_hf32']is False,'actual common precision restored')
 need(len(s['worker_snapshots'])==4,'all4 actual snapshots')
 cmdref=ref(root/'receipts/SERVER_COMMAND.json');cmd=obj(cmdref);need(cmd['source']==sr and cmd['performance_arm']==want,'source-owned actual server argv')
 return dict(manifest=m,result=r,input=inp,payloads=[x['request']for x in rows],command=cmd,metrics=metrics(rows[1]),
  evidence=dict(source=sr,result=rr,HTTP=httpref,input=ref(root/'performance-client/INPUTS.json'),server_command=cmdref,coverage=receipts))
def consume(native_source,native_result,bole_source,bole_result):
 a=arm(native_source,native_result,'native_ar');b=arm(bole_source,bole_result,'bole')
 for field in ('common','installed_sources','runtime_sources','stream_runtime_sources','cache_memory_config','stream_resource_profile','native_speculative_config','checkpoint_config_ref','checkpoint_index_ref','resources','performance_profile','performance_client_contract'):
  need(a['manifest'].get(field)==b['manifest'].get(field),'matched common '+field)
 need(a['input']['token_ids']==b['input']['token_ids']and a['payloads']==b['payloads'],'identical exact requests and order')
 aa=obj(a['manifest']['authority_ref']);ba=obj(b['manifest']['authority_ref'])
 for key in ('user_authorization_ref','start_epoch','cutoff_epoch','phase_seconds','cleanup_seconds'):need(aa[key]==ba[key],'same bounded authority')
 argv=b['command']['argv'];need(argv.count('--speculative-config')==1,'one candidate speculative option')
 i=argv.index('--speculative-config');need(json.loads(argv[i+1])==dict(method='mtp',num_speculative_tokens=8),'exact BOLE native dependency')
 need(a['command']['argv']==argv[:i]+argv[i+2:],'same argv except algorithm dependency')
 for k in ('formal_observation.py','service_runner.py','model_entry.py','service_bridge.py','core112.py','adapter.py','transaction.py'):
  need(a['manifest']['files'][k]['sha256']==b['manifest']['files'][k]['sha256'],'same frozen source '+k)
 am,bm=a['metrics'],b['metrics'];gain=bm['output_tokens_per_second']/am['output_tokens_per_second']-1
 return dict(schema='bole.fixed131-paired-screen/v1',scope=dict(input_tokens=131,output_tokens=1024,concurrency=1,rounds=1),
  native=am,bole=bm,throughput_gain_percent=100*gain,screen_gain_at_least_10_percent=gain>=.1,
  TTFT_scope='first nonempty streamed text',TPOT_scope='HTTP final duration less TTFT over1023',
  evidence=dict(native=a['evidence'],bole=b['evidence']),formal_performance=False,task_accuracy=False,
  new_source_NPU_numerical_qualification='separate prerequisite; not manufactured by timing reader',technology_success=False)
if __name__=='__main__':
 p=argparse.ArgumentParser(allow_abbrev=False)
 for n in ('native-source','native-result','bole-source','bole-result'):p.add_argument('--'+n,required=True,type=json.loads)
 x=p.parse_args();out=ROOT/'LOWOBS_FIXED131_PAIR_SCREEN_v2.json';need(not out.exists(),'exclusive actual paired-screen output')
 result=consume(x.native_source,x.native_result,x.bole_source,x.bole_result)
 with out.open('xb')as f:f.write((json.dumps(result,sort_keys=True)+'\n').encode());f.flush();os.fsync(f.fileno())
 print(json.dumps(result,sort_keys=True))
