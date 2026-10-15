"""Narrow bound-init natural-exit fence. Never retires init or signals a process."""
import hashlib,json,time
from pathlib import Path
EXACT_ERROR="ValueError('never retire init, bound NPU, or protected0-3 PID')"
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def files(root):
 return {str(p):p.stat().st_mtime_ns for p in Path(root).glob('*.json') if p.name.startswith(('protected-ownership-','top-child-departure-','top-child-first-'))}
def new_evidence(root,before):
 paths=[p for p in Path(root).glob('*.json') if p.name.startswith(('protected-ownership-','top-child-departure-','top-child-first-')) and before.get(str(p))!=p.stat().st_mtime_ns]
 return [(ref(p),json.loads(p.read_bytes())) for p in paths]
def exiting_init(evidence,bound,prior):
 need(bound is not None,'already ARM-bound NPU/init required')
 pid=bound['pid'];ticks=bound['start_ticks']
 need(prior['State']['Running']is True and prior['State']['Pid']==pid,'pre-observation actual init == bound host PID')
 verdicts=[(r,v) for r,v in evidence if v.get('schema')=='deltalog-protected-ownership/v002']
 firsts=[(r,v) for r,v in evidence if v.get('schema')=='deltalog.owned-top-child-first-observation/v031repair1']
 need(len(verdicts)==len(firsts)==1,'exact newly saved original exception and first-init frame')
 vr,v=verdicts[0];fr,f=firsts[0]
 need(v['error']==EXACT_ERROR and v['reasons']==['protected ownership observation incomplete'],'only exact init never-retire refusal')
 need(f['pid']==pid and f['classification']=='unresolved-not-retired' and f['resource_release_authority']is False,'first frame exact bound init not child retirement')
 s=f['first'];need(s['status']=='present' and s['pid']==pid and s['start_ticks']==ticks,'known same init/start no missing/unknown/reused')
 parts=s['proc_fields'];stat=parts['stat']['text'];stat2=parts['stat_after']['text']
 for text in(stat,stat2):
  a=text[text.rfind(')')+2:].split()
  need(int(a[19])==ticks and int(a[20])==int(a[21])==0,'same start and actual vsize/RSS zero exiting-frame only')
 need(parts['cmdline']['bytes']==0,'actual exiting init empty cmdline')
 cg=s['cgroup'];need(bool(cg.strip()) and all(x.split(':',2)[-1]=='/' for x in cg.splitlines()),'all-root cgroup exiting init frame')
 return dict(original_verdict=vr,original_first=fr,pid=pid,start_ticks=ticks,classification='bound-init-exit-fence-candidate-not-retired')
def state(x,cid,*,allow_running=False,pid=None):
 need(x['Id']==cid and not x.get('ExecIDs') and not x['State'].get('OOMKilled',False),'same exact CID/noExec/noOOM')
 s=x['State'];need(s['ExitCode']==0,'nonzero exit never accepted')
 if s['Running']:
  need(allow_running and s['Pid']==pid and s['Status']=='running','still-running exact bound init only')
 else:need(s['Pid']==0 and s['Status']=='exited','natural stopped/Pid0/exited required')
 return s
