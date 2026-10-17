import hashlib,json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner as O
class Controls(unittest.TestCase):
 def test_exact_complete_tiny_donor_inverse(self):
  s=(P/'owner.py').read_text();e=json.loads((P/'OWNER_EDITS.json').read_bytes());self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),e['after']['sha256'])
  for x in reversed(e['edits']):self.assertEqual(s.count(x['after']),x['count']);s=s.replace(x['after'],x['before'])
  self.assertEqual(s.encode(),(P/'DONOR_OWNER.py').read_bytes())
 def test_real_create_small_exactCPU_flags(self):
  a=O.create_argv(144,{'/ro':('/ro',False),'/out':('/out',True)},{'ASCEND_RT_VISIBLE_DEVICES':''},'software',['-I','-B','/ro/recover.py'])
  self.assertEqual(a[a.index('--memory')+1],str(2**30));self.assertEqual(a[a.index('--memory-swap')+1],str(2**30));self.assertEqual(a[a.index('--cpus')+1],'1');self.assertNotIn('--device',a);self.assertEqual(O.CAP,128*2**20)
 def test_all_real_main_defaultOFF_and_modelref_required_before_admission(self):
  for n in('owner.py','recover.py','bind22.py'):
   z=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(z.returncode,0,z.stderr);self.assertIs(json.loads(z.stdout)['enabled'],False)
  z=subprocess.run([sys.executable,'-I','-B',str(P/'owner.py'),'--execute','--source-ref','{}','--host-cpu','166','--guest-cpu','144','--output','/unapproved/path'],capture_output=True,text=True,timeout=10);self.assertNotEqual(z.returncode,0);self.assertIn('prepared R22 model template Ref required',z.stderr);self.assertNotIn('unrecognized arguments',z.stderr)
if __name__=='__main__':unittest.main()
