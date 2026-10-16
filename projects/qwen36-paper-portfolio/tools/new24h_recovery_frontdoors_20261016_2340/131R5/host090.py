"""Thin dense-only075/052 workflow over exact025 Joint/Controller. MAIN only."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
import fault_receipt
def client_terminal(c,ctl,tokens,handled):
 label='client-'+str(tokens);receipt=dict(exit_code=ctl.client.returncode,actual_argv=ctl.client_argv,stdout=c.ref(ctl.out/(label+'.stdout')),stderr=c.ref(ctl.out/(label+'.stderr')),ownership_barriers_seen=sorted(handled),profile=tokens)
 path=ctl.out/('CLIENT-TERMINAL-%d.json'%tokens);c.write(path,receipt);return c.ref(path)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--output-contract-only',action='store_true');p.add_argument('--source-ref');p.add_argument('--output');p.add_argument('--cpu-only',action='store_true');a=p.parse_args()
 if a.output_contract_only:
  C.output_argument(a.output);print(json.dumps(dict(output=a.output,NPU=False,contract_only=True)));return 0
 if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);import bind_model;readset=bind_model.readset(sr)+m['dependencies']
 if a.source_audit:print(json.dumps(dict(source=sr,readset=len(readset),NPU=False,resources_admitted=False,candidate_qualification=False)));return 0
 a.output=C.output_argument(a.output);C.need(os.environ.get('BOLE_MODEL131_MAIN_ENABLE')=='1'and a.output==(C.CPU_OUT if a.cpu_only else C.OUT)and not a.output.exists(),'MAIN-only unique registered output')
 actual_argv=[x.decode('utf8','strict')for x in Path('/proc/self/cmdline').read_bytes().split(b'\0')if x];C.need(len(actual_argv)>=4 and actual_argv[1:3]==['-I','-B']and Path(actual_argv[3]).resolve()==Path(__file__).resolve(),'actual source-bound -I/-B host CLI')
 from owned_substrate import load
 from owned_create import create
 from worker_snapshot_owner import snapshot
 import resource
 os.sched_setaffinity(0,{166});soft,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go child AS wrapper');resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard))
 start=time.monotonic();c,S,H,pairs=load(a.output);a.output.mkdir(mode=0o700);joint=H.Joint(start);owned=[];primary=None;summary={};before={r['path']:r['sha256']for r in readset};phase=dict(phase='setup',step='ready',ordinal=0)
 def mark(name,step):phase.update(phase=name,step=step,ordinal=phase['ordinal']+1)
 def ctl_for(role,cpu=False,extra=()):
  mark(role,'fresh-leaf');leaf=H.fresh_leaf(a.output/role);H.outputs(leaf);(leaf/'receipts').mkdir();mark(role,'controller');ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),start);owned.append(ctl);mark(role,'initial-observation');ctl.observe(role+'-admission',initial=True);mark(role,'create-start-inspect');create(c,S,ctl,sr,[*readset,*extra],'cpu-preflight'if cpu else role,P);return ctl
 def child(ctl,label,args,limit):
  mark(ctl.expected['arm'],'child-'+label);return H.child(ctl,label,args,limit,observe=ctl.expected['arm']!='cpu-preflight')
 def spawn(ctl,args,label):
  mark(ctl.expected['arm'],'spawn-'+label);argv=c.docker_argv(ctl.cid,args);so=(ctl.out/(label+'.stdout')).open('x');se=(ctl.out/(label+'.stderr')).open('x');proc=subprocess.Popen(ctl.wrapper(argv),stdout=so,stderr=se,cwd=c.ROOT);so.close();se.close();return proc,argv
 def close(ctl):
  mark(ctl.expected['arm'],'cleanup-close');r=ctl.cleanup();ctl._pair_closed=True;mark(ctl.expected['arm'],'cleanup-receipt');v=c.obj(r);C.need(v['stopped']and v['retained']and not v['errors'],'actual retained release');return r
 try:
  cpu=ctl_for('cpu-preflight');summary['actual_software_child']=child(cpu,'SOFTWARE',[str(P/'entry.py'),'--software'],120);summary['CPU_child']=child(cpu,'CPU',[str(P/'preflight114.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(cpu.out/'CPU.json')],120);report=c.obj(c.ref(cpu.out/'CPU.json'));C.need(report['source']==sr and report['pass_preflight']is True and report['Devices']==[]and report['native_runtime_parser_checked']is True and report['registry_arch_enumerated']is True,'real sameimage source preflight');summary['CPU_report']=c.ref(cpu.out/'CPU.json');summary['CPU_release']=close(cpu)
  if not a.cpu_only:
   mark('dense','checkpoint-model');c.model(c.MODEL_REF);ctl=ctl_for('dense');summary['canary']=child(ctl,'CANARY',[str(P/'guest_canary.py'),'--output',str(ctl.out/'CANARY.json')],180);C.need(c.obj(c.ref(ctl.out/'CANARY.json'))['rows']==[dict(logical=i,values=[4.,5.])for i in range(4)],'genuine all4 tiny values; not model qualification')
   ctl.server_started=H.utc();ctl.server,ctl.server_argv=spawn(ctl,[str(P/'server090.py'),'--execute','--source-ref',json.dumps(sr),'--receipt-root',str(ctl.out/'receipts')],'server');end=time.monotonic()+min(900,ctl.remaining(cap=900))
   while True:
    mark('dense-startup','server-poll');C.need(ctl.server.poll()is None and time.monotonic()<end,'one bounded native server startup');mark('dense-startup','protected-observation');ctl.observe('dense-startup')
    argv=c.docker_argv(ctl.cid,['-c',"import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8230/health',timeout=2).status==200"]);mark('dense-startup','health-run');r=ctl.h.run(ctl.wrapper(argv),min(4,ctl.remaining(cap=4)));mark('dense-startup','health-receipt');c.write(ctl.out/('health-%d.json'%time.time_ns()),r)
    if r['exit_code']==0:break
    time.sleep(1)
   from load_consumer114 import consume as consume_load
   mark('dense-startup','mtp-load-read');load_rows=[C.obj(c.ref(f))for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   mark('dense-startup','mtp-load-consume');load_proof=consume_load(load_rows,report['actual_checkpoint_mtp_names'],m['installed_sources']['qwen_mtp'],m['files']['load_receipt111.py']);summary['MTP_load']=C.write(ctl.out/'MTP-LOAD-CONSUMPTION.json',load_proof)
   summary['MTP_load_receipts']=[c.ref(f)for f in sorted((ctl.out/'receipts').glob('MTP-LOAD-*.json'))]
   ctl.client,ctl.client_argv=spawn(ctl,[str(P/'smoke_client.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(ctl.out)],'model-smoke')
   until=time.monotonic()+min(900,ctl.remaining(cap=900))
   while ctl.client.poll()is None:
    mark('model-smoke','client-server-poll');C.need(ctl.server.poll()is None and time.monotonic()<until,'one bounded actual model smoke client');mark('model-smoke','protected-observation');ctl.observe('model-smoke');time.sleep(.2)
   mark('model-smoke','client-terminal-receipt');summary['actual_client_terminal']=C.write(ctl.out/'CLIENT-TERMINAL.json',dict(actual_argv=ctl.client_argv,exit_code=ctl.client.returncode,stdout=c.ref(ctl.out/'model-smoke.stdout'),stderr=c.ref(ctl.out/'model-smoke.stderr')))
   C.need(ctl.client.returncode==0,'actual HTTP client failed; preserved terminal/stdout/stderr precede all aggregate assertions')
   mark('model-smoke','worker-snapshot');rows,bindings=snapshot(c,ctl,ctl.out/'receipts','AFTER-MODEL')
   C.need(len(rows)==4 and all(v['schema']=='dense.native-worker-snapshot/v090'and v['source_ref']==sr and v['native_core']is v['native_inverse']is True and v['allow_hf32']is False for v in rows),'all4 actual restored native class/precision proof')
   C.need({v['pid']for v in rows}=={v['pid']for v in load_rows},'source-bound MTP loader and actual worker lifetimes')
   summary['worker_bindings']=C.write(ctl.out/'WORKER_BINDINGS.json',bindings)
   mark('model-smoke','rank-receipt-read');receiptroot=ctl.out/'receipts';ranks=[]
   for rank in range(4):
    receipt=c.ref(receiptroot/('BOLE-TREE-RANK-%d.json'%rank));rv=c.obj(receipt)
    C.need(rv['rank']==rank and rv['source']==sr,'actual rank/source capture')
    C.checked(rv['raw']);ranks.append(dict(receipt=receipt,raw=rv['raw']))
   journals=[c.ref(p)for p in sorted(receiptroot.glob('IDENTITY-*.json'))]
   http_ref=c.ref(ctl.out/'HTTP_RESULT.json');http=C.obj(http_ref);response=C.obj(http['rows'][0]['response'])
   assignments=[C.obj(r)['event']for r in journals if C.obj(r)['role']=='frontend'and C.obj(r)['event']['before_request_id']==response['id']+'-0']
   C.need(len(assignments)==1,'one actual source-bound assignment event')
   import identity_owner
   mark('model-smoke','frontend-identity');frontend_binding=identity_owner.frontend(c,S,ctl,assignments[0])
   bundle=dict(schema='bole.actual-four-rank-model-inputs/v1',source=sr,http=http_ref,journal=journals,snapshots=rows,host_bindings=bindings,ranks=ranks,frontend_binding=frontend_binding)
   summary['model_release']=close(ctl)
   bundle_ref=C.write(a.output/'CONSUMER_INPUTS.json',bundle)
   extra=[bundle_ref,bundle['http'],*journals,*[r for pair in ranks for r in pair.values()]]
   extra.extend(r['response']for r in C.obj(bundle['http'])['rows'])
   consumer=ctl_for('cpu-consumer',cpu=True,extra=extra)
   summary['independent_child']=child(consumer,'INDEPENDENT',[str(P/'consume_model.py'),'--execute','--source-ref',json.dumps(sr),'--inputs-ref',json.dumps(bundle_ref),'--output',str(consumer.out)],900)
   mark('consumer','independent-report-read');summary['independent']=c.ref(consumer.out/'ATTRIBUTION.json');value=c.obj(summary['independent'])
   C.need(value['source']==sr and value['diagnostic_complete']is True and value['component_checks_pass']is True and value['model_ready']is False and value['scheduler_committed']is False,'independent component gates and complete whole diagnostic, never model qualification')
   summary['independent_release']=close(consumer)
 except BaseException as e:
  primary=repr(e)
  try:summary['first_host_fault']=fault_receipt.persist(a.output,sr,e,phase)
  except BaseException as evidence_error:joint.secondary.append('first-fault-persistence '+repr(evidence_error))
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
  rr=c.write(a.output/'RESULT.json',dict(schema='bole.actual-three-node-model-owned/v131',BOLE_diagnostic=True,model_ready=False,scheduler_committed=False,cpu_only=a.cpu_only,source=sr,primary=primary,secondary=joint.secondary,summary=summary,source_before=before,source_after=after,phase_seconds=3600,cleanup_seconds=180,cleanup_spent=joint.cleanup_used,elapsed=time.monotonic()-start,actual_host_argv=actual_argv,host_pid=os.getpid(),candidate_qualification=False,performance_gain_measured=False,formal_performance=False,task_accuracy=False));print('MAIN_DENSE090 '+json.dumps(rr),flush=True)
 return 3 if primary or joint.secondary or before!=after else 0
if __name__=='__main__':raise SystemExit(main())
