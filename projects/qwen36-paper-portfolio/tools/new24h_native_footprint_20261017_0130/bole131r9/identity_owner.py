"""One read-only frontend NSpid join inside the existing admitted controller."""
from pathlib import Path


def frontend(c,S,ctl,event):
 x,inspection=ctl.inspect()
 c.require(x['Id']==ctl.cid and x['State']['Running']and x['State']['Pid']>0,'actual live source-validated model container')
 raw,top=ctl.call('frontend-top',[S.DOCKER,'top',ctl.cid,'-eo','pid'])
 c.require(raw['exit_code']==0,'actual complete Docker top frontend proof')
 lines=raw['stdout'].splitlines();c.require(lines and lines[0].strip()=='PID','exact Docker-top PID column')
 pids=[int(line.strip())for line in lines[1:]if line.strip()]
 c.require(pids and len(pids)<=2048 and len(pids)==len(set(pids)),'actual bounded complete source-owned PID list')
 target=event['identity'];matches=[]
 for pid in pids:
  p=Path('/proc')/str(pid)
  try:status=(p/'status').read_text()
  except FileNotFoundError:continue # Only a positive live match can be admitted.
  ns=[int(x)for line in status.splitlines()if line.startswith('NSpid:')for x in line.split()[1:]]
  if not ns or ns[-1]!=target['pid']:continue
  stat=(p/'stat').read_text();fields=stat[stat.rfind(')')+2:].split()
  cgroup=(p/'cgroup').read_text();argv=[s.decode('utf8','strict')for s in(p/'cmdline').read_bytes().split(b'\0')if s]
  exe=(p/'exe').resolve(strict=True)
  proof=dict(pid=pid,start_ticks=int(fields[19]),cgroup=cgroup,argv=argv,executable=str(exe),stat=stat)
  final=(p/'stat').read_text();last=final[final.rfind(')')+2:].split()
  c.require(ctl.cid in cgroup and int(fields[19])==target['start_ticks']and fields[0]not in('Z','X')and
            argv and exe.name.startswith('python')and last[0]not in('Z','X')and last[19]==fields[19]and
            (p/'cgroup').read_text()==cgroup,
            'actual same-bound live Python frontend PID/start/cgroup; CPU counters need not freeze')
  matches.append(dict(host=proof,guest=target,NSpid=ns,actual_top=top,actual_inspect=inspection,owned_cid=ctl.cid))
 c.require(len(matches)==1,'one actual live frontend namespace mapping, never response-ID authority alone')
 return matches[0]
