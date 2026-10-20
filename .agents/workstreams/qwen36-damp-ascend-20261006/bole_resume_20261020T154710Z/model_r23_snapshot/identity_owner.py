"""One read-only frontend NSpid join inside the existing admitted controller."""
from pathlib import Path
import re,hashlib
import frontend_namespace131r18 as NS


def frontend(c,S,ctl,event):
 x,inspection=ctl.inspect()
 c.require(x['Id']==ctl.cid and x['State']['Running']and x['State']['Pid']>0,'actual live source-validated model container')
 c.require(re.fullmatch('[0-9a-f]{64}',ctl.cid)and c.PY==NS.PY,'exact original025 container/interpreter identity')
 init=Path('/proc')/str(x['State']['Pid'])
 init_before=(init/'stat').read_text();init_fields=init_before[init_before.rfind(')')+2:].split()
 init_cgroup=(init/'cgroup').read_text()
 c.require(init_fields[0]not in('Z','X')and ctl.cid in init_cgroup,'actual inspected live container init')
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
  cgroup=(p/'cgroup').read_text();raw_cmdline=(p/'cmdline').read_bytes();argv=[s.decode('utf8','strict')for s in raw_cmdline.split(b'\0')if s]
  c.require(ctl.cid in cgroup and int(fields[19])==target['start_ticks']and fields[0]not in('Z','X')and
            argv,'source-bound actual Python frontend before executable read')
  executable=NS.verify(p,init,c.PY)
  proof=dict(pid=pid,start_ticks=int(fields[19]),cgroup=cgroup,argv=argv,cmdline_bytes=len(raw_cmdline),cmdline_sha256=hashlib.sha256(raw_cmdline).hexdigest(),executable=executable['namespace_executable'],executable_identity=executable,stat=stat)
  final=(p/'stat').read_text();last=final[final.rfind(')')+2:].split()
  c.require(ctl.cid in cgroup and int(fields[19])==target['start_ticks']and fields[0]not in('Z','X')and
            argv and last[0]not in('Z','X')and last[19]==fields[19]and
            (p/'cgroup').read_text()==cgroup and (p/'cmdline').read_bytes()==raw_cmdline and
            (p/'status').read_text().split('NSpid:',1)[1].splitlines()[0].split()==[str(v)for v in ns],
            'actual same-bound live Python frontend PID/start/cgroup; CPU counters need not freeze')
  matches.append(dict(host=proof,guest=target,NSpid=ns,actual_top=top,actual_inspect=inspection,owned_cid=ctl.cid))
 c.require(len(matches)==1,'one actual live frontend namespace mapping, never response-ID authority alone')
 final_init=(init/'stat').read_text();final_fields=final_init[final_init.rfind(')')+2:].split()
 c.require(final_fields[0]not in('Z','X')and final_fields[19]==init_fields[19]and(init/'cgroup').read_text()==init_cgroup,'same inspected init lifetime after frontend join')
 final,final_inspection=ctl.inspect()
 c.require(final['Id']==x['Id']and final['State']['Running']and final['State']['Pid']==x['State']['Pid'],'same actual live inspected container after namespace join')
 matches[0]['actual_final_inspect']=final_inspection
 return matches[0]
