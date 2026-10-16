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
  count=args.requests;warmup=args.warmup_requests
  if(count,warmup)not in((2,2),(40,2))or len(values)!=count+warmup or any(len(v)!=2048 or any(type(x)is not int for x in v)for v in values):raise ValueError('actual registered smoke or complete canonical tokeninputs')
  with(root/'INPUTS.json').open('x',encoding='utf8')as f:json.dump(dict(driver_sha256=SHA,prompts=values,shared_prefix_tokens=1024,warmups=warmup,measured=count),f,sort_keys=True);f.write('\n')
  return values
 d._build_prompts=prompts
 warm=d._run_warmups
 def warmups(args,values):
  original=warm(args,values)
  # Original warmups max_tokens=1 do not execute recurrent candidate decode.
  # This identical BOTH-arm startup probe is outside measured intervals and
  # uses the first exact canonical prompt, not a simpler extra workload.
  result=d._stream_completion(args,-100,values[0],None,10)
  if not(result.ok and result.output_tokens==result.requested_output_tokens==10 and result.finish_reason=='length'):raise ValueError('actual source-qualified dispatch startup10 did not finish')
  from dataclasses import asdict
  with(root/'DISPATCH_STARTUP.json').open('x',encoding='utf8')as f:json.dump(dict(prompt=values[0],output_tokens=10,actual=asdict(result),outside_timing=True,not_performance_sample=True),f,sort_keys=True);f.write('\n')
  return original
 d._run_warmups=warmups
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


