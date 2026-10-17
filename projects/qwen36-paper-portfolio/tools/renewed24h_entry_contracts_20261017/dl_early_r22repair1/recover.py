"""Actual Devices[] child: only prepared-source full suite, no model binding."""
import argparse,hashlib,json,os,subprocess,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
MODEL_ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair22-repair1-20261017-001'
def checked(r):
 assert type(r)is dict and set(r)=={'path','bytes','sha256'};p=Path(r['path']);assert p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents));b=p.read_bytes();assert(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']);return p
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,v):
 with p.open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--model-template-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 started=time.monotonic();sr=json.loads(a.source_ref);own=json.loads(checked(sr).read_bytes());tr=json.loads(a.model_template_ref);m=json.loads(checked(tr).read_bytes())
 assert own['schema']=='deltalog.prebind-software-source/v22'and own['prepared_only']is False and own['root']==str(P)
 for r in own['files'].values():checked(r)
 assert m['root']==MODEL_ROOT and tr['path']==MODEL_ROOT+'/SOURCE_TEMPLATE.json'and m['prepared_only']is True
 assert sys.platform=='linux'and not list(Path('/dev').glob('davinci*'))and os.environ['ASCEND_RT_VISIBLE_DEVICES']==''
 start=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19];identity=dict(source=sr,pid=os.getpid(),start_ticks=start,cgroup=Path('/proc/self/cgroup').read_text(),pid_namespace=os.readlink('/proc/self/ns/pid'));write(a.output/'CHILD_IDENTITY.json',identity)
 until=time.monotonic()+20
 while not(a.output/'MAIN_ARM.json').exists():
  if time.monotonic()>=until:raise TimeoutError('actual source/CID/PID/start namespace ARM20')
  time.sleep(.05)
 assert json.loads((a.output/'MAIN_ARM.json').read_bytes())==dict(source=sr,guest_pid=identity['pid'],start_ticks=start)
 script=checked(m['files']['prebind_software22.py']);report=a.output/'SOFTWARE.json';argv=[sys.executable,'-I','-B',str(script),'--execute','--template-ref',json.dumps(tr,separators=(',',':')),'--output',str(report)]
 primary=None;software_ref=None;timeout=min(70.,80.-(time.monotonic()-started));assert timeout>0
 try:
  z=subprocess.run(argv,capture_output=True,text=True,timeout=timeout);stdout=z.stdout;stderr=z.stderr;code=z.returncode;timed_out=False
 except subprocess.TimeoutExpired as e:
  def decode(v):return v.decode('utf8','replace')if isinstance(v,bytes)else(v or '')
  stdout=decode(e.stdout);stderr=decode(e.stderr);code=None;timed_out=True;primary=repr(e)
 write(a.output/'SOFTWARE_TERMINAL.json',dict(argv=argv,exit=code,stdout=stdout,stderr=stderr,timed_out=timed_out,timeout=timeout))
 if code!=0:primary=primary or 'complete cold software child exit '+str(code)
 if report.is_file():
  software_ref=ref(report);v=json.loads(checked(software_ref).read_bytes())
  if not(v['template']==tr and v['full_suite_pass']is True and v['primary']is None and v['discovered']==v['executed']==m['software_cases']-2 and v['original_discovered']==m['software_cases']and len(v['deferred_to_original_model_cpu'])==2 and v['full_model_suite_executed']is False and v['skipped']==0):primary=primary or 'actual prepared-stage suite contract failed'
 else:primary=primary or 'missing actual software report'
 write(a.output/'ATTRIBUTION.json',dict(schema='deltalog.prebind-software-owned-complete/v22',source=sr,model_template=tr,software_ref=software_ref,primary=primary,Devices=[],NPU=False,qualified=False,model_source_created=False))
 return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())
