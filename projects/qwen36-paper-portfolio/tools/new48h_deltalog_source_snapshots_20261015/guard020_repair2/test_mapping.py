import importlib.util,pathlib,sys,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P))
class Map(unittest.TestCase):
 def test_exact_inverse(self):
  from verify_mapping import verify
  self.assertFalse(verify()['math_changed'])
 def test_scope(self):
  import scope_adapter as S
  self.assertEqual(S.scoped_cards('numeric',True,4),(4,))
  with self.assertRaises(ValueError):S.scoped_cards('numeric',True,5)
  self.assertEqual(S.scoped_cards('native',True,4),(4,5,6,7))
