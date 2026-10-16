"""Untimed diagnostic only: publish operands before unchanged genuine guard.

No predicate is removed, no result transformed, no external process controlled.
Installer must bind exactS/H sources in a new MAIN-reviewed experiment.
"""
import contextvars,datetime,functools,os,sys,time
from pathlib import Path
def install(S,c,source_ref,helper_ref):
 if str(Path(S.__file__).resolve())!=source_ref['path']or c.sha(S.__file__)!=source_ref['sha256']or Path(S.__file__).stat().st_size!=source_ref['bytes']:raise ValueError('actual immutable S source before observer')
 if str(Path(S.H.__file__).resolve())!=helper_ref['path']or c.sha(S.H.__file__)!=helper_ref['sha256']or Path(S.H.__file__).stat().st_size!=helper_ref['bytes']:raise ValueError('actual immutable H source before observer')
 original_observe=S.Controller.observe;original_started=S.H.started
 current=contextvars.ContextVar('mxr_original_ownership_guard_scope',default=None)
 @functools.wraps(original_started)
 def started(*args,**kw):
  result=original_started(*args,**kw);scope=current.get()
  caller=sys._getframe(1)
  if scope is not None and caller.f_code is original_observe.__code__:
   ctl,label=scope;values=caller.f_locals;pid=values.get('pid');chip=values.get('ch');physical=values.get('n')
   exe=None;exe_error=None
   try:exe=os.readlink(Path('/proc')/str(pid)/'exe')
   except BaseException as exc:exe_error=repr(exc)
   actual=result.get('started_utc');time_ok=None;time_error=None
   try:time_ok=ctl.server_started is not None and datetime.datetime.fromisoformat(actual)>=ctl.server_started-datetime.timedelta(seconds=1)
   except BaseException as exc:time_error=repr(exc)
   # These are recorded diagnostics, never a substituted admission decision.
   operands=dict(chip_zero=chip==0,own_cid_present=ctl.cid is not None,
    cgroup_matches=ctl.cid is not None and ctl.cid in result.get('cgroup',''),
    server_anchor_present=ctl.server_started is not None,start_time_matches=time_ok,
    argv_nonempty=bool(result.get('argv')),exe_python=None if exe is None else Path(exe).name.startswith('python'))
   c.write(ctl.out/('ownership-before-guard-%d.json'%time.time_ns()),
    dict(schema='mxr.actual-before-ownership-guard/v1',stage=label,physical=physical,chip=chip,
     actual_process=result,actual_executable=exe,executable_read_error=exe_error,
     start_predicate_error=time_error,server_started=None if ctl.server_started is None else ctl.server_started.isoformat(),
     owned_cid=ctl.cid,operands=operands,original_guard_unchanged=True,
     source_filename=caller.f_code.co_filename,source_line=caller.f_lineno))
  return result
 @functools.wraps(original_observe)
 def observe(self,label,*args,**kw):
  token=current.set((self,label))
  try:return original_observe(self,label,*args,**kw)
  finally:current.reset(token)
 S.H.started=started;S.Controller.observe=observe
 return dict(original_observe=original_observe,original_started=original_started,
             diagnostic_started=started,diagnostic_observe=observe)
