"""Source-only proof of original025 helper API and CPU-test snapshot closure."""
import ast
import hashlib
import json
from pathlib import Path
import sourceio as C

def safe_declared_refs(text):
 """Read only literal BASE/REFS; never execute/import the donor substrate."""
 tree=ast.parse(text)
 def assignment(name):
  values=[n.value for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
  if len(values)!=1:raise ValueError('exact unique '+name+' assignment')
  return values[0]
 base_node=assignment('BASE')
 if not isinstance(base_node,ast.Constant)or type(base_node.value)is not str or not Path(base_node.value).is_absolute():raise ValueError('unique BASE absolute string literal')
 base=base_node.value
 def value(node):
  if isinstance(node,ast.Dict):
   keys=[]
   for k in node.keys:
    if not isinstance(k,ast.Constant)or type(k.value)is not str:raise ValueError('literal string keys; no dictionary unpack')
    keys.append(k.value)
   if len(set(keys))!=len(keys):raise ValueError('no repeated literal keys')
   return{k:value(v)for k,v in zip(keys,node.values)}
  if isinstance(node,ast.Call):
   if not isinstance(node.func,ast.Name)or node.func.id!='dict'or node.args or any(k.arg is None for k in node.keywords):raise ValueError('only dict keyword literals; no positional/star/executable calls')
   keys=[k.arg for k in node.keywords]
   if len(set(keys))!=len(keys):raise ValueError('no repeated dict keywords')
   return{k.arg:value(k.value)for k in node.keywords}
  if isinstance(node,ast.BinOp):
   if not(isinstance(node.op,ast.Add)and isinstance(node.left,ast.Name)and node.left.id=='BASE'and isinstance(node.right,ast.Constant)and type(node.right.value)is str):raise ValueError('only literal BASE plus literal filename')
   return base+node.right.value
  return ast.literal_eval(node)
 root=assignment('REFS')
 if not isinstance(root,(ast.Dict,ast.Call)):raise ValueError('REFS must be literal dict or safe keyword dict')
 refs=value(root);names={'model_contract','safety_host','host_once'}
 if type(refs)is not dict or set(refs)!=names:raise ValueError('exact three genuine025 source Refs')
 for name,r in refs.items():
  if not(type(r)is dict and set(r)=={'path','bytes','sha256'}and r['path']==base+'/'+name+'.py'and
   type(r['bytes'])is int and r['bytes']>0 and type(r['sha256'])is str and len(r['sha256'])==64 and
   all(c in '0123456789abcdef'for c in r['sha256'])):raise ValueError('exact typed declared Ref3')
 return refs



def declarations(path):
    return safe_declared_refs(Path(path).read_text())


def verify_snapshot(m):
    refs=declarations(C.checked(m['files']['owned_substrate.py']));original=refs['safety_host'];snapshot=m['files']['safety_host.py']
    C.checked(original);C.checked(snapshot)
    C.need(snapshot['path']==str(Path(m['root'])/'safety_host.py')and
        (snapshot['bytes'],snapshot['sha256'])==(original['bytes'],original['sha256'])and
        C.checked(snapshot).read_bytes()==C.checked(original).read_bytes(),
        'exact original025 byteequal CPU source-test snapshot; actual owner still loads original declared Ref')
    return dict(original_ref=original,snapshot_ref=snapshot,byteequal=True,CPU_test_source_only=True,actual_owner_original025_Ref_unchanged=True,snapshot_imported_as_controller=False)
