"""Exact source-only input dependency/preflight delta; frozen parents are immutable."""
from pathlib import Path
import ast,hashlib
HERE=Path(__file__).resolve().parent
SHA='cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822'
def need(v,msg):
 if not v:raise ValueError(msg)
def once(body,old,new):
 need(body.count(old)==1,'exact one input seam');return body.replace(old,new,1)
def adapt(files):
 out=dict(files)
 b=out['benchmark_shared_prefix.py'];need(len(b)==49810 and hashlib.sha256(b).hexdigest()==SHA,'actual generator byte identity')
 body=out['hypic32k_input.py'].decode();tree=ast.parse(body)
 rows=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='GENERATOR'for t in n.targets)]
 need(len(rows)==1,'one generator operand')
 row=rows[0];old=ast.get_source_segment(body,row)
 need(isinstance(row.value,ast.Call)and isinstance(row.value.func,ast.Name)and row.value.func.id=='dict','original Ref3 constructor')
 args={k.arg:ast.literal_eval(k.value)for k in row.value.keywords}
 need(set(args)=={'path','bytes','sha256'}and args['bytes']==49810 and args['sha256']==SHA,'exact original generator Ref3')
 need(args['path'].endswith('/bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier/benchmark_shared_prefix.py'),'exact historical lazy operand')
 new="GENERATOR=dict(path=str(Path(__file__).resolve().parent/'benchmark_shared_prefix.py'),bytes=49810,sha256="+repr(SHA)+")"
 out['hypic32k_input.py']=once(body,old,new).encode()
 client=ast.parse(out['performance_service_client.py'])
 calls=[x for x in ast.walk(client)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and isinstance(x.func.value,ast.Name)and x.func.value.id=='AutoTokenizer'and x.func.attr=='from_pretrained']
 need(len(calls)==1 and ast.literal_eval(calls[0].args[0])=='/models/Qwen3.6-27B','actual client checkpoint operand')
 need({k.arg:ast.literal_eval(k.value)for k in calls[0].keywords}==dict(trust_remote_code=True,local_files_only=True),'exact actual local tokenizer options')
 body=out['preflight114.py'].decode()
 parsed=ast.parse(body)
 anchors=[n for n in ast.walk(parsed)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='actual_text_only'for t in n.targets)]
 need(len(anchors)==1,'one actual text-only assignment')
 anchor=anchors[0];indent=' '*anchor.col_offset
 seam=indent+ast.get_source_segment(body,anchor)+'\n'
 out['preflight114.py']=once(body,seam,seam+indent+'from input_preflight import run as actual_input_run\n'+indent+'actual_input = actual_input_run(sr, m, C)\n').encode()
 out['preflight114.py']=once(out['preflight114.py'].decode(),'return dict(text_only_configuration=actual_text_only,','return dict(input_preflight=actual_input, text_only_configuration=actual_text_only,').encode()
 out['input_preflight.py']=(HERE/'input_preflight.py').read_bytes()
 delta={n:dict(before=files.get(n),after=b)for n,b in out.items()if files.get(n)!=b}
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact input inverse')
  if r['before']is None:out.pop(n)
  else:out[n]=r['before']
 return out
