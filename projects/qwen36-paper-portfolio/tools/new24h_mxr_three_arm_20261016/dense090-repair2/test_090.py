import ast,copy,importlib.util,json,os,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C,consume090 as V,client090 as D,server090 as S
ORIGINAL=Path(C.DRIVER['path'])if sys.platform=='linux'else Path('C:/Users/Huawei/paper-piercing-handoff/NEW48H-20261014/profile-source/benchmark_shared_prefix.py')
class Tests(unittest.TestCase):
 def test_off_cold(self):
  for n in('host090.py','client090.py','server090.py','consume090.py','preflight090.py'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)['enabled'])
 def test_real_server_command(self):
  sr={'path':'/source.json','bytes':1,'sha256':'0'*64};leaf=Path('/owned/dense')
  for tokens in C.PROFILES:
   cmd=C.client_command(tokens,leaf,sr)
   self.assertEqual(cmd[cmd.index('--barrier-root')+1],str(leaf/('barriers-'+str(tokens))))
   self.assertEqual(cmd[cmd.index('--output')+1],str(leaf/('profile-%d.json'%tokens)))
   self.assertEqual(json.loads(cmd[cmd.index('--source-ref')+1]),sr)
  args=C.server_command();self.assertIn('--no-async-scheduling',args);self.assertNotIn('--async-scheduling',args);self.assertIn('--no-enable-prefix-caching',args)
  for f,v in(('--max-model-len','17408'),('--max-num-batched-tokens','16384'),('--max-num-seqs','1'),('--mamba-cache-mode','none')):self.assertEqual(args[args.index(f)+1],v)
  p=subprocess.run([sys.executable,'-I','-B',str(P/'host090.py'),'--output-contract-only','--output',C.OUTPUT_POSIX],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout)['output'],C.OUTPUT_POSIX)
  for bad in(C.OUTPUT_POSIX.replace('/','\\'),C.OUTPUT_POSIX+'-wrong','relative/output'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/'host090.py'),'--output-contract-only','--output',bad],capture_output=True,text=True);self.assertNotEqual(p.returncode,0)
 def test_warmup_actual_driver_inverse(self):
  raw=ORIGINAL.read_bytes();self.assertEqual(C.ref(ORIGINAL)['sha256'],C.DRIVER['sha256']);D.warmup_transform(raw)
  # Same check executes inside actual image from canonical absolute driver path.
 def fixture(self):
  rows=[dict(index=i,ok=True,output_tokens=1024,requested_output_tokens=1024,ttft_ms=200.,duration_s=2.)for i in range(C.MEASURED)]
  config=dict(input_tokens=2048,prefix_tokens=1024,output_tokens=1024,requests=C.MEASURED,concurrency=1,warmup_requests=C.WARMUPS,ignore_eos=True)
  return dict(config=config,summary=dict(benchmark_duration_s=6.1),results=rows,warmup_results=[dict(ok=True,output_tokens=1024,requested_output_tokens=1024)]),dict(input_tokens=2048,prompts=[[1]*2048 for _ in range(C.MEASURED+C.WARMUPS)])
 def test_request_bound_and_failure(self):
  r,i=self.fixture();v=V.analyze(r,i,2048);self.assertAlmostEqual(v['prefill_only_loose_fraction'],.2*C.MEASURED/6.1);self.assertFalse(v['candidate_gain_measured'])
  r['results'][0]['output_tokens']=1023;v=V.analyze(r,i,2048);self.assertFalse(v['complete_fixed_output']);self.assertNotIn('prefill_only_loose_fraction',v)
 def test_c16_mismatch_or_timing_reject(self):
  r,i=self.fixture();r['config']['concurrency']=16
  with self.assertRaises(ValueError):V.analyze(r,i,2048)
  r,i=self.fixture();r['results'][0]['duration_s']=100
  with self.assertRaises(ValueError):V.analyze(r,i,2048)
 def test_dense_environment_and_existing_controller(self):
  e=S.environment(dict(MXR_OBSERVERLESS_ENABLE='1',QWEN36_DELTALOG_ENABLE='1'),{},'/receipt');self.assertEqual(e['VLLM_PLUGINS'],'ascend,dense_opportunity090');self.assertNotIn('MXR_OBSERVERLESS_ENABLE',e)
  self.assertEqual(C.ref(P/'owned_create.py')['sha256'],'f6df587ee2913a62b7f70193d57896381f713f6c039151b4db3f16c4baafa7f6');self.assertEqual(C.ref(P/'worker_snapshot_owner.py')['sha256'],'bc0894c9aded1994dc0cf796537fd707d04d1c69174df5aa2d76cc90b1602bd2')
if __name__=='__main__':unittest.main()
