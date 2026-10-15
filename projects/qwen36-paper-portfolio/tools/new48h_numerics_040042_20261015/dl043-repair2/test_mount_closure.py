"""Real target_closure + real GE.create parent-selection AST; source fixture only."""
import ast,copy,json,pathlib,types,unittest
P=pathlib.Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_external022_files_all_RO_without_broad_mount(self):
  tree=ast.parse((P/'host.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='target_closure')
  composite=json.loads((P/'fixtures/022-source-file-readset.json').read_bytes())
  manifest=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
  external=composite['source']
  manifest.update(composite_source_ref=external,composite_cpu_owner_ref=external,lifecycle_source_ref=external)
  checked=[];calls=[]
  def read(r):
   calls.append(r);self.assertEqual(r,external);return composite
  C=types.SimpleNamespace(source=lambda r:manifest,obj=read)
  ns=dict(obj=lambda r:manifest,Path=pathlib.Path,load=lambda *a:C,need=lambda v,m:self.assertTrue(v,m),checked=lambda r:checked.append(r),validate_ref_streamed=lambda r:checked.append(r))
  exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(fn)],type_ignores=[])),str(P/'host.py'),'exec'),ns)
  root,m,_,refs,historical=ns['target_closure'](external)
  self.assertIn(external,calls)
  self.assertTrue(all(r in refs and r in checked for r in composite['files'].values()))
  GE=next(n for n in ast.walk(tree)if isinstance(n,ast.ClassDef)and n.name=='GE')
  create=next(n for n in GE.body if isinstance(n,ast.FunctionDef)and n.name=='create')
  parent=next(n for n in ast.walk(create)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='parents'for t in n.targets))
  # Actual original expression/set minimization block, not a copied algorithm.
  lines=create.body
  i=lines.index(parent);j=next(j for j in range(i+1,len(lines))if isinstance(lines[j],ast.Assign)and any(isinstance(t,ast.Name)and t.id=='mounts'for t in lines[j].targets));block=lines[i:j]
  scope=dict(Path=pathlib.Path,refs=refs,root=root,historical_root=historical,ar=external)
  exec(compile(ast.Module(body=copy.deepcopy(block),type_ignores=[]),'<actualGE.create-parent-block>','exec'),scope)
  parents=scope['parents']
  exec(compile(ast.Module(body=[copy.deepcopy(lines[j])],type_ignores=[]),'<actualGE.create-RO-mounts>','exec'),scope)
  self.assertTrue(all(rw is False for src,rw in scope['mounts'].values()))
  self.assertTrue(all(any(pathlib.Path(r['path']).is_relative_to(p)for p in parents)for r in composite['files'].values()))
  self.assertFalse(any(str(p)in('/','/cache','/cache/cch')for p in parents))
  self.assertTrue(any(str(p).endswith('deltalog-raw-bitwise-audit-v019')for p in parents))
  omitted=[r for r in refs if r not in composite['files'].values()]
  missing_scope=dict(scope,refs=omitted)
  exec(compile(ast.Module(body=copy.deepcopy(block),type_ignores=[]),'<old-missing-closure-counterexample>','exec'),missing_scope)
  external_scope=composite['files']['scope_adapter.py']
  self.assertFalse(any(pathlib.Path(external_scope['path']).is_relative_to(p)for p in missing_scope['parents']))
if __name__=='__main__':unittest.main()
