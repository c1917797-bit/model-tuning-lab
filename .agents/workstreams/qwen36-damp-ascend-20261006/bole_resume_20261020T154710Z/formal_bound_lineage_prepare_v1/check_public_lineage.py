"""One actual public derived-FSV chain in read-only virtual files. No physical bind/authority."""
import ast,copy,hashlib,json,sys,time,types
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import strict_bound_lineage as L
def data(v):return (json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode()
def reference(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def fixture():
 base=HERE/'SYNTHETIC_MEMORY_ONLY'
 trials=[L.render_pair(base/('trial-'+str(i)),i)for i in range(3)]
 chosen=trials[0]['bole'];root=Path(chosen['manifest']['root'])
 original=types.ModuleType('synthetic_schema_only')
 exec(compile(L.checked(L.ORIGINAL_FSV),'actual original schema constants','exec'),original.__dict__)
 rows=[]
 for i,trial in enumerate(trials):
  for arm,p in trial.items():
   m=p['manifest'];rows.append(dict(trial_index=i,arm=arm,source_root=m['root'],output_root=m['output_root'],
     files=m['files'],prepared_source_ref=m['strict_prepared_source_ref']))
 review=dict(schema='bole.MAIN-performance-execution-review/v1',approved=True,scope=original.SCOPE,
  strict_source_bindings=dict(schema='bole.MAIN-exact-six-strict-source-review/v1',
    prepared_source_set_ref=L.PREPARED_SET,renderer_dependencies=L.ASSETS,sources=rows))
 rr=reference(root/'SYNTHETIC_MEMORY_REVIEW.json',data(review))
 now=int(time.time());authority=dict(schema=original.AUTH_SCHEMA,approved=True,start_epoch=now-60,
  cutoff_epoch=now+14400,scope=original.SCOPE,MAIN_review_ref=rr)
 ar=reference(root/'SYNTHETIC_MEMORY_AUTHORITY.json',data(authority))
 memory={rr['path']:data(review),ar['path']:data(authority)}
 old=L.checked
 def actual_read(r):
  if r['path']not in memory:return old(r)
  raw=memory[r['path']];L.need(reference(Path(r['path']),raw)==r,'exact virtual authority bytes');return raw
 with patch.object(L,'checked',actual_read):chosen=L.render_pair(base/'trial-0',0,authority_ref=ar)['bole']
 template=chosen['manifest'];tr=reference(root/'SOURCE_TEMPLATE.json',data(template))
 m=copy.deepcopy(template);m.update(prepared_only=False,prepared_template=tr)
 sr=reference(root/'SOURCE_BOUND.json',data(m));b=dict(chosen,manifest=m)
 ns=dict(Path=Path,json=json)
 tree=ast.parse(b['files']['command_contract.py'])
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='expected')
 exec(compile(ast.Module(body=[node],type_ignores=[]),'actual command constructor','exec'),ns)
 commands=ns['expected'](m['root'],m['output_root'],sr,tr,m['component_refs'])
 historical=json.loads(Path(m['command_scope']['historical_ref']['path']).read_bytes())
 cv=dict(schema='bole.performance-actual-bound-commands/v1',source=tr,bound_source=sr,
  required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
  historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],
  G3_stream_protocol=False,actual_G3_execution_claimed=False,actual_G1_execution_claimed=False,
  legacy_entrypoints_retained_for_inverse_tests_only=True,**commands)
 cr=reference(root/'COMMANDS.json',data(cv));mirror=dict(source=sr,template=tr,commands=cr,
  model=cv['model'],CPU=cv['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases'])
 memory.update({str(root/'SOURCE_TEMPLATE.json'):data(template),str(root/'COMMANDS.json'):data(cv),
  str(root/m['command_scope']['compatibility_file']):data(mirror)})
 return b,memory,sr
def main():
 if sys.argv[1:]!=['--check']:raise SystemExit('defaultOFF; explicit read-only --check only')
 b,extra,sr=fixture();events=[]
 def run(virtual,bundle,root):
  import followup_source_validate as V
  proof=V.validate(sr) # Actual full public gate; no source_validated/expected stub.
  if proof['source_validated']is not True:raise ValueError('actual public source gate rejected')
  events.append('actual-public-FSV-validate-template-bound-expected-component-command-readset')
  if proof['fastpath_numerical_qualified']or proof['formal_performance']:raise ValueError('synthetic source must not claim numeric')
  try:V.require_fastpath_admission(bundle['manifest'])
  except ValueError as e:
   if 'actual fastpath NPU numerical admission adapter remains unbound'not in str(e):raise
   events.append('original-independent-NPU-numerical-admission-still-rejected')
  else:raise ValueError('numerical gate unexpectedly accepted')
 path=HERE.parent/'fastpath_numeric_bridge_prepare_v1/check_source_imports.py'
 tree=ast.parse(path.read_text())
 class Transform(ast.NodeTransformer):
  def visit_Assign(self,node):
   if any(isinstance(t,ast.Name)and t.id=='b'for t in node.targets):
    return ast.copy_location(ast.Assign(targets=node.targets,value=ast.Name(id='FIXTURE',ctx=ast.Load())),node)
   if any(isinstance(t,ast.Subscript)and isinstance(t.value,ast.Name)and t.value.id=='virtual'for t in node.targets):
    return [node,ast.Expr(ast.Call(func=ast.Attribute(value=ast.Name(id='virtual',ctx=ast.Load()),attr='update',ctx=ast.Load()),args=[ast.Name(id='EXTRA',ctx=ast.Load())],keywords=[]))]
   return self.generic_visit(node)
  def visit_Expr(self,node):
   if isinstance(node.value,ast.Call)and ast.unparse(node.value.func)=='Q.inverse':return None
   return self.generic_visit(node)
  def visit_With(self,node):
   if node.body and isinstance(node.body[0],ast.Import)and any(n.name=='qualification_source_validate'for n in node.body[0].names):
    node.body=ast.parse('RUN(virtual,b,root)').body;return node
   return self.generic_visit(node)
 tree=Transform().visit(tree);ast.fix_missing_locations(tree)
 ns=dict(__name__='synthetic_public_strict_lineage',__file__=str(path),FIXTURE=b,EXTRA=extra,RUN=run)
 with patch.object(sys,'argv',[str(path),'--reconstruct-only']):
  exec(compile(tree,'actual-readonly-virtual-source-adapter','exec'),ns);ns['main']()
 print(json.dumps(dict(events=events,physical_SOURCE_BOUND_created=False,physical_authority_created=False,
  source_validated_only_in_memory=True,actual_bound_validated=False,NPU=False,formal_performance=False)))
if __name__=='__main__':main()
