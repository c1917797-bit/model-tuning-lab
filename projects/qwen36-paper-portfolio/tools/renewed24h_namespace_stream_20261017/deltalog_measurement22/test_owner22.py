import ast,hashlib,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner as O
class Controls(unittest.TestCase):
 def test_whole_owner_inverse_and_unchanged_production_guard(self):
  e=json.loads((P/'OWNER_EDITS.json').read_bytes());raw=(P/'owner.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),e['after']['sha256']);s=raw.decode()
  for x in reversed(e['edits']):self.assertEqual(s.count(x['after']),x['count']);s=s.replace(x['after'],x['before'])
  self.assertEqual(s.encode(),(P/'DONOR_OWNER.py').read_bytes())
  evidence=json.loads((P/'HISTORICAL_SOURCE_IDENTITIES.json').read_bytes());self.assertEqual(hashlib.sha256((P/'readonly_binder_guard.py').read_bytes()).hexdigest(),evidence['readonly_binder_guard.py']['sha256'])
 def test_actual_create_budget_and_no_device_escalation_flags(self):
  argv=O.create_argv(144,{'/ro':('/ro',False),'/out':('/out',True)},{'ASCEND_RT_VISIBLE_DEVICES':''},'softwarefixture',['-I','-B','/ro/recover.py'])
  for key,value in(('--memory',str(2**30)),('--memory-swap',str(2**30)),('--cpus','1'),('--cpuset-cpus','144'),('--network','none')):self.assertEqual(argv[argv.index(key)+1],value)
  self.assertIn('--read-only',argv);self.assertNotIn('--device',argv);self.assertNotIn('--privileged',argv);self.assertEqual(O.CAP,4*2**20)
 def test_real_default_OFF_and_typed_missing_refs(self):
  for name in('owner.py','bind22.py','recover.py','diagnose_measurement_r22.py','entry22.py'):
   z=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=10);self.assertEqual(z.returncode,0,z.stderr);self.assertIs(json.loads(z.stdout)['enabled'],False)
  z=subprocess.run([sys.executable,'-I','-B',str(P/'bind22.py'),'--execute','--template-ref','{}'],capture_output=True,text=True,timeout=10);self.assertNotEqual(z.returncode,0);self.assertNotIn('unrecognized arguments',z.stderr)
  z=subprocess.run([sys.executable,'-I','-B',str(P/'entry22.py'),'--source-audit'],capture_output=True,text=True,timeout=10);self.assertEqual(z.returncode,0,z.stderr);self.assertIs(json.loads(z.stdout)['bound_source_checked'],False)
if __name__=='__main__':unittest.main()
