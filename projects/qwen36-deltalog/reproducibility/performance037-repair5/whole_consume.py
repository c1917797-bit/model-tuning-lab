"""After-parent-exit independent whole Ref/cleanup/paired evidence consumer."""
import argparse,datetime,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)<= {'path','bytes','sha256'}and {'path','sha256'}<=set(r),'actual Ref2/3')
 p=Path(r['path']);need(p.is_absolute()and not p.is_symlink(),'ordinary immutable file')
 b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256']and ('bytes'not in r or len(b)==r['bytes']),'rehash complete raw')
 return b
def obj(r):return json.loads(checked(r))
def load(name):
 s=importlib.util.spec_from_file_location('_whole_'+name,P/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def command(r,argv):
 v=obj(r);need(v['exit_code']==0 and v['requested_argv']==argv,'exact actual CLI raw receipt');return v
def cleanup(owned_ref,clean_ref,S,c,parent_pid):
 own=obj(owned_ref);v=obj(clean_ref);cid=own['cid']
 need(re.fullmatch('[0-9a-f]{64}',cid)is not None and v['container']==cid and v['stopped']is v['retained']is True and v['deleted']is False and v['errors']==[]and v['primary_error']is None,'exact owned retained stop')
 command(v['stop_receipt'],[S.DOCKER,'stop','--time','15',cid])
 before=json.loads(command(v['before_inspect'],[S.DOCKER,'inspect',cid])['stdout']);after=json.loads(command(v['after_inspect'],[S.DOCKER,'inspect',cid])['stdout'])
 need(len(before)==len(after)==1,'one exact inspect')
 expected={k:own[k]for k in('cid','name','image','arm','source','host_sha256','guest_cpus','mounts')}
 S.validate_inspect(before[0],expected);S.validate_inspect(after[0],expected)
 x=after[0];need(x['Id']==cid and x['State']['Running']is False and x['State']['Pid']==0 and not x.get('ExecIDs')and not x['State'].get('OOMKilled'),'actual no live init/exec/OOM')
 raw=command(v['release_smi'],[S.SMI,'info'])
 for card in(4,5,6,7):S.H.idle_one(raw['stdout'],card)
 boundary=v['protected_boundary'];need(boundary['schema']=='sparq.protected-boundary/v1'and boundary['own_on_protected']is False,'actual owned protected scope')
 need(c.protected_module().protected_boundary(boundary['baseline'],boundary['observed'],[cid],[parent_pid])==boundary,'independent original protected-boundary recompute')
 return cid
def consume(result_ref,terminal_ref,source_ref):
 audit=load('source_audit');audit.audit(source_ref);r=obj(result_ref);terminal=obj(terminal_ref)
 if 'structuredContent'in terminal:terminal=terminal['structuredContent']
 if 'result'in terminal and 'record'in terminal['result']:
  need(terminal.get('routeDecision')in('peer_direct','upstream_local_peer'),'actual direct parent terminal route')
  rec=terminal['result']['record'];need(rec['state']=='completed'and rec['cancelled']is False and rec['timedOut']is False,'actual completed parent')
  terminal=dict(command=rec['command'],args=rec['args'],cwd=rec['cwd'],exit_code=rec['exitCode'],stdout=rec['stdout'],stderr=rec['stderr'])
 expected=['/usr/bin/python3','-I','-B',str(P/'host_pair.py'),'--execute','--source-ref',json.dumps(source_ref)]
 need(terminal['exit_code']==0 and terminal['command']=='/usr/bin/python3'and terminal['args'][:3]==['-I','-B',str(P/'host_pair.py')],'actual parent terminal -I/-B and exit0')
 need(terminal['cwd']=='/opt/host/vnf/austinov/model-tuning-lab','actual parent cwd')
 need([terminal['command'],*terminal['args']]==r['actual_host_argv'],'exact parent argv receipt')
 marker='MAIN_DL_PRODUCTION_SCREEN '
 lines=[x[len(marker):]for x in terminal['stdout'].splitlines()if x.startswith(marker)]
 need(len(lines)==1 and json.loads(lines[0])==result_ref,'whole parent RESULT publication')
 need(r['source']==source_ref and r['schema']=='deltalog.production-screen-owned-pair/v033'and r['primary']is None and r['secondary']==[]and r['phase_seconds']==3600 and r['cleanup_seconds']==180 and 0<=r['cleanup_spent']<=180 and 0<r['elapsed_seconds']<=3600,'whole runtime budget/primary')
 start=datetime.datetime.fromisoformat(r['started_utc']).timestamp();end=datetime.datetime.fromisoformat(r['completed_utc']).timestamp()
 need(1791962297<=start<=end<=1792135097 and end-start<=3600,'actual frozen UTC window, no reset')
 need(r['source_before']==r['source_after']and r['source_before'],'exact beforeafter readset')
 gate=load('screen_admission');gate.qualify(r['qualification'],source_ref)
 for path,digest in r['source_after'].items():checked(dict(path=path,sha256=digest))
 from screen_binding import SOFTWARE_CASES,startup_gate
 substrate=load('owned_substrate');c,S,H,_=substrate.load()
 cpu=r['cpu'];cp=obj(cpu['child']);need(cp['exit_code']==0 and cp['child_termination_observed']is True,'CPU real terminated child')
 need(obj(cpu['report'])==dict(schema='deltalog.production-screen-CPU/v033',source=source_ref,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False),'actual shared software-count producer')
 for ref in(cp['stdout_ref'],cp['stderr_ref']):checked(ref)
 co=obj(cpu['owned']);ids=[cleanup(cpu['owned'],cpu['cleanup'],S,c,r['host_pid'])]
 need([a['role']for a in r['arms']]==['dense','candidate'],'serial exact pair')
 for a in r['arms']:
  need(a['source']==source_ref,'same arm source');ids.append(cleanup(a['owned'],a['cleanup'],S,c,r['host_pid']))
  client=obj(a['client_terminal']);need(client['exit_code']==0 and client['termination_observed']is True and client['requested_argv']==a['client_argv'],'real client exit/argv')
  server=obj(a['server_terminal']);need(server['termination_observed']is True and type(server['exit_code'])is int and server['requested_argv']==a['server_argv'],'real server Docker parent termination')
  for ref in(client['stdout'],client['stderr'],server['stdout'],server['stderr']):checked(ref)
 need(len(set(ids))==3,'fresh distinct CPU/D/A ownCID')
 root=Path(result_ref['path']).parent
 bindings={stage:obj(r['binding_refs'][stage])for stage in('BEFORE','AFTER')}
 candidate=obj(r['arms'][1]['owned'])
 for stage,rows in bindings.items():
  need(len(rows)==4 and {x['host']['physical']for x in rows}=={4,5,6,7}and len({x['host']['pid']for x in rows})==4,'real four physical binding set')
  for x in rows:need(candidate['cid']in x['host']['cgroup']and x['host']['start_ticks']>0 and x['guest']['source_ref']==source_ref,'actual owned source/start guest association')
  need(sorted((x['guest']for x in rows),key=lambda x:x['pid'])==sorted(obj(r['pair_raw_refs']['workers_before'if stage=='BEFORE'else'workers_after']),key=lambda x:x['pid']),'bound actual guest receipt is measured count input')
  need(all(x['guest']['qualification_ref']==r['qualification']for x in rows),'workers use exact qualification')
  startup_gate([x['guest']for x in rows],source_ref,r['qualification'])
 expected_raw=dict(dense='dense/performance.json',candidate='candidate/performance.json',dense_inputs='dense/barriers/INPUTS.json',candidate_inputs='candidate/barriers/INPUTS.json',workers_before='candidate/WORKERS-BEFORE.json',workers_after='candidate/WORKERS-AFTER.json')
 need(set(r['pair_raw_refs'])==set(expected_raw)and all(Path(r['pair_raw_refs'][k]['path'])==root/v for k,v in expected_raw.items()),'exact canonical raw paths; no substituted reports')
 args=['/usr/bin/python3','-I','-B',str(P/'pair_consume.py'),'--dense',str(root/'dense/performance.json'),'--candidate',str(root/'candidate/performance.json'),'--dense-inputs',str(root/'dense/barriers/INPUTS.json'),'--candidate-inputs',str(root/'candidate/barriers/INPUTS.json'),'--workers-before',str(root/'candidate/WORKERS-BEFORE.json'),'--workers-after',str(root/'candidate/WORKERS-AFTER.json'),'--output',str(root/'WHOLE_RECOMPUTED_PAIR.json')]
 for ref in r['pair_raw_refs'].values():checked(ref)
 proc=subprocess.run(args,capture_output=True,text=True,timeout=30);need(proc.returncode==0,'independent actual42 inputs/40requests/fourworker48 measured delta recompute')
 return dict(schema='deltalog.production-screen-whole-owned/v033',source=source_ref,result=result_ref,terminal=terminal_ref,whole_owned_release_verified=True,owned_cids=ids,paired_metrics_recomputed=True,formal_three_rounds=False,task=False,acceptance=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('result-ref','terminal-ref','source-ref','output'):p.add_argument('--'+k)
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return
 value=consume(json.loads(a.result_ref),json.loads(a.terminal_ref),json.loads(a.source_ref))
 with Path(a.output).open('x',encoding='utf8')as f:json.dump(value,f);f.write('\n')
if __name__=='__main__':main()
