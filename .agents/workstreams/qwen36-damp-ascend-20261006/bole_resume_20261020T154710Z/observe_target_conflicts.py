"""Finite read-only observer for intermittent physical4-7 conflicts."""
from pathlib import Path
import ast,datetime,hashlib,json,re,subprocess,time
OUT=Path('/opt/host/vnf/austinov/bole-target-conflict-20261020T154710Z-v1')
def identity(pid):
 p=Path('/proc')/str(pid);data=(p/'cmdline').read_bytes();args=data.split(b'\0');stat=(p/'stat').read_text();rest=stat[stat.rfind(')')+2:].split()
 cg=(p/'cgroup').read_text();m=re.search(r'/docker/([0-9a-f]{64})',cg)
 value=dict(pid=pid,start_ticks=int(rest[19]),ppid=int(rest[1]),cgroup=cg,
  executable=str((p/'exe').resolve()),cwd=str((p/'cwd').resolve()),
  cmdline_sha256=hashlib.sha256(data).hexdigest(),argv0=args[0].decode(errors='replace')if args else'',
  argv1=args[1].decode(errors='replace')if len(args)>1 else'')
 if value['argv1']=='-c'and len(args)>2:
  try:
   tree=ast.parse(args[2].decode());value['inline_imports']=[x.module if isinstance(x,ast.ImportFrom)else','.join(y.name for y in x.names)for x in ast.walk(tree)if isinstance(x,(ast.Import,ast.ImportFrom))]
  except BaseException:value['inline_imports']=[]
 if m:
  cid=m.group(1);value['container_id']=cid
  q=subprocess.run(['/usr/bin/docker','inspect',cid,'--format','{{json .Name}}'],capture_output=True,text=True,timeout=10)
  value['container_name']=json.loads(q.stdout)if q.returncode==0 else None
 return value
def main():
 assert not OUT.exists();OUT.mkdir(mode=0o700)
 deadline=time.monotonic()+600;seen=set();complete=[]
 while time.monotonic()<deadline:
  q=subprocess.run(['/usr/local/sbin/npu-smi','info'],capture_output=True,text=True,timeout=15)
  if q.returncode:raise RuntimeError(q.stderr)
  rows=[tuple(map(int,m.groups()))for m in re.finditer(r'^\|\s*(\d+)\s+(\d+)\s*\|\s*(\d+)\s*\|',q.stdout,re.M)]
  for physical,chip,pid in rows:
   if physical not in(4,5,6,7)or pid in seen:continue
   seen.add(pid)
   value=dict(physical=physical,chip=chip,observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
   try:value.update(identity(pid))
   except FileNotFoundError:value.update(pid=pid,identity_disappeared=True)
   raw=OUT/('smi-'+str(time.time_ns())+'.txt');raw.write_text(q.stdout);value['smi_path']=str(raw)
   with(OUT/'OBSERVATIONS.jsonl').open('a')as f:f.write(json.dumps(value)+'\n')
   print(json.dumps(value),flush=True);complete.append(value)
   if value.get('container_name')and not value['container_name'].startswith('/adakv-tp4-run-bole-'):
    (OUT/'RESULT.json').write_text(json.dumps(dict(identified=value,read_only=True,stopped_foreign=False),indent=2)+'\n');return
  time.sleep(1)
 (OUT/'RESULT.json').write_text(json.dumps(dict(observations=complete,read_only=True,stopped_foreign=False,deadline_reached=True),indent=2)+'\n')
if __name__=='__main__':main()

