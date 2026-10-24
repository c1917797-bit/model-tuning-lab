"""Typed actual-client input preflight propagation; no production request edits."""
from pathlib import Path
import ast,hashlib,importlib.util,sys
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'bole_client_input_v10_prepare_20261024'
ADAPTER=dict(path=str(BASE/'adapt_input_preflight.py'),bytes=3152,sha256='4d35ac101c6384e63ad3bf76cce91e85406cf121d2911692d01aa7c2ecd157cb')
HELPER=dict(path=str(BASE/'input_preflight.py'),bytes=5490,sha256='bcccf62d8385f2fba0f0cecbe6dffe4d6a0945d57d6799d8b908e051750f3de2')
def checked(r):
 p=Path(r['path']);b=p.read_bytes()
 if not p.is_absolute()or any(x.is_symlink()for x in(p,*p.parents))or len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('actual V10 source Ref')
 return b
def adapt(files):
 name='_exact_V10_input_adapter';had=name in sys.modules;old=sys.modules.get(name)
 spec=importlib.util.spec_from_file_location(name,ADAPTER['path']);A=importlib.util.module_from_spec(spec);sys.modules[name]=A
 try:exec(compile(checked(ADAPTER),ADAPTER['path'],'exec'),A.__dict__);out,delta=A.adapt(files)
 finally:
  if had:sys.modules[name]=old
  else:sys.modules.pop(name,None)
 rows=[]
 tree=ast.parse(out['performance_service_client.py'])
 run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
 for n in ast.walk(run):
  if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='request':
   if len(n.args)<6:raise ValueError('actual request ABI')
   rows.append((ast.literal_eval(n.args[5]),ast.literal_eval(n.args[3]),ast.literal_eval(n.args[4])))
 if [r[0]for r in rows]!=['warmup','measured','retirement-barrier']or [r[1]for r in rows]!=[-1,0,1]:raise ValueError('actual three-role client ABI')
 count=rows[0][2]
 if type(count)is not int or count not in(160,1024)or rows[1][2]!=count or rows[2][2]!=1:raise ValueError('actual declared followup output domain')
 body=checked(HELPER).decode()
 before="for role,index,count in [('warmup',-1,8),('measured',0,8),('retirement-barrier',1,1)]:"
 after='for role,index,count in '+repr(rows)+':'
 if body.count(before)!=1 or body.count('if count==8 else')!=1:raise ValueError('exact V10 preflight count/EOS seam')
 body=body.replace(before,after).replace('if count==8 else','if count>1 else')
 out['input_preflight.py']=body.encode()
 out['adapt_input_preflight.py']=checked(ADAPTER)
 out['followup_input.py']=Path(__file__).read_bytes()
 return out
