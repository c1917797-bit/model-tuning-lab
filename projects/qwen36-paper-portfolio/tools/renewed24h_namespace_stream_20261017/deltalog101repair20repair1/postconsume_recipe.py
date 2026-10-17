"""One serial Devices[] postconsumer on the unchanged R17 Owned machinery."""
import json,time,traceback,os
from pathlib import Path
def cap(now,started,wall,cut):
 value=min(900.,2700.-(now-started)-270.-900.-90.,cut-wall-270.-900.-90.)
 if value<=0:raise ValueError('no positive postconsumer budget after cleanup270/postverify900/margin90/cut')
 return value
def run(h,sr,pr,started,input_ref):
 import resource
 c,S,Owned,state=h.safety(sr,h.POLICY,started);ctl=None;primary=None;result={};secondary=[];detail=None
 import postwork_verify
 postwork_verify.protect(Owned,state,started,h.CUTOFF)
 lease=h._SNAPSHOT
 try:
  _,hard=resource.getrlimit(resource.RLIMIT_AS);h.need(hard==resource.RLIM_INFINITY,'same actual host AS ABI');resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
  lease.extra_opt=h.OUT;lease.open(existing=True);lease.wrap_writer(c);inputs=c.obj(input_ref);m=c.obj(sr);payload=m['firstdecode_contract']['payload_source']
  h.need(inputs['schema']=='deltalog.firstdecode-postconsumer-input/v1'and inputs['model_source']==sr and inputs['payload_source']==payload,'exact actual input, not caller pass boolean')
  root=h.OUT/'cpu-consumer';root.mkdir(mode=0o700);ctl=Owned(root)
  ctl.observe('firstdecode-serial-Devices-empty-admission',initial=True)
  host=S.H.cpu_view(os.getpid());os.sched_setaffinity(0,{min(host['effective_cpus'])})
  _,hard=resource.getrlimit(resource.RLIMIT_AS);h.need(hard==resource.RLIM_INFINITY,'same actual host AS ABI');resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,hard))
  original_inspect=c.obj(inputs['inspect_ref'])
  if type(original_inspect)is list:h.need(len(original_inspect)==1,'one exact parent CID');original_inspect=original_inspect[0]
  parent_cid=original_inspect['Id']
  def parent_stopped(label):
   observed,_=ctl.call(label,[S.DOCKER,'inspect',parent_cid]);h.need(observed['exit_code']==0,'fresh actual parent inspect')
   rows=json.loads(observed['stdout']);h.need(len(rows)==1,'one exact parent inspect row');x=rows[0]
   h.need(x['Id']==parent_cid and x['Image']==original_inspect['Image']and x['State']['Running']is False and x['State']['Pid']==0 and not x['State']['OOMKilled']and not x.get('ExecIDs'),'parent remains exactly stopped/noExec/noOOM')
   return c.write(root/(label+'.json'),rows)
  fresh_inspect=parent_stopped('MODEL-PARENT-BEFORE')
  # No resource is created without a strictly positive dynamic cap. The
  # actual create/inspect must still prove Devices[],8GiB,1CPU.
  child_cap=cap(time.monotonic(),started,time.time(),h.CUTOFF)
  model=c.model(c.MODEL_REF);ctl.create_native(model,True)
  inspected,_=ctl.inspect();hc=inspected['HostConfig']
  h.need(not hc.get('Devices')and hc['Memory']==8*2**30 and len(ctl.expected['guest_cpus'])==1,'actual inspected Devices[],8GiB,1CPU')
  result['actual_CPU_inspect']=c.write(root/'CPU-INSPECT.json',inspected)
  args=[inputs['owner_ref'],fresh_inspect,inputs['loaded_ref'],inputs['reports_ref']]
  pm=c.obj(payload);entry=m['files']['postconsume_entry.py'];output=root/'FIRST-DECODE-INDEPENDENT.json'
  command=[entry['path'],'--execute','--model-source-ref',json.dumps(sr),'--payload-source-ref',json.dumps(payload)]
  for name,r in zip(('owner','inspect','loaded','reports'),args):command+=['--'+name+'-ref',json.dumps(r)]
  command+=['--output','/adakv-results/FIRST-DECODE-INDEPENDENT.json']
  child_cap=min(child_cap,cap(time.monotonic(),started,time.time(),h.CUTOFF));h.child(ctl,c,'firstdecode-independent-all4',command,child_cap,observe=False)
  value=c.obj(c.ref(output));h.need(value['schema']=='deltalog.independent-all4-firstdecode/v1'and value['source']==payload and value['model_source']==sr and value['diagnostic_complete']is True and value['full_model_qualified']is value['performance_qualified']is value['task_qualified']is False,'all actual independent gates, diagnostic only')
  result.update(independent_ref=c.ref(output),child_cap_seconds=child_cap,parent_before=fresh_inspect,parent_after=parent_stopped('MODEL-PARENT-AFTER'))
 except BaseException as e:primary=e;detail=dict(type=type(e).__name__,traceback=''.join(traceback.format_exception(type(e),e,e.__traceback__)))
 finally:
  cleanup_started=time.monotonic();cleanup_before=state['cleanup_spent']
  lease.terminal=True
  if ctl is not None and ctl.cid:
   try:result['cleanup']=h.close_owned(ctl,c,primary)
   except BaseException as e:secondary.append('cleanup '+repr(e))
   secondary.extend(ctl.secondary)
  state['cleanup_spent']=max(state['cleanup_spent'],cleanup_before+time.monotonic()-cleanup_started)
  if time.monotonic()>state['end']or state['cleanup_spent']>h.CLEANUP_TOTAL or time.time()>=h.CUTOFF:secondary.append('original whole/cleanup/cut exhausted')
  released=False
  if result.get('cleanup'):
   note=c.obj(result['cleanup']);released=note['stopped']is note['retained']is True and not note['errors']
  try:
   if lease.fd is not None:
    import postwork_verify
    result['post_work_verification']=postwork_verify.run(h,lease,sr,state,started,released,lambda:postwork_verify.fresh_owned(h,S,[ctl]if ctl else[]))
  except BaseException as e:secondary.append('post-work-verification '+repr(e))
  result.update(schema='deltalog.firstdecode-owned-postconsumer/v1',source=sr,input_ref=input_ref,primary=repr(primary)if primary else None,primary_detail=detail,secondary=secondary,elapsed=time.monotonic()-started,cleanup_seconds=state['cleanup_spent'],cid=ctl.cid if ctl else None,resource_release_verified=released,stopped_retained=released,registered_child_max_seconds=900,Devices=[],NPU=False,model_qualified=False,performance_qualified=False,task_qualified=False)
  try:c.write(h.OUT/'RESULT.json',result)
  finally:lease.release()
 if primary:raise primary
 h.need(not secondary and time.monotonic()<=state['end']and time.time()<h.CUTOFF,'independent CPU source/release/time final gates');return 0
