import ast,copy,io,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sourceio as C
import registration_audit131r11 as A

class Tests(unittest.TestCase):
 def test_exact_pass_and_every_mismatch_still_fail_no_subset(self):
  ref=lambda s:dict(path='/actual/'+s,bytes=1,sha256='a'*64)
  r=dict(actual_extension_ref=ref('ext'),actual_opapi_mappings=[dict(ref=ref('op1')),dict(ref=ref('op2'))])
  self.assertTrue(A.compare(r,r)['exact_pass'])
  for kind in('extra','missing','order','extension','sha'):
   v=copy.deepcopy(r)
   if kind=='extra':v['actual_opapi_mappings'].append(dict(ref=ref('op3')))
   elif kind=='missing':v['actual_opapi_mappings'].pop()
   elif kind=='order':v['actual_opapi_mappings'].reverse()
   elif kind=='extension':v['actual_extension_ref']['path']+='-other'
   else:v['actual_extension_ref']['sha256']='b'*64
   self.assertFalse(A.compare(v,r)['exact_pass'])
 def test_real_serialized_operands_written_before_gate_failure(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);lib=root/'ext.so';lib.write_bytes(b'CPU control, not a native library');r=dict(actual_extension_ref=C.ref(lib),actual_opapi_mappings=[],actual_extension_maps=[],loaded_libraries=[])
   calibration=copy.deepcopy(r);calibration['actual_extension_ref']['sha256']='b'*64
   ar=C.write(root/'ABI.json',dict(registration=calibration));own=dict(files={'registration_audit131r11.py':C.ref(A.__file__)},model_receipt_root=str(root));sr=C.write(root/'SOURCE.json',own)
   original=Path.open;original_open=os.open
   def opened(p,*a,**kw):return io.BytesIO(('1-2 r-xp 0 0:0 1 '+str(lib)+'\n').encode())if p.as_posix()=='/proc/self/maps'else original(p,*a,**kw)
   def op(p,flags,*a,**kw):return original_open(root/'SOURCE.json',os.O_RDWR)if Path(p)==root and os.name=='nt'else original_open(p,flags,*a,**kw)
   # Only the absent Windows proc file/directory-fsync OS calls are modeled;
   # the actual helper/source Ref/serialized ABI/record write execute fully.
   with patch.dict(os.environ,BOLE_MODEL_RAW_ROOT=str(root)),patch.object(Path,'open',opened),patch.object(os,'open',side_effect=op):
    ref,passed=A.persist(C,sr,own,r,ar,C.obj(ar),0)
   self.assertFalse(passed);record=C.obj(ref);self.assertFalse(record['comparison']['extension_equal']);self.assertEqual(record['calibrated_abi_ref'],ar);self.assertIn(str(lib),record['actual_process_maps']);self.assertFalse(record['gate_relaxed'])
 def test_actual_Bridge_persists_before_unchanged_identity_need(self):
  tree=ast.parse((Path(__file__).parent/'model_entry.py').read_bytes());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='Bridge');init=next(x for x in cls.body if isinstance(x,ast.FunctionDef)and x.name=='__init__')
  calls=[(x.lineno,ast.unparse(x))for x in ast.walk(init)if isinstance(x,ast.Call)]
  write=next(n for n,s in calls if s.startswith('RA.persist('));gate=next(n for n,s in calls if s.startswith("need(exact_library_identity,"));self.assertLess(write,gate)

if __name__=='__main__':unittest.main()
