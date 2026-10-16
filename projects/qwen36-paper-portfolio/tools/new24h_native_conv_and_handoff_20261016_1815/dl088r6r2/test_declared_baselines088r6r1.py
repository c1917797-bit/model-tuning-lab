import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import declared_baselines088r6r1 as F
class Tests(unittest.TestCase):
 def test_linux_declared_only_missing_wronghash_refuses(self):
  with tempfile.TemporaryDirectory()as tmp:
   q=Path(tmp)/'declared';q.write_bytes(b'exact');r=dict(path=q.as_posix(),**F.fingerprint(q))
   with patch.object(sys,'platform','linux'),patch.object(F,'manifest',return_value=dict(files={'fixture':r})):
    self.assertEqual(F.checked_fixture('fixture',Path('/no-ambient-fallback')),q)
    q.write_bytes(b'wrong')
    with self.assertRaises(ValueError):F.checked_fixture('fixture',Path('/no-ambient-fallback'))
    q.unlink()
    with self.assertRaises(ValueError):F.checked_fixture('fixture',Path('/no-ambient-fallback'))
 def test_original40_tests_still_registered_plus_this2(self):
  import aggregate088r6 as A
  names=['test088r1','test088r2','test088r3','test_typed_readset088r4','test_storage088r5','test_handshake088r6','test_overlay088r6']
  self.assertEqual(unittest.defaultTestLoader.loadTestsFromNames(names).countTestCases(),40)
if __name__=='__main__':unittest.main()
