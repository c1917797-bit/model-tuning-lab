"""Exact HTTP/token-ID driver; warmup and ownership barriers are untimed."""
import argparse,ast,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import contract090 as C
def warmup_transform(raw):
 tree=ast.parse(raw);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_run_warmups');calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='submit']
 need=C.need;need(len(calls)==1 and isinstance(calls[0].args[-1],ast.Constant)and calls[0].args[-1].value==1,'exact canonical warmup output argument only')
 original=ast.dump(fn,include_attributes=False);calls[0].args[-1]=ast.Attribute(value=ast.Name(id='args',ctx=ast.Load()),attr='output_tokens',ctx=ast.Load());changed=ast.fix_missing_locations(fn)
 inverse=ast.parse(ast.unparse(changed));inv=inverse.body[0];next(n for n in ast.walk(inv)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='submit').args[-1]=ast.Constant(value=1);need(ast.dump(inv,include_attributes=False)==original,'warmup-only AST inverse')
 return changed
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--input-tokens',type=int,choices=C.PROFILES);p.add_argument('--barrier-root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);C.source(sr);raw=C.checked(C.DRIVER).read_bytes();d=C.load(C.DRIVER,'_090_original_http_driver');root=a.barrier_root;C.need(root.is_dir()and not any(root.iterdir())and not a.output.exists(),'fresh profile evidence')
 # Warmups also generate1024; they remain a separately reported untimed phase.
 fn=warmup_transform(raw);exec(compile(ast.Module(body=[fn],type_ignores=[]),C.DRIVER['path']+'#warmup1024-only','exec'),vars(d))
 build=d._build_prompts;measured=d._run_measured
 def prompts(args):
  values=build(args);C.need(len(values)==C.MEASURED+C.WARMUPS and all(len(v)==a.input_tokens and all(type(x)is int for x in v)for v in values),'exact real tokenizer token-ID geometry')
  C.write(root/'INPUTS.json',dict(driver=C.DRIVER,source=sr,input_tokens=a.input_tokens,prompts=values,warmups=C.WARMUPS,measured=C.MEASURED));return values
 def barrier(stage):
  C.write(root/(stage+'-WAIT.json'),dict(stage=stage,source=sr,profile=a.input_tokens));end=time.monotonic()+60
  while not(root/(stage+'-ACK.json')).is_file():C.need(time.monotonic()<end,'owned native worker source barrier60');time.sleep(.1)
  v=C.obj(C.ref(root/(stage+'-ACK.json')));C.need(v==dict(stage=stage,source=sr,profile=a.input_tokens,actual_owned_native_workers=4),'exact native host acknowledgement')
 def run(*args,**kw):barrier('BEFORE');out=measured(*args,**kw);barrier('AFTER');return out
 d._build_prompts=prompts;d._run_measured=run
 sys.argv=[C.DRIVER['path'],'--base-url','http://127.0.0.1:8230','--model','qwen36-mxr-eager','--input-tokens',str(a.input_tokens),'--prefix-tokens','1024','--output-tokens','1024','--requests',str(C.MEASURED),'--concurrency','1','--warmup-requests',str(C.WARMUPS),'--timeout','900','--json-output',str(a.output)]
 return d.main()
if __name__=='__main__':raise SystemExit(main())
