"""Source-derived copied-method/MRO controls; not real-device import evidence."""
import ast,contextvars,hashlib,importlib.util,pathlib,types,unittest
P=pathlib.Path(__file__).parent
s=importlib.util.spec_from_file_location('_binding010_controls',P/'prefix_binding.py');B=importlib.util.module_from_spec(s);s.loader.exec_module(B)
def copied_fixture():
 prefix=contextvars.ContextVar('capture',default=None);algorithm_prefix=contextvars.ContextVar('algorithm',default=None);calls=[];ctx=types.SimpleNamespace(no_compile_layers={});counts={'candidate':0}
 class Base:pass
 class Ascend(Base):
  def _forward_core(self):
   calls.append(('chunk',prefix.get(),algorithm_prefix.get()));calls.append(('recurrent',prefix.get(),algorithm_prefix.get()));return 17
 class Qwen(Base):pass
 tree=ast.parse((P/'actual_binding/patch_qwen3_5.py').read_text())
 assignments=[n for n in ast.walk(tree)if isinstance(n,ast.Assign)and ast.unparse(n)=='_GDN_PATCH_TARGET._forward_core = AscendGatedDeltaNetAttention._forward_core']
 # Actual non-310p assignment AST, not retyped generic inheritance.
 assert len(assignments)==1
 exec(compile(ast.Module(body=assignments,type_ignores=[]),'actual-patch-copy-assignment','exec'),dict(_GDN_PATCH_TARGET=Qwen,AscendGatedDeltaNetAttention=Ascend))
 native=Ascend._forward_core
 def algorithm(self):
  token=algorithm_prefix.set(self.prefix)
  try:counts['candidate']+=1;return native(self)
  finally:algorithm_prefix.reset(token)
 Ascend._forward_core=algorithm
 return prefix,ctx,counts,calls,Ascend,Qwen,algorithm
def bind_fixture(f,after=None):
 prefix,ctx,counts,calls,Ascend,Qwen,algorithm=f;seen=[]
 core,*_=B.bind(Qwen,algorithm,prefix,lambda:ctx,lambda *a:seen.append(a),after)
 obj=Qwen();obj.prefix='model.layers.0.linear_attn';ctx.no_compile_layers[obj.prefix]=obj
 return obj,core,seen
class Binding(unittest.TestCase):
 def test_actual_source_hashes_and_real_dispatch_paths(self):
  names={'gdn.py':B.RUNTIME_PINS['vllm_ascend.ops.gdn'],'patch_qwen3_5.py':B.RUNTIME_PINS['vllm_ascend.patch.worker.patch_qwen3_5'],'qwen_gdn_linear_attn.py':B.RUNTIME_PINS['vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn']}
  for name,digest in names.items():self.assertEqual(hashlib.sha256((P/'actual_binding'/name).read_bytes()).hexdigest(),digest)
  src=(P/'actual_binding/qwen_gdn_linear_attn.py').read_text();self.assertIn('self = forward_context.no_compile_layers[layer_name]',src);self.assertIn('self._forward_core(',src)
  src=(P/'actual_binding/gdn.py').read_text();self.assertIn('chunk_gated_delta_rule(',src);self.assertIn('torch.ops._C_ascend.npu_recurrent_gated_delta_rule(',src)
 def test_old_copied_method_bypasses_later_Ascend_patch_then_fixed_both_boundaries(self):
  f=copied_fixture();prefix,ctx,counts,calls,A,Q,algorithm=f;old=Q();old.prefix='real';old._forward_core();self.assertEqual(counts['candidate'],0);self.assertTrue(all(row[1:] == (None,None)for row in calls));calls.clear()
  obj,core,seen=bind_fixture(f);self.assertEqual(obj._forward_core(),17);self.assertEqual(counts['candidate'],1);self.assertEqual(A._forward_core,algorithm)
  self.assertEqual(calls,[('chunk',obj.prefix,obj.prefix),('recurrent',obj.prefix,obj.prefix)]);self.assertIsNone(prefix.get());self.assertEqual(len(seen),1)
 def test_MRO_inheritance_and_override_failclosed(self):
  f=copied_fixture();obj,core,seen=bind_fixture(f);Q=f[5]
  class Derived(Q):pass
  other=Derived();other.prefix='real2';f[1].no_compile_layers[other.prefix]=other;self.assertEqual(other._forward_core(),17)
  class Bad(Q):
   def _forward_core(self):return 'unbound'
  bad=Bad();bad.prefix='bad';f[1].no_compile_layers['bad']=bad
  with self.assertRaises(ValueError):core(bad)
 def test_bad_prefix_or_foreign_static_instance_rejected(self):
  f=copied_fixture();obj,core,seen=bind_fixture(f);obj.prefix=None
  with self.assertRaises(ValueError):obj._forward_core()
  obj.prefix='not-in-map'
  with self.assertRaises(ValueError):obj._forward_core()
  self.assertEqual(f[2]['candidate'],0)
 def test_exception_reset_and_after_callback_inside_same_scope(self):
  f=copied_fixture();events=[];obj,core,_=bind_fixture(f,lambda self,layer,result:events.append((f[0].get(),layer,result)));obj._forward_core();self.assertEqual(events,[(obj.prefix,obj.prefix,17)])
  def failed(self):raise RuntimeError('actual core failed')
  core,*_=B.bind(f[5],failed,f[0],lambda:f[1],lambda *a:None,lambda *a:events.append('should-not-run'))
  with self.assertRaises(RuntimeError):obj._forward_core()
  self.assertIsNone(f[0].get());self.assertEqual(len(events),1)
 def test_worker_and_consumer_keep_algorithm_hit_and_binding_chain(self):
  w=(P/'worker.py').read_text();c=(P/'consume.py').read_text()
  self.assertIn('binding=bind_actual_core(gdn,runtime,prefix,wr,sr,run_id)',w);self.assertNotIn('gdn.AscendGatedDeltaNetAttention._forward_core=core',w)
  self.assertIn("runtime['counts']['candidate']-before==1",w)
  for name in('core_binding','instance_binding','algorithm_counts_id','resolved_method_id'):self.assertIn(name,c)
if __name__=='__main__':unittest.main()
