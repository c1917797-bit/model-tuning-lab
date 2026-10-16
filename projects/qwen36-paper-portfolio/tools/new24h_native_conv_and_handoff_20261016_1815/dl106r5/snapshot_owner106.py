"""Explicit outside-timing signal after original owned SMIPID/start proof."""
import json,os,signal,time
from pathlib import Path
def stat(pid):
 p=Path('/proc')/str(pid);text=(p/'stat').read_text();fields=text[text.rfind(')')+2:].split()
 return int(fields[19]),(p/'cgroup').read_text(),fields[0]
def snapshot(c,ctl,root,stage):
 ref=ctl.observe('model-snapshot-'+stage);observed=c.obj(ref);rows=observed['actual_compute']
 selected=[]
 for physical in (4,5,6,7):
  choices={r['pid']:r for r in rows if r['physical']==physical}
  if len(choices)!=1:raise ValueError('actual one live owned worker percard')
  row=next(iter(choices.values()));tick,cg,state=stat(row['pid'])
  if tick!=row['start_ticks']or ctl.cid not in cg or state=='Z':raise ValueError('fresh exact owned worker start/cgroup')
  selected.append(row)
 if len({r['pid']for r in selected})!=4:raise ValueError('four distinctactualworkers')
 prior={p.name for p in root.glob('worker-*-snapshot-*.json')}
 for row in selected:
  tick,cg,state=stat(row['pid'])
  if tick!=row['start_ticks']or ctl.cid not in cg or state=='Z':raise ValueError('identity drift before own signal')
  c.write(root/('SIGNAL-'+stage+'-host%d.json'%row['pid']),dict(signal='SIGUSR1',owned_cid=ctl.cid,physical=row['physical'],actual_process=row,observation=ref,outside_timed_client=True))
  os.kill(row['pid'],signal.SIGUSR1)
 until=time.monotonic()+min(20,ctl.remaining(cap=20));new=[]
 while len(new)<4:
  if time.monotonic()>=until:raise TimeoutError('all4 owned worker snapshots')
  new=[p for p in root.glob('worker-*-snapshot-*.json')if p.name not in prior]
  if len(new)>4:raise ValueError('unexpected extra worker snapshot')
  time.sleep(.1)
 values=[json.loads(p.read_text())for p in new]
 # Genuine handler records guestPID. Map each live host PID via NSpid before
 # accepting receipt. Source/count qualification is independent pairconsumer.
 bindings=[]
 for row in selected:
  status=(Path('/proc')/str(row['pid'])/'status').read_text()
  ns=[int(x)for line in status.splitlines()if line.startswith('NSpid:')for x in line.split()[1:]]
  matches=[v for v in values if ns and v['pid']==ns[-1]]
  if len(matches)!=1:raise ValueError('actual host-to-guest snapshot binding')
  bindings.append(dict(host=row,guest=matches[0]))
 return values,bindings
