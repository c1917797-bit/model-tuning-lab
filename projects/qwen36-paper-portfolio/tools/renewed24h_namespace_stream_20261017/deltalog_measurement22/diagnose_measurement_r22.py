"""MAIN-only bounded Devices[] stdlib diagnosis; no imports of ML runtimes."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
def snapshot():
 import resource
 status=Path('/proc/self/status').read_text();v={}
 for line in status.splitlines():
  if line.startswith(('VmRSS:','VmHWM:','VmSize:','VmPeak:')):
   k,value,unit=line.split();assert unit=='kB';v[k[:-1]+'_bytes']=int(value)*1024
 return dict(pid=os.getpid(),ppid=os.getppid(),ru_maxrss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,proc_status=v,exe_link=os.readlink('/proc/self/exe'),executable=sys.executable,executable_resolved=str(Path(sys.executable).resolve()),proc_status_raw=status)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--child',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 assert sys.platform=='linux'and not list(Path('/dev').glob('davinci*')),'actual Devices[] Linux only'
 if a.child:
  before=snapshot();small=bytearray(4*2**20);small[::4096]=b'\1'*len(small[::4096]);after=snapshot()
  print(json.dumps(dict(before=before,after=after,ML_imported=any(n in sys.modules for n in('torch','torch_npu','vllm')),NPU=False)));return 0
 assert a.output is not None and a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists()
 start=time.monotonic();before=snapshot();large=bytearray(192*2**20);large[::4096]=b'\1'*len(large[::4096]);parent=snapshot()
 argv=[sys.executable,'-I','-B',str(Path(__file__).resolve()),'--execute','--child']
 z=subprocess.run(argv,capture_output=True,text=True,timeout=20)
 receipt=dict(schema='deltalog.actual-sameimage-RSS-exec-diagnostic/v22',before=before,parent_after_192MiB=parent,child_argv=argv,child_exit=z.returncode,child_stdout=z.stdout,child_stderr=z.stderr,elapsed=time.monotonic()-start,Devices=[],NPU=False,qualified=False,measurement_contract_decided=False)
 if z.returncode==0:
  child=json.loads(z.stdout);receipt['child']=child
  h=child['before']['proc_status']['VmHWM_bytes'];r=child['before']['ru_maxrss_bytes']
  receipt['observed_ru_vs_current_mm_HWM_bytes']=r-h
  receipt['possible_inherited_ru_maxrss_not_proven_without_actual_run']=r>128*2**20 and h<64*2**20
 with a.output.open('x',encoding='utf8',newline='\n')as f:json.dump(receipt,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 return z.returncode
if __name__=='__main__':raise SystemExit(main())
