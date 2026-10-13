"""Round3 SOFTWARE fault injection only. Never an NPU, task or performance grant."""
import argparse,ast,copy,hashlib,importlib.util,io,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
MF=None
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=module('_dual_decision',P/'decision.py');A=module('_dual_graph_seam',P/'graph_seam.py')
def dep(kind):
 if MF:
  if kind=='oracle':r=MF['oracle']
  elif kind=='evidence':r=MF['files']['graph_evidence.py']
  else:r=json.loads(Path(MF['graph_source']['path']).read_bytes())['files']['standalone_graph.py']
  p=Path(r['path']);b=p.read_bytes();assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];return p
 root=P.parent
 return root/({'oracle':'kivi-direct-fp32-component-20261012-001/numeric/oracle.py','evidence':'kivi-channel32-graph-owner-r118-20261013-006/graph_evidence.py','standalone':'kivi-direct-fp32-fullgraph-20261012-001/standalone_graph.py'}[kind])
def fixture():
 # Explicit SYNTHETIC metadata controls; not an experiment receipt.
 g=dict(schema='kivi.direct-fp32.graph-independent1536/v1',full_outputs=1536,candidate_imported=False,writer_full_pool_byte_equal=True,reference_state='actual-captured-pending-after-append-before-AV-before-seal',metrics=dict(relative_rms=0,threshold=.005))
 a=dict(schema='kivi.active128-slot-reuse-independent/v1',all6_outputs=9216,active_k_seals=2,value_shifts=6,epochs=[1,2],byte_reference='source-exact original author CPU quant+packing',attention_reference='softmax-fp64-fsum-exp-QK-over16-V-final-A16/v1',metrics=[dict(relative_rms=0,threshold=.005)for _ in range(6)])
 return g,a
class Tests(unittest.TestCase):
 def test01_compile(self):
  for p in P.glob('*.py'):compile(p.read_bytes(),str(p),'exec',dont_inherit=True)
 def test02_default_off(self):
  for n in('host.py','guest.py','active_producer.py','consume.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(json.loads(r.stdout)['NPU'])
 def test03_original_actual_ast_inverse(self):
  E=module('_dual_real_evidence',dep('evidence'));raw=dep('standalone').read_bytes();t=A.tree(E,raw,{'writer':'SYNTHETIC'}, {'repair':'SYNTHETIC'},{'overlay':'SYNTHETIC'});self.assertIsInstance(t,ast.Module)
  original=ast.parse(raw);current=ast.unparse(t)
  self.assertIn('torch.npu.is_initialized() is False',current);self.assertIn('lane.warm_compile()',current);self.assertIn('graph.replay()',current)
 def test04_original_oracle_nan(self):
  O=module('_dual_real_oracle_nan',dep('oracle'))
  with self.assertRaises(ValueError):O.compare([float('nan')]*1536,[0.]*1536)
 def test05_original_oracle_shape(self):
  O=module('_dual_real_oracle_shape',dep('oracle'))
  with self.assertRaises(ValueError):O.compare([0.]*1535,[0.]*1536)
 def test06_original_oracle_qshape(self):
  O=module('_dual_real_oracle_qshape',dep('oracle'))
  with self.assertRaises(ValueError):O.attention({}, {}, [[0.]*256]*5,2,'bfloat16')
 def test07_full_pool_single_byte_mutation(self):
  E=module('_dual_real_pool_checker',dep('evidence'));gold=bytes(128*256*2);bad=bytearray(gold);bad[-1]=1
  E.equal_bytes(gold,gold)
  with self.assertRaises(ValueError):E.equal_bytes(bytes(bad),gold)
 def test08_original_oracle_slot_oob(self):
  O=module('_dual_real_oracle_slot',dep('oracle'));row=dict(controls=[1,0,0,16],kp=[],vp=[]);pool={k:bytes(16*128*256*2)if k.endswith('residual')else bytes(4)for k in('key_codes','key_scales','key_minima','key_residual')}
  with self.assertRaises(ValueError):O.decode(pool,row,'K',2,'bfloat16')
 def test09_candidate_reference_sharing_rejected(self):
  g,a=fixture();g['candidate_imported']=True
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test10_scope_counts_rejected(self):
  g,a=fixture();a['all6_outputs']=1536
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test11_epoch_reuse_mutation(self):
  g,a=fixture();a['epochs']=[1,1]
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test12_nan_report_rejected(self):
  g,a=fixture();a['metrics'][2]['relative_rms']=float('nan')
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test13_changed_threshold_rejected(self):
  g,a=fixture();g['metrics']['threshold']=.01
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test14_slot_mutation_receipt_rejected(self):
  g,a=fixture();g['writer_full_pool_byte_equal']=False
  with self.assertRaises(ValueError):D.numeric(g,a)
 def test15_positive_cannot_grant_model_or_perf(self):
  r=D.numeric(*fixture());self.assertFalse(r['model_ready']);self.assertFalse(r['performance_ready'])
  with self.assertRaises(ValueError):D.performance_ready(r)
 def test16_missing_graph_replay(self):
  r=dict(actual_graph_captured=True,actual_graph_replayed=False,writer_full_pool_byte_parity=True,actual_r156_writer='SYNTHETIC',full_outputs=1536)
  with self.assertRaises(ValueError):D.graph_receipt(r,'SYNTHETIC')
 def test17_no_prefix_rerun(self):
  txt=(P/'active_producer.py').read_text();self.assertNotIn('Z.attach(',txt);self.assertIn('lane.warm_compile()',txt);self.assertIn('not torch.npu.is_initialized()',txt)
 def test18_reference_does_not_import_candidate(self):
  txt=(P/'active_reference.py').read_text()
  for bad in('graph_writer','projection_plugin','import triton','import vllm'):self.assertNotIn(bad,txt)
 def test19_observer_before_create(self):
  txt=(P/'host.py').read_text();self.assertLess(txt.index('Observer.install('),txt.index('ctl.create()'))
 def test20_single1800_shared_budget(self):
  txt=(P/'host.py').read_text();self.assertIn("('graph','physical-single',a.physical,600)",txt);self.assertIn("('active','physical-active',a.physical,600)",txt);self.assertIn("phase_seconds=1800",txt)
 def test21_original_writer_identity(self):
  r=MF['actual_writer']if MF else dict(path=str(P.parent/'kivi-continuous-prefix-r156-20261013-002'/'graph_writer.py'),bytes=5636,sha256='33ab969eae661e20af86c5b88331481c789d5a3af54c795c0cf97f27b396f5f9');b=Path(r['path']).read_bytes();self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']))
def run(m=None):
 global MF;MF=m;stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests);result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
 if not result.wasSuccessful()or result.skipped:raise ValueError(stream.getvalue())
 return dict(tests=suite.countTestCases(),successful=True,scope='SOFTWARE_FAULT_INJECTION_ONLY',NPU=False,log=stream.getvalue())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--source-sha256');a=p.parse_args();m=None
 if a.source:
  raw=a.source.read_bytes();assert a.source_sha256 and hashlib.sha256(raw).hexdigest()==a.source_sha256;m=json.loads(raw)
  assert m['root']==str(P)
 elif sys.platform!='win32':raise ValueError('Linux tests require exact deployed --source and --source-sha256')
 print(json.dumps(run(m),sort_keys=True))