def empty_top_exit(evidence,bound,prior,cid):
 """One observed inspect-running/top-header-only natural-exit race, not waiver."""
 need(bound is not None and type(bound['start_ticks'])is int,'actual retained ARM identity')
 need(prior['Id']==cid and prior['State']['Running']is True and prior['State']['Pid']==bound['pid'],'prior same CID and bound running init')
 verdicts=[(r,v)for r,v in evidence if v.get('schema')=='deltalog-protected-ownership/v002']
 firsts=[v for r,v in evidence if v.get('schema')=='deltalog.owned-top-child-first-observation/v031repair1']
 need(len(verdicts)==1 and not firsts,'one new empty-top verdict; no unrelated child frame')
 vr,v=verdicts[0]
 need(v['error']=="ValueError('actual container init included in top')"and v['reasons']==['protected ownership observation incomplete']and v['owned']==[],'exact original empty-top exception, not generic incomplete')
 top=v['actual_owned_top'];need(top['exit_code']==0 and [x.split()for x in top['stdout'].splitlines()if x.strip()]==[['PID','PPID','COMMAND']],'successful Docker top with header only')
 inspected=json.loads(v['exact_owned_inspect']['stdout']);need(type(inspected)is list and len(inspected)==1,'actual single inspect original stdout')
 x=inspected[0];need(x['Id']==cid and x['State']['Running']is True and x['State']['Pid']==bound['pid']and not x.get('ExecIDs')and not x['State'].get('OOMKilled',False),'same original CID/mapping bound init running before top')
 return dict(original_verdict=vr,pid=bound['pid'],start_ticks=bound['start_ticks'],classification='bound-init-header-only-top-exit-candidate-not-retired',protected_boundary_waived=False)
def postexit(lane,receipt,x,bound,save,deadline):
 cid=lane.active;need(cid is not None and bound is not None,'active true CID and actual ARM proof retained')
 state(x,cid);need(time.monotonic()<deadline,'original stage deadline unchanged')
 # Active remains exact CID: protected observer still validates mapping, FDs,
 # protected-card ancestry and fresh SMI, while stopped init needs no retirement.
 observation=lane.observe('numeric',require_idle=True)
 need(not observation['owned_process_proofs'],'postexit no own NPU PID')
 r2,x2=lane.inspect(cid);state(x2,cid)
 need(x2['State']==x['State'],'two exact terminal State snapshots stable')
 save(dict(schema='deltalog.bound-init-postexit/v035repair1',first_inspect=receipt,second_inspect=r2,observation=observation,natural_exit=True,resource_release_authority=False))
 return r2,x2
def recover(lane,error,bound,prior,before,save,deadline):
 need(repr(error)=='''ValueError("owned protected0-3 boundary or incomplete proof: ['protected ownership observation incomplete']")''','only original saved protected-observer exception eligible')
 evidence=new_evidence(lane.a.run_root,before)
 verdicts=[v for r,v in evidence if v.get('schema')=='deltalog-protected-ownership/v002']
 if len(verdicts)==1 and verdicts[0].get('error')=="ValueError('actual container init included in top')":
  proof=empty_top_exit(evidence,bound,prior,lane.active)
 else:proof=exiting_init(evidence,bound,prior)
 save(dict(schema='deltalog.bound-init-observation-error/v035repair1',original_exception=repr(error),proof=proof,old_failure_unchanged=True))
 until=min(deadline,time.monotonic()+2.0);frames=[]
 while True:
  need(time.monotonic()<until,'bounded2s natural exit wait expired')
  r,x=lane.inspect(lane.active);need(time.monotonic()<=until,'fresh inspect itself charged to bounded natural wait');s=state(x,lane.active,allow_running=True,pid=bound['pid'])
  frames.append(r);save(dict(schema='deltalog.bound-init-natural-wait/v035repair1',proof=proof,inspect_frames=list(frames),signal_sent=False))
  if not s['Running']:return postexit(lane,r,x,bound,save,deadline)
  time.sleep(min(.05,max(0,until-time.monotonic())))
def quiescent(childout,consumer,checked_ref,obj):
 stage=checked_ref(childout if consumer else Path(childout)/'STAGE_RESULT.json')
 first=obj(stage);refs=[stage]
 if not consumer and 'actual_result'in first:
  refs.append(first['actual_result']);obj(refs[-1])
 # Natural stopped writer was established before this method; two byte refs.
 need(all(checked_ref(r['path'])==r for r in refs),'quiescent stage/producer Ref bytes drift')
 return dict(schema='deltalog.quiescent-result-refs/v035repair1',refs=refs,writers_naturally_stopped=True)
