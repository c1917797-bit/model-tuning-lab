"""Bounded full post-work verification AFTER original owned cleanup, same whole clock."""
import json,signal,time
import phase_budget_r21 as B

def fresh_owned(h,S,controllers):
 rows=[]
 for ctl in controllers:
  if not ctl.cid:continue
  # Read-only verification belongs to post-work, not a reset cleanup lease.
  value=ctl.h.run(ctl.wrapper([S.DOCKER,'inspect',ctl.cid]),30)
  h.need(value['exit_code']==0,'post-work fresh exact own inspect')
  observed=json.loads(value['stdout']);h.need(len(observed)==1,'single post-work CID')
  x=observed[0];S.validate_inspect(x,ctl.expected)
  h.need(x['Id']==ctl.cid and x['State']['Running']is False and x['State']['Pid']==0 and not x['State']['OOMKilled']and not x.get('ExecIDs'),'post-work own CID stopped/noExec/noOOM')
  rows.append(x)
 return rows

def protect(Owned,state,started,cut):
 original=Owned.remaining
 def remaining(self,cleanup=False,cap=30):
  value=original(self,cleanup=cleanup,cap=cap)
  if not cleanup:
   value=min(value,B.work_remaining(time.monotonic(),started,time.time(),cut))
   if value<=0:raise ValueError('no work time after original cleanup270/postverify900/margin90')
  return value
 Owned.remaining=remaining

def available(now,started,wall,cut):
 value=B.post_remaining(now,started,wall,cut)
 if value<=0:raise ValueError('no positive postverify900 budget within whole3600/cut/margin90')
 return value

def run(h,lease,sr,state,started,released,current_verify):
 h.need(released is True,'all current CIDs released before postverify')
 begun=time.monotonic();seconds=available(begun,started,time.time(),h.CUTOFF)
 old_handler=signal.getsignal(signal.SIGALRM);old_timer=signal.getitimer(signal.ITIMER_REAL)
 if old_timer[0]>0:seconds=min(seconds,old_timer[0])
 def expired(*args):raise TimeoutError('registered post-work verification900/whole/cut exhausted')
 signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,seconds)
 try:
  storage=lease.close(released)
  h.frozen_directory(h.HERE,sr['sha256'])
  current=current_verify()
  lease.final_metadata()
  h.need(time.monotonic()<=state['end']and time.time()<h.CUTOFF,'postverify retains original whole/cut')
  return dict(storage=storage,source_after=True,metadata_after_hash=True,current_owned_inspects=current,elapsed_seconds=time.monotonic()-begun,registered_cap_seconds=900,actual_cap_seconds=seconds)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old_handler)
  if old_timer[0]>0:signal.setitimer(signal.ITIMER_REAL,max(.000001,old_timer[0]-(time.monotonic()-begun)),old_timer[1])
