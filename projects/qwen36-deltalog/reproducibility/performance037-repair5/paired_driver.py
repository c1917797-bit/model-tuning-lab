"""Original byte-pinned driver; barriers outside its measured duration only."""
import argparse,hashlib,importlib.util,json,sys,time
from pathlib import Path
SHA='cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822'
def main():
 p=argparse.ArgumentParser(allow_abbrev=False,add_help=False)
 p.add_argument('--original-driver',required=True,type=Path);p.add_argument('--barrier-root',required=True,type=Path)
 a,rest=p.parse_known_args();raw=a.original_driver.read_bytes()
 if(len(raw),hashlib.sha256(raw).hexdigest())!=(49810,SHA):raise ValueError('actual original canonical driver')
 root=a.barrier_root
 if not root.is_absolute()or not root.is_dir()or any(root.iterdir()):raise ValueError('new owned empty barrier directory')
 spec=importlib.util.spec_from_file_location('_actual_canonical_driver',a.original_driver);d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
 original=d._run_measured;build=d._build_prompts
 def prompts(args):
  values=build(args)
  if len(values)!=42 or any(len(v)!=32768 or any(type(x)is not int for x in v)for v in values):raise ValueError('actual complete canonical tokeninputs')
  with(root/'INPUTS.json').open('x',encoding='utf8')as f:json.dump(dict(driver_sha256=SHA,prompts=values,shared_prefix_tokens=16384,warmups=2,measured=40),f,sort_keys=True);f.write('\n')
  return values
 d._build_prompts=prompts
 def barrier(stage):
  with(root/(stage+'-WAIT.json')).open('x',encoding='utf8')as f:json.dump(dict(stage=stage,pid=__import__('os').getpid(),monotonic=time.monotonic(),driver_sha256=SHA),f);f.write('\n')
  until=time.monotonic()+60
  while not(root/(stage+'-OWNED-ACK.json')).is_file():
   if time.monotonic()>=until:raise TimeoutError('owned worker snapshot barrier '+stage)
   time.sleep(.1)
  value=json.loads((root/(stage+'-OWNED-ACK.json')).read_text())
  if value.get('stage')!=stage or value.get('owned_source_qualified')is not True:raise ValueError('exact MAIN snapshot ACK')
 def measured(*args,**kw):
  barrier('BEFORE');out=original(*args,**kw);barrier('AFTER');return out
 d._run_measured=measured;sys.argv=[str(a.original_driver),*rest]
 return d.main()
if __name__=='__main__':raise SystemExit(main())


