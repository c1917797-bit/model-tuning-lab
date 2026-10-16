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
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--qualification-ref');p.add_argument('--screen',action='store_true');p.add_argument('--smoke-owner-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 if os.environ.get('DL122_PAIR_ENABLE')!='1':raise ValueError('explicit MAIN pair opt-in')
 argv_actual=actual_host_argv()
 import resource
 import api122 as A
 from api122 import source,checked
 from software_contract import SOFTWARE_CASES
 from policy_receipts122 import snapshot as policy_snapshot
 def startup_gate(rows,sr,qref):
  m=A.source(sr,pair=True)
  with A.context(m)as(v,pm):
   for row in rows:v['live106'].validate_snapshot(row,m['production_source_ref'],m['production_qualification_ref'])
 from owned_substrate import load,REFS
 from owned_create import create
 def snapshot(c,ctl,root,stage):
  with A.context(m)as(v,pm):return v['snapshot_owner106'].snapshot(c,ctl,root,stage)
 sr=json.loads(a.source_ref);m,q=A.qualify(sr);qref=m['production_qualification_ref'];count=40 if a.screen else 2;warmups=2
 A.need(time.time()+3600<A.CUT,'full existing owner budget must fit fixed cutoff')
 smoke_refs=[]
 if a.screen:
  A.need(a.smoke_owner_ref is not None,'actual first smoke pair required before40 screen');smr=json.loads(a.smoke_owner_ref);so=A.obj(smr);ipr=so['independent_pair_ref'];A.smoke_gate(so,A.obj(ipr),sr)
  for arm in so['arms']:
   cl=A.obj(A.original025_ref3(arm['cleanup']));A.need(cl['stopped']and cl['retained']and cl['errors']==[],'actual both smoke arms released')
  smoke_refs=[smr,ipr]
 if a.qualification_ref is not None:A.need(json.loads(a.qualification_ref)==qref,'actual106 qualification argument')
 c,S,H,pairs=load(a.output)
 if a.output.parent!=Path('/opt/host/vnf/austinov')or a.output.name!=('run-dl-production122R2-screenpair-MAIN-NEW24H_001'if a.screen else'run-dl-production122R2-smokepair-MAIN-NEW24H_001')or a.output.exists():raise ValueError('new absent production005 output')
 os.sched_setaffinity(0,{166})
 soft,hard=resource.getrlimit(resource.RLIMIT_AS)
 if hard!=resource.RLIM_INFINITY:raise ValueError('original Docker child unlimitedAS wrapper required')
 resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard));a.output.mkdir(mode=0o700)
 co=H.Joint(start);owned=[];arms=[];cpu=None;primary=None
 readset=[sr,*A.readset(m),*REFS.values(),*smoke_refs]
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
  if v!=dict(schema='deltalog.production-pair-CPU/v122',source=sr,tests=SOFTWARE_CASES,pass_software=True,Devices=[],NPU=False,model=False):raise ValueError('actual exact shared sameimage software cases')
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
   args+=['--source-ref',json.dumps(sr),'--receipt-root',str(ctl.out/'receipts')]
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
   client=[str(P/'paired_driver.py'),'--original-driver',driver,'--barrier-root',str(ctl.out/'barriers'),'--base-url','http://127.0.0.1:8230','--model','qwen36-mxr-eager','--input-tokens','2048','--prefix-tokens','1024','--output-tokens','1024','--requests',str(count),'--concurrency','1','--warmup-requests',str(warmups),'--timeout','1800','--json-output',str(ctl.out/'performance.json')]
   ctl.client,ctl.client_argv=spawn(ctl,client,'client');snapshots={};bindings={};handled=set()
   while ctl.client.poll()is None:
    if ctl.server.poll()is not None:raise ValueError('server failed whileclient')
    ctl.observe('model-workload')
    for stage in('BEFORE','AFTER'):
     wait=ctl.out/'barriers'/(stage+'-WAIT.json')
     if wait.is_file()and stage not in handled:
      if stage=='BEFORE':c.write(ctl.out/'COMMON_POLICY.json',policy_snapshot(c,ctl,ctl.out/'receipts'))
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
   if c.obj(row['cleanup'])['errors']or not(c.obj(row['cleanup'])['stopped']and c.obj(row['cleanup'])['retained']):raise ValueError('actual full release before changing arm')
   arms.append(row)
  report_args=[str(P/'pair_consume.py'),'--dense',str(a.output/'dense/performance.json'),'--candidate',str(a.output/'candidate/performance.json'),'--dense-inputs',str(a.output/'dense/barriers/INPUTS.json'),'--candidate-inputs',str(a.output/'candidate/barriers/INPUTS.json'),'--workers-before',str(a.output/'candidate/WORKERS-BEFORE.json'),'--workers-after',str(a.output/'candidate/WORKERS-AFTER.json'),'--output',str(a.output/'PAIR.json'),'--source-ref',json.dumps(sr),'--requests',str(count)]
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
  result=c.write(a.output/'RESULT.json',dict(schema='deltalog.production-owned-single-pair/v122',source=sr,qualification=qref,cpu=cpu,arms=arms,primary=repr(primary)if primary else None,secondary=co.secondary,source_before=before,source_after=after,phase_seconds=3600,cleanup_seconds=180,cleanup_spent=co.cleanup_used,elapsed_seconds=time.monotonic()-start,actual_host_argv=argv_actual,host_pid=os.getpid(),started_utc=started_utc,completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),independent_pair_ref=A.ref(a.output/'PAIR.json')if primary is None else None,binding_refs={stage:c.ref(a.output/'candidate'/('BINDINGS-'+stage+'.json'))for stage in('BEFORE','AFTER')}if primary is None else {},pair_raw_refs={name:c.ref(a.output/relative)for name,relative in dict(dense='dense/performance.json',candidate='candidate/performance.json',dense_inputs='dense/barriers/INPUTS.json',candidate_inputs='candidate/barriers/INPUTS.json',workers_before='candidate/WORKERS-BEFORE.json',workers_after='candidate/WORKERS-AFTER.json').items()}if primary is None else {},model_acceptance=False,task=False))
  print('MAIN_DL122_PAIR '+json.dumps(result),flush=True)
 if primary:raise primary
 if co.secondary or len(arms)!=2 or before!=after:raise ValueError('whole exact pair source/resource/cleanup rejected')
 return 0
if __name__=='__main__':raise SystemExit(main())


