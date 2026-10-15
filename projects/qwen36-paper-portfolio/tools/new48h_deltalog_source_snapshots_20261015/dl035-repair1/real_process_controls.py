"""Actual CPU-only short-lived processes; no Docker/NPU identity is fabricated."""
import argparse,importlib.util,json,os,pathlib,subprocess,sys,tempfile,time
P=pathlib.Path(__file__).resolve().parent
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--output',required=True);a=p.parse_args()
 if os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0' or os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!='' or list(pathlib.Path('/dev').glob('davinci*')):raise ValueError('actual Devices[] CPU environment')
 out=pathlib.Path(a.output)
 if out.exists()or not out.parent.is_dir():raise ValueError('exclusive CPU controls output')
 frames=[]
 for n in range(8):
  child=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(.03)'])
  try:
   start=pathlib.Path('/proc')/str(child.pid)/'stat';text=start.read_text();ticks=int(text[text.rfind(')')+2:].split()[19]);before=dict(pid=child.pid,start_ticks=ticks,actual_stat=text)
   code=child.wait(timeout=2);after_exists=start.exists()
   if code!=0 or after_exists:raise ValueError('actual short-child did not naturally exit/reap')
   frames.append(dict(before=before,exit_code=code,after_proc_absent=True,signal_sent=False,not_Docker_or_NPU_proof=True))
  finally:
   if child.poll()is None:child.kill();child.wait()
 # The complete real policy unit suite includes live-unreadable/unknown/reuse,
 # nonzero/OOM/exec and postexit foreign-protection rejection.
 r=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(P),'-p','test_terminal_fence.py'],capture_output=True,text=True,timeout=30)
 if r.returncode:raise ValueError('fence software controls '+r.stderr)
 with out.open('x')as f:json.dump(dict(schema='deltalog.real-short-process-controls/v035repair1',NPU=False,actual_cpu_processes=frames,software_control_stdout=r.stdout,software_control_stderr=r.stderr,software_controls_pass=True,not_actual_Docker_exit_race_qualification=True),f)
 return 0
if __name__=='__main__':raise SystemExit(main())

