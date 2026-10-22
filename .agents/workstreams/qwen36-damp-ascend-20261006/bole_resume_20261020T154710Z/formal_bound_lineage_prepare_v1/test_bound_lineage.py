"""Pure owning-layer controls; no SOURCE_BOUND/authority/HTTP/NPU is created."""
import ast,copy,sys,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import strict_bound_lineage as L
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.path=L.HERE/'future-review-only-trial-0'
  names=L.ORDER;old={n:sys.modules.get(n)for n in names};had={n:n in sys.modules for n in names}
  poison={}
  cls.oldpath=list(sys.path)
  try:
   for n in names:
    x=types.ModuleType(n);x.__file__='/not-reviewed/'+n+'.py'
    def bad(*a,**k):raise AssertionError('POISONED helper reused')
    x.render_pair=x.render=x.pair=x.validate=x.read_parent=bad
    sys.modules[n]=x;poison[n]=x
   cls.bundle=L.render_pair(cls.path,0)
   assert all(sys.modules[n]is poison[n]for n in names)
   assert sys.path==cls.oldpath
  finally:
   for n in names:
    if had[n]:sys.modules[n]=old[n]
    else:sys.modules.pop(n,None)
 def test_actual_poisoned_parent_alias_render_and_inverse(self):
  self.assertEqual(set(self.bundle),{'native_ar','bole'})
  for arm,p in self.bundle.items():
   self.assertEqual(len(p['files']),403)
   self.assertTrue(L.inverse_files(p))
   self.assertEqual(p['manifest']['strict_prepared_source_ref'],
      L.obj(L.PREPARED_SET)['trials'][0]['arms'][arm])
   self.assertFalse(p['manifest']['performance_ready'])
 def test_same_original_numeric_and_authority_gates(self):
  old=L.checked(L.ORIGINAL_FSV);new=L.validator_delta(old)
  for name in ('require_fastpath_admission','authority_shape','execution_window'):
   n=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)and n.name==name)
   z=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)and n.name==name)
   self.assertEqual(ast.dump(n,include_attributes=False),ast.dump(z,include_attributes=False))
   if name=='require_fastpath_admission':
    env={};exec(compile(ast.Module(body=[z],type_ignores=[]),'actual-complete-gate','exec'),env)
    with self.assertRaisesRegex(ValueError,'actual fastpath NPU numerical admission'):env[name]({})
  self.assertIn(b'readset=bind_model.readset(sr)',new)
  self.assertIn(b'readset+=command_contract.validate(C,sr,m)',new)
  self.assertIn(b'execution_window(m,clock=False,require_phase=False)',new)
 def test_exact_template_binding_states_and_refusals(self):
  t=self.bundle['bole']['manifest'];r=dict(path=str(Path(t['root'])/'SOURCE_TEMPLATE.json'),bytes=1,sha256='0'*64)
  m=copy.deepcopy(t);m.update(prepared_only=False,prepared_template=r)
  self.assertTrue(L.binding_shape(m,t,r))
  for key,value in [('numerical_qualified',True),('default_enabled',True),('prepared_only',True),('performance_ready',True),('strict_trial_index',1)]:
   q=copy.deepcopy(m);q[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):L.binding_shape(q,t,r)
  with self.assertRaises(ValueError):L.validate_bound_source(L.obj(L.PREPARED_SET)['trials'][0]['arms']['bole'])
 def test_module_error_restores_and_no_unbound_authority(self):
  oldpath=list(sys.path);old=dict(sys.modules)
  try:
   with L.renderer_modules():raise RuntimeError('explicit staged error')
  except RuntimeError:pass
  self.assertEqual(sys.path,oldpath)
  for name in L.ORDER:
   self.assertEqual(name in sys.modules,name in old)
   if name in old:self.assertIs(sys.modules[name],old[name])
  for p in self.bundle.values():
   m=p['manifest'];self.assertIsNone(m['followup_authority_ref']);self.assertTrue(m['pending_current_authority'])
 def test_preimport_MAIN_source_review_pins_exact_files_and_lineage(self):
  m=self.bundle['bole']['manifest']
  rows=[]
  for i in range(3):
   for arm in ('native_ar','bole'):
    rows.append(dict(trial_index=i,arm=arm,source_root='other-root-'+str(i)+arm,output_root='other-output-'+str(i)+arm,files={},prepared_source_ref={}))
  actual=dict(trial_index=m['strict_trial_index'],arm=m['performance_arm'],source_root=m['root'],
      output_root=m['output_root'],files=m['files'],prepared_source_ref=m['strict_prepared_source_ref'])
  rows[1]=actual
  fixture=dict(strict_source_bindings=dict(schema='bole.MAIN-exact-six-strict-source-review/v1',
    prepared_source_set_ref=m['strict_prepared_source_set_ref'],renderer_dependencies=m['strict_renderer_dependencies'],sources=rows))
  # Pure in-memory policy fixture: no ticket/review file is issued or written.
  env=dict(need=L.need,json=__import__('json'),execution_window=lambda *a,**k:{'MAIN_review_ref':'fixture-only'},
           read_ref=lambda r:__import__('json').dumps(fixture).encode())
  exec(compile(L.STRICT_REVIEW_FUNCTION,'actual-preimport-policy','exec'),env)
  self.assertTrue(env['strict_source_review'](m))
  for fault in ('unbound','files','root','dependency','prepared','trial'):
   q=copy.deepcopy(m);r=copy.deepcopy(fixture)
   if fault=='unbound':r={}
   if fault=='files':q['files']['strict_bound_lineage.py']=dict(q['files']['strict_bound_lineage.py'],sha256='0'*64)
   if fault=='root':q['root']+='foreign'
   if fault=='dependency':q['strict_renderer_dependencies']=[]
   if fault=='prepared':q['strict_prepared_source_ref']={}
   if fault=='trial':r['strict_source_bindings']['sources'][0]['trial_index']=True
   env['read_ref']=lambda x,r=r:__import__('json').dumps(r).encode()
   with self.subTest(fault=fault),self.assertRaises(ValueError):env['strict_source_review'](q)
  text=L.validator_delta(L.checked(L.ORIGINAL_FSV)).decode()
  self.assertLess(text.index("strict_program=read_ref"),text.index("strict_source_review(m)",text.index("def validate(sr):")))
  self.assertLess(text.index("strict_source_review(m)",text.index("def validate(sr):")),text.index("exec(compile(strict_program"))
  self.assertNotIn('import strict_bound_lineage as STRICT',text)
if __name__=='__main__':unittest.main()
