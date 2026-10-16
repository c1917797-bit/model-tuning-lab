import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import cpu116 as E
class Tests(unittest.TestCase):
 def test_real_subprocess_failure_saved_before_assert(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);s=p/'collector.py';s.write_bytes(b'import sys\nprint("original import fault",file=sys.stderr)\nraise SystemExit(3)\n');m={'files':{'collect_conv_abi.py':E.C.ref(s)}}
   with self.assertRaises(ValueError):E.collect_conv(m,p)
   r=json.loads((p/'CONV_ABI_PROCESS.json').read_bytes());self.assertEqual(r['exit_code'],3);self.assertIn('original import fault',r['stderr']);self.assertFalse((p/'ACTUAL_CONV_ABI.json').exists())
 def test_full_cpu_source_has_same_stage_conv_ref_and_exact_canonical(self):
  import ast
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['header_ref']['path'],'/usr/local/Ascend/cann-9.1.0/aarch64-linux/include/aclnnop/aclnn_fused_infer_attention_score_v3.h')
  self.assertEqual(m['header_ref']['bytes'],4091);self.assertIn('collect_conv_abi.py',m['files'])
  tree=ast.parse((P/'cpu116.py').read_bytes());calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='collect_conv'];self.assertEqual(len(calls),1)
  keywords=[k for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='dict'for k in n.keywords if k.arg=='actual_conv_abi_ref'];self.assertEqual(len(keywords),1)
if __name__=='__main__':unittest.main()
