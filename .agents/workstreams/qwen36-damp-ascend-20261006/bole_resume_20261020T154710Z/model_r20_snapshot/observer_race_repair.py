"""Retry only a proved vanished protected-card PID observation, once.

The original admission, target-card exclusion, ownership and resource checks
execute again. No foreign target-card process is admitted by this repair.
"""
import errno,re,time
from pathlib import Path

def alive(pid):
 return (Path('/proc')/str(pid)).exists()

def install(S,C):
 original=S.Controller.observe
 def observe(self,label,initial=False,cleanup=False):
  previous=set(self.out.glob('smi-*.json'))
  try:return original(self,label,initial=initial,cleanup=cleanup)
  except FileNotFoundError as error:
   match=re.fullmatch(r'/proc/([1-9][0-9]*)/(stat|cgroup|cmdline|exe)',str(error.filename))
   if error.errno!=errno.ENOENT or match is None:raise
   pid=int(match.group(1))
   new=set(self.out.glob('smi-*.json'))-previous
   C.need(len(new)==1,'one exact stale SMI receipt before protected PID race')
   stale_path=next(iter(new));stale=C.obj(C.ref(stale_path))
   rows=self.h.legacy().process_rows(stale['stdout'])
   occurrences=[row for row in rows if row[2]==pid]
   C.need(bool(occurrences)and all(row[0]in(0,1,2,3)for row in occurrences),
          'only a vanished protected-card snapshot; target-card exclusions unchanged')
   fresh,fresh_ref=self.call('smi-race-refresh',[S.SMI,'info'],cleanup=cleanup)
   fresh_rows=self.h.legacy().process_rows(fresh['stdout'])
   C.need(not alive(pid)and all(row[2]!=pid for row in fresh_rows),
          'fresh SMI and proc must both prove sampled protected PID absent')
   C.write(self.out/('protected-pid-race-'+str(time.time_ns())+'.json'),
    dict(schema='bole.proved-protected-pid-exit/v1',repair_source=C.ref(__file__),
         stale_smi=C.ref(stale_path),fresh_smi=fresh_ref,pid=pid,
         original_fault=repr(error),original_filename=error.filename,
         target_exclusion_unchanged=True,retry_count=1))
  return original(self,label,initial=initial,cleanup=cleanup)
 S.Controller.observe=observe
 return original

