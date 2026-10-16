"""DL stage recipe on UNCHANGED actual008 Owned/safety/close/worker PID join."""
import datetime,json,os,resource,subprocess,time,traceback
from pathlib import Path
def run(h,sr,pr,started):
 c,S,Owned,state=h.safety(sr,h.POLICY,started);own=[];primary=None;result={};detail=None
 def make(name):
  leaf=h.OUT/name;leaf.mkdir(mode=0o700);ctl=Owned(leaf)
  if own:ctl.protected=own[0].protected
  own.append(ctl);return ctl
 try:
  cpu=make('cpu-preflight');initial=cpu.observe('initial-DL-admission',initial=True);host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host['effective_cpus'])})
  _,hard=resource.getrlimit(resource.RLIMIT_AS);h.need(hard==resource.RLIM_INFINITY,'same actual host AS ABI');resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
  model=c.model(c.MODEL_REF);cpu.create_native(model,True)
  h.child(cpu,c,'DL-cold-source',[str(h.DEPLOY/'probe.py'),'--execute','--mode','cpu','--source-ref',json.dumps(sr),'--output',str(cpu.out/'CPU.json')],150,observe=False)
  cp=c.obj(c.ref(cpu.out/'CPU.json'));h.need(cp['pass_preflight']is True and cp['NPU']is False and cp['source']==sr,'actual Devices[] CPU source gate')
  result['cpu']=dict(initial=initial,report=c.ref(cpu.out/'CPU.json'),cleanup=h.close_owned(cpu,c))
  ctl=make('candidate');result['fresh_tp4_admission']=ctl.observe('DL-TP4-admission',initial=True);ctl.create_native(model,False)
  h.child(ctl,c,'DL-four-canary',[str(h.DEPLOY/'probe.py'),'--execute','--mode','n1','--source-ref',json.dumps(sr),'--output',str(ctl.out/'CANARY.json')],180)
  canary=c.obj(c.ref(ctl.out/'CANARY.json'));h.need(canary['source']==sr and canary['pass_preflight']and len(canary['canaries'])==4 and canary['real_plugin_registered']is True,'true canary -> normal platform/parser/DL register')
  receipts=ctl.out/'worker-receipts';receipts.mkdir();runid=json.loads((h.HERE/'SOURCE_MANIFEST.json').read_bytes())['runtime_identity']['run_id']
  args=[str(h.DEPLOY/'entry.py'),'--execute','--role','guest','--source-ref',json.dumps(sr),'--capture-source',str(h.SOURCE1),'--upstream-source',str(h.UP),'--output',str(ctl.out/'model'),'--run-id',runid,'--authority',str(h.AUTH),'--model-manifest',c.MODEL_REF['path'],'--port','8252']
  original=c.docker_argv(ctl.cid,args);command=original[:2]+['-e','MST_MXR_NATIVE_WORKER_RECEIPT=1','-e','MST_MXR_NATIVE_WORKER_ROOT='+str(receipts),'-e','MST_MXR_NATIVE_WORKER_RUN_ID='+runid]+original[2:]
  ctl.server_started=datetime.datetime.now(datetime.timezone.utc);stdout=(ctl.out/'server.stdout').open('x');stderr=(ctl.out/'server.stderr').open('x');model_error=None
  try:
   ctl.server=subprocess.Popen(ctl.wrapper(command),stdout=stdout,stderr=stderr,cwd=h.ROOT);deadline=time.monotonic()+min(1500,ctl.remaining(cap=1500))
   while True:
    h.need(ctl.server.poll()is None and time.monotonic()<deadline,'bounded actual DL server startup');ctl.observe('DL-model-startup')
    health=[c.PY,'-I','-B','-c',"import urllib.request;assert urllib.request.urlopen('http://127.0.0.1:8252/health',timeout=2).status==200"]
    v=ctl.h.run(ctl.wrapper([S.DOCKER,'exec',ctl.cid,*health]),min(4,ctl.remaining(cap=4)));c.write(ctl.out/('HEALTH-%d.json'%time.time_ns()),v)
    if v['exit_code']==0:break
    time.sleep(2)
   bindings=h.worker_bindings(ctl,c,receipts,runid);br=c.write(ctl.out/'ALL4-LOADED.json',dict(schema='deltalog.actual-all4-loaded/v004',source=sr,rows=bindings))
   h.child(ctl,c,'DL-real-short-client',[str(h.DEPLOY/'client.py'),'--execute','--source-ref',json.dumps(sr),'--model-config','/models/Qwen3.6-27B/config.json','--server-output',str(ctl.out/'model'),'--output',str(ctl.out/'client'),'--run-id',runid,'--port','8252'],300)
   ctl.observe('DL-real-decode-completed');result.update(actual_loaded_workers=br,client=c.ref(ctl.out/'client/RESULT.json'),canary=c.ref(ctl.out/'CANARY.json'),diagnostic_audit=str(ctl.out/'model/capture'))
  except BaseException as exc:model_error=exc;raise
  finally:
   try:result['TP4_cleanup']=h.close_owned(ctl,c,model_error)
   finally:stdout.close();stderr.close()
  cc=make('cpu-consumer');cc.observe('DL-postrelease-consumption',initial=True);cc.create_native(model,True)
  h.child(cc,c,'DL-independent-response',[str(h.DEPLOY/'consume.py'),'--execute','--source-ref',json.dumps(sr),'--loaded-ref',json.dumps(result['actual_loaded_workers']),'--client-ref',json.dumps(result['client']),'--audit',result['diagnostic_audit'],'--output',str(cc.out/'CONSUMPTION.json')],120,observe=False)
  result['independent_smoke_consumer']=c.ref(cc.out/'CONSUMPTION.json');cv=c.obj(result['independent_smoke_consumer']);h.need(cv['smoke_dispatch_and_response_pass']is True and cv['performance_ready']is False,'real actual4x48 and response/ownership join')
  result['consumer_cleanup']=h.close_owned(cc,c)
 except BaseException as exc:primary=exc;detail=dict(type=type(exc).__name__,traceback=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__)))
 finally:
  secondary=[]
  for ctl in reversed(own):
   if ctl.cid and not getattr(ctl,'_mxr_done',False):
    ctl.primary=primary
    try:h.close_owned(ctl,c,primary)
    except BaseException as exc:secondary.append(repr(exc))
   secondary.extend(ctl.secondary)
  if state['cleanup_spent']>h.CLEANUP_TOTAL or time.monotonic()>state['end']or time.time()>=h.CUTOFF:secondary.append('original cleanup/phase/cutoff exceeded')
  states=[]
  for ctl in own:
   release=False
   if ctl.cid and(ctl.out/'cleanup.json').is_file():
    try:note=c.obj(c.ref(ctl.out/'cleanup.json'));release=note['stopped']is note['retained']is True and not note['errors']
    except BaseException:pass
   states.append(dict(stage=str(ctl.out),cid=ctl.cid,exact_owned_release_verified=release if ctl.cid else None))
  try:h.frozen_directory(h.HERE,sr['sha256'])
  except BaseException as exc:secondary.append('source-after '+repr(exc))
  result.update(schema='deltalog.actual-owned-model-smoke/v004',source=sr,component_owner=pr,primary=repr(primary)if primary else None,primary_detail=detail,secondary=secondary,elapsed=time.monotonic()-started,cleanup_seconds=state['cleanup_spent'],owned_containers=states,all_created_containers_release_verified=all(v['exact_owned_release_verified']for v in states if v['cid']),status='actual-DL-smoke-only'if primary is None and not secondary else'failed',model_numeric_qualified=False,performance_ready=False,task_accuracy=False)
  c.write(h.OUT/'RESULT.json',result)
 if primary:raise primary
 h.need(not result['secondary']and result['all_created_containers_release_verified'],'actual original release/source/time')
 return 0
