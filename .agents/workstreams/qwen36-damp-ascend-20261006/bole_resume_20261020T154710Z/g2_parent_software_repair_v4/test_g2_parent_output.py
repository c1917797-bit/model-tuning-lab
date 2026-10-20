"""Pure software-envelope controls; no NPU/native mathematical success evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
try:import sourceio as C
except ModuleNotFoundError:
 spec=importlib.util.spec_from_file_location('sourceio',P.parent/'g2_long_output/sourceio.py');C=importlib.util.module_from_spec(spec);sys.modules['sourceio']=C;spec.loader.exec_module(C)
import parent_software_output as O

class ParentOutputTests(unittest.TestCase):
 def value(self,sr):
  metadata=dict(schema='bole.service-installed-class-protocol-devicefree/v1',source=sr,NPU=False,actual_model_constructed=False,
   actual_batch_constructed=False,actual_scheduler_executed=False,model_ready=False,actual_torch_context_class_checked=True,
   actual_runtime_method_guards_required_after_real_load=True,classes=[{}for _ in range(6)],
   complete_native_sources_compiled=[dict(full_source_compiled=True,import_executed=False)for _ in range(6)])
  return dict(schema=O.SCHEMA,source=sr,tests=214,all_tests_passed=True,complete_readset_audited=True,NPU=False,
   actual_scheduler_executed=False,model_ready=False,actual_cold_cli=[dict(file=n,mode=m,exit_code=0)for n in O.FILES for m in([],['--help'])],
   actual_installed_metadata=metadata)
 def fixture(self,*,status=0,wrong=False,delay=False):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);parent=root/'PARENT';parent.mkdir();out=root/'OWNED';out.mkdir()
  entry=parent/'service_entry.py';v=self.value(None)
  if wrong:v['tests']=213
  code="import hashlib,json,sys,time\nfrom pathlib import Path\np=Path(__file__).parent/'SOURCE_BOUND.json';b=p.read_bytes();sr=dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())\nv="+repr(v)+"\nv['source']=sr;v['actual_installed_metadata']['source']=sr\nprint('native stdout before',flush=True)\nprint('native stderr retained',file=sys.stderr,flush=True)\n"
  code+=("time.sleep(60)\n"if delay else"print(json.dumps(v),flush=True)\nprint('non-JSON native shutdown tail',flush=True)\n")
  code+='raise SystemExit('+str(status)+')\n';entry.write_text(code)
  sr=C.write(parent/'SOURCE_BOUND.json',dict(root=str(parent),files={'service_entry.py':C.ref(entry)},service_required_sameimage_software_cases=214))
  return sr,out
 def parse(self,value,data=None):
  sr={'fixture-source':1};return O.summary(C,json.dumps(value).encode()if data is None else data,parent_source=sr,expected_tests=214)
 def test_unique_original_JSON_among_native_tail_and_invalid_utf8_is_exactly_selected(self):
  v=self.value({'fixture-source':1});data=b'native before\n'+json.dumps(v).encode()+b'\nnative tail\n\xff\n'
  got,line=self.parse(v,data);self.assertEqual(got,v);self.assertEqual(line,2)
 def test_duplicate_even_identical_expected_schema_is_rejected(self):
  v=self.value({'fixture-source':1});line=json.dumps(v).encode()
  with self.assertRaisesRegex(ValueError,'exactly one'):self.parse(v,line+b'\n'+line)
 def test_missing_schema_or_malformed_JSON_never_counts_as_pass(self):
  v=self.value({'fixture-source':1})
  for data in(b'native passed all214\n',b'{"schema":"'+O.SCHEMA.encode()+b'" invalid}',b'{"schema":"foreign"}'):
   with self.subTest(data=data),self.assertRaisesRegex(ValueError,'exactly one'):self.parse(v,data)
 def test_different_source_is_rejected(self):
  v=self.value({'foreign-source':1})
  with self.assertRaises(ValueError):self.parse(v)
 def test_wrong_count_bool_count_failed_tests_or_incomplete_readset_is_rejected(self):
  for key,value in(('tests',213),('tests',True),('all_tests_passed',False),('complete_readset_audited',False)):
   v=self.value({'fixture-source':1});v[key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.parse(v)
 def test_device_or_model_claim_flags_fail_closed(self):
  for key in('NPU','actual_scheduler_executed','model_ready'):
   v=self.value({'fixture-source':1});v[key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):self.parse(v)
 def test_missing_or_changed_native_metadata_gates_rejected(self):
  for key,value in(('source',{'foreign':1}),('actual_torch_context_class_checked',False),('complete_native_sources_compiled',[])):
   v=self.value({'fixture-source':1});v['actual_installed_metadata'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.parse(v)
 def test_all_original_cold_CLI_checks_required(self):
  for wrong in('missing','failed'):
   v=self.value({'fixture-source':1})
   if wrong=='missing':v['actual_cold_cli'].pop()
   else:v['actual_cold_cli'][0]['exit_code']=1
   with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.parse(v)
 def test_fresh_process_complete_streams_returncode_saved_before_extraction(self):
  sr,out=self.fixture();v,evidence=O.run(C,source_ref={'new-source':1},parent_source_ref=sr,expected_tests=214,evidence_root=out)
  terminal=C.obj(evidence['terminal']);self.assertEqual(terminal['returncode'],0);self.assertFalse(terminal['reused_cached_PASS'])
  self.assertIn(b'non-JSON native shutdown tail',C.checked(evidence['stdout']).read_bytes())
  self.assertIn(b'native stderr retained',C.checked(evidence['stderr']).read_bytes());self.assertEqual(v['source'],sr)
 def test_nonzero_returncode_never_uses_even_valid_summary_and_preserves_raw(self):
  sr,out=self.fixture(status=7)
  with self.assertRaises(ValueError):O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=out)
  leaf=out/'PARENT-G1-SOFTWARE';t=C.obj(C.ref(leaf/'TERMINAL.json'));self.assertEqual(t['returncode'],7)
  self.assertTrue((leaf/'stdout').is_file());self.assertFalse((leaf/'EXTRACTION.json').exists())
 def test_returncode0_bad_summary_keeps_full_raw_and_terminal_without_false_extraction(self):
  sr,out=self.fixture(wrong=True)
  with self.assertRaises(ValueError):O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=out)
  leaf=out/'PARENT-G1-SOFTWARE';self.assertEqual(C.obj(C.ref(leaf/'TERMINAL.json'))['returncode'],0)
  self.assertTrue((leaf/'stderr').is_file());self.assertFalse((leaf/'EXTRACTION.json').exists())
 def test_timeout_preserves_live_written_streams_and_observed_returncode(self):
  sr,out=self.fixture(delay=True)
  with self.assertRaises(ValueError):O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=out,timeout=.15)
  t=C.obj(C.ref(out/'PARENT-G1-SOFTWARE/TERMINAL.json'));self.assertTrue(t['timed_out']);self.assertIsInstance(t['returncode'],int)
  self.assertNotEqual(t['returncode'],0);self.assertIn(b'native stdout before',C.checked(t['stdout']).read_bytes())
 def test_exclusive_owned_leaf_refuses_cached_PASS_reuse(self):
  sr,out=self.fixture();O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=out)
  with self.assertRaises(FileExistsError):O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=out)
 def test_no_fallback_to_missing_or_symlink_output_path(self):
  sr,out=self.fixture();alias=out.parent/'ALIAS';alias.symlink_to(out,target_is_directory=True)
  model=out.parent/'MODEL';model.mkdir();cpu=model/'cpu-preflight';cpu.mkdir()
  actual,binding=O.owned_output(C,dict(output_root=str(model)),alias=cpu)
  self.assertEqual(actual,cpu);self.assertTrue(binding['actual_samefile'])
  with self.assertRaises(ValueError):O.owned_output(C,dict(output_root=str(model)),alias=out)
  for p in(out/'missing',alias):
   with self.subTest(path=p),self.assertRaises(ValueError):O.run(C,source_ref={},parent_source_ref=sr,expected_tests=214,evidence_root=p)

if __name__=='__main__':unittest.main()
