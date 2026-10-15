"""Exact unchanged-source and finite arithmetic AST comparison to023repair1."""
import ast,hashlib,json
from pathlib import Path
UNCHANGED=('binding.py','builder_mirror.py','contract.py','cpu_metadata.py','layout_controls.py','transform.py')
class Projection(ast.NodeTransformer):
 def visit_Expr(self,n):
  if isinstance(n.value,ast.Call) and (isinstance(n.value.func,ast.Name)and n.value.func.id in('_audit','_audit_once','emit')or ast.unparse(n.value.func)=='health.observe'):return None
  return self.generic_visit(n)
 def visit_If(self,n):
  s=ast.unparse(n.test)
  if s=='DIAGNOSTIC' or 'torch.isfinite(logical)' in s:return None
  return self.generic_visit(n)
 def visit_Pass(self,n):return None
def function(source,name):return next(n for n in ast.walk(ast.parse(source))if isinstance(n,ast.FunctionDef)and n.name==name)
def compare(old,new):
 old,new=Path(old),Path(new);result={}
 for name in UNCHANGED:
  a,b=(old/name).read_bytes(),(new/name).read_bytes()
  if a!=b:raise ValueError('changed actual CPU lifecycle/source '+name)
  result[name]=hashlib.sha256(a).hexdigest()
 for filename,name in(('primitives.py','_flush_slots'),('runtime_helpers.py','execute_mixed_core'),('integration.py','install')):
  a=Projection().visit(function((old/filename).read_text(),name));b=Projection().visit(function((new/filename).read_text(),name))
  if ast.dump(a,include_attributes=False)!=ast.dump(b,include_attributes=False):raise ValueError('finite-domain math/metadata AST differs '+name)
  result[name]='projected AST exact; only diagnostic logging / finite-check policy changed'
 def opcall(p):
  t=ast.parse(p.read_text());return next(n for n in ast.walk(t)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='_OP')
 if ast.dump(opcall(old/'runtime.py'))!=ast.dump(opcall(new/'runtime.py')):raise ValueError('actual B010 argument/arithmetic ABI changed')
 result['B010_OP_ABI']='exact AST';return result
