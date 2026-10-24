"""Exact function-level text-only successor, fully reversible."""
import ast
from pathlib import Path
def need(v,s):
 if not v:raise ValueError(s)
def insert_after(raw,line,text):
 lines=raw.decode().splitlines(keepends=True);lines[line:line]=[text];return ''.join(lines).encode()
def adapt(files):
 out=dict(files)
 a=ast.parse(out['bole_performance_profile.py'])
 f=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name=='paired_argv')
 first=f.body[0];line=first.end_lineno if isinstance(first,ast.Expr)and isinstance(first.value,ast.Constant)and type(first.value.value)is str else f.lineno
 pad=' '*first.col_offset
 out['bole_performance_profile.py']=insert_after(out['bole_performance_profile.py'],line,pad+"from text_only_profile import argv as _text_argv\n"+pad+"candidate_argv=_text_argv(candidate_argv)\n")
 a=ast.parse(out['preflight114.py']);f=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name=='run')
 matches=[n for n in ast.walk(f)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='engine'for t in n.targets)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='from_cli_args']
 need(len(matches)==1,'actual same-image AsyncEngineArgs seam')
 n=matches[0];pad=' '*n.col_offset
 out['preflight114.py']=insert_after(out['preflight114.py'],n.end_lineno,pad+"from text_only_profile import require_parsed\n"+pad+"actual_text_only=require_parsed(args,engine)\n")
 old="return dict(schema='bole.actual-devicefree-native-MTP-parser/v114'"
 new="return dict(text_only_configuration=actual_text_only,schema='bole.actual-devicefree-native-MTP-parser/v114'"
 text=out['preflight114.py'].decode();need(text.count(old)==1,'actual parser receipt seam')
 out['preflight114.py']=text.replace(old,new,1).encode()
 out['text_only_profile.py']=(Path(__file__).parent/'text_only_profile.py').read_bytes()
 delta={n:dict(before=files.get(n),after=b)for n,b in out.items()if files.get(n)!=b}
 need(set(delta)=={'bole_performance_profile.py','preflight114.py','text_only_profile.py'},'only common argv and actual parsed quotas')
 for n,b in out.items():
  if n.endswith('.py'):compile(b,n,'exec')
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact text-only delta inverse')
  if r['before']is None:out.pop(n)
  else:out[n]=r['before']
 return out
