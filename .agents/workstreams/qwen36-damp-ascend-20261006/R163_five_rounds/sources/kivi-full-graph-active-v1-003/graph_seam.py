"""Private source-bound writer/window seam. Original math and initialization stay intact."""
import ast,copy,hashlib,types
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def tree(E,raw,writer,repair,evidence):
 original=E.tree(raw);tree=copy.deepcopy(original)
 clocks=[n for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='CUT']
 need(len(clocks)==1 and clocks[0].value.value==1791922930,'exact historical overlay clock');clocks[0].value.value=1792002456
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 report=next(n.value for n in fn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='report'for t in n.targets))
 kw=next(k for k in report.keywords if k.arg=='runtime_window');old=copy.deepcopy(kw.value)
 kw.value=ast.parse(repr(dict(start_epoch=1791916056,cutoff=1792002456,overlay_source=evidence)),mode='eval').body
 report.keywords.extend([ast.keyword(arg='channel32_writer_source',value=ast.parse(repr(repair),mode='eval').body),ast.keyword(arg='actual_r156_writer',value=ast.parse(repr(writer),mode='eval').body)])
 inverse=copy.deepcopy(tree);invclock=next(n for n in inverse.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='CUT');invclock.value.value=1791922930
 invfn=next(n for n in inverse.body if isinstance(n,ast.FunctionDef)and n.name=='main');r=next(n.value for n in invfn.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='report'for t in n.targets))
 need([k.arg for k in r.keywords[-2:]]==['channel32_writer_source','actual_r156_writer'],'only two source receipts');r.keywords=r.keywords[:-2];next(k for k in r.keywords if k.arg=='runtime_window').value=old
 need(ast.dump(inverse,include_attributes=False)==ast.dump(original,include_attributes=False),'full inverse AST, original compute/warm/graph/state/threshold unchanged')
 return ast.fix_missing_locations(tree)
def bind(G,source,E,evidence,writer,repair):
 raw=G.checked(source);G.checked(writer);G.checked(repair)
 private=E.bind(G,source,evidence);ns=dict(private.__dict__)
 exec(compile(tree(E,raw,writer,repair,evidence),source['path'],'exec',dont_inherit=True),ns)
 original=ns['load'];seen=[];gm=__import__('json').loads(G.checked(dict(path=str(Path(source['path']).parent/'SOURCE_MANIFEST.json'),bytes=7774,sha256='d0eed41cbda770c59e4fdb6ef2ed648362a5d074928c254df2307c291cfc3f82')))
 def load(r,name):
  if r==gm['files']['graph_writer.py']:
   need(not seen,'one actual complete writer load');seen.append(writer);return original(writer,name+'_safe_r156')
  return original(r,name)
 ns['load']=load
 return types.SimpleNamespace(**ns)
