"""No-resource phase/clock/raw/original-source controls; no installed ML import."""
import importlib.util,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_software_stages as S
import g2_cold_clock as K
import prepare_g2_phases_v11 as B


def original(name):
 review=P.parent/'g2_callee_contract_repair_v10'
 if review.is_dir():return review/name
 m=C.obj(B.SOURCE);return C.checked(m['files'][name])


class PhaseControls(unittest.TestCase):
 def budget(self,now=100.,wall=K.CUTOFF-10000.,start=100.,deadline=400.,phase=100.):
  clock=NS(now=now,wall=wall);fake=NS(monotonic=lambda:clock.now,time=lambda:clock.wall)
  with patch.object(S,'time',fake):b=S.Budget(phase,start,deadline,K.CUTOFF,now)
  return b,clock,fake
 def test_explicit_120_60_120_allocation_stays_inside_same_original_phase(self):
  b,clock,fake=self.budget()
  with patch.object(S,'time',fake):
   self.assertEqual(S.CAPS,dict(parent279=120.,controls=60.,metadata=120.));self.assertEqual(S.LANE_CAP,300.)
   self.assertEqual(b.remaining('parent279'),120.);self.assertEqual(b.remaining('metadata'),120.);self.assertEqual(b.remaining('controls'),60.)
 def test_source_pre_hash_time_consumes_control_allowance_without_reset(self):
  b,clock,fake=self.budget()
  with patch.object(S,'time',fake):
   clock.now=159.;self.assertEqual(b.remaining('controls'),1.);clock.now=160.
   with self.assertRaisesRegex(ValueError,'budget exhausted'):b.check()
 def test_parent_elapsed_excluded_only_from_control_lane_not_common_deadline(self):
  b,clock,fake=self.budget()
  with patch.object(S,'time',fake):
   clock.now=205.;b.exclude(100.);self.assertEqual(b.remaining('controls'),55.)
   clock.now=395.;b.exclude(120.);self.assertEqual(b.remaining('metadata'),5.)
   clock.now=400.
   with self.assertRaisesRegex(ValueError,'budget exhausted'):b.remaining('parent279')
 def test_renewed_entry_lane_301_nonfinite_and_absolute_cutoff_are_rejected(self):
  for opts in(dict(phase=101.),dict(deadline=401.),dict(now=99.),dict(deadline=float('inf')),dict(wall=K.CUTOFF-479.)):
   with self.subTest(opts=opts),self.assertRaises(ValueError):self.budget(**opts)
 def test_phase_and_absolute_wall_remaining_clamp_every_stage(self):
  b,clock,fake=self.budget(phase=-3000.)
  with patch.object(S,'time',fake):
   clock.now=399.;self.assertEqual(b.remaining('metadata'),1.)
   clock.wall=K.CUTOFF-180.5;self.assertEqual(b.remaining('parent279'),0.5)
   clock.wall=K.CUTOFF-180.
   with self.assertRaises(ValueError):b.remaining('metadata')
 def test_real_process_retains_whole_noisy_stdout_stderr_and_terminal(self):
  with tempfile.TemporaryDirectory()as tmp:
   argv=[sys.executable,'-I','-B','-c',"import sys;print('noise');print('actual stderr',file=sys.stderr)"]
   ev,cost=S.process(Path(tmp)/'stage','controls',argv,2.,source={})
   t=C.obj(ev['terminal']);self.assertEqual(t['actual_argv'],argv);self.assertEqual(t['returncode'],0);self.assertFalse(t['timed_out']);self.assertEqual(C.checked(ev['stdout']).read_bytes(),b'noise\n');self.assertEqual(C.checked(ev['stderr']).read_bytes(),b'actual stderr\n');self.assertGreaterEqual(cost,0.);self.assertTrue(t['complete_streams_retained'])
 def test_real_timeout_retains_failure_terminal_and_partial_raw_without_retry(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'stage';argv=[sys.executable,'-I','-B','-c',"import time;print('before timeout',flush=True);time.sleep(5)"]
   with self.assertRaisesRegex(ValueError,'stage failed'):S.process(root,'metadata',argv,.15,source={})
   t=C.obj(C.ref(root/'TERMINAL.json'));self.assertTrue(t['timed_out']);self.assertFalse(t['cached_PASS_reused']);self.assertIn(b'before timeout',C.checked(t['stdout']).read_bytes());self.assertNotEqual(t['returncode'],0)
 def test_real_nonzero_process_preserves_full_fault_not_caller_pass(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'stage'
   with self.assertRaises(ValueError):S.process(root,'controls',[sys.executable,'-I','-B','-c',"raise RuntimeError('actual retained fault')"],2.,source={})
   t=C.obj(C.ref(root/'TERMINAL.json'));self.assertNotEqual(t['returncode'],0);self.assertIn(b'actual retained fault',C.checked(t['stderr']).read_bytes());self.assertIsNone(t['primary'])
 def test_unique_schema_extraction_refuses_missing_duplicate_and_duplicate_key(self):
  schema='bounded.test/v1';raw=json.dumps(dict(schema=schema,all_tests_passed=True)).encode()
  self.assertEqual(S.one(b'prefix\n'+raw+b'\ntail\n',schema)['all_tests_passed'],True)
  for data in(b'only noise',raw+b'\n'+raw,b'{"schema":"bounded.test/v1","x":1,"x":2}'):
   with self.subTest(data=data),self.assertRaises(ValueError):S.one(data,schema)
 def test_original_metadata_incomplete_wrong_source_and_failed_class_receipt_rejected(self):
  good=dict(schema='bole.service-installed-class-protocol-devicefree/v1',source={},NPU=False,actual_model_constructed=False,actual_batch_constructed=False,actual_scheduler_executed=False,actual_torch_context_class_checked=True,classes=[{}]*6,complete_native_sources_compiled=[dict(full_source_compiled=True,import_executed=False)]*6)
  S.metadata_gate(good,{})
  for row in(dict(good,source={'wrong':True}),dict(good,NPU=True),dict(good,complete_native_sources_compiled=[]),dict(good,actual_torch_context_class_checked=False)):
   with self.subTest(row=row),self.assertRaises(ValueError):S.metadata_gate(row,{})
 def test_whole_host_inverse_and_actual_first_MAIN_clock_preserved(self):
  text=(P/'host_service.py').read_text();self.assertEqual(B.inverse_host(text),original('host_service.py').read_text());self.assertTrue(K.validate(text)['source_hashes_in_phase'])
  self.assertIn("summary['CPU_child']=child(cpu,'CPU'",text);self.assertIn("coldleaf=H.fresh_leaf(a.output/'candidate')",text)
  self.assertNotEqual(B.inverse_host(text+'\n# undeclared change\n'),original('host_service.py').read_text())
 def test_no_new_parent_alias_and_original_metadata_transport_resource_sources_unchanged(self):
  for n in('g2_cold_parent_output.py','g2_cold_clock.py','owned_substrate.py','owned_create.py','g2_handoff.py','g2_handoff_cold.py','g2_callee_proof.py','g2_contract.py'):
   self.assertEqual((P/n).read_bytes(),original(n).read_bytes(),n)
  body=(P/'g2_software_stages.py').read_text();self.assertIn("[sys.executable,'-B',str(C.checked(m['files']['service_metadata.py']))",body);self.assertNotIn("m['files']['service_metadata.py']],'--software'",body)
 def test_historical25_runner_never_invokes_old_software_or_adds_RW_alias(self):
  body=(P/'g2_exact_controls.py').read_text();self.assertIn("unittest.defaultTestLoader.discover",body);self.assertIn("need('sourceio'not in sys.modules",body);self.assertNotIn('subprocess',body);self.assertNotIn('parent_alias',body)
  body=(P/'g2_software_stages.py').read_text();self.assertIn("('source10',25,s['controls_source'])",body);self.assertIn("alias_exports(prior['parent_software_evidence']",body)
 def test_actual_host_allocation_uses_existing_controller_remaining_and_same_firstentry(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);sr=C.write(root/'source.json',dict(files={'g2_software_stages.py':C.ref(S.__file__)},service_required_sameimage_software_cases=320));calls=[]
   ctl=NS(out=root,created_monotonic=100.,deadline=3700.,remaining=lambda **kw:200.)
   fake=NS(monotonic=lambda:200.,time=lambda:K.CUTOFF-10000.)
   def child(ctl,label,args,limit,observe):
    calls.append((label,args,limit,observe));v=dict(schema='bole.actual-G2-three-source-staged-software-gate/v11',source=sr,phase_entry=100.,lane_start=200.,lane_deadline=400.,all_tests_passed=True,tests=320,allocation_seconds=S.CAPS,aggregate_cap_seconds=S.LANE_CAP,controls_total_elapsed_seconds=1.,elapsed_seconds=100.);(root/'SOFTWARE.stdout').write_text(json.dumps(v)+'\n');return {'actual_child':True}
   with patch.object(S,'time',fake):self.assertEqual(S.host_run(C,None,NS(child=child),ctl,sr,100.),{'actual_child':True})
   self.assertEqual(calls[0][0],'SOFTWARE');self.assertEqual(calls[0][2],200.);self.assertFalse(calls[0][3]);self.assertIn('--phase-entry',calls[0][1]);self.assertEqual(C.obj(C.ref(root/'SOFTWARE-ADMISSION.json'))['allocated_seconds'],200.)
 def test_actual_host_refuses_reset_controller_or_empty_remaining_before_child(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);sr=C.write(root/'source.json',dict(files={'g2_software_stages.py':C.ref(S.__file__)}));calls=[]
   for ctl in(NS(out=root,created_monotonic=101.,deadline=3700.,remaining=lambda **kw:300.),NS(out=root,created_monotonic=100.,deadline=3700.,remaining=lambda **kw:0.)):
    with self.assertRaises(ValueError):S.host_run(C,None,NS(child=lambda *a,**k:calls.append(a)),ctl,sr,100.)
   self.assertEqual(calls,[])
 def test_all_new_CLI_default_OFF_help_and_no_ML_import(self):
  for n in('prepare_g2_phases_v11.py','audit_source_v11.py','service_entry.py','g2_exact_controls.py','host_service.py'):
   for args in([],['--help']):
    q=subprocess.run([sys.executable,'-I','-B',str(P/n),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,n+q.stderr)
    if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))
  self.assertNotIn('torch',sys.modules);self.assertNotIn('torch_npu',sys.modules)
 def fixture_controls(self,root):
  old=root/'exact-old';old.mkdir();(old/'sourceio.py').write_bytes((P/'sourceio.py').read_bytes())
  body="import unittest,pathlib,sys\nclass Real(unittest.TestCase):\n def test_actual_selected_namespace(self):\n  import sourceio\n  self.assertEqual(pathlib.Path(sourceio.__file__).parent,pathlib.Path(__file__).parent)\n  self.assertNotIn('torch',sys.modules)\n"
  (old/'test_g2_cold_real.py').write_text(body);selected=C.write(old/'SOURCE_BOUND.json',dict(root=str(old),files={n:C.ref(old/n)for n in('sourceio.py','test_g2_cold_real.py')}))
  current=root/'current';current.mkdir();sr=C.write(current/'SOURCE_BOUND.json',dict(root=str(current),files={'g2_exact_controls.py':C.ref(P/'g2_exact_controls.py')},service_software_scope=dict(schema='bole.G2-three-source-staged-software-scope/v11',controls_source=selected,controls_source_cases=1,new_current_cases=1)))
  return sr,selected
 def test_real_only_tests_child_imports_exact_old_namespace_and_zero_skip(self):
  with tempfile.TemporaryDirectory()as tmp:
   sr,selected=self.fixture_controls(Path(tmp));q=subprocess.run([sys.executable,'-I','-B',str(P/'g2_exact_controls.py'),'--execute','--source-ref',json.dumps(sr),'--role','source10'],capture_output=True,timeout=10)
   self.assertEqual(q.returncode,0,q.stderr);v=S.one(q.stdout,'bole.actual-exact-source-only-unittest/v11');self.assertEqual(v['test_source'],selected);self.assertEqual(v['tests'],1);self.assertEqual(v['skipped'],0);self.assertFalse(v['original_software_entry_invoked']);self.assertIn(b'Ran 1 test',q.stderr)
 def test_real_only_tests_child_rejects_wrong_source_or_changed_actual_test_bytes(self):
  with tempfile.TemporaryDirectory()as tmp:
   sr,selected=self.fixture_controls(Path(tmp));base=[sys.executable,'-I','-B',str(P/'g2_exact_controls.py'),'--execute','--source-ref']
   q=subprocess.run(base+[json.dumps(dict(sr,sha256='0'*64)),'--role','source10'],capture_output=True,timeout=10);self.assertNotEqual(q.returncode,0);self.assertNotIn(b'"all_tests_passed": true',q.stdout)
   old=Path(selected['path']).parent;(old/'test_g2_cold_real.py').write_text('raise RuntimeError("changed source must never execute")\n');q=subprocess.run(base+[json.dumps(sr),'--role','source10'],capture_output=True,timeout=10);self.assertNotEqual(q.returncode,0);self.assertIn(b'whole bytes remain exact',q.stderr);self.assertNotIn(b'changed source must never execute',q.stderr)


if __name__=='__main__':unittest.main()
