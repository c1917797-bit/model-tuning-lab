"""Thin dense-only075/052 workflow over exact025 Joint/Controller. MAIN only."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
def client_terminal(c,ctl,tokens,handled):
 label='client-'+str(tokens);receipt=dict(exit_code=ctl.client.returncode,actual_argv=ctl.client_argv,stdout=c.ref(ctl.out/(label+'.stdout')),stderr=c.ref(ctl.out/(label+'.stderr')),ownership_barriers_seen=sorted(handled),profile=tokens)
 path=ctl.out/('CLIENT-TERMINAL-%d.json'%tokens);c.write(path,receipt);return c.ref(path)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--output-contract-only',action='store_true');p.add_argument('--source-ref');p.add_argument('--output');p.add_argument('--cpu-only',action='store_true');a=p.parse_args()
 if a.output_contract_only:
  C.output_argument(a.output);print(json.dumps(dict(output=a.output,NPU=False,contract_only=True)));return 0
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);readset=[sr,*m['files'].values(),*m['dependencies']]
 if a.source_audit:print(json.dumps(dict(source=sr,readset=len(readset),NPU=False,resources_admitted=False,candidate_qualification=False)));return 0
 a.output=C.output_argument(a.output);C.need(os.environ.get('DENSE_OPPORTUNITY090_MAIN_ENABLE')=='1'and a.output==(C.CPU_OUT if a.cpu_only else C.OUT)and not a.output.exists(),'MAIN-only unique registered output')
 actual_argv=[x.decode('utf8','strict')for x in Path('/proc/self/cmdline').read_bytes().split(b'\0')if x];C.need(len(actual_argv)>=4 and actual_argv[1:3]==['-I','-B']and Path(actual_argv[3]).resolve()==Path(__file__).resolve(),'actual source-bound -I/-B host CLI')
 from owned_substrate import load
 from owned_create import create
 from worker_snapshot_owner import snapshot
 import resource
 os.sched_setaffinity(0,{166});soft,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go child AS wrapper');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 start=time.monotonic();c,S,H,pairs=load(a.output);a.output.mkdir(mode=0o700);joint=H.Joint(start);owned=[];primary=None;summary={};before={r['path']:r['sha256']for r in readset}
 def ctl_for(role):
  leaf=H.fresh_leaf(a.output/role);H.outputs(leaf);(leaf/'receipts').mkdir();ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start);owned.append(ctl);ctl.observe(role+'-admission',initial=True);create(c,S,ctl,sr,readset,role,P);return ctl
 def child(ctl,label,args,limit):return H.child(ctl,label,args,limit,observe=ctl.expected['arm']!='cpu-preflight')
 def spawn(ctl,args,label):
  argv=c.docker_argv(ctl.cid,args);so=(ctl.out/(label+'.stdout')).open('x');se=(ctl.out/(label+'.stderr')).open('x');proc=subprocess.Popen(ctl.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT);so.close();se.close();return proc,argv
 def close(ctl):
  r=ctl.cleanup();ctl._pair_closed=True;v=c.obj(r);C.need(v['stopped']and v['retained']and not v['errors'],'actual retained release');return r
 try:
  cpu=ctl_for('cpu-preflight');summary['CPU_child']=child(cpu,'CPU',[str(P/'preflight114.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(cpu.out/'CPU.json')],120);report=c.obj(c.ref(cpu.out/'CPU.json'));C.need(report['source']==sr and report['pass_preflight']is True and report['Devices']==[]and report['native_runtime_parser_checked']is True and report['registry_arch_enumerated']is True,'real sameimage source preflight');summary['CPU_report']=c.ref(cpu.out/'CPU.json');summary['CPU_release']=close(cpu)
  if not a.cpu_only:
   c.model(c.MODEL_REF);ctl=ctl_for('dense');summary['canary']=child(ctl,'CANARY',[str(P/'guest_canary.py'),'--output',str(ctl.out/'CANARY.json')],180);C.need(c.obj(c.ref(ctl.out/'CANARY.json'))['rows']==[dict(logical=i,values=[4.,5.])for i in range(4)],'genuine all4 tiny values; not model qualification')
   ctl.server_started=H.utc();ctl.server,ctl.server_argv=spawn(ctl,[str(P/'server090.py'),'--execute','--source-ref',json.dumps(sr),'--receipt-root',str(ctl.out/'receipts')],'server');end=time.monotonic()+min(900,ctl.remaining(cap=900))
   while True:
    C.need(ctl.server.poll()is None and time.monotonic()<end,'one bounded native server startup');ctl.observe('dense-startup')
    argv=c.docker_argv(ctl.cid,['-c',"import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8230/health',timeout=2).status==200"]);r=ctl.h.run(ctl.wrapper(argv),min(4,ctl.remaining(cap=4)));c.write(ctl.out/('health-%d.json'%time.time_ns()),r)
    if r['exit_code']==0:break
    time.sleep(1)
   from load_consumer114 import consume as consume_load
   load_rows=[C.obj(c.ref(f))for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   load_proof=consume_load(load_rows,report['actual_checkpoint_mtp_names'],m['installed_sources']['qwen_mtp'],m['files']['load_receipt111.py']);summary['MTP_load']=C.write(ctl.out/'MTP-LOAD-CONSUMPTION.json',load_proof)
   summary['MTP_load_receipts']=[c.ref(f)for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   summary['profiles']=[];summary['client_terminals']=[]
   for tokens in C.PROFILES:
    barriers=ctl.out/('barriers-%d'%tokens);barriers.mkdir();ctl.client,ctl.client_argv=spawn(ctl,C.client_command(tokens,ctl.out,sr),'client-'+str(tokens));handled=set();profile_end=time.monotonic()+min(900,ctl.remaining(cap=900))
    while ctl.client.poll()is None:
     C.need(ctl.server.poll()is None and time.monotonic()<profile_end,'one bounded900s profile, original whole deadline');ctl.observe('dense-profile-'+str(tokens))
     for stage in('BEFORE','AFTER'):
      if(barriers/(stage+'-WAIT.json')).is_file()and stage not in handled:
       rows,bindings=snapshot(c,ctl,ctl.out/'receipts','%d-%s'%(tokens,stage));C.need(len(rows)==4 and all(v['schema']=='dense.native-worker-snapshot/v090'and v['source_ref']==sr and v['native_core']is v['native_inverse']is True and v['allow_hf32']is False for v in rows),'all4 actual native sources and HF32 readback')
       C.need({v['pid']for v in rows}=={v['pid']for v in load_rows},'actual native snapshot worker lifetimes join actual MTP loader workers')
      c.write(ctl.out/('BINDINGS-%d-%s.json'%(tokens,stage)),bindings);c.write(barriers/(stage+'-ACK.json'),dict(stage=stage,source=sr,profile=tokens,actual_owned_native_workers=4));handled.add(stage)
     time.sleep(.2)
    summary['client_terminals'].append(client_terminal(c,ctl,tokens,handled))
    C.need(ctl.client.returncode==0,'canonical native HTTP client failed; inspect preserved CLIENT-TERMINAL stdout/stderr first')
    C.need(handled=={'BEFORE','AFTER'},'ownership snapshots bracket actual measured requests');summary['profiles'].append(dict(tokens=tokens,exit_code=ctl.client.returncode,report=c.ref(ctl.out/('profile-%d.json'%tokens)),inputs=c.ref(barriers/'INPUTS.json'),client_argv=ctl.client_argv))
   summary['dense_release']=close(ctl)
   args=['/usr/bin/python3','-I','-B',str(P/'consume090.py'),'--execute','--source-ref',json.dumps(sr),'--dense-root',str(ctl.out),'--output',str(a.output/'OPPORTUNITY.json')];r=subprocess.run(args,capture_output=True,text=True,timeout=min(30,max(1,joint.deadline-time.monotonic()-180)));c.write(a.output/'CONSUMER.json',dict(argv=r.args,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));C.need(r.returncode==0,'independent request-level opportunity consumer');summary['opportunity']=c.ref(a.output/'OPPORTUNITY.json')
 except BaseException as e:primary=repr(e)
 finally:
  for ctl in reversed(owned):
   if ctl.cid and not getattr(ctl,'_pair_closed',False):
    ctl.primary=primary
    try:ctl.cleanup()
    except BaseException as e:joint.secondary.append(repr(e))
   joint.secondary.extend(ctl.secondary)
  after={}
  try:
   for r in readset:C.checked(r);after[r['path']]=r['sha256']
  except BaseException as e:joint.secondary.append('source-after '+repr(e))
  joint.secondary.extend(S.formal_time_failures(joint.deadline))
  if joint.cleanup_used>180:joint.secondary.append('shared cleanup180 exceeded')
  rr=c.write(a.output/'RESULT.json',dict(schema='bole.native-linear-MTP-baseline-owned/v114',BOLE=False,cpu_only=a.cpu_only,source=sr,primary=primary,secondary=joint.secondary,summary=summary,source_before=before,source_after=after,phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,elapsed=time.monotonic()-start,actual_host_argv=actual_argv,host_pid=os.getpid(),candidate_qualification=False,performance_gain_measured=False,formal_performance=False,task_accuracy=False));print('MAIN_DENSE090 '+json.dumps(rr),flush=True)
 return 3 if primary or joint.secondary or before!=after else 0
if __name__=='__main__':raise SystemExit(main())
