"""Pure metadata pressure control; same executable child, no Docker/backend/data."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import readset127 as R
def peak():
 if os.name=='nt':
  import ctypes
  from ctypes import wintypes
  class Info(ctypes.Structure):
   _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t)for n in('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
  info=Info();info.cb=ctypes.sizeof(info);kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetCurrentProcess.restype=wintypes.HANDLE
  psapi=ctypes.WinDLL('psapi',use_last_error=True);psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Info),wintypes.DWORD]
  if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(info),info.cb):raise ctypes.WinError(ctypes.get_last_error())
  return int(info.PeakWorkingSetSize)
 import resource
 return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024
def checked(r):
 p=Path(r['path']);h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 R.need((n,h.hexdigest())==(r['bytes'],r['sha256']),'actual pressure INDEX hash');return p
def child(manifest):
 # Reproduce both m/om loading, but never store an array of Ref dictionaries.
 raw=Path(manifest).read_bytes();om=json.loads(raw);m=json.loads(raw);d=m['recovery_readset_index'];refs=R.Readset([],d,checked);counts=[]
 for iteration in range(3):
  count=0
  for r in refs:R.validate_ref(r);count+=1
  counts.append(count)
 parents=refs.parents;good=counts==[d['entries']]*3 and len(refs)==d['entries']and len(parents)==81 and peak()<=64*2**20
 value=dict(schema='deltalog.metadata-pressure-control/v127-repair3',metadata_only=True,actual_input_validation=False,scientific_qualification=False,executable=sys.executable,version=sys.version,entries=d['entries'],index_bytes=d['index_ref']['bytes'],manifest_bytes=len(raw),passes=counts,parents=len(parents),peak_rss_bytes=peak(),control_limit_bytes=64*2**20,metadata_control_pass=good)
 print(json.dumps(value,sort_keys=True));return 0 if good else 3
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--child-manifest');ap.add_argument('--entries',type=int,default=135520);ap.add_argument('--output');a=ap.parse_args()
 if a.child_manifest:return child(a.child_manifest)
 R.need(a.entries>=81,'all81 parent pressure groups')
 with tempfile.TemporaryDirectory(prefix='dl127-metadata-pressure-')as td:
  root=Path(td);p=root/'pressure.jsonl';h=hashlib.sha256();size=0;parents=[]
  with p.open('xb')as f:
   for group in range(81):
    parent='/metadata-pressure/'+('x'*192)+'/p%02d'%group;parents.append(parent)
    for i in range(group,a.entries,81):
     line=R.encoded(dict(path=parent+'/%09d.bin'%i,bytes=1048576,sha256='%064x'%i));f.write(line);h.update(line);size+=len(line)
  description=dict(schema=R.SCHEMA,index_ref=dict(path=p.as_posix(),bytes=size,sha256=h.hexdigest()),entries=a.entries,parents=parents,parent_count=81)
  mf=root/'small-manifest.json';mf.write_bytes(json.dumps(dict(recovery_readset_index=description,prior_small_metadata='x'*67100),sort_keys=True).encode('utf8'))
  run=subprocess.run([sys.executable,'-I','-B',str(P/'memory_pressure127.py'),'--child-manifest',str(mf)],capture_output=True,text=True,timeout=240)
  print(run.stdout,end='');print(run.stderr,end='',file=sys.stderr)
  if a.output:
   out=Path(a.output);R.need(out.is_absolute()and out.parent.is_dir()and not out.exists(),'fresh exclusive pressure receipt')
   with out.open('x',encoding='utf8',newline='\n')as f:json.dump(dict(child_returncode=run.returncode,stdout=run.stdout,stderr=run.stderr,local_parent_executable=sys.executable,NPU=False,Docker=False),f,sort_keys=True);f.write('\n')
  return run.returncode
if __name__=='__main__':raise SystemExit(main())
