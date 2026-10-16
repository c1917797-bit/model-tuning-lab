"""Two independently reserved filesystems; never claim another /cache path is space."""
import os,stat,time,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
PARENT=Path('/opt/host/vnf/austinov/qwen36-paper-results-new48h')
RAW=PARENT/'run-mxr-block-long065-NEW24H_MXR065_001'
BUDGET=216*1024**3;RESERVE=8*1024**3+512*1024**2
def need(v,s):
 if not v:raise ValueError(s)
def ancestry(p):
 for x in(p,*p.parents):need(not x.is_symlink(),'no symlink output ancestor')
 need(p.resolve()==p,'exact resolved authorized raw path')
def scan(root):
 total=0;files=0;entries=0;stack=[root];inodes=set();dev=root.stat().st_dev
 while stack:
  p=stack.pop()
  with os.scandir(p)as directory:
   for x in directory:
    entries+=1;need(entries<=10000,'bounded raw files and directories')
    s=Path(x.path).lstat();need(s.st_dev==dev and not stat.S_ISLNK(s.st_mode),'no alias or crossed raw filesystem')
    if stat.S_ISDIR(s.st_mode):stack.append(Path(x.path))
    else:
     need(stat.S_ISREG(s.st_mode)and s.st_nlink==1,'sole ordinary raw evidence, no hardlink/specialfile')
     need((s.st_dev,s.st_ino)not in inodes,'no duplicate raw inode');inodes.add((s.st_dev,s.st_ino));total+=s.st_size;files+=1
    need(files<=10000 and len(inodes)<=10000,'bounded raw evidence inventory')
 need(total<=BUDGET,'actual raw216GiB total limit')
 return dict(bytes=total,files=files,device=dev)
def preflight(control):
 """No writes: fail before old008 main can mkdir a control output."""
 control=Path(control);ancestry(PARENT);ancestry(control)
 need(PARENT.is_dir(),'MAIN must create exact authorized RAW parent before execution')
 need(control.is_absolute()and control.parent.is_dir()and not control.exists()and not RAW.exists(),'new source-owned control/RAW leaves; never reuse failed output')
 need(PARENT.stat().st_dev==control.parent.stat().st_dev,'same explicit opt filesystem before output creation')
 v=os.statvfs(PARENT);free=v.f_bavail*v.f_frsize
 from combined_budget import check
 ledger=check(free,0,0,initial=True)
 return dict(schema='mxr.long050r1-no-write-parent-preflight/v1',parent=str(PARENT),control=str(control),raw=str(RAW),parent_exists=True,output_created=False,raw_created=False,ledger=ledger,NPU=False)

def prepare(control):
 ancestry(PARENT);need(PARENT.is_dir()and not RAW.exists(),'MAIN existing authorized parent; fresh raw root only')
 need(PARENT.stat().st_dev==Path(control).stat().st_dev,'same explicit opt filesystem; one total ledger')
 free=os.statvfs(PARENT).f_bavail*os.statvfs(PARENT).f_frsize;from combined_budget import check
 check(free,0,0,initial=True)
 RAW.mkdir(mode=0o700);return dict(path=str(RAW),device=RAW.stat().st_dev,initial_free=free,budget=BUDGET,reserve=RESERVE)
def install(Owned,c,control):
 original=Owned.resources
 def resources(self,initial=False):
  result=original(self,initial);ancestry(RAW);need(RAW.is_dir(),'own raw root exists')
  v=os.statvfs(RAW);free=v.f_bavail*v.f_frsize;used=scan(RAW)
  row=dict(schema='mxr.raw-filesystem-admission/v1',path=str(RAW),control_path=str(control),device=RAW.stat().st_dev,control_device=Path(control).stat().st_dev,free=free,reserve=RESERVE,budget=BUDGET,used=used,initial=initial)
  need(row['device']==row['control_device'],'registered sameopt ledger only')
  from combined_budget import check
  _,control_bytes=c.output_scan(Path(control))
  row['combined_opt_ledger']=check(free,control_bytes,used['bytes'],initial=False)
  c.write(self.out/('RAW-FS-%d.json'%time.time_ns()),row)
  return dict(result,independent_raw_filesystem=row)
 Owned.resources=resources
 return dict(schema='mxr.single-opt-combined-contract/v047',raw_root=str(RAW),raw_budget_GiB=216,shared_reserve_GiB=8.5,control_budget_GiB=3,initial_combined_GiB=227.5,not_independent_concurrent_reservation=True,failures_retained=True)

def main():
 import argparse,json
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--preflight',action='store_true');p.add_argument('--control-output',type=Path);a=p.parse_args()
 if not a.preflight:print('{"enabled":false,"NPU":false}');return 0
 need(str(a.control_output)=='/opt/host/vnf/austinov/run-mxr-block-long-model065-main-NEW24H_MXR065_001','exact new source-owned control leaf only')
 print(json.dumps(preflight(a.control_output),sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
