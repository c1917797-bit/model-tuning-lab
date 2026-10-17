"""Real Ref IO + producer/Bridge/unchanged adapter source path to native boundary.
CPU tensors only; no fake Torch schema, HAL, NPU module or model qualification.
"""
import ast,copy,json,os,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import torch
import sourceio as C,model_entry as E,adapter as A
P=Path(__file__).parent
class NativeBoundary(Exception):pass
class TorchUntilNative:
 def __getattr__(self,name):
  if name=='ops':raise NativeBoundary('real native dispatcher schema lookup required; not emulated')
  return getattr(torch,name)
class Tests(unittest.TestCase):
 def files(self,root):
  sr=C.write(root/'SOFTWARE_SOURCE.json',dict(schema='software-source-identity-fixture-only'))
  ar=C.write(root/'SOFTWARE_ABI.json',dict(source=sr,schema='bole.actual-FIA-installed-ABI/v115',NPU=False,operator_executed=False,schema_family={},argument_names=[]))
  return sr,ar
 def test_actual_producer_ref_binding_and_real_adapter_boundary(self):
  with tempfile.TemporaryDirectory()as td:
   sr,ar=self.files(Path(td));producer=dict(components=dict(paged=dict(source=sr,actual_fia_abi=ar)))
   # Execute the actual producer's reference extraction, not a handwritten
   # replacement ABI dictionary at the Bridge callsite.
   tree=ast.parse((P/'model_smoke.py').read_bytes());assign=copy.deepcopy(next(n for n in ast.walk(tree)if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='fia'for x in n.targets)))
   ns=dict(prerequisite=producer);exec(compile(ast.fix_missing_locations(ast.Module(body=[assign],type_ignores=[])),str(P/'model_smoke.py'),'exec'),ns)
   bridge=E.Bridge.__new__(E.Bridge);bridge.C=C;bridge.t=TorchUntilNative();bridge.A=A;bridge.torch_npu=None;bridge.prerequisites=producer;bridge.fia_ref=ns['fia'];bridge.fia=E.resolve_fia(C,bridge.fia_ref,producer['components']['paged']['actual_fia_abi'],sr)
   self.assertEqual(bridge.fia_ref,ar);self.assertNotEqual(bridge.fia,ar)
   owner=E.Owner('software-owned-request',1,0,131,0);ctx=E.Context(owner,(1,2,3),(131,132,132),'TREE');ctx.phase='FORWARD'
   b=dict(index=0,table=(0,1),key=torch.zeros((2,128,1,256),dtype=torch.bfloat16),value=torch.zeros((2,128,1,256),dtype=torch.bfloat16));q=torch.zeros((3,1536),dtype=torch.bfloat16);k=torch.zeros((3,256),dtype=torch.bfloat16)
   token=E.BUS.set(ctx)
   try:
    with patch.dict(os.environ,{'BOLE_PAGED_TREE_ENABLE':'1'}):
     with self.assertRaises(NativeBoundary):bridge._fa(b,q,k,k)
     trial=ctx.captures[0]['trial']
     with self.assertRaisesRegex(ValueError,'actual released CPU ABI receipt required'):A.native(bridge.t,None,trial,ar,sparse_mode=1)
   finally:E.BUS.reset(token)
   self.assertEqual(ctx.captures[0]['phase'],'BEFORE_NATIVE_PAGED_FA');self.assertEqual(ctx.order,[(0,'fa')])
   self.assertEqual(trial['status'],'STAGED');self.assertTrue(torch.equal(b['key'],torch.zeros_like(b['key'])))
   cls=next(n for n in ast.parse((P/'model_entry.py').read_bytes()).body if isinstance(n,ast.ClassDef)and n.name=='Bridge');init=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='__init__');text=ast.unparse(init)
   self.assertIn('self.fia_ref = actual_fia_abi',text);self.assertIn('self.fia = resolve_fia(',text);self.assertIn("actual_fia_abi == self.prerequisites['components']['paged']['actual_fia_abi']",text)
 def test_unknown_ref_hash_source_and_ref2_rejected_by_real_IO(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);sr,ar=self.files(root)
   for bad in(dict(path=ar['path'],sha256=ar['sha256']),dict(ar,sha256='f'*64)):
    with self.assertRaises(ValueError):E.resolve_fia(C,bad,ar,sr)
   alias=root/'SAME_BYTES_UNKNOWN_PATH.json';alias.write_bytes(C.checked(ar).read_bytes())
   with self.assertRaises(ValueError):E.resolve_fia(C,C.ref(alias),ar,sr)
   wrong=C.write(root/'WRONG_SOURCE.json',dict(schema='software-other-source'))
   with self.assertRaises(ValueError):E.resolve_fia(C,ar,ar,wrong)
   changed=dict(C.obj(ar),operator_executed=True);Path(ar['path']).write_bytes((json.dumps(changed)+'\n').encode())
   with self.assertRaises(ValueError):E.resolve_fia(C,ar,ar,sr)
 def test_default_OFF_and_cached_value_cannot_bypass_reopen(self):
  with patch.dict(os.environ,{'BOLE_PAGED_TREE_ENABLE':'0'}):
   with self.assertRaisesRegex(ValueError,'default OFF'):A.native(TorchUntilNative(),None,dict(status='STAGED'),{},sparse_mode=1)
  cls=next(n for n in ast.parse((P/'model_entry.py').read_bytes()).body if isinstance(n,ast.ClassDef)and n.name=='Bridge');fa=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='_fa');text=ast.unparse(fa)
  self.assertLess(text.index('actual_fia = resolve_fia('),text.index('self.A.native('));self.assertIn('trial, actual_fia, sparse_mode=1',text);self.assertIn('actual_fia == self.fia',text)
 def test_new_window_active_gates_and_historical_math_unchanged(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['authority_ref'],dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/RENEW24H_AUTHORITY_20261017_084320.json',bytes=3012,sha256='cdba34641b429a6132e7af5a6a88a93b63faf7d0834a9313a8b948e2a4907b6d'))
  for n in('contract090.py','bind_model.py','owned_substrate.py','worker_bootstrap.py'):
   text=(P/n).read_text(encoding='utf8');self.assertNotIn('1792220533',text);self.assertIn('1792313000',text)
  self.assertEqual(m['resources']['guest_model_GiB'],32);self.assertEqual(m['resources']['initial_RAM_GiB'],40.5)
if __name__=='__main__':unittest.main()
