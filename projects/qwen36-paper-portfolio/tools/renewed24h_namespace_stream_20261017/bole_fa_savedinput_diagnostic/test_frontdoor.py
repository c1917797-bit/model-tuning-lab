"""Execute new cold CLI and real predecessor consume until missing evidence."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
import plan as R,recovery_io as C
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_new_full_sourceaudit_and_actual_predecessor_consume_fail_before_write(self):
  z=subprocess.run([sys.executable,'-I','-B',str(P/'entry.py'),'--source-audit'],capture_output=True,text=True,timeout=15)
  self.assertEqual(z.returncode,0,z.stderr)
  command=json.loads((P/'COMMANDS.json').read_bytes())['sourceaudit']
  with tempfile.TemporaryDirectory()as td:
   absent=dict(path=str(Path(td)/'missing-actual-bound-source.json'),bytes=0,sha256='0'*64)
   argv=[sys.executable,'-I','-B',str(P/'owner.py'),*command[4:]]
   argv[argv.index('--source-ref')+1]=json.dumps(absent)
   z=subprocess.run(argv,capture_output=True,text=True,timeout=15)
   self.assertNotEqual(z.returncode,0);self.assertIn('ordinary exact',z.stderr);self.assertNotIn('unrecognized arguments',z.stderr)
   plan=dict(schema='bole.r17-failed-owner-math-recovery-plan/v1',original_source=R.SOURCE,failed_owner=R.OWNER,terminal=absent)
   pr=C.write(Path(td)/'plan.json',plan)
   # Real consume -> real bind -> real terminal -> real exactRef reader.
   # No mock import, fake lease, template PASS or native backend is involved.
   with self.assertRaises(ValueError):R.consume(C,pr)
  self.assertFalse((P/'SOURCE_BOUND.json').exists());self.assertFalse((P/'RECOVERY_PLAN.json').exists())
if __name__=='__main__':unittest.main()
