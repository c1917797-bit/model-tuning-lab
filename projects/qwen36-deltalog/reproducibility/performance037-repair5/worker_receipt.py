"""Snapshot only on explicit owned-worker SIGUSR1, outside timed requests."""
import hashlib,json,os,signal,time
from pathlib import Path
from snapshot_publication import publish as atomic_publish
def install(snapshot):
 root=Path(os.environ['QWEN36_DELTALOG_SCREEN033_RECEIPT_ROOT'])
 if not root.is_absolute()or not root.is_dir()or root.is_symlink():raise ValueError('owned receipt directory')
 if signal.getsignal(signal.SIGUSR1)not in(signal.SIG_DFL,signal.SIG_IGN):raise ValueError('no clobber existing worker signal')
 number=0
 def publish(signum,frame):
  nonlocal number
  value=snapshot();number+=1
  value.update(schema='deltalog.production-screen-worker/v033',pid=os.getpid(),
   proc_stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),
   ordinal=number,epoch=time.time(),monotonic=time.monotonic(),
   source_ref=json.loads(os.environ['QWEN36_DELTALOG_SCREEN033_SOURCE_REF']),
   qualification_ref=json.loads(os.environ['QWEN36_DELTALOG_SCREEN033_QUALIFICATION_REF']),
   receipt_trigger='SIGUSR1 outside timed client interval',tensor_snapshot=False,
   synchronization=value['health']['synchronization_performed'],synchronization_outside_timing=True,publication='exclusive-fsynced-stage-link-final-directory-fsync; retained-staging')
  dest=root/('worker-%d-snapshot-%d.json'%(os.getpid(),number))
  atomic_publish(dest,value)
 signal.signal(signal.SIGUSR1,publish)
 return publish


