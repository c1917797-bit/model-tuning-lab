"""Read exact own init PID/cgroup counters; never hostCLI RSS as guestpeak."""
import os,time
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def locate(text,cid):
 lines=[x.split(':',2)for x in text.splitlines()]
 selected=next((('v2',v[2])for v in lines if v[0]=='0'and v[1]==''),None)
 if selected is None:selected=next((('v1',v[2])for v in lines if'memory'in v[1].split(',')),None)
 need(selected is not None,'actual memory cgroup required')
 version,path=selected;need(path.startswith('/')and'..'not in Path(path).parts and cid in path,'exact own CID in actual memory cgroup')
 root=Path('/sys/fs/cgroup')if version=='v2'else Path('/sys/fs/cgroup/memory')
 return version,root/path.lstrip('/')
def counters(version,path):
 names=('memory.current','memory.peak','memory.max','memory.events','memory.events.local','memory.swap.max')if version=='v2'else('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.limit_in_bytes','memory.memsw.limit_in_bytes','memory.failcnt','memory.oom_control')
 values={}
 for name in names:
  p=path/name
  if p.is_file():
   b=p.read_bytes();need(len(b)<=4096,'bounded actual memory counter');values[name]=b.decode().strip()
  else:values[name]=None
 return values
def install(Owned,c,S):
 original_observe=Owned.observe;original_cleanup=Owned.cleanup;original_create=Owned.create_native;paths={}
 def snapshot(ctl,label,cleanup=False):
  if not ctl.cid:return None
  try:
   if not cleanup:
    x,ir=ctl.inspect();pid=x['State']['Pid'];need(x['State']['Running']and pid>0,'own live init')
    text=(Path('/proc')/str(pid)/'cgroup').read_text();version,path=locate(text,ctl.cid);paths[ctl.cid]=(version,path,pid,text,ir)
   need(ctl.cid in paths,'actual live own cgroup observed before cleanup');version,path,pid,text,ir=paths[ctl.cid]
   v=counters(version,path);limit=v['memory.max'if version=='v2'else'memory.limit_in_bytes']
   if limit is not None:need(int(limit)==(8 if ctl._mxr_resource_profile=='cpu-preflight'else 32)*c.GIB,'actual own cgroup cap matches create/inspect/profile')
   row=dict(schema='mxr.cap48.actual-memory-cgroup/v1',cid=ctl.cid,init_pid=pid,init_inspect=ir,actual_proc_cgroup=text,cgroup_version=version,cgroup_path=str(path),path_exists=path.is_dir(),counters=v,stage=label,epoch=time.time(),host_RSS_is_guest_peak=False)
  except BaseException as e:
   row=dict(schema='mxr.cap48.memory-observation-failure/v1',cid=ctl.cid,stage=label,error=repr(e),counter_unavailable_not_zero=True)
   if not cleanup:
    c.write(ctl.out/('CGROUP-MEMORY-FAIL-%d.json'%time.time_ns()),row);raise
  return c.write(ctl.out/('CGROUP-MEMORY-%s-%d.json'%(label,time.time_ns())),row)
 def observe(ctl,label,initial=False,cleanup=False):
  value=original_observe(ctl,label,initial=initial,cleanup=cleanup)
  snapshot(ctl,label,cleanup=cleanup);return value
 def create(ctl,model,cpu):
  value=original_create(ctl,model,cpu);snapshot(ctl,'created-init');return value
 def close(ctl):
  # Observation failure must never prevent original exact-owned safety cleanup.
  try:snapshot(ctl,'before-stop',cleanup=True)
  except BaseException as e:ctl.secondary.append('memory-before-stop '+repr(e))
  try:return original_cleanup(ctl)
  finally:
   try:snapshot(ctl,'after-stop',cleanup=True)
   except BaseException as e:ctl.secondary.append('memory-after-stop '+repr(e))
 Owned.observe=observe;Owned.cleanup=close;Owned.create_native=create
 return dict(schema='mxr.cap48.memory-observer/v1',v1_usage_maxusage_failcnt_oom=True,v2_current_peak_events=True,missing_counters_never_zero=True,foreign_signals=False)
