"""Narrow Docker-top child exit race. No signaling/device/release authority."""
import os,time,hashlib
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def tree_order(pids,ppids,init_pid):
 """This ONE actual Docker-top tree only; no cross-observation anchors."""
 need(1<=len(pids)<=512 and len(pids)==len(set(pids)) and set(pids)==set(ppids),'bounded unique complete original top snapshot')
 need(all(type(p)is int and p>0 and type(ppids[p])is int for p in pids)and init_pid in ppids,'actual positive PID inventory and exact inspected init')
 need(ppids[init_pid]not in ppids,'original init parent outside its own snapshot; cycle refused')
 ordered=[init_pid];anchored={init_pid};pending=set(pids)-anchored
 while pending:
  ready=[p for p in pids if p in pending and ppids[p]in anchored]
  need(bool(ready),'unknown parent or cyclic original Docker-top tree')
  ordered.extend(ready);anchored.update(ready);pending.difference_update(ready)
 return ordered
def snapshot(pid):
 p=Path('/proc')/str(pid);parts={}
 for name in('stat','cgroup','cmdline','stat_after'):
  actual='stat'if name=='stat_after'else name
  try:parts[name]=p.joinpath(actual).read_bytes()
  except(FileNotFoundError,ProcessLookupError):parts[name]=None
 # Permission/other errors propagate; missing is not fabricated from them.
 if all(x is None for x in parts.values()):return dict(status='missing',pid=pid)
 # Keep the original partial/wrong-cgroup observation. cmdline is projected to
 # name/hash/length, never foreign args/environment. Subsequent absence must
 # be independently established; incomplete is not itself evidence of exit.
 fields={k:(None if v is None else dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest(),text=v.decode(errors='replace')if k!='cmdline'else None))for k,v in parts.items()}
 if parts['stat']is not None and parts['stat_after']is not None:
  left=parts['stat'].decode();right=parts['stat_after'].decode();a=left[left.rfind(')')+2:].split();z=right[right.rfind(')')+2:].split()
  need(len(a)>=20 and len(z)>=20 and a[19]==z[19],'PID reused during partial independent snapshot')
 if not all(x is not None for x in parts.values()):return dict(status='partial',pid=pid,proc_fields=fields)
 text=parts['stat'].decode();a=text[text.rfind(')')+2:].split();need(len(a)>=20,'actual proc stat')
 end=parts['stat_after'].decode();z=end[end.rfind(')')+2:].split();need(a[19]==z[19],'PID reused during independent snapshot')
 return dict(status='present',pid=pid,start_ticks=int(a[19]),state=z[0],ppid=int(a[1]),cgroup=parts['cgroup'].decode(),proc_fields=fields)
def confirm(pid,ppid,init_pid,forbidden,owned_parents,first,read,fresh_top,publish,*,pause=time.sleep):
 publish(dict(schema='deltalog.owned-top-child-first-observation/v031repair1',pid=pid,ppid=ppid,first=first,classification='unresolved-not-retired',resource_release_authority=False))
 need(pid!=init_pid and pid not in forbidden,'never retire init, bound NPU, or protected0-3 PID')
 need(ppid in owned_parents,'original Docker-top parent must already be proven owned')
 need(first['status']in('present','partial','missing'),'known independent proc observation schema')
 known=first.get('start_ticks');frames=[first]
 for _ in range(2):
  pause(.02);s=read(pid);frames.append(s)
  need(s['status']=='missing','two consecutive fully absent independent proc reads required')
 top=fresh_top();need(pid not in top,'fresh Docker top still contains PID')
 final=read(pid);frames.append(final);need(final['status']=='missing','PID reused or reappeared after fresh top')
 v=dict(schema='deltalog.owned-top-child-departure/v028',pid=pid,ppid=ppid,known_start_ticks=known,proc_frames=frames,fresh_top_pids=sorted(top),classification='original-top-child-confirmed-departed',resource_release_authority=False,protected_boundary_waived=False)
 publish(v);return None
def classify(lane,pid,ppid,init_pid,owned_parents,forbidden,m):
 first=snapshot(pid)
 if first['status']=='present'and first['state']!='Z':
  if lane.active not in first['cgroup']:
   return _confirm_lane(lane,pid,ppid,init_pid,owned_parents,forbidden,m,first)
  try:proof=lane.h.gate_process(pid)
  except(FileNotFoundError,ProcessLookupError):proof=None
  if proof is not None:
   need(proof['start_ticks']==first['start_ticks'],'top PID reused during observation')
   if lane.active in proof['cgroup']:return proof
  # An originally own live child may exit between the independent snapshot
  # and original helper. Only fresh terminal/absent confirmation can retire it.
  terminal=snapshot(pid)
  need(terminal['status']=='missing'or terminal.get('start_ticks')==first['start_ticks'],'PID reuse after original helper')
  first=terminal
 return _confirm_lane(lane,pid,ppid,init_pid,owned_parents,forbidden,m,first)
def _confirm_lane(lane,pid,ppid,init_pid,owned_parents,forbidden,m,first):
 def top():
  receipt=lane.call([m.DOCKER,'top',lane.active,'-eo','pid,ppid,args'],30)
  m.save(lane.a.run_root/('top-child-fresh-'+str(time.time_ns())+'.json'),receipt)
  need(receipt['exit_code']==0,'fresh Docker top failed')
  return {int(x.split()[0])for x in receipt['stdout'].splitlines()if x.split()and x.split()[0].isdigit()}
 return confirm(pid,ppid,init_pid,forbidden,owned_parents,first,snapshot,top,lambda v:m.save(lane.a.run_root/('top-child-departure-'+str(time.time_ns())+'.json'),v))
