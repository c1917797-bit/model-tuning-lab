"""MAIN-only small D/C workflow over actual025 owned safety classes. DefaultOFF."""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))

def actual_host_argv():
 raw=Path('/proc/self/cmdline').read_bytes()
 values=[x.decode('utf-8','strict') for x in raw.split(b'\0') if x]
 if len(values)<4 or values[1:3]!=['-I','-B'] or Path(values[3]).resolve()!=Path(__file__).resolve():raise ValueError('actual host -I/-B entry required')
 return values
def main():
 start=time.monotonic()
 started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--qualification-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 if os.environ.get('QWEN36_DELTALOG_SCREEN033_PAIR_ENABLE')!='1':raise ValueError('explicit MAIN pair opt-in')
 argv_actual=actual_host_argv()
 import resource
 from screen_binding import SOFTWARE_CASES,startup_gate
 from screen_admission import readset as admission_readset
 from screen_admission import source,qualify,checked,CUT
 
 from owned_substrate import load,REFS
 from owned_create import create
 from worker_snapshot_owner import snapshot
 sr=json.loads(a.source_ref);m=source(sr);qref=json.loads(a.qualification_ref);q=qualify(qref,sr)
 if time.time()+3600>1792135097:raise ValueError('full frozen phase cannot fit fixed cutoff')
 c,S,H,pairs=load()
 if a.output.parent!=c.PREP/'lowbit'or not a.output.name.startswith('run-dl-production-screen-PF037R5-')or a.output.exists():raise ValueError('new absent PF037R5 performance output, not savedraw033')
 os.sched_setaffinity(0,{166})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 if hard!=resource.RLIM_INFINITY:raise ValueError('original Docker child unlimitedAS wrapper required')
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard));a.output.mkdir(mode=0o700)
 co=H.Joint(start);owned=[];arms=[];cpu=None;primary=None
 passed={'readset':admission_readset(qref)}
 readset=[sr,qref,*passed['readset'],*m['files'].values(),*m['dependencies'],*REFS.values(),*admission_readset(qref)]
 # Exact Ref3, deduplicate before mounts; library/artifact closure never assumed.
 normalized={}
 for item in readset:
  r=dict(path=item['path'],bytes=Path(item['path']).stat().st_size,sha256=item['sha256'])
  if 'bytes'in item and item['bytes']!=r['bytes']:raise ValueError('whole dependency bytecount')
  if r['path']in normalized and normalized[r['path']]!=r:raise ValueError('ambiguous closure')
  normalized[r['path']]=r
 readset=list(normalized.values())
 for ref in readset:checked(ref)
 before={ref['path']:ref['sha256']for ref in readset}
 def child(ctl,label,args,cap):return H.child(ctl,label,args,cap,observe=ctl.expected['arm']!='cpu-preflight')
 def spawn(ctl,args,label):
  argv=c.docker_argv(ctl.cid,args)
  if label=='server':ctl.server_started=H.utc()
  so=(ctl.out/(label+'.stdout')).open('x');se=(ctl.out/(label+'.stderr')).open('x')
  proc=subprocess.Popen(ctl.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT);so.close();se.close()
  return proc,argv
 def ctl_for(role):
  leaf=H.fresh_leaf(a.output/role);H.outputs(leaf)
  for name in('receipts','barriers'):(leaf/name).mkdir()
  ctl=H.controller(S,co)(argparse.Namespace(output_dir=leaf),start);owned.append(ctl)
  ctl.observe(role+'-admission',initial=True);create(c,S,ctl,sr,readset,role,P)
  return ctl
 try:
  ctl=ctl_for('cpu-preflight')
  ch=child(ctl,'CPU',[str(P/'cpu_preflight.py'),'--source-ref',json.dumps(sr),'--output',str(ctl.out/'CPU.json')],120)
  v=c.obj(c.ref(ctl.out/'CPU.json'))
  if v!=dict(schema='deltalog.production-screen-CPU/v033',source=sr,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False):raise ValueError('actual exact shared sameimage software cases')
  clean=ctl.cleanup();ctl._pair_closed=True
  if c.obj(clean)['errors']or not(c.obj(clean)['stopped']and c.obj(clean)['retained']):raise ValueError('CPU owned release beforemodel')
  cpu=dict(child=ch,owned=c.ref(ctl.out/'OWNED.json'),report=c.ref(ctl.out/'CPU.json'),cleanup=clean)
  c.model(c.MODEL_REF) # Genuine complete original29file/15shard checkpoint gate.
  for role in('dense','candidate'):
   ctl=ctl_for(role)
   ch=child(ctl,'CANARY',[str(P/'guest_canary.py'),'--output',str(ctl.out/'CANARY.json')],180)
   cv=c.obj(c.ref(ctl.out/'CANARY.json'))
   if cv['rows']!=[dict(logical=i,values=[4.,5.])for i in range(4)]:raise ValueError('actual allfour smoke, not algorithm qualification')
   args=[str(P/'server_entry.py'),'--execute','--role',role,'--port','8230']
   if role=='candidate':args+=['--source-ref',json.dumps(sr),'--qualification-ref',json.dumps(qref),'--receipt-root',str(ctl.out/'receipts')]
   ctl.server,ctl.server_argv=spawn(ctl,args,'server')
   deadline=time.monotonic()+min(900,ctl.remaining(cap=900))
   while True:
    if ctl.server.poll()is not None or time.monotonic()>=deadline:raise ValueError('one bounded serverstartup; no retry')
    ctl.observe('model-startup')
    health=c.docker_argv(ctl.cid,['-c',"import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8230/health',timeout=2).status==200"])
    got=ctl.h.run(ctl.wrapper(health),min(4,ctl.remaining(cap=4)))
    c.write(ctl.out/('health-%d.json'%time.time_ns()),got)
    if got['exit_code']==0:break
    time.sleep(1)
   driver='/cache/cch/hypic_vllm_ascend-v0.8.5/tools/benchmark_shared_prefix.py'
   client=[str(P/'paired_driver.py'),'--original-driver',driver,'--barrier-root',str(ctl.out/'barriers'),'--base-url','http://127.0.0.1:8230','--model','qwen36-dl-sync','--input-tokens','32768','--prefix-tokens','16384','--output-tokens','1024','--requests','40','--concurrency','16','--warmup-requests','2','--timeout','1800','--json-output',str(ctl.out/'performance.json')]
   ctl.client,ctl.client_argv=spawn(ctl,client,'client');snapshots={};bindings={};handled=set()
   while ctl.client.poll()is None:
    if ctl.server.poll()is not None:raise ValueError('server failed whileclient')
    ctl.observe('model-workload')
    for stage in('BEFORE','AFTER'):
     wait=ctl.out/'barriers'/(stage+'-WAIT.json')
     if wait.is_file()and stage not in handled:
      if role=='candidate':
       snapshots[stage],bindings[stage]=snapshot(c,ctl,ctl.out/'receipts',stage)
       startup_gate(snapshots[stage],sr,qref)
      c.write(ctl.out/'barriers'/(stage+'-OWNED-ACK.json'),dict(stage=stage,owned_source_qualified=True,owned=ctl.cid,source=sr))
      handled.add(stage)
    time.sleep(.5)
   if ctl.client.returncode!=0 or handled!={'BEFORE','AFTER'}:raise ValueError('full40 canonical driver/barriers failed')
   if role=='candidate':
    for stage in('BEFORE','AFTER'):c.write(ctl.out/('WORKERS-'+stage+'.json'),snapshots[stage]);c.write(ctl.out/('BINDINGS-'+stage+'.json'),bindings[stage])
   row=dict(role=role,source=sr,owned=c.ref(ctl.out/'OWNED.json'),report=c.ref(ctl.out/'performance.json'),canary_child=ch,
    server_argv=ctl.server_argv,client_argv=ctl.client_argv,worker_process_proofs=ctl.process_proofs,observations=ctl.observations)
   row['cleanup']=ctl.cleanup();ctl._pair_closed=True
   row['client_terminal']=c.write(ctl.out/'CLIENT_TERMINAL.json',dict(requested_argv=ctl.client_argv,host_pid=ctl.client.pid,exit_code=ctl.client.returncode,termination_observed=ctl.client.poll()is not None,stdout=c.ref(ctl.out/'client.stdout'),stderr=c.ref(ctl.out/'client.stderr')))
   row['server_terminal']=c.write(ctl.out/'SERVER_TERMINAL.json',dict(requested_argv=ctl.server_argv,host_pid=ctl.server.pid,exit_code=ctl.server.returncode,termination_observed=ctl.server.poll()is not None,stdout=c.ref(ctl.out/'server.stdout'),stderr=c.ref(ctl.out/'server.stderr')))
   if c.obj(row['cleanup'])['errors']:raise ValueError('exact owned arm cleanup failure')
   arms.append(row)
  report_args=[str(P/'pair_consume.py'),'--dense',str(a.output/'dense/performance.json'),'--candidate',str(a.output/'candidate/performance.json'),'--dense-inputs',str(a.output/'dense/barriers/INPUTS.json'),'--candidate-inputs',str(a.output/'candidate/barriers/INPUTS.json'),'--workers-before',str(a.output/'candidate/WORKERS-BEFORE.json'),'--workers-after',str(a.output/'candidate/WORKERS-AFTER.json'),'--output',str(a.output/'PAIR.json')]
  # Only stdlib CPU: no guest after stop, no hiddenmodel reuse.
  proc=subprocess.run(['/usr/bin/python3','-I','-B',*report_args],capture_output=True,text=True,timeout=min(30,max(1,co.deadline-time.monotonic()-180)))
  c.write(a.output/'CONSUMER_CHILD.json',dict(argv=proc.args,exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr))
  if proc.returncode:raise ValueError('complete independent pair statistics failed')
 except BaseException as exc:primary=exc
 finally:
  for ctl in reversed(owned):
   if ctl.cid and not getattr(ctl,'_pair_closed',False):
    ctl.primary=primary
    try:ctl.cleanup()
    except BaseException as exc:co.secondary.append(repr(exc))
   co.secondary.extend(ctl.secondary)
  after={}
  try:
   for ref in readset:checked(ref);after[ref['path']]=ref['sha256']
  except BaseException as exc:co.secondary.append('source-after '+repr(exc))
  co.secondary.extend(S.formal_time_failures(co.deadline))
  if co.cleanup_used>180:co.secondary.append('shared180cleanup exceeded')
  result=c.write(a.output/'RESULT.json',dict(schema='deltalog.production-screen-owned-pair/v033',source=sr,qualification=qref,cpu=cpu,arms=arms,primary=repr(primary)if primary else None,secondary=co.secondary,source_before=before,source_after=after,phase_seconds=3600,cleanup_seconds=180,cleanup_spent=co.cleanup_used,elapsed_seconds=time.monotonic()-start,actual_host_argv=argv_actual,host_pid=os.getpid(),started_utc=started_utc,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),binding_refs={stage:c.ref(a.output/'candidate'/('BINDINGS-'+stage+'.json'))for stage in('BEFORE','AFTER')}if primary is None else {},pair_raw_refs={name:c.ref(a.output/relative)for name,relative in dict(dense='dense/performance.json',candidate='candidate/performance.json',dense_inputs='dense/barriers/INPUTS.json',candidate_inputs='candidate/barriers/INPUTS.json',workers_before='candidate/WORKERS-BEFORE.json',workers_after='candidate/WORKERS-AFTER.json').items()}if primary is None else {},model_acceptance=False,task=False))
  print('MAIN_DL_PRODUCTION_SCREEN '+json.dumps(result),flush=True)
 if primary:raise primary
 if co.secondary or len(arms)!=2 or before!=after:raise ValueError('whole exact pair source/resource/cleanup rejected')
 return 0
if __name__=='__main__':raise SystemExit(main())


