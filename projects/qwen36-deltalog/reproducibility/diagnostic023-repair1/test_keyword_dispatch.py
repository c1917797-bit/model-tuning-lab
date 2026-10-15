"""Actual pinned Qwen AST dispatcher through repaired algorithm/real reader; CPU wiring only."""
import ast,hashlib,inspect,types,unittest,os
from pathlib import Path
import torch
import test_wiring as T
from qwen36_deltalog_service import builder_mirror as M,integration as W,binding as B,layout_controls as LC,runtime_helpers as H,primitives as L
QWEN=Path(os.environ.get('DELTALOG_ACTUAL_QWEN_SOURCE','C:/Users/Huawei/AppData/Local/Temp/mxr-qwen-core-binding-new48h-20261015-010/actual_binding/qwen_gdn_linear_attn.py'))
def extracted(path,name,namespace):
 tree=ast.parse(path.read_bytes());nodes=[x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name==name];assert len(nodes)==1
 module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),nodes[0]],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(path)+':exact-extraction','exec'),namespace);return namespace[name]
class Tests(unittest.TestCase):
 def run_case(self,nd,dummy=False):
  self.assertEqual(hashlib.sha256(QWEN.read_bytes()).hexdigest(),B.PINS['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn'])
  r,ls=T.fixture();M.register_layers(r,W.rows_from_native(r,T.Layer),T.Layer);meta,ids,seq,ctx=T.attach(r,ls,nd)
  for layer in ls:W._RUNNERS[id(layer)]=r
  calls=[];payload=[torch.empty(0)for _ in range(4)]
  def native(self,mixed_qkv,b,a,core_attn_out):calls.append(('native',mixed_qkv,b,a,core_attn_out));return 'native'
  signature=inspect.signature(H.execute_mixed_core)
  def helper(*args,**kw):
   bound=signature.bind(*args,**kw);calls.append(('helper',bound.arguments['mixed_qkv'],bound.arguments['b'],bound.arguments['a'],bound.arguments['core']));return 'helper'
  gdn=types.SimpleNamespace(get_forward_context=lambda:ctx)
  ns=dict(M=M,W=W,H=types.SimpleNamespace(execute_mixed_core=helper),L=L,LC=LC,gdn=gdn,torch=torch,native=native,specialized=object(),emit=lambda *a,**kw:None)
  algorithm=extracted(Path(__file__).parent/'qwen36_deltalog_service/runtime.py','algorithm',ns)
  T.Layer._forward_core=native;B.install(T.Layer,native,algorithm,lambda:ctx,lambda *a:None)
  dispatcher=extracted(QWEN,'qwen_gdn_attention_core',dict(get_forward_context=lambda:ctx,_resolve_layer_name=lambda s:s))
  token=M._DUMMY.set(dummy)
  try:dispatcher(*payload,ls[0].prefix)
  finally:M._DUMMY.reset(token)
  self.assertEqual(calls[0][0],'native'if dummy else'helper')
  self.assertTrue(all(x is y for x,y in zip(calls[0][1:],payload)))
  if not dummy:self.assertIn((ls[0].prefix,'core'),meta._deltalog018_cpu_receipt['seen'])
  with self.assertRaises(TypeError):algorithm(ls[0],mixed_qkv=payload[0],b=payload[1],a=payload[2],core_attn_ou=payload[3])
 def test_actual_keyword_pureprefill(self):self.run_case(0)
 def test_actual_keyword_mixed(self):self.run_case(1)
 def test_actual_keyword_dummy_native_route(self):self.run_case(0,True)
if __name__=='__main__':unittest.main()
