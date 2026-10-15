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
 grandparents=[]
 for n in range(8):
  child=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(.03)'])
  try:
   start=pathlib.Path('/proc')/str(child.pid)/'stat';text=start.read_text();ticks=int(text[text.rfind(')')+2:].split()[19]);before=dict(pid=child.pid,start_ticks=ticks,actual_stat=text)
   code=child.wait(timeout=2);after_exists=start.exists()
   if code!=0 or after_exists:raise ValueError('actual short-child did not naturally exit/reap')
   frames.append(dict(before=before,exit_code=code,after_proc_absent=True,signal_sent=False,not_Docker_or_NPU_proof=True))
  finally:
   if child.poll()is None:child.kill();child.wait()
 spec=importlib.util.spec_from_file_location('actual_same_snapshot_tree_guard',P/'top_guard.py');T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
 for n in range(4):
  code="import subprocess,sys; c=subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(.15)']); print(c.pid,flush=True); sys.exit(c.wait())"
  parent=subprocess.Popen([sys.executable,'-I','-B','-c',code],stdout=subprocess.PIPE,text=True)
  try:
   grandchild=int(parent.stdout.readline().strip());init=os.getpid()
   original={}
   for pid in(parent.pid,grandchild):
    text=(pathlib.Path('/proc')/str(pid)/'stat').read_text();a=text[text.rfind(')')+2:].split();original[pid]=dict(start_ticks=int(a[19]),ppid=int(a[1]),stat=text)
   if original[parent.pid]['ppid']!=init or original[grandchild]['ppid']!=parent.pid:raise ValueError('actual parent/grandchild lineage')
   if parent.wait(timeout=2)!=0:raise ValueError('actual natural parent wait/reap failed')
   if any((pathlib.Path('/proc')/str(pid)).exists()for pid in original):raise ValueError('parent and its reaped child must independently disappear')
   ids=[grandchild,init,parent.pid];ppids={init:os.getppid(),parent.pid:init,grandchild:parent.pid};order=T.tree_order(ids,ppids,init);anchors={init};proofs=[]
   def fresh_cpu_top():return {pid for pid in ids if (pathlib.Path('/proc')/str(pid)).exists()}
   for pid in order[1:]:
    result=T.confirm(pid,ppids[pid],init,set(),anchors,T.snapshot(pid),T.snapshot,fresh_cpu_top,proofs.append)
    if result is not None:raise ValueError('confirmed departure must not become a live owned proof')
    anchors.add(pid)
   grandparents.append(dict(original_actual_proc=original,parent_exit_code=0,actual_order=order,strict_departure_events=proofs,live_owned_credit=[],signal_sent=False,CPU_only_not_Docker_or_NPU_proof=True))
  finally:
   if parent.poll()is None:parent.kill();parent.wait()
   parent.stdout.close()
 # Both actual policy suites: live-unreadable/unknown/reuse/forbidden/tree
 # and nonzero/OOM/exec/postexit foreign protection remain hard failures.
 suites=[]
 for pattern in('test_terminal_fence.py','test_tree_anchor.py'):
  r=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(P),'-p',pattern],capture_output=True,text=True,timeout=30)
  suites.append(dict(pattern=pattern,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
  if r.returncode:raise ValueError('policy software controls '+r.stderr)
 with out.open('x')as f:json.dump(dict(schema='deltalog.real-short-process-controls/v035repair2',NPU=False,actual_cpu_processes=frames,actual_parent_grandchild_processes=grandparents,software_control_suites=suites,software_controls_pass=True,not_actual_Docker_exit_race_qualification=True),f)
 return 0
if __name__=='__main__':raise SystemExit(main())

