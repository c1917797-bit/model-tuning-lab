import unittest,types,sys
from compilation_budget_r45 import patch as p
class Controls(unittest.TestCase):
 def fake(self,emit=None,clock=None,max_calls=512):
  events=[];exported=types.SimpleNamespace();root=types.SimpleNamespace();calls=[]
  def compile(src,*args,**kwargs):calls.append((src,args,kwargs));return src
  exported.compile=root.compile=compile
  class J:
   def create_binder(self,backend):self.compile=exported.compile;return backend
   def _do_compile(self,key,signature,device,backend,target,constants,options,attrs,warmup):
    return self.compile(target)
  class C:
   def _init_handles(self):
    if self.module is not None:return
    self.module="loaded";return self.src
  jit=types.SimpleNamespace(JITFunction=J);compiler=types.SimpleNamespace(CompiledKernel=C,compile=compile)
  kw={"max_calls":max_calls}
  if clock:kw["clock"]=clock
  o=p.CompilationObserver(emit or events.append,**kw);p.install_bindings(o,jit,exported,compiler,root,async_mode=lambda:None,verify=False)
  return o,events,J,C,root,compile,calls
 def test_default_off_no_triton_import(self):
  before=set(sys.modules);self.assertIsNone(p.activate());self.assertEqual(set(sys.modules)-before,set())
 def test_original_arg_result_identity_and_nested_parent(self):
  o,es,J,C,root,original,calls=self.fake();j=J();j.create_binder(object());target=object()
  got=j._do_compile("key",{},0,None,target,{"task_num":4620},None,None,False)
  self.assertIs(got,target);self.assertIs(calls[0][0],target)
  begins=[e for e in es if e["event"]=="r45_compilation_begin"]
  self.assertEqual([x["kind"]for x in begins],["jit_cache_miss","compiler_api"]);self.assertEqual(begins[1]["parent_call_id"],begins[0]["call_id"])
  o.stop();self.assertIs(root.compile,original);self.assertIs(j.compile,original)
 def test_binder_alias_restored_without_compile_call(self):
  o,es,J,C,root,original,calls=self.fake();j=J();j.create_binder(None);o.stop();self.assertIs(j.compile,original);self.assertEqual(calls,[])
 def test_existing_binder_alias_is_owned_then_restored(self):
  o,es,J,C,root,original,calls=self.fake();j=J();j.compile=original;j._do_compile("k",{},0,None,4,{},None,None,False);o.stop();self.assertIs(j.compile,original)
 def test_original_exception_identity(self):
  o,es,J,C,root,original,calls=self.fake();error=KeyError("actual")
  def fail(x):raise error
  with self.assertRaises(KeyError)as seen:o.call("probe",{},fail,(object(),),{})
  self.assertIs(seen.exception,error)
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,original)
 def test_writer_failure_does_not_mask_original_error(self):
  n=[0]
  def emit(e):
   n[0]+=1
   if n[0]==2:raise OSError("sink")
  o,es,J,C,root,original,calls=self.fake(emit=emit);error=ValueError("original")
  def fail():raise error
  with self.assertRaises(ValueError)as seen:o.call("probe",{},fail,(),{})
  self.assertIs(seen.exception,error)
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,original)
 def test_successful_return_not_changed(self):
  o,*_=self.fake();obj=object();self.assertIs(o.call("probe",{},lambda x:x,(obj,),{}),obj);o.stop()
 def test_initialized_load_passthrough_without_event(self):
  o,es,J,C,root,original,calls=self.fake();k=C();k.module="ready";k.src=object();self.assertIsNone(k._init_handles());self.assertEqual(es,[]);self.assertEqual(o.skipped_initialized,1);o.stop()
 def test_load_record_does_not_change_result(self):
  o,es,J,C,root,original,calls=self.fake();k=C();k.module=None;k.src=object();self.assertIs(k._init_handles(),k.src);self.assertEqual(k.module,"loaded");o.stop()
 def test_call_bound_fails_closed_no_silent_drop(self):
  o,es,J,C,root,original,calls=self.fake(max_calls=1);o.call("one",{},lambda:None,(),{})
  with self.assertRaises(p.ObservationFailure):o.call("two",{},lambda:None,(),{})
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,original)
 def test_unknown_and_foreign_alias_rejected_not_clobbered(self):
  o,es,J,C,root,original,calls=self.fake();j=J();foreign=lambda:None;j.compile=foreign
  with self.assertRaises(p.ObservationFailure):o.bind_jit(j)
  self.assertIs(j.compile,foreign);o.stop()
 def test_slot_drift_refuses_overwrite(self):
  o,es,J,C,root,original,calls=self.fake();wrapped=root.compile;foreign=lambda:None;root.compile=foreign
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,foreign);root.compile=wrapped;o.stop()
 def test_exact_large_monotonic_ns(self):
  values=iter([2**60+1,2**60+3,2**60+12])
  o,es,*_=self.fake(clock=lambda:next(values));o.call("x",{},lambda:None,(),{})
  end=es[-1];self.assertEqual(end["original_started_ns"],str(2**60+3));self.assertEqual(end["original_duration_ns"],"9");o.stop()
 def test_nonfinite_clock_rejected_and_can_uninstall(self):
  o,es,J,C,root,original,calls=self.fake(clock=lambda:float("nan"))
  with self.assertRaises(p.ObservationFailure):o.call("x",{},lambda:None,(),{})
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,original)
 def test_interval_union_not_sum(self):
  self.assertEqual(p.interval_union_ns([(2**60+1,2**60+9),(2**60+4,2**60+12)]),11)
  with self.assertRaises(ValueError):p.interval_union_ns([(2,1)])
 def test_recursive_sink_rejected_and_restorable(self):
  holder={}
  def emit(e):holder["o"].call("sink",{},lambda:None,(),{})
  o,es,J,C,root,original,calls=self.fake(emit=emit);holder["o"]=o
  with self.assertRaises(p.ObservationFailure):o.call("x",{},lambda:None,(),{})
  with self.assertRaises(p.ObservationFailure):o.stop()
  self.assertIs(root.compile,original)
 def test_readonly_class_identity_drift(self):
  o,es,J,C,root,original,calls=self.fake();owner,name,expected=o.readonly_objects[0]
  setattr(owner,name,type("Foreign",(),{}))
  with self.assertRaises(p.ObservationFailure):o.assert_ownership()
  setattr(owner,name,expected);o.stop()
 def test_source_class_name_spoof_not_trusted(self):
  Real=type("ASTSource",(),{});Fake=type("ASTSource",(),{});src=Fake();src.signature={}
  self.assertTrue(p._source_metadata(src,Real)["unassociated"])
if __name__=="__main__":unittest.main()
