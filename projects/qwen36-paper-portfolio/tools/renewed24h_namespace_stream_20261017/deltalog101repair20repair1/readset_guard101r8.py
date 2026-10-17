"""Own-source AST read closure, including P/name aliases, before CPU aggregate."""
import ast
from pathlib import Path,PurePosixPath
ANCHOR=PurePosixPath('/__declared_own__')
def check(m,root):
 root=Path(root);declared=set(m['files'])|{'SOURCE_TEMPLATE.json','SOURCE_MANIFEST.json'};resolved=[];unresolved=[]
 for name in sorted(m['files']):
  if not name.startswith('test_')or not name.endswith('.py'):continue
  tree=ast.parse((root/name).read_bytes());env={'P':{ANCHOR},'__file__':{ANCHOR/name}}
  def values(n):
   if isinstance(n,ast.Constant)and type(n.value)is str:return{n.value}
   if isinstance(n,ast.Name):return env.get(n.id,set())
   if isinstance(n,ast.BinOp)and isinstance(n.op,ast.Div):return{a/b for a in values(n.left)for b in values(n.right)if isinstance(a,PurePosixPath)and type(b)is str}
   if isinstance(n,ast.Attribute)and n.attr=='parent':return{a.parent for a in values(n.value)if isinstance(a,PurePosixPath)}
   if isinstance(n,ast.Call):
    if isinstance(n.func,ast.Name)and n.func.id in('Path','PurePosixPath'):return{PurePosixPath(x)for a in n.args[:1]for x in values(a)}
    if isinstance(n.func,ast.Attribute)and n.func.attr in('resolve','absolute'):return values(n.func.value)
    if isinstance(n.func,ast.Attribute)and n.func.attr in('Path','PurePosixPath'):return{PurePosixPath(x)for a in n.args[:1]for x in values(a)}
   return set()
  for _ in range(8):
   changed=False
   for n in ast.walk(tree):
    assignments=[]
    if isinstance(n,ast.Assign):assignments=[(t,n.value)for t in n.targets if isinstance(t,ast.Name)]
    if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and isinstance(n.iter,(ast.Tuple,ast.List)):assignments=[(n.target,a)for a in n.iter.elts]
    for target,value in assignments:
     v=values(value);old=env.get(target.id,set());new=old|v
     if new!=old:env[target.id]=new;changed=True
   if not changed:break
  for n in ast.walk(tree):
   if not isinstance(n,ast.Call):continue
   receiver=None
   if isinstance(n.func,ast.Attribute)and n.func.attr in('read_bytes','read_text','open'):
    if n.func.attr=='open'and any(isinstance(x,ast.Constant)and type(x.value)is str and any(k in x.value for k in('w','x','a'))for x in n.args[:1]):continue
    receiver=n.func.value
   elif isinstance(n.func,ast.Name)and n.func.id=='open'and n.args:receiver=n.args[0]
   if receiver is None:continue
   candidates=values(receiver);own=[str(x.relative_to(ANCHOR))for x in candidates if isinstance(x,PurePosixPath)and x.is_relative_to(ANCHOR)]
   if not candidates:unresolved.append(dict(file=name,line=n.lineno,expression=ast.unparse(receiver)))
   for path in own:
    if path not in declared:raise ValueError('undeclared own read '+name+':'+str(n.lineno)+' -> '+path)
    resolved.append(dict(file=name,line=n.lineno,path=path))
 return dict(schema='deltalog.own-read-closure-AST/v101-repair8',files_checked=sum(n.startswith('test_')and n.endswith('.py')for n in m['files']),statically_resolved_own_reads=len(resolved),unresolved_read_sites=unresolved,qualification=False)
