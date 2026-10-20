import ast,copy,hashlib,json,tempfile,unittest
from pathlib import Path
import sourceio as C
import model_calibration131r12 as M
P=Path(__file__).parent
class Tests(unittest.TestCase):
 def registration(self):
  r=lambda n:dict(path='/exact/'+n,bytes=1,sha256='a'*64)
  return dict(actual_extension_ref=r('extension'),actual_opapi_mappings=[dict(ref=r('vendor'))])
 def test_entire_preregistered_set_not_subset_or_dynamic_expected(self):
  old=self.registration();good=copy.deepcopy(old);good['actual_opapi_mappings']=[dict(ref=r)for r in M.expected(old)['opapi']]
  self.assertEqual(M.identity(good),M.expected(old))
  for how in('missing','extra','order','sha'):
   bad=copy.deepcopy(good)
   if how=='missing':bad['actual_opapi_mappings'].pop()
   elif how=='extra':bad['actual_opapi_mappings'].append(dict(ref=old['actual_extension_ref']))
   elif how=='order':bad['actual_opapi_mappings'].reverse()
   else:bad['actual_opapi_mappings'][0]['ref']['sha256']='f'*64
   self.assertNotEqual(M.identity(bad),M.expected(old))
 def test_serialized_full12_reader_and_wrong_raw_source_paths_fail(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);sr=C.write(root/'SOURCE.json',dict(model_receipt_root=str(root)));old=dict(registration=self.registration(),actual_schema_family={'':'actual software schema fixture, not runtime'})
   oldref=C.write(root/'OLD.json',old);leaf=root/'CONV-MODEL-CALIBRATION-RANK-0';leaf.mkdir();refs=[];before=[]
   for kind,out in(('row',refs),('before',before)):
    for i in range(12):
     p=leaf/('%s-%02d.pt'%(kind,i));p.write_bytes(b'only typed raw identity fixture, not numerical data');out.append(C.ref(p))
   reg=copy.deepcopy(old['registration']);reg['actual_opapi_mappings']=[dict(ref=r)for r in M.expected(old['registration'])['opapi']]
   v=dict(schema='bole.same-model-initialization-conv-calibration/v131r12',source=sr,rank=0,old_abi_ref=oldref,actual_schema_family=old['actual_schema_family'],model_ready=False,cap_bytes=M.CAP,registration=reg,registration_after=reg,expected_identity=M.expected(old['registration']),rows=refs,before=before,raw_bytes=sum(r['bytes']for r in refs+before),worker_reference=dict(pass_gate=True),worker_diagnostic_only=True,independent_consumer_pending=True)
   v['callable_object_id']=1
   ar=C.write(leaf/'ABI.json',v);self.assertEqual(len(M.validate(C,ar,oldref,sr,0)['rows']),12)
   for key,value in(('source',oldref),('rows',refs[:-1]),('rank',1),('registration_after',old['registration'])):
    bad=dict(v,**{key:value});p=leaf/'ABI.json';p.unlink();ar=C.write(p,bad)
    with self.assertRaises(ValueError):M.validate(C,ar,oldref,sr,0)
 def test_original_matrix_source_and_full_real_call_edges(self):
  self.assertEqual(hashlib.sha256((P/'calibrate_conv118.py').read_bytes()).hexdigest(),'46d6d8e84d717f24b9ffcaf561649dc7b54c3a5b25102c3aa1b952c2b50367ed')
  tree=ast.parse((P/'model_calibration131r12.py').read_bytes());text=ast.unparse(tree)
  self.assertIn('K.execute(',text);self.assertIn('K.consume(t, rows, require_native_metadata=True)',text)
  consume=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='consume')
  self.assertIn("t.load(C.checked(rr), map_location='cpu', weights_only=False)",ast.unparse(consume))
  self.assertIn('K.consume(t, rows, require_native_metadata=True)',ast.unparse(consume))
  bridge=(P/'model_entry.py').read_text()
  self.assertLess(bridge.index('calibration_handle.acquire('),bridge.index('exact_library_identity=RA.compare(registration,convabi'))
  helper=ast.parse((P/'model_process_calibration.py').read_bytes())
  cls=next(n for n in helper.body if isinstance(n,ast.ClassDef)and n.name=='ProcessCalibration')
  acquire=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='acquire')
  calls=[n for n in ast.walk(acquire)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='MC'and n.func.attr=='run']
  self.assertEqual(len(calls),1)
  branch=next(n for n in acquire.body if isinstance(n,ast.If)and isinstance(n.test,ast.Name)and n.test.id=='created')
  self.assertTrue(any(n is calls[0]for item in branch.body for n in ast.walk(item)))
  text=ast.unparse(acquire);self.assertLess(text.index('MC.run('),text.index('MC.validate('))
  # Execute the real handle twice: original matrix once, original receipts reopened twice.
  import test_g1_lifecycle as lifecycle
  case=lifecycle.CalibrationTests('test_original_matrix_once_and_all_original_receipts_revalidated_for_second_request')
  try:
   handle,t,C_,arguments,*_=case.fixture()
   first=handle.acquire(t,C_,request_epoch=1,**arguments)
   second=handle.acquire(t,C_,request_epoch=2,**arguments)
   self.assertEqual(first[0],second[0]);self.assertTrue(first[2]['created']);self.assertTrue(second[2]['reused'])
   import model_process_calibration as PC
   self.assertEqual(PC.MC.run.call_count,1);self.assertEqual(PC.MC.validate.call_count,2)
  finally:case.doCleanups()
  self.assertIn('MC.validate(C, actual_abi, abi_ref', ast.unparse(ast.parse((P/'native_seams.py').read_text())))
  self.assertIn('MC.consume(t,C,raw[', (P/'consume_model.py').read_text())
if __name__=='__main__':unittest.main()
