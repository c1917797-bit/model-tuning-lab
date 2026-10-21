"""Explicit domain extension controls; original kernel/oracle math is untouched."""
import ast
import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_contract as G
import g3_fia_contract as D


class DomainTests(unittest.TestCase):
 def test_fixed1024_is_single_long_request_and_not_smoke_or_task_capacity(self):
  self.assertEqual(G.SCOPE,dict(schema='bole.c1-single-request-fixed1024-stream-service/v3',profile='fixed1024',prefix=131,
   request_count=1,max_steps_per_request=1023,max_output_tokens=1024,capture_protocol='every-frame-independent-CPU-ACK/v1'))
  for other in('smoke4','task5199','normalEOS'):
   with self.assertRaises(ValueError):G.scope(other)
  with self.assertRaises(ValueError):D.shape(5199)
 def test_all_long_prefixes_cover_full_private_tree_and_publication_inside_one_allocation(self):
  for length in range(131,1154):
   value=D.shape(length);private=length+3;committed=length+2
   self.assertGreaterEqual(value['scratch_kernel_pages']*128,private)
   self.assertLess((value['scratch_kernel_pages']-1)*128,private)
   self.assertGreaterEqual(value['publication_kernel_pages']*128,committed)
   self.assertLess((value['publication_kernel_pages']-1)*128,committed)
   self.assertLessEqual(private,1536);self.assertFalse(value['physical_allocation_growth_proven'])
  self.assertEqual(D.shape(1153)['KV_shape'],(10,1,128,256))
  for length in(130,1154,-1,True,131.0):
   with self.assertRaises(ValueError):D.shape(length)
 def test_page_edges_distinguish_rejected_private_child_from_selected_write_capacity(self):
  for length in range(254,1154,128):
   v=D.shape(length)
   self.assertEqual(v['scratch_kernel_pages'],v['publication_kernel_pages']+1)
   self.assertEqual(v['mask_shape'][-1],v['scratch_kernel_pages']*128)
  self.assertEqual(D.shape(131)['scratch_kernel_pages'],2)
  self.assertEqual(D.shape(1153)['scratch_kernel_pages'],10)
 def test_exact_initial_hybrid1536_owner_not_allocator_growth(self):
  good=dict(table=list(range(12,24)),physical_blocks=[1],ratio=12,physical_size=1536,kernel_size=128,use_hybrid=True)
  self.assertTrue(D.allocation(**good))
  for change in(dict(table=list(range(24,36))),dict(physical_blocks=[1,2]),dict(ratio=1),dict(physical_size=2048),dict(use_hybrid=False)):
   with self.subTest(change=change),self.assertRaises(ValueError):D.allocation(**dict(good,**change))
 def test_original_numerics_and_128_destination_transaction_stay_exact(self):
  base=P.parent/'g2_long_output'
  if not base.is_dir():base=Path(C.obj(C.obj(C.ref(P/'SOURCE_TEMPLATE.json'))['g3_predecessor']['source'])['root'])
  for name in('model_entry.py','service_bridge.py','transaction.py','eligibility.py','model_calibration131r12.py','model_process_calibration.py'):
   self.assertEqual((P/name).read_bytes(),(base/name).read_bytes(),name)
  marker='  converted=dict(kwargs);before={}'
  a,b=(P/'service_fia.py').read_text(),(base/'service_fia.py').read_text()
  self.assertEqual(a[a.index(marker):],b[b.index(marker):])
  def functions(path):return {n.name:n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)}
  original,current=functions(base/'g2_numeric.py'),functions(P/'g2_numeric.py')
  for name in original:
   a,b=copy.deepcopy(original[name]),copy.deepcopy(current[name])
   if name=='fa_math':b.body=b.body[3:]
   self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False),name)


if __name__=='__main__':unittest.main()
