"""Record actual same-process inherited MAIN lock and nonblocking exclusion."""
import argparse,hashlib,json,os,pathlib,subprocess,time
T=pathlib.Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=pathlib.Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--unit',required=True);p.add_argument('--receipt',required=True,type=pathlib.Path);a=p.parse_args()
assert a.unit.startswith('bole-') and a.unit.endswith('.service') and '*' not in a.unit
assert a.receipt.is_absolute() and not a.receipt.exists()
lock=T/'MAIN_ADMISSION.lock';assert lock.is_file() and not lock.is_symlink()
argv=['/usr/bin/systemctl','show',a.unit,'--property=Id,ActiveState,SubState,MainPID,ExecStart']
r=subprocess.run(argv,capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
rows=dict(l.split('=',1)for l in r.stdout.splitlines()if '='in l);pid=int(rows['MainPID'])
assert rows['Id']==a.unit and rows['ActiveState']=='active' and rows['SubState']=='running' and pid>0,rows
assert 'path=/usr/bin/flock' in rows['ExecStart'] and '--nonblock --no-fork '+str(lock)in rows['ExecStart']
proc=pathlib.Path('/proc')/str(pid);cmd=proc.joinpath('cmdline').read_bytes().split(b'\0');cmd=[v.decode()for v in cmd if v]
assert cmd[:3]==['/usr/bin/python3','-I','-B'],cmd
fds={}
for f in proc.joinpath('fd').iterdir():
 try:
  v=os.readlink(f)
  if v==str(lock):fds[f.name]=v
 except FileNotFoundError:pass
assert fds,'same actual Python owner must inherit locked fd'
st=lock.stat();key='%02x:%02x:%d'%(os.major(st.st_dev),os.minor(st.st_dev),st.st_ino)
locks=[l for l in pathlib.Path('/proc/locks').read_text().splitlines()if key in l and 'FLOCK' in l and 'WRITE' in l and str(pid)in l.split()]
assert len(locks)==1,dict(key=key,locks=locks)
z=subprocess.run(['/usr/bin/flock','--nonblock',str(lock),'/usr/bin/true'],capture_output=True,text=True,timeout=5);assert z.returncode==1
x=dict(schema='bole.actual-MAIN-whole-owner-admission-lock/v1',unit=a.unit,pid=pid,systemctl_argv=argv,systemctl_properties=rows,actual_python_argv=cmd,inherited_lock_fds=fds,actual_kernel_lock=locks[0],nonblocking_contender_exit_code=z.returncode,lock=ref(lock),reader=ref(__file__),observed_at_ns=time.time_ns(),actual_lock_verified=True,formal_success=False)
a.receipt.write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(dict(receipt=ref(a.receipt),unit=a.unit,pid=pid,actual_lock_verified=True)))
