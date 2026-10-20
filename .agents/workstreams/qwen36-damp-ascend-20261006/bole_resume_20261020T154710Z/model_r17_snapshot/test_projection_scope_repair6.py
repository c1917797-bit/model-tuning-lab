"""Real sys.settrace + exact complete native module code; no fake frames/HAL."""
import importlib.util,sys,types,unittest
from pathlib import Path
import projection_trace as NEW
import test_projection_trace as BASE
from test_projection_trace import C,native,ref,S
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_old_r5_projection_observer',P/'evidence/ORIGINAL_R5_projection_trace.py')
OLD=importlib.util.module_from_spec(spec);spec.loader.exec_module(OLD)
def observer(module,layer,rows,ordinal):
 refs={str(S/n):ref(S/n)for n in('ascend_linear.py','vllm_linear.py')}
 return module.ProjectionTrace(C,layer,refs,lambda c,s,v:rows.append((c,s,v)),lambda:(ordinal[0],types.SimpleNamespace(out_proj=layer)))
def column(target,shared):
 fn=native('vllm_linear.py','ColumnParallelLinear.forward',{})
 cls=type('ActualCodeInputColumn',(),{'forward':fn});obj=cls()
 obj.quant_method=target.quant_method if shared else type(target.quant_method)()
 obj.weight=object();obj.bias=None;obj.skip_bias_add=False;obj.gather_output=False;obj.tp_size=4;obj.return_bias=True
 return obj
def run_trace(w,body):
 before=sys.gettrace()
 def trace(frame,event,arg):return trace if w.event(frame,event,arg)else None
 try:sys.settrace(trace);return body()
 finally:sys.settrace(before)
class Tests(unittest.TestCase):
 def fixture(self,shared=False):
  layer,ops,local,reduced=BASE.Tests().fixture();return layer,column(layer,shared),ops,local,reduced
 def test_actual_input_column_different_quant_instance_reproduces_R5_then_fixed(self):
  layer,inproj,ops,local,reduced=self.fixture();ordinal=[0];old=observer(OLD,layer,[],ordinal)
  with self.assertRaisesRegex(ValueError,'same active receiver/globals'):run_trace(old,lambda:inproj.forward(object()))
  layer,inproj,ops,local,reduced=self.fixture();rows=[];w=observer(NEW,layer,rows,ordinal)
  def calls():
   for c in(0,2):
    ordinal[0]=c;self.assertIs(inproj.forward(object())[0],local);self.assertIs(layer.forward(object())[0],reduced)
  run_trace(w,calls);self.assertFalse(w.finish()['qualified'])
  self.assertEqual(len(ops),6);self.assertEqual(sum(s=='quant.apply.entry'for _,s,_ in rows),2)
 def test_shared_quant_instance_still_requires_active_outproj_and_actual_layer(self):
  layer,inproj,ops,local,reduced=self.fixture(shared=True);ordinal=[0];rows=[];old=observer(OLD,layer,rows,ordinal)
  run_trace(old,lambda:inproj.forward(object()));self.assertTrue(any(s=='quant.apply.entry'for _,s,_ in rows),'old observer wrongly records input projection even with shared quant self')
  layer,inproj,ops,local,reduced=self.fixture(shared=True);rows=[];w=observer(NEW,layer,rows,ordinal)
  def calls():
   for c in(0,2):ordinal[0]=c;inproj.forward(object());layer.forward(object())
  run_trace(w,calls);w.finish();self.assertEqual(sum(s=='quant.apply.entry'for _,s,_ in rows),2);self.assertEqual(len(ops),6)
 def test_inside_target_projection_foreign_layer_rejected_before_second_GEMM(self):
  layer,inproj,ops,local,reduced=self.fixture(shared=True);rows=[];w=observer(NEW,layer,rows,[0]);quant=layer.quant_method
  f=quant.apply.__func__;oldgemm=f.__globals__['torch'].ops.vllm.unquantized_gemm;entered=[]
  def nested(*args):
   entered.append(1);return quant.apply(inproj,object(),None)
  f.__globals__['torch'].ops.vllm.unquantized_gemm=nested
  try:
   with self.assertRaisesRegex(ValueError,'same active quantized projection layer owner'):run_trace(w,lambda:layer.forward(object()))
   self.assertEqual(entered,[1]);self.assertEqual(ops,[])
  finally:f.__globals__['torch'].ops.vllm.unquantized_gemm=oldgemm
 def test_target_projection_matching_code_foreign_globals_still_rejected(self):
  layer,inproj,ops,local,reduced=self.fixture();w=observer(NEW,layer,[],[0]);f=layer.quant_method.apply.__func__
  foreign=types.FunctionType(f.__code__,dict(f.__globals__),f.__name__,f.__defaults__);foreign.__qualname__=f.__qualname__
  type(layer.quant_method).apply=foreign
  with self.assertRaisesRegex(ValueError,'same active receiver/globals'):run_trace(w,lambda:layer.forward(object()))
  self.assertEqual(ops,[])
if __name__=='__main__':unittest.main()
