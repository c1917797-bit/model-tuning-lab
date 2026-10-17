"""Cold-program metadata/real import frontiers; not backend admission."""
import ast,copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
import payload_contract_plan as C
P=Path(__file__).resolve().parent

class Contract(unittest.TestCase):
 def actual(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());snap=json.loads((P/'payload_cold_readset_preflight.json').read_bytes());return m,snap,m['firstdecode_contract']['payload_source']
 def test_all_actual_payload_and_cold_command_layers_same_Ref(self):
  m,snap,sr=self.actual();v=C.validate(snap,sr)
  ticket=json.loads((P/'COMMANDS_FINAL.json').read_bytes())
  self.assertEqual(ticket['payload_source'],sr);self.assertEqual(ticket['postconsumer_input_ticket']['payload_source'],sr)
  self.assertEqual(m['software_cases'],181);self.assertEqual(v['source'],sr)
  self.assertEqual(m['early_software_policy']['required_payload_source'],sr);self.assertEqual(m['early_software_policy']['required_payload_cases'],26)
  early_gate=(P/'early_software_gate22.py').read_text();self.assertIn("pg['path']=='/adakv-results/PAYLOAD_TERMINAL.json'",early_gate);self.assertIn("pv['source']==policy['required_payload_source']",early_gate)
  proof=json.loads((P/'R23_CONTRACT_REBIND.json').read_bytes());self.assertIs(proof['cold_AST']['entire_cold_AST_inverse'],True)
  self.assertNotEqual(proof['cold_AST']['original_embedded_source'],proof['cold_AST']['top_original_source'])
 def test_wrong_embedded_hash_source_importroot_or_flags_rejected(self):
  m,snap,sr=self.actual()
  for defect in('hash','path','root','argv','plan'):
   bad=copy.deepcopy(snap)
   if defect in('hash','path'):
    code=bad['plan']['cold_source_tiny_loader_preflight'][-1];tree,row,old=C.literal_source(code);old['sha256'if defect=='hash'else'path']='0'*64 if defect=='hash'else'/old/SOURCE_MANIFEST.json';row.value=ast.parse(repr(old),mode='eval').body;bad['plan']['cold_source_tiny_loader_preflight'][-1]=ast.unparse(tree)
   elif defect=='root':
    tree,_,_=C.literal_source(bad['plan']['cold_source_tiny_loader_preflight'][-1]);C.path_insert(tree).args[1]=ast.Constant('/old');bad['plan']['cold_source_tiny_loader_preflight'][-1]=ast.unparse(tree)
   elif defect=='argv':bad['plan']['cold_source_tiny_loader_preflight'].insert(3,'-B')
   else:bad['plan']['source']=dict(sr,sha256='0'*64)
   with self.assertRaises(ValueError):C.validate(bad,sr)
 def test_actual_cold_prefix_fresh_I_real_imports_and_source_literal(self):
  m,snap,sr=self.actual();code=snap['plan']['cold_source_tiny_loader_preflight'][-1];tree,row,_=C.literal_source(code)
  # Run the actual complete prefix through the sr assignment, stopping before
  # the first external proof read. Source-owned mirror modules have identical
  # runtime bytes. This deliberately does not create a bound/source PASS.
  prefix=ast.Module(body=tree.body[:tree.body.index(row)+1],type_ignores=[])
  text=ast.unparse(prefix)
  bootstrap="import sys;sys.path.insert(0,"+repr(str(P/'software_dependencies/payload_contract_mirror'))+");import firstdecode_gate,firstdecode_cli\n"
  result=subprocess.run([sys.executable,'-I','-B','-c',bootstrap+text+"\nassert sr=="+repr(sr)+"\nassert 'torch' not in sys.modules and 'torch_npu' not in sys.modules\nprint('actual-prefix-and-source-literal-only')"],capture_output=True,text=True,timeout=15)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'actual-prefix-and-source-literal-only')
 def test_actual_heavy_binder_and_CPU_frontdoors_preserve_rejection(self):
  for name in('bind_source.py','host_ticket.py','probe.py'):
   z=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=15)
   self.assertEqual(z.returncode,0,z.stderr)
  z=subprocess.run([sys.executable,'-I','-B',str(P/'bind_source.py'),'--execute'],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(z.returncode,0);self.assertIn('--closed-evidence-ref',z.stderr)
  text=(P/'payload_cpu_preflight.py').read_text();self.assertIn('PLAN.validate(snapshot,sr)',text);self.assertLess(text.index('PLAN.validate(snapshot,sr)'),text.index('subprocess.run('))
  unchanged=json.loads((P/'R23_CONTRACT_REBIND.json').read_bytes())['unchanged']
  for name,r in unchanged.items():self.assertEqual(hashlib.sha256((P/name).read_bytes()).hexdigest(),r['sha256'])
  import prior_released_empty_r22 as R,types
  rows={}
  for r,proof_original_name in((R.OWNER,'RESULT.json'),(R.CLEANUP,'cleanup.json'),(R.INSPECT,'FINAL_INSPECT.json'),(R.JOURNAL,'MODEL_SNAPSHOTS_LEDGER.R22repair1.json')):
   b=(P/'software_dependencies/R22_ORIGINAL'/proof_original_name).read_bytes()
   self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']));rows[r['path']]=(r,json.loads(b))
  def obj(r):
   expected,value=rows[r['path']];C.need(r==expected,'real original metadata Ref3');return copy.deepcopy(value)
  proof=R.documents(types.SimpleNamespace(obj=obj,need=C.need));self.assertIs(proof['prior_lease_terminal'],True);self.assertIs(proof['numeric_qualified'],False)
  rows[R.OWNER['path']][1]['secondary']=['must reject changed actual FAIL']
  with self.assertRaises(ValueError):R.documents(types.SimpleNamespace(obj=obj,need=C.need))

if __name__=='__main__':unittest.main()
