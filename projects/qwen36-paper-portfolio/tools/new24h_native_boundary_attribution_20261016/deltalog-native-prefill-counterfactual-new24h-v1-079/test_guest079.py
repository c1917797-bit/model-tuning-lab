import ast,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import guest_core as G
BASE=P.parent/'deltalog-split-scale-numeric-new24h-20261016-069-repair1'
class Tests(unittest.TestCase):
 def test_actual_cold_default_OFF(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'guest_core.py')],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout),dict(enabled=False,NPU=False));self.assertNotIn('torch',G.sys.modules)
 def test_real_registered_selection_and_negative(self):
  a=dict(kind='mixed',batch=1,step=89,raw={});b=dict(kind='mixed',batch=1,step=90,raw={});v=dict(source=G.SOURCE,records=[a,b])
  self.assertEqual(G.select_records(v),[a,b])
  for records in ([a],[b,a],[a,b,b],[dict(a,batch=16),b]):
   with self.assertRaises(ValueError):G.select_records(dict(v,records=records))
  with self.assertRaises(ValueError):G.select_records(dict(v,source={}))
 def test_original_chunk_actual_keyword_ABI(self):
  p=P.parent/'mxr-boundary-oracle-audit-20261015-028/source/chunk.py';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),G.CHUNK_SHA)
  tree=ast.parse(p.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='chunk_gated_delta_rule');names={n.arg for n in fn.args.args}
  required={'q','k','v','g','beta','initial_state','cu_seqlens','use_qk_l2norm_in_kernel','output_final_state','head_first','prebuilt_meta'};self.assertLessEqual(required,names);self.assertIn('scale',names)
  calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='chunk_gated_delta_rule_fwd_h'];self.assertEqual(len(calls),1)
 def test_reuses_original_real_PCP_function_without_candidate_import(self):
  p=BASE/'qwen36_deltalog_fresh/native_fixture.py';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'e557b34be77e9e1ea85e4663df879228425eb8931b2aa162eb9e9d156b46aaff')
  m=dict(files={'qwen36_deltalog_fresh/native_fixture.py':G.ref(p)});fn=G.native_context(m);self.assertTrue(callable(fn));self.assertNotIn('vllm.distributed',sys.modules)
 def test_wrong_whole_source_bytes_reject(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'source';p.write_bytes(b'good');r=G.ref(p);G.checked(r);p.write_bytes(b'evil')
   with self.assertRaises(ValueError):G.checked(r)
 def test_flush_live_dead_and_nonprefill_real_CPU_tensors(self):
  import torch
  torch.set_num_threads(1)
  old=dict(base=torch.zeros(3,12,128,128),k_log=torch.zeros(3,4,7,128),u_log=torch.zeros(3,12,7,128),lambda_log=torch.zeros(3,12,16),decay=torch.ones(3,12,16),length=torch.full((3,12,16),2,dtype=torch.int32))
  before={k:v.clone()for k,v in old.items()};before['base'][1]+=0.25;before['k_log'][1,:,2:]=float('nan');before['u_log'][1,:,2:]=float('nan');before['decay'][1].zero_();before['length'][1].zero_()
  self.assertTrue(G.flush_join(torch,old,before,1)['dead_payload_not_compared_as_live'])
  for mutation in ('live','other','length','lambda'):
   bad={k:v.clone()for k,v in before.items()}
   if mutation=='live':bad['k_log'][1,0,0,0]=1
   if mutation=='other':bad['base'][0,0,0,0]=1
   if mutation=='length':bad['length'][1,0,0]=1
   if mutation=='lambda':bad['lambda_log'][1,0,0]=1
   with self.assertRaises(ValueError):G.flush_join(torch,old,bad,1)
 def test_original_scalar_limits_unchanged_and_no_qualification(self):
  text=(P/'guest_core.py').read_text();self.assertNotIn('STATE_LIMIT=',text);self.assertNotIn('OUTPUT_LIMIT=',text);self.assertIn('whole_correctness_qualified=False',text);self.assertIn('source_to_binary_identity_proved=False',text)
if __name__=='__main__':unittest.main()
