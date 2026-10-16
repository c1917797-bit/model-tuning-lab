"""Local ABI/inverse/source/response controls, no device or resource admission."""
import ast,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
from unittest import mock
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_dl004test_'+n[:-3],P/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 def test_cold_off(self):
  for n in('host_ticket.py','bind_source.py','entry.py','probe.py','client.py','consume.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(r.returncode,0,(n,r.stderr))
 def test_ast(self):
  for p in P.glob('*.py'):ast.parse(p.read_bytes(),str(p))
 def test_actual008_whole_inverse(self):
  H=load('host_ticket.py');old=Path(r'C:/Users/Huawei/AppData/Local/Temp/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py').read_text()
  m=dict(runtime_identity=dict(owner='dl-service004-new48h',run_id='dl-service004-new48h',container_prefix='dl-service004-'))
  with mock.patch.object(Path,'read_bytes',return_value=json.dumps(m).encode()):new,pairs=H.adapt(old,{}, {})
  self.assertGreater(len(pairs),20);ast.parse(new);self.assertIn('CLEANUP_TOTAL = 270',new);self.assertIn('new short-GDN complete output cap4GiB',new)
 def test_real_environment_signature(self):
  E=load('entry.py');m=dict(plugin_source={'path':'/plugin/SOURCE_MANIFEST.json'},CPU_owner_ref={'x':1},numeric_owner_ref={'x':2})
  E.current=lambda sr:m;calls=[]
  class O:
   def environment_original(self,*a):calls.append(a);return dict(a[0])
  env=E.environment(O(),{},dict(ASCEND_RT_VISIBLE_DEVICES='0,1,2,3'),Path('/source'),Path('/audit'),'run')
  self.assertEqual(len(calls),1);self.assertEqual(len(calls[0]),4);self.assertIsInstance(calls[0][0],dict)
  self.assertEqual(env['QWEN36_DELTALOG_SERVICE003_ENABLE'],'1');self.assertEqual(env['MST_MXR_SOLVE_ENABLE'],'0');self.assertNotIn('mxr_diag16_gdn_shadow',env['VLLM_PLUGINS'])
 def test_strict_response_and_bad_tokens(self):
  C=load('consume.py');request={'payload':dict(n=1,max_tokens=2,min_tokens=2,ignore_eos=True,echo=False,return_token_ids=True,temperature=0,seed=0,prompt=[1,2,3])}
  wire=('data: '+json.dumps(dict(choices=[dict(index=0,token_ids=[4,5],finish_reason='length')]))+'\n\ndata: '+json.dumps(dict(choices=[],usage=dict(prompt_tokens=3,completion_tokens=2)))+'\n\ndata: [DONE]\n\n').encode()
  self.assertEqual(C.response(request,wire)['token_ids'],[4,5])
  with self.assertRaises(ValueError):C.response(request,wire.replace(b'[4, 5]',b'[4]'))
  with self.assertRaises(ValueError):C.response(request,wire+wire)
 def test_no_MXR_admission_in_new_main(self):
  h=(P/'host_ticket.py').read_text();self.assertIn("h.run=lambda source_ref,started:leaf('run_owned.py').run(h,source_ref,pr,started)",h)
  p=(P/'prerequisite.py').read_text();self.assertIn('A.consume(ps,nr,cr)',p);self.assertNotIn('original039',p)
 def test_direct_NPU_rejected_without_manifest(self):
  r=subprocess.run([sys.executable,'-I','-B',str(P/'host_ticket.py'),'--execute'],capture_output=True,text=True);self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
