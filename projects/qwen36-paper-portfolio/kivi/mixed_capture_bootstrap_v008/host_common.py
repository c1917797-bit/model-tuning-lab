"""MAIN-owned existing safety host -> CPU8 -> TP4 EAGER32768+2 first-decode diagnostic.
No FULL/mixed/model-performance/task admission. Default OFF.
"""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import model_contract as c
def utc():return datetime.datetime.now(datetime.timezone.utc)
def fresh_leaf(path):
 p=c.ordinary(path);c.require(Path("/cache/cch")in p.parents and p.parent.is_dir()and not p.exists(),"new exact owned leaf")
 p.mkdir(mode=0o700);return p
def outputs(leaf):
 for n in("graph-output","qkv-output","identities","audit-parent"): (leaf/n).mkdir()
def child(ctl,label,args,limit,observe=True):
 argv=c.docker_argv(ctl.cid,args);start=utc();ctl.server_started=start
 so=ctl.out/(label+".stdout");se=ctl.out/(label+".stderr")
 with so.open("x")as stdout,se.open("x")as stderr:
  p=subprocess.Popen(ctl.wrapper(argv),stdout=stdout,stderr=stderr,cwd=c.ROOT);ctl.server=p;ctl.server_argv=argv
  deadline=time.monotonic()+min(limit,ctl.remaining(cap=limit))
  while p.poll()is None:
   c.require(time.monotonic()<deadline,"bounded original child; never retry")
   if observe:ctl.observe(label)
   else:ctl.remaining(cap=limit)
   time.sleep(1)
  if observe:ctl.observe(label+"-finished")
 r=c.write(ctl.out/(label+"-CHILD.json"),dict(requested_argv=argv,actual_host_argv=ctl.wrapper(argv),
  child_host_pid=p.pid,child_started_utc=start.isoformat(),child_termination_observed=True,exit_code=p.returncode,
  stdout_ref=c.ref(so),stderr_ref=c.ref(se)))
 c.require(p.returncode==0,"actual original child failed "+str(r));return r
class Joint:
 def __init__(self,start):
  self.start=start;self.deadline=start+c.phase_seconds();self.cleanup_used=0.;self.cleanup_started=None;self.secondary=[];self.recovery_deadline=None
 def begin_cleanup(self):
  c.require(self.cleanup_started is None,"no overlapping cleanup")
  now=time.monotonic();self.cleanup_started=now;formal=min(self.deadline-now,c.CUTOFF-time.time())
  remaining=90-self.cleanup_used
  if min(remaining,formal)<=0:
   self.secondary.append("formal cleanup/phase expired; bounded safety-only recovery, stage FAILED")
   if self.recovery_deadline is None:self.recovery_deadline=now+90
   return self.recovery_deadline
  return now+min(remaining,formal)
 def end_cleanup(self):
  self.cleanup_used+=time.monotonic()-self.cleanup_started;self.cleanup_started=None
 def rss(self):
  import resource
  own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;ch=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
  c.require(own+ch<=512*1024,"host+CLI cumulative peak512MiB")
  return dict(host_peak_rss_kib=own,child_peak_rss_kib=ch,aggregate_rss_kib=own+ch)
def controller(S,co):
 class Owned(S.Controller):
  def rss(self):return co.rss()
  def remaining(self,cleanup=False,cap=30):
   if cleanup:
    c.require(self.cleanup_deadline is not None,"one joint bounded cleanup lane")
    value=self.cleanup_deadline-time.monotonic()
    c.require(value>0,"bounded exact owned recovery exhausted");return min(value,cap)
   return super().remaining(False,cap)
  def cleanup(self):
   self.cleanup_deadline=co.begin_cleanup()
   try:return super().cleanup()
   finally:co.end_cleanup()
 return Owned

